using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Text.Json.Nodes;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Guidance.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Guidance.Systems;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Missiles;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Missiles.Components;
using Il2CppBrokenArrow.Client.Ecs.Render.Components;
using Il2CppDefaultEcs;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;
// NLOS trait (Osama, 12 November 2026): "if the target moves and there's no laser it loses track right? I think a special
// hook for this unit is ok" / "Any future weapon with this NLOS trait will receive the same benefits".
// Data (apply_0_8_dev7.py): an NLOS missile flies the CTL-181 precision path (TrajectoryType 200), which the game fires at
// spotted enemies without the launcher's line of sight, and has a fire-and-forget seeker (Seeker 10).
// Hook, for missiles whose ammunition ID is in UserData/FreedomArrow/nlos.json, while the original target is alive:
// - SeekerSystem.InternalUpdate prefix: the seeker keeps the original target, with line of sight and vision set and the last
//   target position set to where the target is now, so the missile follows a moving target with no laser.
// - SeekerSystem.DropCurrentTarget prefix: drops for no line of sight, not visible, too far, beyond seeker angles, shooter
//   without target and no laser spot are skipped. Target dead or a target switch drop as in vanilla.
// Both patched methods take only Entity, bool and enum parameters (no ref non-blittable struct; see MissileHitChance.cs).
// Every action is logged (FREEDOM_ARROW_NLOS lines, capped) and written to the diagnostic log.
static class NlosTrait
{
    const int MaxLog=400,Prune=2048,MaxRestore=20,MaxTries=30;
    static readonly int[] KeptReasons={5,6,7,25,26,28};
    static readonly HashSet<int> ammo=new();
    // Missile -> original target (0 = not an NLOS missile).
    static readonly Dictionary<ulong,ulong> missiles=new();
    static readonly HashSet<ulong> tracked=new();
    static readonly Dictionary<ulong,int> restores=new();
    static readonly Dictionary<ulong,int> tries=new();
    static readonly HashSet<(ulong,int)> keptLogged=new();
    static bool broken;
    static int logged,kept,updates;
    [StructLayout(LayoutKind.Sequential,Pack=4)] struct NullableEntity{public byte HasValue;public byte P1,P2,P3;public int Lo,Hi;}
    static ulong Key(Entity e)=>Unsafe.As<Entity,ulong>(ref e);
    static Entity FromKey(ulong k)=>Unsafe.As<ulong,Entity>(ref k);
    public static void Install(HarmonyLib.Harmony harmony,string root)
    {
        if(Unsafe.SizeOf<Entity>()!=8||Unsafe.SizeOf<NullableEntity>()!=12)throw new InvalidOperationException("Entity layout changed");
        var path=Path.Combine(root,"nlos.json");
        if(!File.Exists(path)){MelonLogger.Msg("FREEDOM_ARROW_NLOS not installed: no nlos.json");return;}
        foreach(var n in JsonNode.Parse(File.ReadAllText(path))!["ammunition"]!.AsArray())ammo.Add(n!.GetValue<int>());
        if(ammo.Count==0){MelonLogger.Msg("FREEDOM_ARROW_NLOS not installed: empty ammunition list");return;}
        var update=AccessTools.Method(typeof(SeekerSystem),"InternalUpdate")??throw new InvalidOperationException("SeekerSystem.InternalUpdate not found");
        var drop=AccessTools.Method(typeof(SeekerSystem),nameof(SeekerSystem.DropCurrentTarget))??throw new InvalidOperationException("SeekerSystem.DropCurrentTarget not found");
        harmony.Patch(update,prefix:new HarmonyMethod(typeof(NlosTrait),nameof(UpdateBefore)));
        harmony.Patch(drop,prefix:new HarmonyMethod(typeof(NlosTrait),nameof(DropBefore)));
        MelonLogger.Msg($"FREEDOM_ARROW_NLOS installed: ammunition {string.Join(",",ammo)} keep their seeker on a live target without line of sight or laser");
        DiagnosticLog.Write("nlos_installed",new{ammunition=ammo.ToArray()});
    }
    static void Log(string kind,string text,object data)
    {
        DiagnosticLog.Write(kind,data);
        if(++logged<=MaxLog)MelonLogger.Msg("FREEDOM_ARROW_NLOS "+text);
        else if(logged==MaxLog+1)MelonLogger.Msg($"FREEDOM_ARROW_NLOS log cap {MaxLog} reached; diagnostic log continues");
    }
    static void Fail(Exception e)
    {
        broken=true;missiles.Clear();tracked.Clear();restores.Clear();tries.Clear();keptLogged.Clear();
        MelonLogger.Error("FREEDOM_ARROW_NLOS_FAILED: vanilla seeker behaviour for this session. "+e);
        DiagnosticLog.Write("nlos_failed",new{error=e.ToString()});
    }
    static bool SeekerTarget(Entity missile,out Entity target)
    {
        target=default;
        var t=NativeEcs.Field<SeekerComponent,NullableEntity>(missile,"Target");
        if(t.HasValue==0)return false;
        ulong raw=(uint)t.Lo|((ulong)(uint)t.Hi<<32);target=FromKey(raw);
        return true;
    }
    static Vector3 Position(Entity e)=>NativeEcs.Read<ViewComponent>(e).transform.position;
    static float Distance(Entity a,Entity b)=>a.Has<ViewComponent>()&&b.Has<ViewComponent>()?Vector3.Distance(Position(a),Position(b)):-1;
    static int Id(Entity e)=>e.GetHashCode();
    // Returns the original target of an NLOS missile, or false for any other missile. Target: seeker, else the seeker's
    // original target, else the launcher's target; retried for MaxTries calls while none is alive.
    static bool NlosTarget(Entity missile,out Entity target)
    {
        target=default;ulong key=Key(missile);
        if(missiles.TryGetValue(key,out var orig))
        {
            if(orig==0)return false;
            target=FromKey(orig);return true;
        }
        if(missiles.Count>Prune)
        {
            foreach(var k in missiles.Keys.ToList())if(!FromKey(k).IsAlive){missiles.Remove(k);tracked.Remove(k);restores.Remove(k);tries.Remove(k);}
        }
        if(!missile.Has<MissileGuidanceInfoComponent>()||!missile.Has<SeekerComponent>()){missiles[key]=0;return false;}
        var info=NativeEcs.Read<MissileGuidanceInfoComponent>(missile).AmmunitionInfo;
        if(info==null||!ammo.Contains(info.Id)){missiles[key]=0;return false;}
        bool has=SeekerTarget(missile,out target)&&target.IsAlive;string from="seeker";
        if(!has)
        {
            var original=NativeEcs.Field<SeekerComponent,Entity>(missile,"OriginalTarget");
            if(original.IsAlive){target=original;from="original target";}
        }
        // 0.8.0-dev.7 game log (Osama, 12 Nov 14:53): a ground HJ-10 missile had neither, so take the launcher's own target.
        string weaponState="no shooter weapon";
        if(!target.IsAlive)
        {
            var weapon=NativeEcs.Field<MissileGuidanceInfoComponent,Entity>(missile,"ShooterWeapon");
            weaponState=!weapon.IsAlive?"shooter weapon gone":!weapon.Has<TargetComponent>()?"shooter weapon has no unit target":"shooter weapon target dead";
            if(weapon.IsAlive&&weapon.Has<TargetComponent>())
            {
                var aim=NativeEcs.Field<TargetComponent,Entity>(weapon,"Target");
                if(aim.IsAlive){target=aim;from="launcher target";}
            }
        }
        if(!target.IsAlive)
        {
            // The seeker can be empty on the first frames after launch: retry before giving up.
            tries.TryGetValue(key,out int n);tries[key]=n+1;
            if(n+1<MaxTries)return false;
            missiles[key]=0;tries.Remove(key);
            Log("nlos_no_target",$"launch ammo {info.Id} missile {Id(missile)}: no live target after {MaxTries} checks ({weaponState}); vanilla behaviour",new{ammo=info.Id,missile=Id(missile),weaponState});
            return false;
        }
        tries.Remove(key);missiles[key]=Key(target);
        Log("nlos_launch",$"launch ammo {info.Id} missile {Id(missile)} target {Id(target)} at {Distance(missile,target):0} world units; target from {from}",
            new{ammo=info.Id,missile=Id(missile),target=Id(target),distance=Distance(missile,target),from});
        return true;
    }
    public static void UpdateBefore(in Entity __0)
    {
        if(broken||!Runtime.IsApplied)return;
        try
        {
            var missile=__0;
            if(!missile.IsAlive||!NlosTarget(missile,out var target))return;
            ulong key=Key(missile);
            if(!target.IsAlive)
            {
                missiles[key]=0;
                Log("nlos_target_dead",$"missile {Id(missile)}: target {Id(target)} gone; vanilla behaviour from here",new{missile=Id(missile),target=Id(target)});
                return;
            }
            if(!SeekerTarget(missile,out var current)||Key(current)!=Key(target))
            {
                // The seeker lost or switched its target: put the original target back, at most MaxRestore times per missile.
                restores.TryGetValue(key,out int n);
                if(n>=MaxRestore)
                {
                    missiles[key]=0;
                    Log("nlos_restore_limit",$"missile {Id(missile)}: target restored {MaxRestore} times and lost again; vanilla behaviour from here",new{missile=Id(missile),target=Id(target)});
                    return;
                }
                restores[key]=n+1;
                MissilesHelper.SetNewTargetToMissile(ref missile,ref target,true,true);
                Log("nlos_reacquired",$"missile {Id(missile)}: seeker target restored to {Id(target)} at {Distance(missile,target):0} world units",new{missile=Id(missile),target=Id(target),distance=Distance(missile,target)});
            }
            NativeEcs.WriteField<SeekerComponent,bool>(missile,"HasLOSOnCurrentTarget",true);
            NativeEcs.WriteField<SeekerComponent,bool>(missile,"HasVisionOnCurrentTarget",true);
            if(target.Has<ViewComponent>())NativeEcs.WriteField<SeekerComponent,Vector3>(missile,"LastTargetPosition",Position(target));
            updates++;
            if(tracked.Add(key))Log("nlos_tracking",$"missile {Id(missile)}: tracking target {Id(target)} (line of sight and vision held by the NLOS trait)",new{missile=Id(missile),target=Id(target)});
        }
        catch(Exception e){Fail(e);}
    }
    public static bool DropBefore(in Entity __0,bool __2,TargetRemoveReason __3)
    {
        if(broken||!Runtime.IsApplied||__2)return true;
        try
        {
            var missile=__0;int reason=(int)__3;
            if(!missile.IsAlive||!NlosTarget(missile,out var target))return true;
            if(!target.IsAlive||Array.IndexOf(KeptReasons,reason)<0)
            {
                Log("nlos_drop_allowed",$"missile {Id(missile)}: drop reason {__3} ({reason}) allowed",new{missile=Id(missile),reason,targetAlive=target.IsAlive});
                return true;
            }
            kept++;
            if(keptLogged.Count>Prune)keptLogged.Clear();
            if(keptLogged.Add((Key(missile),reason)))Log("nlos_lock_kept",$"missile {Id(missile)}: drop reason {__3} ({reason}) skipped, target {Id(target)} at {Distance(missile,target):0} world units (kept {kept}, tracked updates {updates})",
                new{missile=Id(missile),reason,target=Id(target),distance=Distance(missile,target),kept});
            return false;
        }
        catch(Exception e){Fail(e);return true;}
    }
}

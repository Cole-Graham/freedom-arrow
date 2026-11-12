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
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems;
using Il2CppBrokenArrow.Client.Ecs.FogOfWar;
using Il2CppBrokenArrow.Client.Ecs.FogOfWar.Components;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppNetworkCommon.Enums;
using Il2CppBrokenArrow.Client.Ecs.Render.Components;
using Il2CppDefaultEcs;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;
// NLOS trait (Osama, 12 November 2026): "if the target moves and there's no laser it loses track right? I think a special
// hook for this unit is ok" / "Any future weapon with this NLOS trait will receive the same benefits".
// 0.8.0-dev.14 (Osama: "the HJ-10 should be the same bradley hellfire weapon but doesn't require line of sight"): the
// missile is the ground Hellfire again (TrajectoryType 110, seeker 50). Two parts, both driven by nlos.json:
// - Firing: FogOfWarUnit.Update postfix. That update rebuilds the unit's FogOfWarComponent.Shootable set from its own line
//   of sight; for a unit carrying a "fire_weapons" launcher the hook then adds every enemy (the update's target list) that
//   any unit of the shooter's side sees (target VisibleTo) and that is within the game's own shooting distance for the
//   launcher's selected ammunition (BattleSystemHelpers.GetAmmoShootingDistance). Patched method takes classes only.
// - Missile, for ammunition IDs in "ammunition", while the original target is alive:
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
    static bool broken,fireBroken;
    // Firing part: unit -> (launcher weapon entity, 0 = not an NLOS shooter), and the last added targets per unit.
    static readonly HashSet<int> fireWeapons=new(),fireUnits=new();
    static readonly Dictionary<ulong,ulong> shooters=new();
    static readonly Dictionary<ulong,(float time,List<Entity> targets)> fireCache=new();
    static readonly HashSet<(ulong,ulong)> fireLogged=new();
    static int mainThread,fireAdds,offThread;
    static EntitySet weaponSet;static World weaponWorld,fireWorld;
    const float Refresh=0.5f;
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
        var cfg=JsonNode.Parse(File.ReadAllText(path))!;
        foreach(var n in cfg["fire_weapons"]?.AsArray()??new JsonArray())fireWeapons.Add(n!.GetValue<int>());
        foreach(var n in cfg["fire_units"]?.AsArray()??new JsonArray())fireUnits.Add(n!.GetValue<int>());
        if(fireWeapons.Count>0&&fireUnits.Count>0)
        {
            mainThread=Environment.CurrentManagedThreadId;
            var fog=AccessTools.Method(typeof(FogOfWarUnit),nameof(FogOfWarUnit.Update))??throw new InvalidOperationException("FogOfWarUnit.Update not found");
            harmony.Patch(fog,postfix:new HarmonyMethod(typeof(NlosTrait),nameof(FogAfter)));
            MelonLogger.Msg($"FREEDOM_ARROW_NLOS fire hook installed: units {string.Join(",",fireUnits)} with launchers {string.Join(",",fireWeapons)} may shoot enemies their side has spotted, within launcher range, without own line of sight");
        }
        MelonLogger.Msg($"FREEDOM_ARROW_NLOS installed: ammunition {string.Join(",",ammo)} keep their seeker on a live target without line of sight or laser");
        DiagnosticLog.Write("nlos_installed",new{ammunition=ammo.ToArray()});
    }
    // Finds the NLOS launcher on a unit (once per unit).
    static Entity Launcher(Entity unit)
    {
        ulong key=Key(unit);
        if(shooters.TryGetValue(key,out var w))return FromKey(w);
        shooters[key]=0;
        if(!unit.Has<UnitComponent>()||!fireUnits.Contains(NativeEcs.Read<UnitComponent>(unit).UnitData.Id))return default;
        var world=ShootingSystem._gameContext;if(world==null)return default;
        if(weaponSet==null||weaponWorld==null||weaponWorld.Pointer!=world.Pointer){weaponWorld=world;weaponSet=world.GetEntities().With<WeaponComponent>().AsSet();}
        var arr=weaponSet._entities;int n=Math.Min(weaponSet.Count,arr?.Length??0);
        for(int i=0;i<n;i++)
        {
            var e=arr![i];if(!e.IsAlive)continue;
            var wc=NativeEcs.Read<WeaponComponent>(e);
            if(wc?.WeaponInfo==null||!fireWeapons.Contains(wc.WeaponInfo.Id))continue;
            if(Key(wc.GetUnitEntity())!=key)continue;
            shooters[key]=Key(e);
            Log("nlos_fire_unit",$"fire: unit {Id(unit)} ({NativeEcs.Read<UnitComponent>(unit).UnitData.HUDName}) launcher {wc.WeaponInfo.HUDName} found",new{unit=Id(unit),weapon=wc.WeaponInfo.Id});
            return e;
        }
        Log("nlos_fire_unit_missing",$"fire: unit {Id(unit)} has no NLOS launcher among {n} weapons",new{unit=Id(unit)});
        return default;
    }
    static bool Spotted(Entity target,TeamSide side)
    {
        if(!target.Has<FogOfWarComponent>())return false;
        var seen=NativeEcs.Read<FogOfWarComponent>(target).VisibleTo;if(seen==null)return false;
        foreach(var o in seen)if(o.IsAlive&&o.Has<UnitComponent>()&&NativeEcs.Read<UnitComponent>(o).Owner?.TeamSide==side)return true;
        return false;
    }
    public static void FogAfter(FogOfWarUnit __instance,Il2CppSystem.Collections.Generic.HashSet<FogOfWarUnit> __0)
    {
        if(fireBroken||!Runtime.IsApplied||__instance==null)return;
        try
        {
            var world=ShootingSystem._gameContext;
            if(world!=null&&(fireWorld==null||fireWorld.Pointer!=world.Pointer)){fireWorld=world;shooters.Clear();fireCache.Clear();fireLogged.Clear();}
            var unit=__instance.UnitEntity;
            if(!unit.IsAlive)return;
            ulong key=Key(unit);
            if(shooters.TryGetValue(key,out var known)&&known==0)return;
            if(Environment.CurrentManagedThreadId!=mainThread){if(++offThread==1)Log("nlos_fire_off_thread","fire: fog update ran off the main thread; firing part skipped there",new{offThread});return;}
            var weapon=Launcher(unit);if(!weapon.IsAlive||!unit.Has<FogOfWarComponent>())return;
            var shootable=NativeEcs.Read<FogOfWarComponent>(unit).Shootable;if(shootable==null)return;
            float now=Time.time;
            if(!fireCache.TryGetValue(key,out var cache)||now-cache.time>=Refresh||__0==null)
            {
                var list=new List<Entity>();
                var ammoInfo=NativeEcs.Read<WeaponComponent>(weapon).SelectedAmmunition;
                var side=NativeEcs.Read<UnitComponent>(unit).Owner?.TeamSide;
                if(ammoInfo!=null&&side!=null&&__0!=null)
                {
                    var here=Position(unit);
                    foreach(var t in __0)
                    {
                        var e=t?.UnitEntity??default;
                        if(!e.IsAlive||!e.Has<ViewComponent>())continue;
                        float range=BattleSystemHelpers.GetAmmoShootingDistance(unit,e,ammoInfo);
                        float dist=Vector3.Distance(here,Position(e));
                        if(dist>range||!Spotted(e,side.Value))continue;
                        list.Add(e);
                        if(fireLogged.Count<4096&&fireLogged.Add((key,Key(e))))Log("nlos_fire_target",$"fire: unit {Id(unit)} may shoot spotted enemy {Id(e)} at {dist:0} (shooting distance {range:0}); own line of sight {(shootable.Contains(e)?"yes":"no")}",new{unit=Id(unit),target=Id(e),dist,range,ownLos=shootable.Contains(e)});
                    }
                }
                cache=(now,list);fireCache[key]=cache;
            }
            foreach(var e in cache.targets)if(e.IsAlive&&!shootable.Contains(e)){shootable.Add(e);fireAdds++;}
        }
        catch(Exception e){fireBroken=true;fireCache.Clear();MelonLogger.Error("FREEDOM_ARROW_NLOS_FIRE_FAILED: vanilla line of sight for this session. "+e);DiagnosticLog.Write("nlos_fire_failed",new{error=e.ToString()});}
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
            // 0.8.0-dev.11 log (15:09): MissileGuidanceInfoComponent.ShooterWeapon was empty on every HJ-10 missile, so also try the warhead's.
            var weapon=NativeEcs.Field<MissileGuidanceInfoComponent,Entity>(missile,"ShooterWeapon");string via="guidance";
            if(!weapon.IsAlive&&missile.Has<WarheadComponent>()){weapon=NativeEcs.Field<WarheadComponent,Entity>(missile,"ShooterWeapon");via="warhead";}
            if(!weapon.IsAlive)weaponState="shooter weapon not found (guidance and warhead links empty)";
            else if(weapon.Has<TargetComponent>())
            {
                var aim=NativeEcs.Field<TargetComponent,Entity>(weapon,"Target");
                if(aim.IsAlive){target=aim;from="launcher target via "+via;}
                else weaponState="shooter weapon target dead (via "+via+")";
            }
            else weaponState=(weapon.Has<GroundTargetComponent>()?"shooter weapon is firing at a ground position, not a unit":"shooter weapon has no target component")+" (via "+via+")";
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

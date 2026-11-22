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
// - Firing: FogOfWarUnit.Update postfix (0.9.0-dev.37: FogOfWarWorker update postfix, once per worker per frame; see Install). That update rebuilds the unit's FogOfWarComponent.Shootable set from its own line
//   of sight; for a unit carrying a "fire_weapons" launcher the hook then adds every enemy (the update's target list) that
//   any unit of the shooter's side sees (target VisibleTo) and that is within the game's own shooting distance for the
//   launcher's selected ammunition (BattleSystemHelpers.GetAmmoShootingDistance). Patched method takes classes only.
// - Missile, for ammunition IDs in "ammunition", while the original target is alive:
// - SeekerSystem.InternalUpdate prefix: the seeker keeps the original target, with line of sight and vision set and the last
//   target position set to where the target is now, so the missile follows a moving target with no laser.
// - SeekerSystem.DropCurrentTarget prefix: drops for no line of sight, not visible, too far, beyond seeker angles, shooter
//   without target and no laser spot are skipped. Target dead or a target switch drop as in vanilla. 0.9.4 batch: any other drop
//   hands the missile to the game for good, and a seeker that switches to another live target keeps it (player guidance).
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
            // 0.9.0-dev.37: one call per fog worker per frame instead of one per unit (FogOfWarUnit.Update ran ~7,500 times a second in a 5v5).
            // The only native caller of FogOfWarUnit.Update (RVA 0x6A2CC0 in 1.2.2.1) is FogOfWarWorker.IFogOfWarWorker.Update (0x6A3FB0),
            // which calls it for each of the worker's own units with the worker's enemy set; our postfix on the worker runs right after
            // those per-unit updates, so the NLOS targets are added at the same point in the frame as before.
            var fog=AccessTools.Method(typeof(FogOfWarWorker),"BrokenArrow_Client_Ecs_FogOfWar_IFogOfWarWorker_Update")??throw new InvalidOperationException("FogOfWarWorker.IFogOfWarWorker.Update not found");
            harmony.Patch(fog,postfix:new HarmonyMethod(typeof(NlosTrait),nameof(WorkerAfter)));
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
    // Health counters (FREEDOM_ARROW_HOOK_HEALTH, HookHealth.cs): worker calls, NLOS units found, units processed, targets added.
    public static long WorkerCalls,UnitsProcessed;public static int NlosUnits=>workerUnits.Values.Sum(v=>v.units.Count);
    public static int FireAdds=>fireAdds;public static bool FireBroken=>fireBroken;public static bool FireInstalled=>mainThread!=0;
    static readonly Dictionary<IntPtr,(float at,List<FogOfWarUnit> units)> workerUnits=new();
    const float UnitScan=1f;
    // Once per worker per frame. Every second the worker's own units are scanned for NLOS shooters (Launcher caches the answer per unit);
    // in between only those units are processed, with the worker's enemy set as the target list (the same list FogOfWarUnit.Update gets).
    public static void WorkerAfter(FogOfWarWorker __instance)
    {
        if(fireBroken||!Runtime.IsApplied||__instance==null)return;
        WorkerCalls++;
        try
        {
            var world=ShootingSystem._gameContext;
            if(world!=null&&(fireWorld==null||fireWorld.Pointer!=world.Pointer)){fireWorld=world;shooters.Clear();fireCache.Clear();fireLogged.Clear();workerUnits.Clear();}
            if(Environment.CurrentManagedThreadId!=mainThread){if(++offThread==1)Log("nlos_fire_off_thread","fire: fog worker ran off the main thread; firing part skipped there",new{offThread});return;}
            float now=Time.time;var ptr=__instance.Pointer;
            if(!workerUnits.TryGetValue(ptr,out var wu)||now-wu.at>=UnitScan)
            {
                var list=new List<FogOfWarUnit>();var team=__instance._teamUnits;
                if(team!=null)foreach(var u in team)
                {
                    if(u==null)continue;var e=u.UnitEntity;if(!e.IsAlive)continue;
                    if(shooters.TryGetValue(Key(e),out var known)&&known==0)continue;
                    if(Launcher(e).IsAlive)list.Add(u);
                }
                wu=(now,list);workerUnits[ptr]=wu;
            }
            if(wu.units.Count==0)return;
            var enemies=__instance._enemyUnits;
            foreach(var u in wu.units){UnitsProcessed++;Apply(u,enemies);}
        }
        catch(Exception e){fireBroken=true;fireCache.Clear();MelonLogger.Error("FREEDOM_ARROW_NLOS_FIRE_FAILED: vanilla line of sight for this session. "+e);DiagnosticLog.Write("nlos_fire_failed",new{error=e.ToString()});}
    }
    // The former FogOfWarUnit.Update postfix body, for one NLOS unit (called from WorkerAfter only).
    static void Apply(FogOfWarUnit __instance,Il2CppSystem.Collections.Generic.HashSet<FogOfWarUnit> __0)
    {
        if(__instance==null)return;
        {
            var unit=__instance.UnitEntity;
            if(!unit.IsAlive)return;
            ulong key=Key(unit);
            if(shooters.TryGetValue(key,out var known)&&known==0)return;
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
    const float LaserSpotRadius=60f;
    static EntitySet unitSet;static World unitWorld;
    // The live unit nearest p within r, not on side notSide (the shooter's side, when known).
    static Entity UnitNear(Vector3 p,float r,TeamSide? notSide)
    {
        var world=ShootingSystem._gameContext;if(world==null)return default;
        if(unitSet==null||unitWorld==null||unitWorld.Pointer!=world.Pointer){unitWorld=world;unitSet=world.GetEntities().With<UnitComponent>().AsSet();}
        var arr=unitSet._entities;int n=Math.Min(unitSet.Count,arr?.Length??0);Entity best=default;float bd=r;
        for(int i=0;i<n;i++)
        {
            var e=arr![i];if(!e.IsAlive||!e.Has<ViewComponent>())continue;
            if(notSide!=null&&NativeEcs.Read<UnitComponent>(e).Owner?.TeamSide==notSide)continue;
            float d=Vector3.Distance(Position(e),p);if(d<bd){bd=d;best=e;}
        }
        return best;
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
        string weaponState="no shooter weapon";TeamSide? side=null;
        if(!target.IsAlive)
        {
            // 0.8.0-dev.11 log (15:09): MissileGuidanceInfoComponent.ShooterWeapon was empty on every HJ-10 missile, so also try the warhead's.
            var weapon=NativeEcs.Field<MissileGuidanceInfoComponent,Entity>(missile,"ShooterWeapon");string via="guidance";
            if(!weapon.IsAlive&&missile.Has<WarheadComponent>()){weapon=NativeEcs.Field<WarheadComponent,Entity>(missile,"ShooterWeapon");via="warhead";}
            if(weapon.IsAlive&&weapon.Has<WeaponComponent>())
            {
                var su=NativeEcs.Read<WeaponComponent>(weapon)?.GetUnitEntity()??default;
                if(su.IsAlive&&su.Has<UnitComponent>())side=NativeEcs.Read<UnitComponent>(su).Owner?.TeamSide;
            }
            if(!weapon.IsAlive)weaponState="shooter weapon not found (guidance and warhead links empty)";
            else if(weapon.Has<TargetComponent>())
            {
                var aim=NativeEcs.Field<TargetComponent,Entity>(weapon,"Target");
                if(aim.IsAlive){target=aim;from="launcher target via "+via;}
                else weaponState="shooter weapon target dead (via "+via+")";
            }
            else weaponState=(weapon.Has<GroundTargetComponent>()?"shooter weapon is firing at a ground position, not a unit":"shooter weapon has no target component")+" (via "+via+")";
        }
        // 0.9.5-dev.5 (Osama 22 Nov 2026 00:0x PST: "all the other laser guided cruise missiles are broken"). dev.4 flight trace: a cruise round fired
        // at a lased tank has no seeker target, only LastTargetPosition = the lased tank, and the cruise path then flies straight north and never
        // turns (CH-901 2687, CTL-181 2762, QN-502 2761 at 00:01:11-21). Lock it on the enemy unit nearest that laser spot.
        if(!target.IsAlive&&missile.Has<SeekerComponent>())
        {
            var spot=NativeEcs.Field<SeekerComponent,Vector3>(missile,"LastTargetPosition");
            if(spot!=Vector3.zero)
            {
                var u=UnitNear(spot,LaserSpotRadius,side);
                if(u.IsAlive)
                {
                    target=u;from=$"unit {Vector3.Distance(Position(u),spot):0} from the laser spot";
                    // dev.5 trace (00:21:47-55): locked on the lased tank, the rounds climbed, turned, then froze in the air at cruise height. The
                    // cruise path plans with LaunchHorizontalDistance, set at launch from the target; fired at a laser spot it has none. Give it
                    // the real horizontal distance when it is missing.
                    var lhd=NativeEcs.Field<MissileGuidanceInfoComponent,float>(missile,"LaunchHorizontalDistance");
                    var mp=Position(missile);var tp=Position(u);float hd=new Vector2(tp.x-mp.x,tp.z-mp.z).magnitude;
                    if(!(lhd>1f)){NativeEcs.WriteField<MissileGuidanceInfoComponent,float>(missile,"LaunchHorizontalDistance",hd);from+=$", launch distance {lhd:0.#} -> {hd:0}";}
                }
                else weaponState+=$"; no enemy unit within {LaserSpotRadius:0} of the laser spot ({spot.x:0},{spot.z:0})";
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
    // Flight trace (Osama 21 Nov 2026 23:5x PST, thread 1567745029781454889: lased NLOS missiles "chasing something off the edge of the map").
    // The four NLOS cruise rounds (HJ-10, QN-502, CTL-181 and the Blood Wolves' CH-901, which is not on the keep-lock list) log position, seeker
    // target, last target position and line of sight every TraceStep s for their first TraceLines steps; at most TraceMissiles missiles a session.
    static readonly HashSet<int> traceAmmo=new(){2009623,2009651,2018321,2018448};
    static readonly Dictionary<ulong,(int ammo,float start,float next,int n)> traces=new();
    const int TraceLines=40,TraceMissiles=40;const float TraceStep=0.5f;
    static int tracedMissiles;static bool traceBroken;
    static void Trace(Entity missile)
    {
        if(traceBroken)return;
        try
        {
            ulong key=Key(missile);float now=Time.time;
            if(!traces.TryGetValue(key,out var tr))
            {
                if(traces.Count>Prune)foreach(var k in traces.Keys.ToList())if(!FromKey(k).IsAlive)traces.Remove(k);
                int id=0;
                if(missile.Has<MissileGuidanceInfoComponent>()){var info=NativeEcs.Read<MissileGuidanceInfoComponent>(missile).AmmunitionInfo;if(info!=null)id=info.Id;}
                if(!traceAmmo.Contains(id)||tracedMissiles>=TraceMissiles){traces[key]=(0,0,0,0);return;}
                tracedMissiles++;tr=(id,now,now,0);
            }
            if(tr.ammo==0||now<tr.next||tr.n>=TraceLines||!missile.Has<SeekerComponent>())return;
            string tgt="none";float tdist=-1;
            if(SeekerTarget(missile,out var t)&&t.IsAlive){tgt=Id(t).ToString();tdist=Distance(missile,t);}
            var last=NativeEcs.Field<SeekerComponent,Vector3>(missile,"LastTargetPosition");
            bool los=NativeEcs.Field<SeekerComponent,bool>(missile,"HasLOSOnCurrentTarget");
            var pos=missile.Has<ViewComponent>()?Position(missile):Vector3.zero;
            string g="";
            if(missile.Has<MissileGuidanceInfoComponent>())
                g=$" | launch dist {NativeEcs.Field<MissileGuidanceInfoComponent,float>(missile,"LaunchHorizontalDistance"):0.#} lofting {NativeEcs.Field<MissileGuidanceInfoComponent,bool>(missile,"CurrentlyLofting")} dive at {NativeEcs.Field<MissileGuidanceInfoComponent,float>(missile,"DiveStartDistance"):0.#} loft start {NativeEcs.Field<MissileGuidanceInfoComponent,Vector3>(missile,"LoftStartPosition")}";
            MelonLogger.Msg($"FREEDOM_ARROW_NLOS_TRACE ammo {tr.ammo} missile {Id(missile)} t+{now-tr.start:0.0}s pos ({pos.x:0},{pos.y:0},{pos.z:0}) seeker target {tgt} at {tdist:0} last target pos ({last.x:0},{last.y:0},{last.z:0}) los {los}{g}");
            DiagnosticLog.Write("nlos_trace",new{ammo=tr.ammo,missile=Id(missile),t=now-tr.start,x=pos.x,y=pos.y,z=pos.z,target=tgt,tdist,lx=last.x,ly=last.y,lz=last.z,los});
            traces[key]=(tr.ammo,tr.start,now+TraceStep,tr.n+1);
        }
        catch(Exception e){traceBroken=true;MelonLogger.Warning("FREEDOM_ARROW_NLOS_TRACE off: "+e.Message);}
    }
    public static void UpdateBefore(in Entity __0)
    {
        if(broken||!Runtime.IsApplied)return;
        Trace(__0);
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
            bool hasCurrent=SeekerTarget(missile,out var current);
            if(hasCurrent&&current.IsAlive&&Key(current)!=Key(target))
            {
                // 0.9.4 batch (Osama 21 Nov 2026 21:3x PST, thread 1572407822849810463: "many bug reports with the HJ-10 and other loitering munitions.
                // Guiding them makes them go erratic"). Player logs 19-22 Nov: HJ-10 and QN-502 missiles were snapped back to their first target
                // about 3 times each and 1 in 7 hit the 20-restore limit, while the CTL-181 had none. A seeker that has switched to another live target
                // (the player re-guided it, or a new laser spot) now keeps that target, and it becomes the target the trait holds.
                missiles[key]=Key(current);restores.Remove(key);
                Log("nlos_retarget",$"missile {Id(missile)}: seeker switched from {Id(target)} to {Id(current)}; the new target is kept",new{missile=Id(missile),from=Id(target),to=Id(current)});
                target=current;
            }
            else if(!hasCurrent||Key(current)!=Key(target))
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
                // 0.9.4 batch (Osama 21 Nov 2026 21:3x PST: "Guiding them makes them go erratic"). An allowed drop now hands the missile to the
                // game for good. Before, the seeker update put the old target back on the next frame and the game dropped it again: player logs
                // show HJ-10 / QN-502 missiles pulled back and forth 20 frames in a row (drop reason Unspecified after the launcher's target changed).
                missiles[Key(missile)]=0;
                Log("nlos_drop_allowed",$"missile {Id(missile)}: drop reason {__3} ({reason}) allowed; vanilla guidance from here",new{missile=Id(missile),reason,targetAlive=target.IsAlive});
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

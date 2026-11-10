using System.Collections.Concurrent;
using System.Diagnostics;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Guidance.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Guidance.Systems;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppBrokenArrow.Shared.Ecs.Enums;
using Il2CppBrokenArrow.Client.Ecs.GNetwork.Components.Ownership;
using Il2CppDefaultEcs;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;

// Passive LateUpdate reader. NEVER patch targeting/shooting/scoring methods, invoke
// combat helpers, inspect the shared TargetSearchHelper scratch list, or write ECS.
static class GroundAaLog
{
    const long MaxBytes=16*1024*1024;
    const int MaxLines=60000,MaxPending=2048,MaxKeys=8192,WeaponBatch=16,DiscoveryBatch=64,ThreatCap=256;
    const float Interval=.2f,ThreatAge=2f;
    const double WorkBudgetMs=3;
    static readonly ConcurrentQueue<string> Pending=new();
    static readonly ConcurrentQueue<Entity> ShotSignals=new();
    static readonly Dictionary<string,(string state,float time)> Last=new();
    static readonly Dictionary<ulong,Threat> Threats=new();
    sealed class Threat
    {
        public Entity Entity;public int Type;public int? Ammo;public string Team;public Vector3 Position;public float Seen;
        public Threat(Entity entity,int type,int? ammo,string team,Vector3 position,float seen)
        {Entity=entity;Type=type;Ammo=ammo;Team=team;Position=position;Seen=seen;}
    }
    static EntitySet weaponSet,unitSet;
    static World world;
    static StreamWriter writer;
    static long bytes;
    static int lines,dropped,sequence,weaponCursor,unitCursor;
    static bool off;
    static float nextSample,nextMetrics;
    static long samples,scanned,rounds;
    static double maxWorkMs;
    static ulong Key(Entity e)=>Unsafe.As<Entity,ulong>(ref e);
    public static void Install(string root)
    {
        if(Unsafe.SizeOf<Entity>()!=8)throw new InvalidOperationException("Entity layout changed");
        string dir=Path.Combine(root,"diagnostics");Directory.CreateDirectory(dir);
        foreach(var f in new DirectoryInfo(dir).GetFiles("aa-targeting-*.jsonl").OrderByDescending(x=>x.LastWriteTimeUtc).Skip(7))
            try{f.Delete();}catch{ }
        string path=Path.Combine(dir,$"aa-targeting-{DateTime.UtcNow:yyyyMMdd-HHmmssfffffff}.jsonl");
        writer=new StreamWriter(new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.ReadWrite),new UTF8Encoding(false));
        Emit("coverage",default,default,new{path,mode="passive_late_update",nativeHooksEnabled=false,nativeHooksInstalled=0,
            nonFiniteNumbers="NaN/Infinity/-Infinity are JSON strings; ordinary values stay numeric",
            intervalSeconds=Interval,weaponBatch=WeaponBatch,discoveryBatch=DiscoveryBatch,threatCap=ThreatCap,workBudgetMs=WorkBudgetMs,
            caveat="Observed state, not native rejection reasons. Nearby observations may be stale/incomplete and do not prove visibility or candidate eligibility. Brief states/interceptions can be missed. No kill attribution from disappearance."},true);
        Flush();MelonLogger.Msg("FREEDOM_ARROW_AA_LOG "+path+"; PASSIVE LateUpdate observer, ZERO native AA hooks; invocation unproved until observer_bound/state records");
    }
    public static void SceneChanged()
    {
        try
        {
            if(world!=null&&!world._isDisposed){weaponSet?.Dispose();unitSet?.Dispose();}
        }
        catch(Exception e){Fail(e);}
        finally{weaponSet=null;unitSet=null;world=null;Threats.Clear();Last.Clear();while(ShotSignals.TryDequeue(out _)){ }weaponCursor=unitCursor=0;nextSample=0;}
    }
    public static void LateUpdate()
    {
        if(off||writer==null||!Runtime.IsApplied||!Conquest.Prototype.DiagnosticSceneActive)return;
        float now=Time.time;if(now<nextSample)return;nextSample=now+Interval;
        var clock=Stopwatch.StartNew();
        try
        {
            var current=ShootingSystem._gameContext;if(current==null||current._isDisposed)return;
            if(world==null||world.Pointer!=current.Pointer)
            {
                SceneChanged();if(off)return;world=current;
                // Our own read-only subscriptions, not the game's search/system sets.
                weaponSet=world.GetEntities().With<WeaponComponent>().AsSet();
                unitSet=world.GetEntities().With<UnitComponent>().AsSet();
                Emit("observer_bound",default,default,new{world=(long)world.Pointer,weapons=weaponSet.Count,units=unitSet.Count},true);
            }
            for(int n=0;n<16&&clock.Elapsed.TotalMilliseconds<WorkBudgetMs&&ShotSignals.TryDequeue(out var fired);n++)
                Snapshot("shot_callback_deferred",fired);
            var units=unitSet._entities;int unitCount=Math.Min(unitSet.Count,units?.Length??0);
            for(int n=0;n<Math.Min(DiscoveryBatch,unitCount)&&clock.Elapsed.TotalMilliseconds<1;n++)
            {
                if(unitCursor>=unitCount)unitCursor=0;var e=units[unitCursor++];scanned++;
                if(!e.IsAlive||!e.Has<UnitComponent>()||!e.Has<TransformComponent>())continue;
                var u=NativeEcs.Read<UnitComponent>(e);int type=(int)(u.UnitData?.Type??0);
                if((type&(16|128|256|512|1024))==0)continue;
                var k=Key(e);if(Threats.Count>=ThreatCap&&!Threats.ContainsKey(k))continue;
                int? ammo=null;
                if(e.Has<WarheadComponent>())
                {
                    var shooter=NativeEcs.Field<WarheadComponent,Entity>(e,"ShooterWeapon");
                    if(shooter.IsAlive&&shooter.Has<WeaponComponent>())ammo=NativeEcs.Read<WeaponComponent>(shooter).SelectedAmmunition?.Id;
                }
                Threats[k]=new(e,type,ammo,u.Owner?.TeamSide.ToString(),Position(e),now);
            }
            foreach(var pair in Threats.ToArray())
                if(!pair.Value.Entity.IsAlive||now-pair.Value.Seen>ThreatAge)Threats.Remove(pair.Key);
            var weapons=weaponSet._entities;int count=Math.Min(weaponSet.Count,weapons?.Length??0);
            int visited=0;
            while(visited<Math.Min(WeaponBatch,count)&&clock.Elapsed.TotalMilliseconds<WorkBudgetMs)
            {
                if(weaponCursor>=count){weaponCursor=0;rounds++;}
                var e=weapons[weaponCursor++];visited++;
                Snapshot("state",e,true);samples++;
            }
            maxWorkMs=Math.Max(maxWorkMs,clock.Elapsed.TotalMilliseconds);
            if(now>=nextMetrics)
            {
                nextMetrics=now+5;
                Emit("observer_metrics",default,default,new{samples,scanned,rounds,weapons=count,units=unitCount,weaponCursor,unitCursor,
                    cachedAirAndProjectiles=Threats.Count,lastWorkMs=clock.Elapsed.TotalMilliseconds,maxWorkMs,dropped,pending=Pending.Count,
                    budget="Cooperative loop budget; one native read or query binding may exceed it. Runtime performance must be measured."},true);
            }
        }
        catch(Exception e){Fail(e);}
    }
    static bool GroundAA(Entity e,out WeaponComponent w,out Entity unit)
    {
        w=null;unit=default;
        if(off||!Runtime.IsApplied||!e.IsAlive||!e.Has<WeaponComponent>())return false;
        w=NativeEcs.Read<WeaponComponent>(e);if(w==null||!w.IsAntiAir)return false;
        unit=w.GetUnitEntity();if(!unit.IsAlive||!unit.Has<UnitComponent>())return false;
        var d=NativeEcs.Read<UnitComponent>(unit).UnitData;return d!=null&&(((int)d.Type&38)!=0);
    }
    static object Unit(Entity e)
    {
        if(!e.IsAlive||!e.Has<UnitComponent>())return new{entity=e.GetHashCode(),identity=Key(e).ToString("X16"),alive=e.IsAlive};
        var u=NativeEcs.Read<UnitComponent>(e);
        return new{entity=e.GetHashCode(),identity=Key(e).ToString("X16"),alive=true,id=u.UnitData?.Id,name=u.UnitData?.Name,
            type=(int)(u.UnitData?.Type??0),team=u.Owner?.TeamSide.ToString()};
    }
    static Vector3 Position(Entity e)=>NativeEcs.Property<TransformComponent,Vector3>(e,"CenterPosition");
    static object Coords(Vector3 p)=>new{x=Math.Round(p.x,1),y=Math.Round(p.y,1),z=Math.Round(p.z,1)};
    static Entity Target(Entity w)=>w.IsAlive&&w.Has<TargetComponent>()?NativeEcs.Field<TargetComponent,Entity>(w,"Target"):default;
    static void Snapshot(string kind,Entity weapon,bool nearby=false)
    {
        try
        {
            if(!GroundAA(weapon,out var w,out var unit))return;
            var target=Target(weapon);var a=w.SelectedAmmunition;
            bool selected=weapon.Has<TargetComponent>();
            bool canAim=selected&&NativeEcs.Field<TargetComponent,bool>(weapon,"CanAim");
            bool margin=selected&&NativeEcs.Field<TargetComponent,bool>(weapon,"IsWithinMargin");
            bool overkill=selected&&NativeEcs.Field<TargetComponent,bool>(weapon,"IsTargetOverkilledByOthers");
            bool hold=unit.Has<HoldFireComponent>()||weapon.Has<HoldFireComponent>();
            bool reload=weapon.Has<MagazineReloadingComponent>(),burst=weapon.Has<BurstCooldownComponent>(),cycle=weapon.Has<WeaponCycleComponent>();
            bool aimed=weapon.Has<AimedComponent>(),aiming=weapon.Has<AimingComponent>();
            float? aimRemaining=aiming?NativeEcs.Property<AimingComponent,float>(weapon,"TimeRemaining"):(float?)null;
            bool? aimingInProgress=AaObservationPolicy.AimingInProgress(aiming,aimRemaining);
            object selectedData=selected?new{target=Unit(target),overkilled=overkill,canAim,withinMargin=margin,
                markedForRemoval=NativeEcs.Field<TargetComponent,bool>(weapon,"MarkedForRemoval"),
                mode=(int)NativeEcs.Field<TargetComponent,TargetFireMode>(weapon,"TargetingMode"),
                lastDamageScore=NativeEcs.EncodedField<TargetComponent>(weapon,"LastDamageScore"),
                lastHitChance=NativeEcs.EncodedField<TargetComponent>(weapon,"LastHitChance")}:null;
            Vector3 pos=default;bool hasPosition=unit.Has<TransformComponent>();if(hasPosition)pos=Position(unit);
            var owner=NativeEcs.Read<UnitComponent>(unit).Owner;string team=owner?.TeamSide.ToString();
            object[] observed=null;
            if(nearby&&hasPosition)
                observed=Threats.Values.Where(x=>x.Team!=null&&team!=null&&x.Team!=team)
                    .OrderBy(x=>(x.Position-pos).sqrMagnitude).Take(4).Select(x=>(object)new{
                        target=Unit(x.Entity),ammoId=x.Ammo,position=Coords(x.Position),distanceWorld=Math.Round(Vector3.Distance(pos,x.Position),1),
                        ageSeconds=Math.Round(Time.time-x.Seen,3),tableMaskMatches=a!=null&&(((int)a.TargetType&x.Type)!=0),
                        candidateEligibility="NOT evaluated; no visibility/LOS/kinematic/overkill calls"}).ToArray();
            object targetPriority=null;
            if(target.IsAlive&&target.Has<ShootPriorityComponent>())
            {
                var s=NativeEcs.Read<ShootPriorityComponent>(target);
                targetPriority=new{excludeUnguided=s.ExcludeUnguidedOnThisUnit,registeredShooters=s.Shooters?.Count??0,
                    incomingMissiles=s.IncommingMissiles?.Count??0,channelEntries=s.ShootingChannels?.Count??0};
            }
            Emit(kind,weapon,target,new{shooter=Unit(unit),weaponId=w.WeaponInfo?.Id,weaponName=w.WeaponInfo?.Name,enabled=w.IsEnabled,
                ammoId=a?.Id,ammoInMagazine=w.AmmoInMagazine.Value,shotsMade=w.ShotsMade.Value,
                radarActive=RadarSystem.ActiveRadars?.Contains(unit)??false,radarDependent=w.WeaponInfo?.IsRadarDependent,
                holdFire=hold,aimed,aiming,aimingInProgress,aimSecondsConfigured=w._aimingTime.Value,
                aimSecondsRemaining=aimRemaining,
                magazineReload=reload,burstCooldown=burst,weaponCycle=cycle,targetSearchDelayed=weapon.Has<TargetSearchDelayComponent>(),
                networkRemote=weapon.Has<NetworkWeaponRemoteComponent>(),guidingMissiles=weapon.Has<ActiveGuidanceComponent>(),
                targetHorizontalAngle=w.TargetHorizontalAngle,targetVerticalAngle=w.TargetVerticalAngle,currentVerticalAngle=w.CurrentVerticalAngle,
                lowRangeRaw=a?.LowAltRange,highRangeRaw=a?.HighAltRange,seadRangeOverrideRaw=a?.SeadProjectileRangeOverride,
                position=hasPosition?Coords(pos):null,selected=selectedData,targetPriority,
                observations=AaObservationPolicy.Describe(w.IsEnabled,hold,w.AmmoInMagazine.Value,reload,burst,cycle,aimingInProgress==true,selected,canAim,margin)
                    .Concat(aimingInProgress==null?new[]{"aim_time_nonfinite_or_unavailable"}:Array.Empty<string>()).ToArray(),
                nearbyObserved=observed,explanation="LateUpdate sampled state, including deferred shot signals; NOT exact state at shot time or native rejection reasons."});
        }
        catch(Exception e){Fail(e);}
    }
    static void Emit(string kind,Entity weapon,Entity target,object data,bool force=false)
    {
        if(off)return;
        try
        {
            string state=AaLogJson.Serialize(data);float now=Time.time;
            string key=kind+":"+Key(weapon)+":"+Key(target);
            if(!force&&Last.TryGetValue(key,out var old)&&old.state==state&&now-old.time<1)return;
            if(Last.Count>=MaxKeys)Last.Clear();Last[key]=(state,now);
            if(Pending.Count>=MaxPending){dropped++;return;}
            Pending.Enqueue(AaLogJson.Serialize(new{seq=++sequence,t=now,kind,weapon=weapon.GetHashCode(),target=target.GetHashCode(),data}));
        }
        catch(Exception e){Fail(e);}
    }
    // Called by the already-existing shot logger. Do not read ECS or invoke Unity
    // here: a shot callback can execute inside combat code/on a worker thread.
    public static void Fired(Entity weapon)
    {
        if(off||writer==null)return;
        if(ShotSignals.Count<256)ShotSignals.Enqueue(weapon);
        else Interlocked.Increment(ref dropped);
    }
    public static void Flush()
    {
        if(writer==null||off)return;
        try
        {
            for(int i=0;i<256&&Pending.TryDequeue(out var s);i++)
            {
                if(bytes+Encoding.UTF8.GetByteCount(s)+1>MaxBytes||lines>=MaxLines)
                {writer.WriteLine(AaLogJson.Serialize(new{kind="limit",bytes,lines,dropped}));writer.Dispose();writer=null;off=true;return;}
                writer.WriteLine(s);bytes+=Encoding.UTF8.GetByteCount(s)+1;lines++;
            }
            writer.Flush();
        }
        catch(Exception e){Fail(e);}
    }
    public static void Close(){try{Flush();SceneChanged();writer?.Dispose();}catch(Exception e){Fail(e);}finally{writer=null;}}
    static void Fail(Exception e)
    {
        if(off)return;off=true;
        DiagnosticLog.Write("aa_log_failed",new{error=e.ToString()});
        MelonLogger.Warning("FREEDOM_ARROW_AA_LOG_FAILED: passive observer stopped; no gameplay writes. "+e.Message);
        try{writer?.Dispose();}catch{ }writer=null;
    }
}

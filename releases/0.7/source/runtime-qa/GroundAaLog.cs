using System.Collections.Concurrent;
using System.Reflection;
using System.Text;
using System.Text.Json;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Guidance.Systems;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppBrokenArrow.Shared.Ecs.Enums;
using Il2CppBrokenArrow.Client.Ecs.GNetwork.Components.Ownership;
using Il2CppDefaultEcs;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;

// Observation only. No extra RNG, target searches, score calculations or writes
// to ECS. Avoid patches involving non-blittable ref components, Nullable<T>,
// spans and tuple returns (the dev.94 native crash pattern).
static class GroundAaLog
{
    const long MaxBytes=16*1024*1024;
    const int MaxLines=60000,MaxPending=2048,MaxKeys=8192;
    static readonly ConcurrentQueue<string> Pending=new();
    static readonly object Gate=new();
    static readonly Dictionary<string,(string state,float time)> Last=new();
    static StreamWriter writer;
    static long bytes;
    static int lines,dropped,sequence;
    static bool off;
    [ThreadStatic] static Entity contextWeapon;
    [ThreadStatic] static Entity contextTarget;
    sealed class Scope { public Entity Weapon,Target; }
    static Scope Enter(Entity weapon,Entity target)
    {
        var s=new Scope{Weapon=contextWeapon,Target=contextTarget};
        contextWeapon=weapon;contextTarget=target;return s;
    }
    static Exception Leave(Exception __exception,Scope __state)
    {
        if(__state!=null){contextWeapon=__state.Weapon;contextTarget=__state.Target;}
        return __exception;
    }
    // A/B isolation after devtest.lat.1 rejected all 564 observed candidates.
    // No native targeting/overkill/shooting detours are installed by default.
    // Keep the pre-existing shot callback observer for evidence of restored fire.
    public static void Install(HarmonyLib.Harmony h,string root,bool enableNativeHooks=false)
    {
        string dir=Path.Combine(root,"diagnostics");Directory.CreateDirectory(dir);
        foreach(var f in new DirectoryInfo(dir).GetFiles("aa-targeting-*.jsonl").OrderByDescending(x=>x.LastWriteTimeUtc).Skip(7))f.Delete();
        string path=Path.Combine(dir,$"aa-targeting-{DateTime.UtcNow:yyyyMMdd-HHmmssfffffff}.jsonl");
        writer=new StreamWriter(new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.ReadWrite),new UTF8Encoding(false));
        var coverage=new List<object>();
        void Bind(Type type,string method,string before=null,string after=null,Type[] args=null,string finalizer=null)
        {
            if(!enableNativeHooks)
            {
                coverage.Add(new{method=type.Name+"."+method,installed=false,reason="Disabled for devtest.lat.2 A/B isolation"});
                return;
            }
            try
            {
                var m=AccessTools.Method(type,method,args)??throw new MissingMethodException(type.Name,method);
                h.Patch(m,prefix:before==null?null:new HarmonyMethod(typeof(GroundAaLog),before),
                    postfix:after==null?null:new HarmonyMethod(typeof(GroundAaLog),after),
                    finalizer:finalizer==null?null:new HarmonyMethod(typeof(GroundAaLog),finalizer));
                coverage.Add(new{method=type.Name+"."+method,installed=true});
            }
            catch(Exception e){coverage.Add(new{method=type.Name+"."+method,installed=false,error=e.Message});}
        }
        Bind(typeof(TargetSearchHelper),"SearchForTargets",nameof(SearchBefore),nameof(SearchAfter),finalizer:nameof(Leave));
        Bind(typeof(TargetSearchHelper),"SearchForTargetsInZone",nameof(SearchBefore),nameof(SearchAfter),finalizer:nameof(Leave));
        Bind(typeof(TargetSearchHelper),"TryAddTargetToCheckList",nameof(CandidateBefore),nameof(CandidateAfter),finalizer:nameof(Leave));
        Bind(typeof(BattleSystemHelpers),"RemoveTarget",nameof(Removing));
        Bind(typeof(TargetMaintenanceSystem),"InternalUpdate",nameof(SearchBefore),nameof(Maintained),finalizer:nameof(Leave));
        Bind(typeof(ShootingSystem),"InternalUpdate",nameof(ShootingBefore),nameof(ShootingAfter),finalizer:nameof(Leave));
        Bind(typeof(ShellHitSystem),"InternalUpdate",nameof(Hit));
        Bind(typeof(OverkillScoringSystem),"IsTargetOverkilled",after:nameof(Overkill));
        Bind(typeof(OverkillScoringSystem),"UpdateWeaponScoreOnTarget",after:nameof(Score));
        Bind(typeof(OverkillScoringSystem),"UpdateWeaponTimes",after:nameof(Times),args:new[]{typeof(Entity).MakeByRefType(),typeof(Entity).MakeByRefType(),typeof(float),typeof(float)});
        Bind(typeof(BattleSystemHelpers),"CanUseFiringChannel",after:nameof(Channel),args:new[]{typeof(Entity).MakeByRefType(),typeof(bool)});
        Bind(typeof(BattleSystemHelpers),"DoesWeaponHaveAmmo",after:nameof(Ammo));
        Bind(typeof(BattleSystemHelpers),"CheckLocalAnglesToTarget",after:nameof(Angles));
        Bind(typeof(BattleSystemHelpers),"IsGuidedShellSelectedOnNonPriporityOverkilled",after:nameof(GuidedOverkill));
        Bind(typeof(BattleSystemHelpers),"GetAmmoShootingDistance",after:nameof(Range));
        Bind(typeof(BattleSystemHelpers),"IsValidToTarget",after:nameof(Valid));
        Bind(typeof(BattleSystemHelpers),"CanAmmoTargetUnitType",after:nameof(Mask));
        Emit("coverage",default,default,new{path,hooks=coverage,nativeHooksEnabled=enableNativeHooks,observationOnly=true,limitBytes=MaxBytes,limitLines=MaxLines,
            caveat=enableNativeHooks?"Not an exhaustive trace before spatial/FOW candidate enumeration. Native invocation unproved.":"A/B build: all 17 native diagnostic hooks disabled. Existing shot callback snapshots only; no target-decision trace."},true);
        Flush();MelonLogger.Msg("FREEDOM_ARROW_AA_LOG "+path+(enableNativeHooks?"; hook invocation unproved until events arrive":"; all 17 native diagnostic hooks DISABLED for A/B isolation; shot snapshots only"));
    }
    static bool GroundAA(Entity e,out WeaponComponent w,out Entity unit)
    {
        w=null;unit=default;
        if(off||!Runtime.IsApplied||!e.IsAlive||!e.Has<WeaponComponent>())return false;
        w=NativeEcs.Read<WeaponComponent>(e);if(w==null||!w.IsAntiAir)return false;
        unit=w.GetUnitEntity();if(!unit.IsAlive||!unit.Has<UnitComponent>())return false;
        var d=NativeEcs.Read<UnitComponent>(unit).UnitData;
        return d!=null&&(((int)d.Type&38)!=0);
    }
    static object Unit(Entity e)
    {
        if(!e.IsAlive||!e.Has<UnitComponent>())return new{entity=e.GetHashCode(),alive=e.IsAlive};
        var d=NativeEcs.Read<UnitComponent>(e).UnitData;
        return new{entity=e.GetHashCode(),alive=true,id=d?.Id,name=d?.Name,type=(int)(d?.Type??0)};
    }
    static Entity Target(Entity w)=>w.IsAlive&&w.Has<TargetComponent>()?NativeEcs.Field<TargetComponent,Entity>(w,"Target"):default;
    static void Emit(string kind,Entity weapon,Entity target,object data,bool force=false)
    {
        if(off)return;
        try
        {
            string state=JsonSerializer.Serialize(data);float now=Time.time;
            string key=kind+":"+weapon.GetHashCode()+":"+target.GetHashCode();
            lock(Gate)
            {
                if(!force&&Last.TryGetValue(key,out var old)&&old.state==state&&now-old.time<1)return;
                if(Last.Count>=MaxKeys)Last.Clear();Last[key]=(state,now);
            }
            if(Pending.Count>=MaxPending){Interlocked.Increment(ref dropped);return;}
            Pending.Enqueue(JsonSerializer.Serialize(new{seq=Interlocked.Increment(ref sequence),t=now,kind,
                weapon=weapon.GetHashCode(),target=target.GetHashCode(),data}));
        }
        catch(Exception e){Fail(e);}
    }
    static void Snapshot(string kind,Entity weapon)
    {
        try
        {
            if(!GroundAA(weapon,out var w,out var unit))return;
            var target=Target(weapon);var a=w.SelectedAmmunition;
            object selected=null;
            if(weapon.Has<TargetComponent>())
                selected=new{target=Unit(target),overkilled=NativeEcs.Field<TargetComponent,bool>(weapon,"IsTargetOverkilledByOthers"),
                    canAim=NativeEcs.Field<TargetComponent,bool>(weapon,"CanAim"),withinMargin=NativeEcs.Field<TargetComponent,bool>(weapon,"IsWithinMargin"),
                    markedForRemoval=NativeEcs.Field<TargetComponent,bool>(weapon,"MarkedForRemoval"),mode=(int)NativeEcs.Field<TargetComponent,TargetFireMode>(weapon,"TargetingMode")};
            Emit(kind,weapon,target,new{shooter=Unit(unit),weaponId=w.WeaponInfo?.Id,weaponName=w.WeaponInfo?.Name,
                enabled=w.IsEnabled,ammoId=a?.Id,ammoInMagazine=w.AmmoInMagazine.Value,shotsMade=w.ShotsMade.Value,
                radarActive=RadarSystem.ActiveRadars?.Contains(unit)??false,radarDependent=w.WeaponInfo?.IsRadarDependent,
                aimed=weapon.Has<AimedComponent>(),magazineReload=weapon.Has<MagazineReloadingComponent>(),
                burstCooldown=weapon.Has<BurstCooldownComponent>(),weaponCycle=weapon.Has<WeaponCycleComponent>(),
                networkRemote=weapon.Has<NetworkWeaponRemoteComponent>(),selected});
        }
        catch(Exception e){Fail(e);}
    }
    static void SearchBefore(in Entity __0,out Scope __state)=>__state=Enter(__0,default);
    static void SearchAfter(in Entity __0,bool __result){try{Snapshot("search",__0);Evaluated(__0);if(GroundAA(__0,out _,out _))Emit("search_result",__0,Target(__0),new{found=__result});}catch(Exception e){Fail(e);}}
    static void Maintained(in Entity __0)=>Snapshot("maintenance",__0);
    static void CandidateBefore(in Entity __1,in Entity __2,out Scope __state)=>__state=Enter(__1,__2);
    static void CandidateAfter(in Entity __0,in Entity __1,in Entity __2)
    {
        try
        {
            if(!GroundAA(__1,out _,out _))return;
            var list=TargetSearchHelper._targetsList;object result=null;
            if(list!=null)foreach(var t in list)if(t.TargetEntity.Equals(__2))
                result=new{t.CanAim,t.CanKinematicallyHit,t.IsOverkilledByOthers,t.GuidedProjectileWasSelectedOnNonPriority,t.IsTracked,t.IsPriority,t.IsProjectile,t.Distance,t.SelectedShellID};
            Emit("candidate",__1,__2,new{shooter=Unit(__0),candidate=Unit(__2),added=result!=null,checks=result});
        }
        catch(Exception e){Fail(e);}
    }
    static void Evaluated(in Entity __0)
    {
        try
        {
            if(!GroundAA(__0,out _,out _))return;
            var list=TargetSearchHelper._targetsList;if(list==null)return;
            foreach(var t in list)Emit("evaluated",__0,t.TargetEntity,new{t.CanAim,t.CanKinematicallyHit,t.IsOverkilledByOthers,t.IsTracked,t.IsPriority,t.IsProjectile,
                t.HitChance,t.OwnScore,t.ScoreToOthers,t.TimeToHit,t.SelectedShellID});
        }
        catch(Exception e){Fail(e);}
    }
    static void Removing(in Entity __0,bool __1,bool __2,TargetRemoveReason __3)
    {try{if(GroundAA(__0,out _,out _))Emit("target_removed",__0,Target(__0),new{reason=__3.ToString(),reasonId=(int)__3,removeGuided=__1,immediateSearch=__2},true);}catch(Exception e){Fail(e);}}
    static void ShootingBefore(in Entity __0,out Scope __state)
    {__state=Enter(__0,default);try{contextTarget=Target(__0);}catch(Exception e){Fail(e);}}
    static void ShootingAfter(in Entity __0)=>Snapshot("shooting",__0);
    static void Overkill(in Entity __0,bool __1,bool __2,in Entity __3,bool __4,bool __5,bool __6,bool __7,bool __8,bool __9,bool __result)
    {try{var w=contextWeapon.IsAlive?contextWeapon:__3;if(GroundAA(w,out _,out _))Emit("overkill",w,__0,new{blocked=__result,ignoreOnHold=__1,filterUnguided=__2,excludeShooter=__3.GetHashCode(),sameTurret=__4,onlyVisible=__5,includeSEAD=__6,includeBlocked=__7,excludeMissiles=__8,excludeGuns=__9});}catch(Exception e){Fail(e);}}
    static void Score(in Entity __0,in Entity __1,bool __2,float __3,float __4,bool __5,bool __6,bool __7)
    {try{if(GroundAA(__0,out _,out _))Emit("overkill_score",__0,__1,new{guided=__2,damageScore=__3,hitChance=__4,shootingBlocked=__5,holdFire=__6,guidingMissile=__7});}catch(Exception e){Fail(e);}}
    static void Times(in Entity __0,in Entity __1,float __2,float __3)
    {try{if(GroundAA(__0,out _,out _))Emit("weapon_times",__0,__1,new{timeToAim=__2,projectileFlightTime=__3});}catch(Exception e){Fail(e);}}
    static void Channel(in Entity __0,bool __result)=>GateResult("channel",__0,contextTarget,__result);
    static void Ammo(in Entity __0,bool __result)=>GateResult("has_ammo",__0,contextTarget,__result);
    static void Angles(Entity __0,Entity __1,bool __result)=>GateResult("angles",__1,__0,__result);
    static void GuidedOverkill(in Entity __0,in Entity __1,in Entity __2,bool __result)=>GateResult("guided_overkill",__1,__2,__result);
    static void Valid(in Entity __0,bool __result)=>GateResult("target_valid",contextWeapon,__0,__result);
    static void Mask(bool __result)=>GateResult("target_mask",contextWeapon,contextTarget,__result);
    static void GateResult(string kind,Entity weapon,Entity target,bool value)
    {try{if(GroundAA(weapon,out _,out _))Emit(kind,weapon,target,new{result=value});}catch(Exception e){Fail(e);}}
    static void Range(Entity __0,Entity __1,Il2CppBrokenArrow.DataBase.Models.Ammunitions __2,float __result)
    {try{if(GroundAA(contextWeapon,out _,out _))Emit("range",contextWeapon,__1,new{ammo=__2?.Id,worldRange=__result});}catch(Exception e){Fail(e);}}
    public static void Fired(Entity weapon)
    {try{if(GroundAA(weapon,out _,out _))Snapshot("shot_callback",weapon);}catch(Exception e){Fail(e);}}
    static void Hit(in Entity __0)
    {
        try
        {
            if(off||!Runtime.IsApplied||!__0.IsAlive||!__0.Has<WarheadComponent>()||!__0.Has<HitComponent>())return;
            var w=NativeEcs.Field<WarheadComponent,Entity>(__0,"ShooterWeapon");
            if(!GroundAA(w,out _,out _))return;
            var target=NativeEcs.Field<HitComponent,Entity>(__0,"TargetEntity");
            var type=NativeEcs.Field<HitComponent,HitType>(__0,"Type");
            Emit("hit_observed",w,target,new{shell=__0.GetHashCode(),hitType=type.ToString(),hitTypeId=(int)type,targetInfo=Unit(target)},true);
        }
        catch(Exception e){Fail(e);}
    }
    public static void Flush()
    {
        if(writer==null||off)return;
        try
        {
            for(int i=0;i<512&&Pending.TryDequeue(out var s);i++)
            {
                if(bytes+Encoding.UTF8.GetByteCount(s)+1>MaxBytes||lines>=MaxLines)
                {writer.WriteLine(JsonSerializer.Serialize(new{kind="limit",bytes,lines,dropped}));writer.Dispose();writer=null;off=true;return;}
                writer.WriteLine(s);bytes+=Encoding.UTF8.GetByteCount(s)+1;lines++;
            }
            writer.Flush();
        }
        catch(Exception e){Fail(e);}
    }
    public static void Close(){try{Flush();writer?.Dispose();}catch(Exception e){Fail(e);}finally{writer=null;}}
    static void Fail(Exception e)
    {if(off)return;off=true;DiagnosticLog.Write("aa_log_failed",new{error=e.Message});MelonLogger.Warning("FREEDOM_ARROW_AA_LOG_FAILED: logging off; gameplay unchanged. "+e.Message);}
}

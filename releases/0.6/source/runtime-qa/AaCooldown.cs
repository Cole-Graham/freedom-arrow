using System.Collections.Concurrent;
using System.Diagnostics;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Text.Json.Nodes;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppDefaultEcs;
using MelonLoader;

namespace FreedomArrow;

// One scalar-bool behavior hook. It consumes immutable managed snapshots only:
// no ECS, Unity, search/scoring helper, reflection or file IO in the native callback.
static class AaCooldown
{
    sealed class Target
    {
        public readonly float Impact; public readonly int Incoming; public readonly AaCooldownPolicy.Contributor[] Contributors;
        public Target(float impact,int incoming,AaCooldownPolicy.Contributor[] contributors){Impact=impact;Incoming=incoming;Contributors=contributors;}
    }
    sealed class Frame
    {
        public readonly long Stamp; public readonly HashSet<ulong> GroundWeapons; public readonly Dictionary<ulong,Target> Targets;
        public Frame(long stamp,HashSet<ulong> groundWeapons,Dictionary<ulong,Target> targets){Stamp=stamp;GroundWeapons=groundWeapons;Targets=targets;}
    }
    static readonly Frame Empty = new(0, new(), new());
    static Frame frame = Empty;
    static EntitySet units, weapons;
    static World world;
    static bool enabled, shadow, failed;
    static int cursor, reported, invocations, corrections, wouldCorrect;
    static float next, nextMetrics, nextSampleLog;
    static readonly ConcurrentQueue<(ulong Target, ulong Caller)> Corrected = new();
    // Weapon entity -> interceptor role and when it was checked. Main thread only (LateUpdate).
    static readonly Dictionary<ulong,(bool Defender,float At)> roles = new();
    const int MaxWeapons=8192;
    static ulong Key(Entity e) => Unsafe.As<Entity,ulong>(ref e);

    public static void Install(HarmonyLib.Harmony harmony, string root)
    {
        var cfg=JsonNode.Parse(File.ReadAllText(Path.Combine(root,"game-config.json")));
        enabled=cfg?["AaCooldownEnabled"]?.GetValue<bool>()??false;
        shadow=cfg?["AaCooldownShadowOnly"]?.GetValue<bool>()??true;
        if(!enabled)return;
        var method=AccessTools.Method(typeof(OverkillScoringSystem),"IsTargetOverkilled")
            ??throw new MissingMethodException("IsTargetOverkilled");
        var p=method.GetParameters();
        if(method.ReturnType!=typeof(bool)||p.Length!=10
            ||p[0].ParameterType!=typeof(Entity).MakeByRefType()
            ||p[3].ParameterType!=typeof(Entity).MakeByRefType()
            ||p.Where((_,i)=>i!=0&&i!=3).Any(x=>x.ParameterType!=typeof(bool)))
            throw new InvalidOperationException("Overkill hook signature changed");
        if(Unsafe.SizeOf<Entity>()!=8)throw new InvalidOperationException("Entity layout changed");
        harmony.Patch(method,postfix:new HarmonyMethod(typeof(AaCooldown),nameof(After)));
        DiagnosticLog.Write("aa_cooldown_installed",new{shadow,nativeBehaviorHooks=1,
            scope="Land/naval interceptor caller (current round has a projectile TargetType bit), native projectile target, all other future reservations clearly late, no airborne protection. Native priority retained.",
            caveat="Native invocation and safety unproven until this build is exercised. Mixed/unknown/stale cases retain native behavior."});
        MelonLogger.Msg("FREEDOM_ARROW_AA_COOLDOWN installed: one bool hook; managed cache only; shadow="+shadow);
    }
    // Reference shape matches the original in Entity parameters. Never read native storage here.
    static void After(ref Entity __0, ref Entity __3, bool __7, ref bool __result)
    {
        Interlocked.Increment(ref invocations);
        if(!__result||!enabled||failed)return;
        var f=Volatile.Read(ref frame);
        ulong target=Key(__0), caller=Key(__3);
        if(!f.Targets.TryGetValue(target,out var t))return;
        double age=(Stopwatch.GetTimestamp()-f.Stamp)/(double)Stopwatch.Frequency;
        if(!AaCooldownPolicy.Release(__result,f.GroundWeapons.Contains(caller),__7,age,
            t.Incoming,caller,t.Impact,t.Contributors))return;
        Interlocked.Increment(ref wouldCorrect);
        if(!shadow){__result=false;Interlocked.Increment(ref corrections);}
        if(Corrected.Count<256)Corrected.Enqueue((target,caller));
    }
    public static void SceneChanged()
    {
        Volatile.Write(ref frame,Empty);
        try{if(world!=null&&!world._isDisposed){units?.Dispose();weapons?.Dispose();}}
        catch(Exception e){Fail(e);}
        finally{world=null;units=weapons=null;cursor=0;next=0;roles.Clear();}
    }
    static bool Defender(Entity e)
    {
        if(!e.IsAlive||!e.Has<WeaponComponent>())return false;
        var w=NativeEcs.Read<WeaponComponent>(e);if(w==null)return false;
        var info=w.WeaponInfo;var ammo=w.SelectedAmmunition;
        bool gun=info!=null&&ammo!=null&&CramPredictionPolicy.Gun((int)info.Type,info.IsRadarDependent,
            (int)ammo.TrajectoryType,(int)ammo.Seeker,(long)ammo.TargetType);
        var u=w.GetUnitEntity();
        return ammo!=null&&u.IsAlive&&u.Has<UnitComponent>()
            &&AaCooldownPolicy.Defender((int)NativeEcs.Read<UnitComponent>(u).UnitData.Type,w.IsAntiAir,gun,(long)ammo.TargetType);
    }
    static float Timer<T>(Entity e,string field)=>e.Has<T>()?NativeEcs.EncodedField<T>(e,field):0;
    static AaCooldownPolicy.Contributor Contributor(Entity e, bool launched)
    {
        ulong key=Key(e);
        if(launched||!Defender(e))return new(key,0,false,launched);
        float remaining=AaCooldownPolicy.Remaining(Timer<BurstCooldownComponent>(e,"CooldownTime"),
            Timer<MagazineReloadingComponent>(e,"MagazineReloadingTime"),Timer<WeaponCycleComponent>(e,"TimeCycling"));
        return new(key,remaining,float.IsFinite(remaining),false);
    }
    public static void LateUpdate()
    {
        if(!enabled||failed)return;
        if(!Runtime.IsApplied||!Conquest.Prototype.DiagnosticSceneActive){Volatile.Write(ref frame,Empty);return;}
        float now=UnityEngine.Time.time;if(now<next)return;next=now+.05f;
        var clock=Stopwatch.StartNew();
        try
        {
            var current=ShootingSystem._gameContext;
            if(current==null||current._isDisposed){Volatile.Write(ref frame,Empty);return;}
            if(world==null||world.Pointer!=current.Pointer)
            {
                SceneChanged();if(failed)return;world=current;
                units=world.GetEntities().With<UnitComponent>().AsSet();
                weapons=world.GetEntities().With<WeaponComponent>().AsSet();
            }
            var ground=new HashSet<ulong>();var wa=weapons._entities;
            int wc=Math.Min(weapons.Count,wa?.Length??0);
            // Only interceptors count toward the limit (was: every weapon, which turned this off in large battles).
            // Each weapon's role is cached and rechecked every 2 s (its selected round can change). A scan that runs out
            // of time keeps native behavior this update and continues from the cache on the next one.
            if(wc>MaxWeapons){Volatile.Write(ref frame,Empty);return;}
            if(roles.Count>wc*4+1024)roles.Clear();
            for(int i=0;i<wc;i++)
            {
                ulong k=Key(wa[i]);
                if(!roles.TryGetValue(k,out var r)||now-r.At>2f)
                {
                    if(clock.Elapsed.TotalMilliseconds>2){Volatile.Write(ref frame,Empty);return;}
                    r=(Defender(wa[i]),now);roles[k]=r;
                }
                if(r.Defender)ground.Add(k);
            }
            if(ground.Count>AaCooldownPolicy.MaxDefenders){Volatile.Write(ref frame,Empty);return;}
            var targets=new Dictionary<ulong,Target>();var ua=units._entities;
            int count=Math.Min(units.Count,ua?.Length??0),visited=0,observed=0,unknownDeadlines=0;
            while(visited<Math.Min(count,64)&&observed<8&&clock.Elapsed.TotalMilliseconds<3)
            {
                if(cursor>=count)cursor=0;
                var e=ua[cursor++];visited++;
                if(!e.IsAlive||!e.Has<UnitComponent>()||!e.Has<ShootPriorityComponent>()||!e.Has<WarheadComponent>())continue;
                if(!AaCooldownPolicy.ProjectileType((int)NativeEcs.Read<UnitComponent>(e).UnitData.Type))continue;
                observed++;
                // Read-only native scalar estimator follows the projectile's own intended target.
                float impact=BattleSystemHelpers.GetProjectileTimeToTarget(e);
                if(!float.IsFinite(impact)||impact<=.05f||impact>20){unknownDeadlines++;continue;}
                var priority=NativeEcs.Read<ShootPriorityComponent>(e);
                if(priority.Shooters==null||priority.IncommingMissiles==null||priority.Shooters.Count>32)continue;
                int originalCount=priority.Shooters.Count;
                var contributors=new List<AaCooldownPolicy.Contributor>();
                var it=priority.Shooters.GetEnumerator();
                try{while(it.MoveNext()){var kv=it.Current;contributors.Add(Contributor(kv.Key,kv.Value==null||kv.Value.MissileLaunched));}}
                finally{it.Dispose();}
                if(contributors.Count!=originalCount||priority.Shooters.Count!=originalCount)continue;
                targets[Key(e)]=new(impact,priority.IncommingMissiles.Count,contributors.ToArray());
            }
            // Stamp from the START of collection: a slow collection expires rather than becoming fresh again.
            Volatile.Write(ref frame,new(Stopwatch.GetTimestamp()-(long)(clock.Elapsed.TotalSeconds*Stopwatch.Frequency),ground,targets));
            if(now>=nextSampleLog&&targets.Count>0)
            {
                nextSampleLog=now+1;
                DiagnosticLog.Write("aa_cooldown_sample",new{t=now,targets=targets.Select(pair=>new{
                    target=pair.Key.ToString("X16"),impact=pair.Value.Impact,incoming=pair.Value.Incoming,
                    contributors=pair.Value.Contributors.Select(c=>new{weapon=c.Weapon.ToString("X16"),c.Known,c.Airborne,
                        remaining=float.IsFinite(c.Remaining)?c.Remaining:(float?)null,
                        clearlyLate=c.Known&&AaCooldownPolicy.ClearlyLate(c.Remaining,pair.Value.Impact)}).ToArray()}).ToArray()});
            }
            int flushed=0;
            while(flushed++<32&&Corrected.TryDequeue(out var c))
                if(reported++<1000)DiagnosticLog.Write("aa_cooldown_reservation",new{t=now,target=c.Target.ToString("X16"),caller=c.Caller.ToString("X16"),shadow,
                    reason="All other registered future contributors clearly late; no incoming/airborne protection in fresh snapshot"});
            if(now>=nextMetrics)
            {
                nextMetrics=now+5;
                DiagnosticLog.Write("aa_cooldown_metrics",new{t=now,shadow,targets=targets.Count,observedProjectiles=observed,unknownDeadlines,weapons=wc,groundWeapons=ground.Count,
                    invocations=Volatile.Read(ref invocations),wouldCorrect=Volatile.Read(ref wouldCorrect),corrections=Volatile.Read(ref corrections),
                    workMs=clock.Elapsed.TotalMilliseconds,scope="Conservative all-late rule; mixed reservations and unknown estimates retain native behavior"});
            }
        }
        catch(Exception e){Fail(e);}
    }
    static void Fail(Exception e)
    {
        failed=true;Volatile.Write(ref frame,Empty);
        DiagnosticLog.Write("aa_cooldown_failed",new{error=e.ToString(),fallback="Native behavior retained"});
        MelonLogger.Error("FREEDOM_ARROW_AA_COOLDOWN_FAILED: native fallback. "+e.Message);
    }
}

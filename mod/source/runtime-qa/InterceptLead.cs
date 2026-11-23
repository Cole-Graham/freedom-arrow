using System.Reflection;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Ballistics;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems;
using Il2CppBrokenArrow.DataBase.Models;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppBrokenArrow.Shared.Ecs.Components.Movement;
using Il2CppDefaultEcs;
using Il2CppInterop.Runtime;
using MelonLoader;
using MelonLoader.NativeUtils;
using MelonLoader.Utils;
using UnityEngine;
using NVector=System.Numerics.Vector3;

namespace FreedomArrow;

// Intercept Lead: corrected lead for every gun that can shoot down missiles (37 units in 0.9.0-dev.21: the 12 SPAAG guns, Linebacker,
// M-SHORAD, ship CIWS), chosen by data in InterceptLeadPolicy.Gun. Called CramPrediction (logs cram_prediction_*, cram_lead) before
// 16 Nov 2026; renamed at Lateralus's request because it was never C-RAM only. Logs are now intercept_lead_*.
// Separate active experiment; GroundAaLog remains a passive observer.
// A verified missile-defence gun muzzle query supplies a one-use scope. Only
// its immediately following matching native projectile lead may change.
internal static unsafe class InterceptLead
{
    // BA 1.2.2.1 (build 26627577, 16 Nov 2026): game code rebuilt; was 12e70883 (build 26273833).
    const string GameHash="007c019575fabcf16748fcdc02052d3bb2571757b8bfd8c69b05508eaf022cc1";
    // Lateralus missile-hp batch (15 Nov 2026): the old 1,000-sample log ended at ~105-138 s, before the Tunguska salvos. Every eligible
    // lead call (applied or fallback, with its reason) is now logged in a compact line, up to 12,000 per session.
    const int MaxTargets=128,MaxSamples=12000;
    // Explicit pointer ABI avoids automatic marshaling of the two bool fields
    // in ref BallisticDataStruct. Native metadata/layout and engine hash gate it.
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    delegate void LeadNative(IntPtr target,IntPtr origin,IntPtr data,int cycles,IntPtr method);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    delegate void AngleNative(IntPtr data,IntPtr method);
    static readonly LeadNative LeadCallback=LeadThunk;
    static NativeHook<LeadNative> leadHook;
    static AngleNative angleSolver;
    static IntPtr angleMethod;
    static HarmonyLib.Harmony harmony;
    static bool installed,off;
    static int mainThread,logged;
    static IntPtr worldPointer;
    static long eligible,applied,dropped;
    static float nextSummary;
    static string pendingError;
    static readonly Dictionary<ulong,InterceptMotionHistory> histories=new();
    // Lateralus 15 Nov 2026 ("yes lets record a missile's motion as soon as it's spotted"): in the hp7 lead logs every new target
    // started with ~0.08 s of history_missing (264 calls), because motion was only recorded once a gun aimed at it. Interceptable
    // missiles are now observed every frame from launch. Only the last 0.075-0.25 s is ever used, so a gun gains no earlier
    // knowledge than its own sight of the missile; the first shot simply gets the corrected lead.
    static EntitySet missileSet;static IntPtr missileWorld;static long tracked;
    static readonly Dictionary<string,long> fallbacks=new();
    static readonly Dictionary<string,long> appliedByWeaponAmmo=new();
    readonly record struct Scope(bool Valid,ulong Target,Entity Weapon,int WeaponId,int AmmoId,int TargetType,Vector3 Center,float OriginRadius,
        NVector Velocity,NVector Acceleration,float HistoryInterval,float Time,float Speed,bool History,int HistoryCount);
    readonly record struct Sample(float Time,ulong Target,int WeaponId,int AmmoId,int TargetType,float HistoryInterval,NVector Acceleration,
        NVector Before,NVector After,NVector Fire,float BeforeTime,float AfterTime,int Iterations,bool Limited,string Reason,NVector Velocity,int HistoryCount);
    [ThreadStatic] static Scope scope;
    static readonly Queue<Sample> samples=new();
    static ulong Key(Entity e)=>Unsafe.As<Entity,ulong>(ref e);
    static NVector N(Vector3 v)=>new(v.x,v.y,v.z);
    static object V(NVector v)=>new{x=v.X,y=v.Y,z=v.Z};
    static void Fallback(string reason)=>fallbacks[reason]=fallbacks.GetValueOrDefault(reason)+1;
    static bool Active=>installed&&!off&&Environment.CurrentManagedThreadId==mainThread
        &&Runtime.IsApplied&&Conquest.Prototype.DiagnosticSceneActive;

    public static void Install()
    {
        var layout=new{pointer=IntPtr.Size,entity=Unsafe.SizeOf<Entity>(),vector=Unsafe.SizeOf<Vector3>(),
            wire=Unsafe.SizeOf<InterceptBallisticValue>(),wireReferences=RuntimeHelpers.IsReferenceOrContainsReferences<InterceptBallisticValue>()};
        DiagnosticLog.Write("intercept_lead_managed_layout",layout);
        if(layout.pointer!=8||layout.entity!=8||layout.vector!=12||layout.wire!=44||layout.wireReferences)
            throw new InvalidOperationException("Prediction ABI: "+System.Text.Json.JsonSerializer.Serialize(layout));
        using(var file=File.OpenRead(Path.Combine(MelonEnvironment.GameRootDirectory,"GameAssembly.dll")))
        using(var sha=SHA256.Create())
            if(Convert.ToHexString(sha.ComputeHash(file)).ToLowerInvariant()!=GameHash)
                throw new InvalidOperationException("Prediction engine fingerprint mismatch");
        RuntimeHelpers.RunClassConstructor(typeof(BallisticsCalculationsHelper).TypeHandle);
        try
        {
            var proxy=typeof(BallisticsCalculationsHelper).Assembly.GetType("Il2CppBrokenArrow.Client.Ecs.BattleSystem.Ballistics.BallisticDataStruct");
            if(proxy!=null)DiagnosticLog.Write("intercept_lead_proxy_shape",typeof(InterceptLead)
                .GetMethod(nameof(ProxyShape),BindingFlags.NonPublic|BindingFlags.Static).MakeGenericMethod(proxy).Invoke(null,null));
        }
        catch(Exception e){DiagnosticLog.Write("intercept_lead_proxy_shape_unavailable",new{error=e.GetType().Name});}
        IntPtr Method(string name)=>(IntPtr)(typeof(BallisticsCalculationsHelper).GetFields(BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic)
            .Single(f=>f.Name.StartsWith("NativeMethodInfoPtr_"+name+"_",StringComparison.Ordinal)).GetValue(null)
            ??throw new MissingMethodException(name+" metadata"));
        var method=Method("CalculateLeadShot");angleMethod=Method("CalculateBallisticsAngle");
        if(method==IntPtr.Zero||angleMethod==IntPtr.Zero||Marshal.ReadIntPtr(method)==IntPtr.Zero||Marshal.ReadIntPtr(angleMethod)==IntPtr.Zero)
            throw new MissingMethodException("Native ballistic methods");
        var helper=IL2CPP.il2cpp_method_get_declaring_type(method);
        var klass=IL2CPP.il2cpp_class_from_name(IL2CPP.il2cpp_class_get_image(helper),
            "BrokenArrow.Client.Ecs.BattleSystem.Ballistics","BallisticDataStruct");
        if(klass==IntPtr.Zero||!IL2CPP.il2cpp_class_is_valuetype(klass))throw new InvalidOperationException("Native ballistic value type missing");
        uint align=0;int nativeSize=IL2CPP.il2cpp_class_value_size(klass,ref align);
        DiagnosticLog.Write("intercept_lead_native_layout",new{nativeSize,align,wireSize=44});
        // Accept only known trailing padding variants. All occupied field offsets
        // still have to match, and only the first 44 bytes are ever copied back.
        if(nativeSize!=44&&nativeSize!=48)throw new InvalidOperationException("Native ballistic size: "+nativeSize);
        foreach(var (name,offset) in new[]{("VectorToTarget",0),("InitialProjectileSpeed",12),("FireVector",16),
            ("FireAngleTan",28),("TimeToImpact",32),("GravityMultiplyer",36),("CanShoot",40),("<Initialized>k__BackingField",41)})
        {
            var field=IL2CPP.il2cpp_class_get_field_from_name(klass,name);
            if(field==IntPtr.Zero||IL2CPP.il2cpp_field_get_offset(field)-2*IntPtr.Size!=offset)
                throw new InvalidOperationException("Native ballistic field mismatch: "+name);
        }
        angleSolver=Marshal.GetDelegateForFunctionPointer<AngleNative>(Marshal.ReadIntPtr(angleMethod));
        var muzzle=AccessTools.Method(typeof(BattleSystemHelpers),"GetShellMuzzleSpeed",new[]{typeof(Entity).MakeByRefType(),typeof(Ammunitions)})
            ??throw new MissingMethodException("GetShellMuzzleSpeed(in Entity,Ammunitions)");
        mainThread=Environment.CurrentManagedThreadId;
        harmony=new HarmonyLib.Harmony("FreedomArrow.InterceptLead");
        attachMuzzle=muzzle;attachTarget=Marshal.ReadIntPtr(method);
        _=Marshal.GetDelegateForFunctionPointer<LeadNative>(attachTarget);
        // Lateralus 16 Nov 2026 (thread 1571554273639006392): on his PC the attach failed once with "Could not create snapshot to process.
        // Error 1450". MelonLoader's NativeHook.Attach first runs CoreClrDelegateFixer.SanityCheckDetour, which takes a Windows snapshot of the
        // whole game process; Windows refused it (ERROR_NO_SYSTEM_RESOURCES). Every check above passed, and a failed attach leaves nothing
        // patched, so only the attach is retried: about 5, 15, 30 and 60 s later from LateUpdate (main thread). Native leading meanwhile.
        if(!TryAttach())return;
        Installed();
    }
    static MethodInfo attachMuzzle;static IntPtr attachTarget;static int attachAttempts;static long retryAt;
    static readonly int[] RetrySeconds={5,15,30,60};
    static bool TryAttach()
    {
        attachAttempts++;
        try
        {
            harmony.Patch(attachMuzzle,postfix:new HarmonyMethod(typeof(InterceptLead),nameof(MuzzleAfter)));
            leadHook=new NativeHook<LeadNative>(attachTarget,Marshal.GetFunctionPointerForDelegate(LeadCallback));
            leadHook.Attach();installed=true;retryAt=0;return true;
        }
        catch(Exception e)
        {
            try{if(leadHook?.IsHooked==true)leadHook.Detach();}catch{}
            leadHook=null;harmony.UnpatchSelf();
            bool again=attachAttempts<=RetrySeconds.Length;
            retryAt=again?Environment.TickCount64+RetrySeconds[attachAttempts-1]*1000L:0;
            DiagnosticLog.Write("intercept_lead_attach_failed",new{attempt=attachAttempts,error=e.ToString(),
                retryInSeconds=again?RetrySeconds[attachAttempts-1]:0,fallback="native leading"+(again?" until a retry succeeds":" for the rest of the session")});
            MelonLogger.Warning($"FREEDOM_ARROW_INTERCEPT_LEAD attach attempt {attachAttempts} failed ({e.Message}); "
                +(again?$"retrying in {RetrySeconds[attachAttempts-1]} s, native leading meanwhile":"giving up, native leading for this session"));
            return false;
        }
    }
    static void Installed()
    {
        DiagnosticLog.Write("intercept_lead_installed",new{scope="direct unguided missile-defence AA guns and radar-dependent autocannons; existing ammo masks",targetTypes=new[]{128,256,512,1024},nativeHooks=2,
            horizon=InterceptLeadPolicy.MaxHorizon,maxCorrection=InterceptLeadPolicy.MaxCorrection,
            maxFraction=InterceptLeadPolicy.MaxFraction,abi="x64 pointer lead detour;44-byte ballistic value",appliedCalls=0,attempts=attachAttempts});
        MelonLogger.Msg("FREEDOM_ARROW_INTERCEPT_LEAD installed; invocation unproved until intercept_lead_applied; missile-defence guns; existing target masks");
    }
    static object ProxyShape<T>()=>new{type=typeof(T).FullName,valueType=typeof(T).IsValueType,
        managedSize=Unsafe.SizeOf<T>(),references=RuntimeHelpers.IsReferenceOrContainsReferences<T>()};

    static void MuzzleAfter(ref Entity __0,Ammunitions __1,float __result)
    {
        scope=default;
        if(!Active||__1==null)return;
        try
        {
            if((int)__1.TrajectoryType!=10||(int)__1.Seeker!=0||((long)__1.TargetType&(128|256|512|1024))==0)return;
            var weapon=__0;
            if(!weapon.IsAlive||!weapon.Has<WeaponComponent>()||!weapon.Has<TargetComponent>())return;
            var w=NativeEcs.Read<WeaponComponent>(weapon);
            var info=w.WeaponInfo;
            if(info==null||w.SelectedAmmunition==null||w.SelectedAmmunition.Pointer!=__1.Pointer
                ||!InterceptLeadPolicy.Gun((int)info.Type,info.IsRadarDependent,(int)__1.TrajectoryType,
                    (int)__1.Seeker,(long)__1.TargetType))return;
            var target=NativeEcs.Field<TargetComponent,Entity>(weapon,"Target");
            if(!target.IsAlive||!target.Has<UnitComponent>()||!target.Has<WarheadComponent>()||!target.Has<SpeedComponent>()||!target.Has<TransformComponent>())return;
            int type=(int)(NativeEcs.Read<UnitComponent>(target).UnitData?.Type??0);
            if(!InterceptLeadPolicy.Scope((int)info.Type,info.IsRadarDependent,(int)__1.TrajectoryType,
                (int)__1.Seeker,(long)__1.TargetType,type))return;
            var unit=w.GetUnitEntity();if(!unit.IsAlive||!unit.Has<TransformComponent>()||!unit.Has<UnitComponent>())return;
            var hull=NativeEcs.Read<UnitComponent>(unit).UnitData;if(hull==null)return;
            float originRadius=InterceptLeadPolicy.OriginRadius(hull.Length,hull.Width,hull.Height);
            var world=ShootingSystem._gameContext;if(world==null||world._isDisposed)return;
            if(worldPointer!=world.Pointer){histories.Clear();worldPointer=world.Pointer;}
            float now=Time.time;ulong key=Key(target);
            var direction=NativeEcs.Field<SpeedComponent,Vector3>(target,"Direction");
            var velocity=N(direction*NativeEcs.Field<SpeedComponent,float>(target,"Value"));
            if(!histories.TryGetValue(key,out var history))
            {
                if(histories.Count>=MaxTargets)
                    foreach(var old in histories.Where(p=>now-p.Value.LastTime>2).Select(p=>p.Key).ToArray())histories.Remove(old);
                if(histories.Count>=MaxTargets){Fallback("history_capacity");return;}
                history=new InterceptMotionHistory();histories.Add(key,history);
            }
            bool ready=history.Observe(now,velocity,out var acceleration,out float interval);
            scope=new(true,key,weapon,info.Id,__1.Id,type,NativeEcs.Property<TransformComponent,Vector3>(unit,"CenterPosition"),originRadius,
                velocity,acceleration,interval,now,__result,ready,history.Count);
        }
        catch(Exception e){Disable(e);}
    }

    static void LeadThunk(IntPtr targetPointer,IntPtr originPointer,IntPtr dataPointer,int cycles,IntPtr method)
    {
        var call=scope;scope=default;
        // Always preserve the original calculation, including its native failure behavior.
        leadHook.Trampoline(targetPointer,originPointer,dataPointer,cycles,method);
        if(!call.Valid||!Active)return;
        long probeStart=PerfProbe.On?System.Diagnostics.Stopwatch.GetTimestamp():0;   // hook timing (perf-probe.txt only)
        try
        {
        try
        {
            eligible++;
            if(targetPointer==IntPtr.Zero||originPointer==IntPtr.Zero||dataPointer==IntPtr.Zero){Fallback("null_pointer");return;}
            var target=Unsafe.ReadUnaligned<Entity>((void*)targetPointer);
            var origin=Unsafe.ReadUnaligned<Vector3>((void*)originPointer);
            var original=Unsafe.ReadUnaligned<InterceptBallisticValue>((void*)dataPointer);
            if(Key(target)!=call.Target||!target.IsAlive||!call.Weapon.IsAlive
                ||Time.time-call.Time<0||Time.time-call.Time>.05f||!InterceptLeadPolicy.Finite(N(origin))||!InterceptLeadPolicy.Finite(N(call.Center))
                ||(origin-call.Center).sqrMagnitude>call.OriginRadius*call.OriginRadius
                ||Math.Abs(original.InitialProjectileSpeed-call.Speed)>.01f)
            {Fallback("scope_mismatch");return;}
            var native=new InterceptLeadPolicy.Solution(original.VectorToTarget,original.FireVector,original.TimeToImpact,original.FireAngleTan,original.CanShoot!=0);
            if(!call.History){Fallback("history_missing");Record(call,"history_missing",native,null);return;}
            InterceptLeadPolicy.Solution Solve(NVector aim)
            {
                // Overallocate known trailing padding so either validated native
                // size can be solved without touching an undersized CLR proxy.
                byte* buffer=stackalloc byte[64];new Span<byte>(buffer,64).Clear();
                var candidate=original;candidate.VectorToTarget=aim;
                Unsafe.WriteUnaligned(buffer,candidate);
                angleSolver((IntPtr)buffer,angleMethod);
                candidate=Unsafe.ReadUnaligned<InterceptBallisticValue>(buffer);
                return new(aim,candidate.FireVector,candidate.TimeToImpact,candidate.FireAngleTan,candidate.CanShoot!=0);
            }
            if(!InterceptLeadPolicy.TryCorrect(native,call.Velocity,call.Acceleration,Solve,out var result,out string reason))
            {
                Fallback(reason);Record(call,reason,native,null);if(reason=="solver_exception")Disable(new InvalidOperationException("Native ballistic re-solve failed"));return;
            }
            var corrected=original;corrected.VectorToTarget=result.Solution.Aim;corrected.FireVector=result.Solution.Fire;
            corrected.TimeToImpact=result.Solution.Time;corrected.FireAngleTan=result.Solution.Tan;corrected.CanShoot=(byte)(result.Solution.CanShoot?1:0);
            // Commit only a complete validated value. No target position/velocity or
            // weapon tables are changed, and failed solves leave native bytes intact.
            Unsafe.WriteUnaligned((void*)dataPointer,corrected);applied++;
            string pair=call.WeaponId+":"+call.AmmoId;
            if(appliedByWeaponAmmo.ContainsKey(pair)||appliedByWeaponAmmo.Count<128)
                appliedByWeaponAmmo[pair]=appliedByWeaponAmmo.GetValueOrDefault(pair)+1;
            Record(call,"applied",native,result);
        }
        catch(Exception e){Disable(e);}
        }
        finally{if(probeStart!=0)PerfProbe.Record("InterceptLead lead correction (native detour, mod part)",probeStart);}
    }
    static void TrackMissiles()
    {
        var world=ShootingSystem._gameContext;if(world==null||world._isDisposed){missileSet=null;missileWorld=IntPtr.Zero;return;}
        if(missileWorld!=world.Pointer){try{missileSet?.Dispose();}catch{}missileSet=world.GetEntities().With<UnitComponent>().With<WarheadComponent>().With<SpeedComponent>().AsSet();missileWorld=world.Pointer;}
        if(worldPointer!=world.Pointer){histories.Clear();worldPointer=world.Pointer;}
        var list=missileSet._entities;int count=Math.Min(missileSet.Count,list?.Length??0);float now=Time.time;
        for(int i=0;i<count&&i<MaxTargets;i++)
        {
            var e=list[i];if(!e.IsAlive||!e.Has<UnitComponent>()||!e.Has<SpeedComponent>())continue;
            int type=(int)(NativeEcs.Read<UnitComponent>(e).UnitData?.Type??0);if(type is not (128 or 256 or 512 or 1024))continue;
            ulong key=Key(e);
            if(!histories.TryGetValue(key,out var history))
            {
                if(histories.Count>=MaxTargets)
                    foreach(var old in histories.Where(p=>now-p.Value.LastTime>2).Select(p=>p.Key).ToArray())histories.Remove(old);
                if(histories.Count>=MaxTargets)return;
                history=new InterceptMotionHistory();histories.Add(key,history);
            }
            var velocity=N(NativeEcs.Field<SpeedComponent,Vector3>(e,"Direction")*NativeEcs.Field<SpeedComponent,float>(e,"Value"));
            history.Observe(now,velocity,out _,out _);tracked++;
        }
    }
    static void Record(Scope call,string reason,InterceptLeadPolicy.Solution native,InterceptLeadPolicy.Result? result)
    {
        if(logged+samples.Count>=MaxSamples||samples.Count>=512){dropped++;return;}
        var r=result.GetValueOrDefault();
        samples.Enqueue(new(call.Time,call.Target,call.WeaponId,call.AmmoId,call.TargetType,call.HistoryInterval,result.HasValue?r.Acceleration:call.Acceleration,
            native.Aim,result.HasValue?r.Solution.Aim:native.Aim,result.HasValue?r.Solution.Fire:native.Fire,native.Time,result.HasValue?r.Solution.Time:native.Time,
            result.HasValue?r.Iterations:0,result.HasValue&&r.Limited,reason,call.Velocity,call.HistoryCount));
    }
    static object R(NVector v)=>new[]{MathF.Round(v.X,1),MathF.Round(v.Y,1),MathF.Round(v.Z,1)};
    static void Disable(Exception e){off=true;scope=default;pendingError=e.ToString();}
    public static void SceneChanged(){scope=default;histories.Clear();worldPointer=IntPtr.Zero;try{missileSet?.Dispose();}catch{}missileSet=null;missileWorld=IntPtr.Zero;}
    public static void LateUpdate()
    {
        if(!installed&&retryAt!=0&&!off&&Environment.TickCount64>=retryAt&&TryAttach())Installed();
        if(!installed)return;
        mainThread=Environment.CurrentManagedThreadId;
        if(pendingError!=null)
        {
            DiagnosticLog.Write("intercept_lead_failed",new{error=pendingError,fallback="native leading for rest of session"});
            MelonLogger.Error("FREEDOM_ARROW_INTERCEPT_LEAD_FAILED: native leading restored; "+pendingError);pendingError=null;
        }
        for(int i=0;i<64&&samples.TryDequeue(out var s);i++)
        {
            logged++;DiagnosticLog.Write("intercept_lead",new{t=MathF.Round(s.Time,3),target=s.Target.ToString("X16"),weapon=s.WeaponId,reason=s.Reason,
                hist=s.HistoryCount,histS=MathF.Round(s.HistoryInterval,3),vel=R(s.Velocity),acc=R(s.Acceleration),nat=R(s.Before),cor=R(s.After),
                tNat=MathF.Round(s.BeforeTime,3),tCor=MathF.Round(s.AfterTime,3),it=s.Iterations,lim=s.Limited});
        }
        if(Time.time>=nextSummary)
        {
            nextSummary=Time.time+5;
            DiagnosticLog.Write("intercept_lead_summary",new{t=Time.time,eligible,applied,off,logged,dropped,tracked,
                appliedByWeaponAmmo=new Dictionary<string,long>(appliedByWeaponAmmo),fallbackReasons=new Dictionary<string,long>(fallbacks)});
        }
        if(!Conquest.Prototype.DiagnosticSceneActive){scope=default;histories.Clear();}
        else if(!off)
        {
            try{TrackMissiles();}
            catch(Exception e){missileSet=null;missileWorld=IntPtr.Zero;DiagnosticLog.Write("intercept_lead_track_failed",new{error=e.ToString()});off=true;
                MelonLogger.Error("FREEDOM_ARROW_INTERCEPT_LEAD_FAILED: missile tracking; native leading restored. "+e.Message);}
        }
    }
    public static void Close()
    {
        if(!installed)return;
        off=true;LateUpdate();
        for(int i=0;i<16&&samples.Count>0;i++)LateUpdate();
        DiagnosticLog.Write("intercept_lead_final",new{shutdown=true,eligible,applied,logged,dropped,pending=samples.Count,appliedByWeaponAmmo=new Dictionary<string,long>(appliedByWeaponAmmo),fallbackReasons=new Dictionary<string,long>(fallbacks)});
        installed=false;harmony?.UnpatchSelf();if(leadHook?.IsHooked==true)leadHook.Detach();SceneChanged();
    }
}

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

// Separate active experiment; GroundAaLog remains a passive observer.
// A verified C-RAM muzzle query supplies a one-use, thread-local scope. Only the
// immediately following matching SEAD lead solution can be changed.
internal static unsafe class CramPrediction
{
    const string GameHash="12e7088369539b029a7bf0064062ce030a53b5189e7067420903f47b4281fddf";
    const int MaxTargets=128,MaxSamples=1000;
    // Explicit pointer ABI avoids automatic marshaling of the two bool fields
    // in ref BallisticDataStruct. Native metadata/layout and engine hash gate it.
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    delegate void LeadNative(IntPtr target,IntPtr origin,IntPtr data,int cycles,IntPtr method);
    static readonly LeadNative LeadCallback=LeadThunk;
    static NativeHook<LeadNative> leadHook;
    static HarmonyLib.Harmony harmony;
    static bool installed,off;
    static int mainThread,logged;
    static IntPtr worldPointer;
    static long eligible,applied,dropped;
    static float nextSummary;
    static string pendingError;
    static readonly Dictionary<ulong,CramMotionHistory> histories=new();
    static readonly Dictionary<string,long> fallbacks=new();
    readonly record struct Scope(bool Valid,ulong Target,Entity Weapon,Vector3 Center,
        NVector Velocity,NVector Acceleration,float HistoryInterval,float Time,float Speed,bool History);
    readonly record struct Sample(float Time,ulong Target,float HistoryInterval,NVector Acceleration,
        NVector Before,NVector After,NVector Fire,float BeforeTime,float AfterTime,int Iterations,bool Limited);
    [ThreadStatic] static Scope scope;
    static readonly Queue<Sample> samples=new();
    static ulong Key(Entity e)=>Unsafe.As<Entity,ulong>(ref e);
    static NVector N(Vector3 v)=>new(v.x,v.y,v.z);
    static Vector3 U(NVector v)=>new(v.X,v.Y,v.Z);
    static object V(NVector v)=>new{x=v.X,y=v.Y,z=v.Z};
    static void Fallback(string reason)=>fallbacks[reason]=fallbacks.GetValueOrDefault(reason)+1;
    static bool Active=>installed&&!off&&Environment.CurrentManagedThreadId==mainThread
        &&Runtime.IsApplied&&Conquest.Prototype.DiagnosticSceneActive;

    public static void Install()
    {
        if(IntPtr.Size!=8||Unsafe.SizeOf<Entity>()!=8||Unsafe.SizeOf<Vector3>()!=12
            ||Unsafe.SizeOf<BallisticDataStruct>()!=44||RuntimeHelpers.IsReferenceOrContainsReferences<BallisticDataStruct>())
            throw new InvalidOperationException("Prediction ABI does not match the pinned x64 value layouts");
        using(var file=File.OpenRead(Path.Combine(MelonEnvironment.GameRootDirectory,"GameAssembly.dll")))
        using(var sha=SHA256.Create())
            if(Convert.ToHexString(sha.ComputeHash(file)).ToLowerInvariant()!=GameHash)
                throw new InvalidOperationException("Prediction engine fingerprint mismatch");
        RuntimeHelpers.RunClassConstructor(typeof(BallisticDataStruct).TypeHandle);
        var klass=Il2CppClassPointerStore<BallisticDataStruct>.NativeClassPtr;uint align=0;
        if(IL2CPP.il2cpp_class_value_size(klass,ref align)!=44)throw new InvalidOperationException("Native ballistic size mismatch");
        foreach(var (name,offset) in new[]{("VectorToTarget",0),("InitialProjectileSpeed",12),("FireVector",16),
            ("FireAngleTan",28),("TimeToImpact",32),("GravityMultiplyer",36),("CanShoot",40),("<Initialized>k__BackingField",41)})
        {
            var field=IL2CPP.il2cpp_class_get_field_from_name(klass,name);
            if(field==IntPtr.Zero||IL2CPP.il2cpp_field_get_offset(field)-2*IntPtr.Size!=offset)
                throw new InvalidOperationException("Native ballistic field mismatch: "+name);
        }
        RuntimeHelpers.RunClassConstructor(typeof(BallisticsCalculationsHelper).TypeHandle);
        var method=(IntPtr)(typeof(BallisticsCalculationsHelper).GetFields(BindingFlags.Static|BindingFlags.NonPublic)
            .Single(f=>f.Name.StartsWith("NativeMethodInfoPtr_CalculateLeadShot_",StringComparison.Ordinal)).GetValue(null)
            ??throw new MissingMethodException("CalculateLeadShot metadata"));
        if(method==IntPtr.Zero||Marshal.ReadIntPtr(method)==IntPtr.Zero)throw new MissingMethodException("CalculateLeadShot");
        var muzzle=AccessTools.Method(typeof(BattleSystemHelpers),"GetShellMuzzleSpeed",new[]{typeof(Entity).MakeByRefType(),typeof(Ammunitions)})
            ??throw new MissingMethodException("GetShellMuzzleSpeed(in Entity,Ammunitions)");
        mainThread=Environment.CurrentManagedThreadId;
        harmony=new HarmonyLib.Harmony("FreedomArrow.CramPrediction");
        var callbackPointer=Marshal.GetFunctionPointerForDelegate(LeadCallback);
        _=Marshal.GetDelegateForFunctionPointer<LeadNative>(Marshal.ReadIntPtr(method));
        try
        {
            harmony.Patch(muzzle,postfix:new HarmonyMethod(typeof(CramPrediction),nameof(MuzzleAfter)));
            leadHook=new NativeHook<LeadNative>(Marshal.ReadIntPtr(method),callbackPointer);
            leadHook.Attach();installed=true;
        }
        catch
        {
            if(leadHook?.IsHooked==true)leadHook.Detach();
            harmony.UnpatchSelf();throw;
        }
        DiagnosticLog.Write("cram_prediction_installed",new{weapon=345,ammo=262,targetType=256,seeker=200,nativeHooks=2,
            horizon=CramPredictionPolicy.MaxHorizon,maxCorrection=CramPredictionPolicy.MaxCorrection,
            maxFraction=CramPredictionPolicy.MaxFraction,abi="x64 pointer lead detour;44-byte ballistic value",appliedCalls=0});
        MelonLogger.Msg("FREEDOM_ARROW_CRAM_PREDICTION installed; invocation unproved until cram_prediction_applied; C-RAM/SEAD only");
    }

    static void MuzzleAfter(ref Entity __0,Ammunitions __1,float __result)
    {
        scope=default;
        if(!Active||__1==null)return;
        try
        {
            if(__1.Id!=262)return;
            var weapon=__0;
            if(!weapon.IsAlive||!weapon.Has<WeaponComponent>()||!weapon.Has<TargetComponent>())return;
            var w=NativeEcs.Read<WeaponComponent>(weapon);
            if(w.WeaponInfo?.Id!=345||w.SelectedAmmunition?.Id!=262||w.SelectedAmmunition.Pointer!=__1.Pointer)return;
            var target=NativeEcs.Field<TargetComponent,Entity>(weapon,"Target");
            if(!target.IsAlive||!target.Has<UnitComponent>()||!target.Has<WarheadComponent>()||!target.Has<SpeedComponent>()||!target.Has<TransformComponent>())return;
            int type=(int)(NativeEcs.Read<UnitComponent>(target).UnitData?.Type??0);
            var ammo=NativeEcs.Read<WarheadComponent>(target).AmmunitionInfo;
            if(!CramPredictionPolicy.Scope(345,262,type,(int)(ammo?.Seeker??0)))return;
            var unit=w.GetUnitEntity();if(!unit.IsAlive||!unit.Has<TransformComponent>())return;
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
                history=new CramMotionHistory();histories.Add(key,history);
            }
            bool ready=history.Observe(now,velocity,out var acceleration,out float interval);
            scope=new(true,key,weapon,NativeEcs.Property<TransformComponent,Vector3>(unit,"CenterPosition"),
                velocity,acceleration,interval,now,__result,ready);
        }
        catch(Exception e){Disable(e);}
    }

    static void LeadThunk(IntPtr targetPointer,IntPtr originPointer,IntPtr dataPointer,int cycles,IntPtr method)
    {
        var call=scope;scope=default;
        // Always preserve the original calculation, including its native failure behavior.
        leadHook.Trampoline(targetPointer,originPointer,dataPointer,cycles,method);
        if(!call.Valid||!Active)return;
        try
        {
            eligible++;
            if(targetPointer==IntPtr.Zero||originPointer==IntPtr.Zero||dataPointer==IntPtr.Zero){Fallback("null_pointer");return;}
            var target=Unsafe.ReadUnaligned<Entity>((void*)targetPointer);
            var origin=Unsafe.ReadUnaligned<Vector3>((void*)originPointer);
            var original=Unsafe.ReadUnaligned<BallisticDataStruct>((void*)dataPointer);
            if(Key(target)!=call.Target||!target.IsAlive||!call.Weapon.IsAlive
                ||Time.time-call.Time<0||Time.time-call.Time>.05f||(origin-call.Center).sqrMagnitude>225
                ||Math.Abs(original.InitialProjectileSpeed-call.Speed)>.01f)
            {Fallback("scope_mismatch");return;}
            if(!call.History){Fallback("history_missing");return;}
            var native=new CramPredictionPolicy.Solution(N(original.VectorToTarget),N(original.FireVector),original.TimeToImpact,original.FireAngleTan,original.CanShoot);
            CramPredictionPolicy.Solution Solve(NVector aim)
            {
                var candidate=original;candidate.VectorToTarget=U(aim);
                BallisticsCalculationsHelper.CalculateBallisticsAngle(ref candidate);
                return new(aim,N(candidate.FireVector),candidate.TimeToImpact,candidate.FireAngleTan,candidate.CanShoot);
            }
            if(!CramPredictionPolicy.TryCorrect(native,call.Velocity,call.Acceleration,Solve,out var result,out string reason))
            {
                Fallback(reason);if(reason=="solver_exception")Disable(new InvalidOperationException("Native ballistic re-solve failed"));return;
            }
            var corrected=original;corrected.VectorToTarget=U(result.Solution.Aim);corrected.FireVector=U(result.Solution.Fire);
            corrected.TimeToImpact=result.Solution.Time;corrected.FireAngleTan=result.Solution.Tan;corrected.CanShoot=result.Solution.CanShoot;
            // Commit only a complete validated value. No target position/velocity or
            // weapon tables are changed, and failed solves leave native bytes intact.
            Unsafe.WriteUnaligned((void*)dataPointer,corrected);applied++;
            if(logged+samples.Count<MaxSamples&&samples.Count<128)
                samples.Enqueue(new(call.Time,call.Target,call.HistoryInterval,result.Acceleration,native.Aim,result.Solution.Aim,
                    result.Solution.Fire,native.Time,result.Solution.Time,result.Iterations,result.Limited));
            else dropped++;
        }
        catch(Exception e){Disable(e);}
    }
    static void Disable(Exception e){off=true;scope=default;pendingError=e.ToString();}
    public static void SceneChanged(){scope=default;histories.Clear();worldPointer=IntPtr.Zero;}
    public static void LateUpdate()
    {
        if(!installed)return;
        mainThread=Environment.CurrentManagedThreadId;
        if(pendingError!=null)
        {
            DiagnosticLog.Write("cram_prediction_failed",new{error=pendingError,fallback="native leading for rest of session"});
            MelonLogger.Error("FREEDOM_ARROW_CRAM_PREDICTION_FAILED: native leading restored; "+pendingError);pendingError=null;
        }
        for(int i=0;i<8&&samples.TryDequeue(out var s);i++)
        {
            logged++;DiagnosticLog.Write("cram_prediction_applied",new{t=s.Time,target=s.Target.ToString("X16"),weapon=345,ammo=262,
                historySeconds=s.HistoryInterval,acceleration=V(s.Acceleration),nativeVector=V(s.Before),correctedVector=V(s.After),
                fireVector=V(s.Fire),nativeTime=s.BeforeTime,correctedTime=s.AfterTime,iterations=s.Iterations,limited=s.Limited,
                caveat="Native lead calculation; may be aiming or launch, not a shot counter"});
        }
        if(Time.time>=nextSummary)
        {
            nextSummary=Time.time+5;
            DiagnosticLog.Write("cram_prediction_summary",new{t=Time.time,eligible,applied,off,logged,dropped,
                fallbackReasons=new Dictionary<string,long>(fallbacks)});
        }
        if(!Conquest.Prototype.DiagnosticSceneActive){scope=default;histories.Clear();}
    }
    public static void Close()
    {
        if(!installed)return;
        off=true;LateUpdate();
        for(int i=0;i<16&&samples.Count>0;i++)LateUpdate();
        DiagnosticLog.Write("cram_prediction_final",new{shutdown=true,eligible,applied,logged,dropped,pending=samples.Count,fallbackReasons=new Dictionary<string,long>(fallbacks)});
        installed=false;harmony?.UnpatchSelf();if(leadHook?.IsHooked==true)leadHook.Detach();SceneChanged();
    }
}

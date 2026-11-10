using System.Text.Json.Nodes;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.Configs;
using Il2CppBrokenArrow.Client.Ecs.Economy.Systems;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppDefaultEcs;
using MelonLoader;
namespace FreedomArrow;

// Only primitive arguments and in Entity cross the hook boundary. Do not hook the
// nullable/struct-heavy purchase-delay method. All refund calls share the lock,
// so another unit cannot read the temporary plane coefficient during a refund.
static class PlaneRefund
{
    static readonly object Gate=new();
    static float healthMultiplier;
    static int logged;
    sealed class Saved { public bool Locked,Changed; public float Original; public GameConfig Config; public bool Plane; }
    public static void Install(HarmonyLib.Harmony harmony,string root)
    {
        var c=JsonNode.Parse(File.ReadAllText(Path.Combine(root,"game-config.json")));
        healthMultiplier=c["PlaneRefundHealthMultiplier"].GetValue<float>();
        if(!float.IsFinite(healthMultiplier)||healthMultiplier<0||healthMultiplier>1)throw new InvalidDataException("PlaneRefundHealthMultiplier must be 0..1");
        harmony.Patch(AccessTools.Method(typeof(RefundSystem),"RefundUnit"),
            prefix:new HarmonyMethod(typeof(PlaneRefund),nameof(Before)){priority=Priority.First},
            postfix:new HarmonyMethod(typeof(PlaneRefund),nameof(After)),
            finalizer:new HarmonyMethod(typeof(PlaneRefund),nameof(Finally)));
        MelonLogger.Msg($"FREEDOM_ARROW_PLANE_REFUND installed health multiplier {healthMultiplier}; original cap/floor and timers retained; invocation unproved");
    }
    static void Before(in Entity __0,out Saved __state)
    {
        __state=new Saved();
        Monitor.Enter(Gate);__state.Locked=true;
        try
        {
            var cfg=GameConfig.Instance;
            if(cfg==null)return;
            __state.Config=cfg;__state.Original=cfg.HealthCostMultiplier;
            if(!Runtime.IsApplied||!__0.IsAlive||!__0.Has<UnitComponent>())return;
            var data=NativeEcs.Read<UnitComponent>(__0).UnitData;
            __state.Plane=data!=null&&(int)data.CategoryType==6;
            if(!__state.Plane)return;
            __state.Changed=true;cfg.HealthCostMultiplier=healthMultiplier;
        }
        catch(Exception e)
        {
            if(__state.Changed)__state.Config.HealthCostMultiplier=__state.Original;
            __state.Changed=false;
            DiagnosticLog.Write("plane_refund_failed",new{error=e.Message});
        }
    }
    static void After(in Entity __0,bool __1,float __result,Saved __state)
    {
        if(__state?.Changed!=true||(__1&&Volatile.Read(ref logged)>=15)||Interlocked.Increment(ref logged)>600)return;
        try
        {
            var data=NativeEcs.Read<UnitComponent>(__0).UnitData;
            DiagnosticLog.Write("plane_refund",new{unit=data.Id,cost=data.Cost,onlyCount=__1,refund=__result,
                healthMultiplier,cap=__state.Config.MaximumRefundPercent,floor=__state.Config.MinimumRefundPercent});
        }
        catch(Exception e){DiagnosticLog.Write("plane_refund_log_failed",new{error=e.Message});}
    }
    static Exception Finally(Exception __exception,Saved __state)
    {
        try { if(__state?.Changed==true)__state.Config.HealthCostMultiplier=__state.Original; }
        finally { if(__state?.Locked==true)Monitor.Exit(Gate); }
        return __exception;
    }
}

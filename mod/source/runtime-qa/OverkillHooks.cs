using System.Threading;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems;
using Il2CppDefaultEcs;
using MelonLoader;
namespace FreedomArrow;

// 0.9.0-dev.37 (Osama 17 Nov 2026 14:0x PST, thread 1567745029781454889: "merge the three over kill hooks"). AaCooldown, SameUnitClaim and
// SeadOverkill each put a postfix on OverkillScoringSystem.IsTargetOverkilled, which the game calls about 3,900 times a second in a 5v5.
// Now there is one postfix that calls the three bodies in the order Harmony ran them before: AaCooldown (normal priority) first, then
// SameUnitClaim and SeadOverkill (both Priority.Last, in install order). Each module's Install calls Use() instead of patching. A module
// that throws is switched off for the session (logged once); the other two keep running. Counters: HookHealth.cs.
static class OverkillHooks
{
    static bool aa,claim,sead,installed;
    public static long Calls;
    public static readonly string[] Errors=new string[3];
    public static string Modules=>string.Join("+",new[]{aa?"aa_cooldown":null,claim?"same_unit_claim":null,sead?"sead_overkill":null}.Where(x=>x!=null));
    public static void Use(string module)
    {
        if(module=="aa_cooldown")aa=true;else if(module=="same_unit_claim")claim=true;else if(module=="sead_overkill")sead=true;
        else throw new ArgumentException(module);
    }
    // After every module Install (Runtime.cs), once.
    public static void Install(HarmonyLib.Harmony harmony)
    {
        if(installed||!(aa||claim||sead))return;
        var m=AccessTools.Method(typeof(OverkillScoringSystem),"IsTargetOverkilled")??throw new MissingMethodException("IsTargetOverkilled");
        harmony.Patch(m,postfix:new HarmonyMethod(typeof(OverkillHooks),nameof(After)));installed=true;
        MelonLogger.Msg($"FREEDOM_ARROW_OVERKILL_HOOK installed: one postfix on IsTargetOverkilled for {Modules}");
        DiagnosticLog.Write("overkill_hook_installed",new{modules=Modules});
    }
    // Native callback; may run off the main thread (the module bodies only read snapshots and use Interlocked counters).
    static void After(ref Entity __0,ref Entity __3,bool __7,ref bool __result)
    {
        Interlocked.Increment(ref Calls);
        if(aa)try{AaCooldown.After(ref __0,ref __3,__7,ref __result);}catch(Exception e){aa=false;Fail(0,"aa_cooldown",e);}
        if(claim)try{SameUnitClaim.After(ref __0,ref __3,ref __result);}catch(Exception e){claim=false;Fail(1,"same_unit_claim",e);}
        if(sead)try{SeadOverkill.After(ref __0,ref __3,__result);}catch(Exception e){sead=false;Fail(2,"sead_overkill",e);}
    }
    static void Fail(int i,string module,Exception e)
    {
        Errors[i]=e.GetType().Name+": "+e.Message;
        MelonLogger.Error($"FREEDOM_ARROW_OVERKILL_HOOK {module} failed and is off for this session (native behaviour for it): {e}");
        DiagnosticLog.Write("overkill_hook_failed",new{module,error=e.ToString()});
    }
}

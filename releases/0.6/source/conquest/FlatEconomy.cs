using System.Reflection;
using Il2CppBrokenArrow.Client.Ecs.Controllers;
using Il2CppBrokenArrow.Client.Ecs.Economy;
using Il2CppBrokenArrow.Client.Ecs.Utils;

namespace FreedomArrow.Conquest;
public sealed partial class Prototype
{
    static readonly EconomyWindow economyWindow = new();
    static readonly List<(PlayerInfo player, float rate)> economyRates = new();
    static Func<bool> economyGuard, economyOnlineGuard, economyRuntime;
    static int economyThread;
    static int economyDepth;
    static IntPtr economySession;
    static bool economyFailed;
    static volatile bool economyConflict;
    static volatile bool economyForeignThread;
    static int economyLogBucket = -1;
    static string economyLastReason = "";

    // 0.6 dev.3: FlatIncomeMod 0.9.16 has no income code (read from its decompiled source), so only the engine counts.
    static bool IsEconomyWriter(Assembly a) => a.GetName().Name is "FreedomArrow.Engine";
    static void EconomyAssemblyLoaded(object sender, AssemblyLoadEventArgs e)
    { if (IsEconomyWriter(e.LoadedAssembly)) economyConflict = true; }
    static void InitializeEconomy()
    {
        if (config.FixedIncomePerMinute == 0) return;
        economyConflict = AppDomain.CurrentDomain.GetAssemblies().Any(IsEconomyWriter);
        AppDomain.CurrentDomain.AssemblyLoad += EconomyAssemblyLoaded;
        BindEconomyGuards();
        Patch(typeof(PlayerEconomyService), "Update", nameof(EconomyBefore), nameof(EconomyAfter));
        Log("economy_registered", new { perMinute = config.FixedIncomePerMinute,
            perSimulationSecond = EconomyWindow.PerSecond(config.FixedIncomePerMinute),
            scope = "local setup battles and private scenario lobbies; online execution unverified" });
    }
    static void BindEconomyGuards()
    {
        foreach (var a in AppDomain.CurrentDomain.GetAssemblies())
        {
            if (economyGuard == null && a.GetName().Name == "BALocalSkirmish")
            {
                economyGuard = BindBool(a, "BALocalSkirmish.Core", "IsGuardedLocalBattle");
                economyOnlineGuard = BindBool(a, "BALocalSkirmish.Core", "IsOnlineScenarioBattle");
            }
            if (economyRuntime == null && a.GetName().Name == "FreedomArrow.Runtime")
                economyRuntime = BindBool(a, "FreedomArrow.Runtime", "IsApplied");
        }
    }
    static Func<bool> BindBool(Assembly a, string type, string name)
    {
        var p = a.GetType(type)?.GetProperty(name, BindingFlags.Public | BindingFlags.Static);
        return p?.PropertyType == typeof(bool) && p.GetMethod != null
            ? (Func<bool>)p.GetMethod.CreateDelegate(typeof(Func<bool>)) : null;
    }
    static EconomyState ReadEconomy() => new(PlayerEconomyService.UseIncomeCurve,
        PlayerEconomyService.CurrentGlobalUpkeepModifier, PlayerEconomyService.CurrentUpkeepFloor);
    static void WriteEconomy(EconomyState s)
    {
        PlayerEconomyService.UseIncomeCurve = s.Curve;
        PlayerEconomyService.CurrentGlobalUpkeepModifier = s.Upkeep;
        PlayerEconomyService.CurrentUpkeepFloor = s.Floor;
    }
    static IntPtr CurrentEconomySession()
    {
        var game = GameController.Instance;
        return game == null || game.GameSession == null ? IntPtr.Zero : game.GameSession.Pointer;
    }
    static void CloseEconomy(IntPtr current, string reason)
    {
        if (!economyWindow.Active && economyRates.Count == 0) { economyDepth = 0; return; }
        if (current != IntPtr.Zero && current != economySession)
        {
            economyWindow.Discard(); economyRates.Clear();
            economyDepth = 0;
            Log("economy_scope_discarded", new { reason, explanation = "new session owns native values" });
            return;
        }
        // Restore rates only while the original session is still current. Keep references local
        // to the update window; never write discarded player wrappers after a scene transition.
        // Restore global policy first. A failed player setter must not leave zero-upkeep
        // statics active while the native update is refused pending another cleanup attempt.
        economyWindow.End(WriteEconomy);
        if (current == economySession)
            foreach (var p in economyRates) if (p.player.PlayerIncome.Value != p.rate) p.player.PlayerIncome = p.rate;
        economyRates.Clear();
        economyDepth = 0;
    }
    static void EconomyFrame()
    {
        if (config.FixedIncomePerMinute == 0) return;
        economyThread = Environment.CurrentManagedThreadId;
        try
        {
            if (economyForeignThread)
                EconomyFault(new InvalidOperationException("Economy Update observed on another thread; override disabled"));
            if (economyWindow.Active || economyRates.Count != 0)
            {
                EconomyFault(new InvalidOperationException("Economy postfix did not close its scope; restoring before further overrides"));
                CloseEconomy(CurrentEconomySession(), "frame cleanup after skipped postfix");
            }
            if (economyGuard == null || economyRuntime == null) BindEconomyGuards();
        }
        catch (Exception e) { EconomyFault(e); }
    }
    static void EconomyFault(Exception e)
    {
        if (!economyFailed) Log("economy_failed", new { e.Message, scopePending = economyWindow.Active });
        economyFailed = true;
    }
    static bool EconomyAllowed(PlayerEconomyService service, out string reason)
    {
        reason = "";
        if (config.FixedIncomePerMinute == 0) reason = "disabled";
        else if (!initialized || economyFailed || !config.Enabled) reason = "plugin not ready"; // A scoring fault must not stop flat income.
        else if (economyThread == 0 || Environment.CurrentManagedThreadId != economyThread) reason = "not the observed Unity update thread";
        else if (economyConflict) reason = "another known economy writer is loaded";
        else if (economyRuntime?.Invoke() is not true) reason = "gameplay payload not applied";
        else if (service == null || service._session == null) reason = "no economy session";
        else if (service._netRoomService == null && economyGuard?.Invoke() is not true) reason = "Local Skirmish guard not initialized";
        else if (service._netRoomService != null && economyOnlineGuard?.Invoke() is not true) reason = "network session is not a private-rule scenario lobby";
        else if (service._netRoomService != null && !(service._netRoomService.NetUserRoomStateHandler?.IncomeMultiplayer > 0)) reason = "network income multiplier unavailable";
        else if (CurrentEconomySession() != service._session.Pointer) reason = "economy session is not the current game";
        return reason.Length == 0;
    }
    public static bool EconomyBefore(PlayerEconomyService __instance, out bool __state)
    {
        __state = false;
        if (economyThread == 0) return true;
        if (Environment.CurrentManagedThreadId != economyThread)
        {
            economyForeignThread = true; // Report on the Unity thread; no worker-side log/native writes.
            return System.Threading.Volatile.Read(ref economyDepth) == 0;
        }
        try
        {
            // A nested call must not close its caller's scope. OnUpdate owns cleanup if a
            // postfix was skipped; refuse this call until that same-thread cleanup runs.
            if (economyDepth != 0) { EconomyFault(new InvalidOperationException("Nested or unfinished economy update")); return false; }
            if (!EconomyAllowed(__instance, out string reason))
            {
                if (reason != economyLastReason) { Log("economy_inactive", new { reason }); economyLastReason = reason; }
                return true; // Native economy remains responsible when this override is inactive.
            }
            economyLastReason = ""; // A later loss of the same guard must produce a fresh log.
            economySession = __instance._session.Pointer;
            economyRates.Clear();
            int humans = 0, bots = 0;
            foreach (var pair in __instance._session._players)
            {
                var player = pair.Value; // Same dictionary and entries as native Update; no filter.
                economyRates.Add((player, player.PlayerIncome.Value));
                if (player.IsBot) bots++; else humans++;
            }
            economyDepth = 1;
            economyWindow.Begin(ReadEconomy, WriteEconomy);
            float rate = EconomyWindow.PerSecond(config.FixedIncomePerMinute);
            // Native online income is PlayerIncome x this lobby multiplier (Update at 0x6D8820).
            if (__instance._netRoomService != null) rate /= __instance._netRoomService.NetUserRoomStateHandler.IncomeMultiplayer;
            foreach (var entry in economyRates)
                if (entry.player.PlayerIncome.Value != rate) entry.player.PlayerIncome = rate;
            int bucket = (int)UnityEngine.Time.unscaledTime / 10;
            if (bucket != economyLogBucket)
            {
                economyLogBucket = bucket;
                Log("economy_scope_prepared", new { perMinute = config.FixedIncomePerMinute,
                    perSecond = rate, humans, bots, originalRates = economyRates.Select(p => new { uid = p.player.UID, perSecond = p.rate }).ToArray(),
                    note = "scenario income bonuses are overridden within this call; this is not a credit measurement" });
            }
            __state = true;
            return true;
        }
        catch (Exception e)
        {
            EconomyFault(e);
            try { CloseEconomy(CurrentEconomySession(), "prefix rollback"); } catch (Exception restore) { EconomyFault(restore); }
            return !economyWindow.Active && economyRates.Count == 0;
        }
    }
    public static void EconomyAfter(PlayerEconomyService __instance, bool __state)
    {
        if (!__state) return;
        if (!economyWindow.Active && economyRates.Count == 0) return;
        try { CloseEconomy(__instance?._session?.Pointer ?? IntPtr.Zero, "normal postfix"); }
        catch (Exception e) { EconomyFault(e); }
    }
    public override void OnDeinitializeMelon()
    {
        try { if (economyWindow.Active || economyRates.Count != 0) CloseEconomy(CurrentEconomySession(), "plugin unload"); }
        catch (Exception e) { EconomyFault(e); }
        AppDomain.CurrentDomain.AssemblyLoad -= EconomyAssemblyLoaded;
    }
}

using System.Reflection;
using System.Security.Cryptography;
using System.Text.Json;
using HarmonyLib;
using MelonLoader;
using MelonLoader.Utils;
using UnityEngine;
using Il2CppBrokenArrow.Client.Ecs.GameMode;
using Il2CppBrokenArrow.Client.Ecs.UI.HUD.GameModes.WarGoals;
using Il2CppBrokenArrow.MissionEditor.Data.ObjectiveZone;
using Il2CppBrokenArrow.MissionEditor.MissionResolver;
using Il2CppNetworkCommon.Enums;
using Il2CppNetworkCommon.Messages.GameModes;
using NativeScores = Il2CppSystem.Collections.Generic.Dictionary<Il2CppNetworkCommon.Enums.TeamSide, int>;
using NativeZones = Il2CppSystem.Collections.Generic.List<Il2CppBrokenArrow.MissionEditor.Data.ObjectiveZone.ObjectiveZoneScript>;
using NativeOwners = Il2CppSystem.Collections.Generic.Dictionary<Il2CppNetworkCommon.Enums.TeamSide, Il2CppSystem.Collections.Generic.HashSet<int>>;

[assembly: MelonInfo(typeof(FreedomArrow.Conquest.Prototype), "Freedom Arrow Conquest", "0.2.0-dev.10", "Freedom Arrow development")]
[assembly: MelonGame(null, null)]
[assembly: HarmonyDontPatchAll]
namespace FreedomArrow.Conquest;

public sealed partial class Prototype : MelonMod
{
    public const string HarmonyId = "freedomarrow.conquestbatch";
    static readonly string Root = Path.Combine(MelonEnvironment.GameRootDirectory, "UserData", "FAConquestPrototype");
    static readonly string ConfigFile = Path.Combine(Root, "settings.json");
    static readonly string WeightOverridesFile = Path.Combine(Root, "weights-overrides.json");
    static Settings config = new();
    static Prototype instance;
    static PropertyInfo localGuard;
    static View view;
    static Ledger ledger;
    static List<Zone> zones = new();
    static bool ready, faulted;
    static string status = "Waiting for verified offline Local Skirmish";
    static string logPath = "";
    static int sequence;
    static long match;
    static double lastTelemetry = -10;

    // Public hooks prevent private generated-wrapper access problems when Harmony emits a trampoline.
    public override void OnInitializeMelon()
    {
        instance = this;
        Directory.CreateDirectory(Root);
        logPath = Path.Combine(Root, $"events-{DateTime.UtcNow:yyyyMMdd-HHmmss}-{Environment.ProcessId}.jsonl");
        try
        {
            config = JsonSerializer.Deserialize<Settings>(File.ReadAllText(ConfigFile), Settings.Json) ?? throw new InvalidDataException("Missing settings");
            config.Validate();
            VerifyInputs();
            if(File.Exists(WeightOverridesFile))
            {
                var overrides=JsonSerializer.Deserialize<Dictionary<string,Dictionary<string,int>>>(File.ReadAllText(WeightOverridesFile),Settings.Json)
                    ??throw new InvalidDataException("Invalid saved weight overrides");
                foreach(var map in overrides)config.MapZoneWeights[map.Key]=map.Value;
                config.Validate();
                Log("saved_weights_loaded",overrides);
            }
            if (!config.Enabled) { status = "Disabled in settings.json"; Log("disabled", new { }); return; }
            // Do not compete with the other task's scoring/economy experiment or ActualArrow hooks.
            foreach (var a in AppDomain.CurrentDomain.GetAssemblies())
            {
                if (a.GetName().Name is "FlatIncomeMod")
                    throw new InvalidOperationException("Disable FlatIncomeMod for this scoring experiment");
                if(a.GetName().Name=="FreedomArrow.Engine" && a.GetType("FreedomArrow.Engine")?.GetProperty("UsesConquestBatch")?.GetValue(null) is not true)
                    throw new InvalidOperationException("Engine has not delegated its mode/timer/phase hooks to ConquestBatch");
            }
            Patch(typeof(GameModeService), "SetWarGoalsMode", nameof(SetWar), null);
            Patch(typeof(GameModeService), "SetConquestGameMode", nameof(SetConquest), null);
            Patch(typeof(WarGoalsMode), "OnTimerTick", nameof(WarTimerBefore), nameof(WarTimerAfter));
            Patch(typeof(ConquestMode), "OnTimerTick", nameof(ConquestTimerBefore), nameof(ConquestTimerAfter));
            Patch(typeof(WarGoalsMode), "CalculateEndPhase", nameof(PhaseBefore), nameof(WarPhaseAfter));
            Patch(typeof(ConquestMode), "CalculateEndPhase", nameof(PhaseBefore), nameof(ConquestPhaseAfter));
            Patch(typeof(WarGoalsMode), "GetWinner", nameof(WarWinner), nameof(WarWinnerAfter));
            Patch(typeof(ConquestMode), "GetWinner", nameof(ConquestWinner), nameof(ConquestWinnerAfter));
            Patch(typeof(GameModeService), "OnWinnerFound", nameof(WinnerFoundBefore), null);
            Patch(typeof(GameModeService), "OfflineTick", nameof(OfflineTickBefore), null);
            Patch(typeof(GameModeService), "StopGameMode", null, nameof(Stopped));
            Patch(typeof(Il2CppBrokenArrow.MissionEditor.Systems.ObjectiveZoneSystem), "UpdateZones", nameof(FixtureZonesBefore), null);
            Patch(typeof(WarGoalsPanel), "Update", null, nameof(UpdateNativeUi));
            Patch(typeof(WarGoalsPanel), "SetPhase", null, nameof(UpdateNativeUi));
            Patch(typeof(WarGoalsPanel), "SetEndPhaseMessage", null, nameof(UpdateNativeUi));
            InitializeEconomy();
            ready = true;
            Log("initialized", new { config, implementation = "native mode retained; custom VP ledger; native final result" });
            LoggerInstance.Msg("Conquest prototype ready; scoring requires the pinned Local Skirmish guard and an offline game-mode service.");
        }
        catch (Exception e)
        {
            HarmonyInstance.UnpatchSelf();
            Fail(e);
        }
    }
    static void Patch(Type type, string name, string before, string after)
    {
        var method = AccessTools.Method(type, name) ?? throw new MissingMethodException(type.FullName, name);
        instance!.HarmonyInstance.Patch(method,
            prefix: before == null ? null : new HarmonyMethod(typeof(Prototype), before),
            postfix: after == null ? null : new HarmonyMethod(typeof(Prototype), after));
        Log("hook_registered", new { type = type.FullName, name });
    }
    static void VerifyInputs()
    {
        var pins = JsonSerializer.Deserialize<Dictionary<string, string>>(File.ReadAllText(Path.Combine(Root, "compatibility.json")))!;
        foreach (var pin in pins)
        {
            string path = Path.Combine(MelonEnvironment.GameRootDirectory, pin.Key.Replace('/', Path.DirectorySeparatorChar));
            // Both standard and extracted-game layouts are supported, without guessing a different DLL.
            if (pin.Key == "GameAssembly.dll" && !File.Exists(path)) path = Path.Combine(MelonEnvironment.GameRootDirectory, "BrokenArrow_Data", pin.Key);
            BuildFingerprint.Verify(pin.Key, File.ReadAllBytes(path), pin.Value);
        }
        Log("compatibility_verified", pins);
    }
    static bool Guarded(GameModeService service)
    {
        if (!ready || faulted || !config.Enabled || service == null || service._isOnline) return false;
        var runtime=AppDomain.CurrentDomain.GetAssemblies().FirstOrDefault(a=>a.GetName().Name=="FreedomArrow.Runtime");
        if(runtime?.GetType("FreedomArrow.Runtime")?.GetProperty("IsApplied")?.GetValue(null) is not true)return false;
        if (localGuard == null)
        {
            var type = AppDomain.CurrentDomain.GetAssemblies().FirstOrDefault(a => a.GetName().Name == "BALocalSkirmish")?.GetType("BALocalSkirmish.Core");
            localGuard = type?.GetProperty("IsGuardedLocalBattle", BindingFlags.Public | BindingFlags.Static);
        }
        return localGuard?.PropertyType == typeof(bool) && localGuard.GetValue(null) is true;
    }
    public static void SetWar(GameModeService __instance, WarGoalsModeData data)
    {
        BeginModeLifetime();
        try
        {
            if (!Guarded(__instance)) return;
            if(config.PhasePolicy == "continuous") throw new InvalidOperationException("Continuous phase policy was audited only for ConquestMode");
            Reset("new WarGoalsMode");
            if(config.TestDurationSeconds>0)data.TimeLimitSec=config.TestDurationSeconds;
            data.VictoryPointsDestructionCompensation = 0; data.VictoryPointsConquestCompensation = 0;
            data.VictoryPointsFlatCompensation = false;
            Log("mode_configuration", new { mode = "WarGoalsMode", duration = data.TimeLimitSec });
        }
        catch (Exception e) { Fail(e); }
    }
    public static void SetConquest(GameModeService __instance, ConquestModeData data)
    {
        BeginModeLifetime();
        try
        {
            if (!Guarded(__instance)) return;
            Reset("new ConquestMode");
            if(config.TestDurationSeconds>0)data.TimeLimitInSec=config.TestDurationSeconds;
            data.IsDestructionEnabled = false; data.IsCompensationEnabled = false; data.CompensationDestruction = 0;
            data.DeathByScore = false;
            Log("mode_configuration", new { mode = "ConquestMode", duration = data.TimeLimitInSec,
                config.PhasePolicy,config.Ending,config.ScoreLimit,data.DeathByScore,data.IsDestructionEnabled,data.IsCompensationEnabled });
        }
        catch (Exception e) { Fail(e); }
    }
    static bool Prepare(View candidate)
    {
        if(dispatching||candidate.Pointer==retiredModePointer||candidate.Pointer==endingModePointer)return false;
        if (!Guarded(candidate.Service) || !candidate.Service._gameModeIsActive) return false;
        if(candidate.Conquest==null&&(config.PhasePolicy=="continuous"||config.Ending=="score_or_time"))
            throw new InvalidOperationException("Continuous and score-limit adapters require audited ConquestMode");
        var current = candidate.Service.CurrentGameMode;
        if (current == null || current.Pointer != candidate.Pointer) return false;
        if (candidate.Service.Timers.TryGetValue(TimerType.DeploymentPhase, out float deployment) && deployment > 0) return false;
        if (view == null || view.Pointer != candidate.Pointer)
        {
            DiscardModeFixture("new ledger");pendingEnding=null;terminalStarted=false;ledgerEpoch++;
            fixtureUsedThisMatch=false;nativePhaseCalls=0;continuousTimerCalls=0;lastModeSample=-1;lastTelemetry=-10;lastUiSecond=-1;
            uiEnabled=false;RestoreNativeUi();uiFault=false;
            var active = ScenariosService.ActiveScenario ?? throw new InvalidOperationException("No active local scenario");
            view = candidate;
            modeServicePointer=candidate.Service.Pointer;
            ledger = new Ledger(config, active.Name, candidate.Duration);
            if(config.PhasePolicy == "continuous")uiEnabled=true;
            Log("match_started", new { mode = candidate.Name, map = active.Name, duration = candidate.Duration, config });
            try{Log("zone_geometry",candidate.Geometry());}catch(Exception e){Log("zone_geometry_unavailable",new{message=e.Message});}
        }
        return true;
    }
    static bool Observe(View candidate, float remaining)
    {
        if (!Prepare(candidate)) return false;
        if (!float.IsFinite(remaining) || remaining < -5 || remaining > ledger!.Duration + 0.01)
            throw new InvalidOperationException("Unexpected GameMode countdown value");
        ValidateModeFixture();
        zones = candidate.ReadZones();
        foreach (var award in ledger!.Advance(ledger.Duration - Math.Max(0, remaining), zones))
            Log("conquest_tick", new { award, zones, map = ledger.Map, synthetic=fixtureUsedThisMatch });
        Publish();
        QueueScoreLimitEnding();
        LogModeSnapshot(false);
        status = $"{candidate.Name} | A {ledger.Alpha} : {ledger.Bravo} B | combat {ledger.Elapsed:F1}s | next tick in {Math.Max(0,ledger.NextTick-ledger.Elapsed):F1}s";
        if (ledger.Elapsed - lastTelemetry >= 5)
        {
            lastTelemetry = ledger.Elapsed;
            Log("clock_and_zones", new { remaining, elapsed = ledger.Elapsed, next = ledger.NextTick, zones });
        }
        return true;
    }
    static void Publish()
    {
        if (ledger == null || view == null || !Guarded(view.Service)) return;
        var points = view.Points ?? throw new InvalidOperationException("Native VP dictionary missing");
        points[TeamSide.Alpha] = ledger.Alpha; points[TeamSide.Bravo] = ledger.Bravo;
        var destruction = view.Destruction;
        if (destruction != null) { destruction[TeamSide.Alpha] = 0; destruction[TeamSide.Bravo] = 0; }
        var panel=view.Panel;if(panel!=null)panel.SetVictoryPoints(points);
    }
    public static void WarTimerBefore(WarGoalsMode __instance, TimerType type, float timer)
    { try { if (type == TimerType.GameMode) Observe(new View(__instance), timer); } catch (Exception e) { Fail(e); } }
    public static bool ConquestTimerBefore(ConquestMode __instance, TimerType type, float timer)
    {
        if(type==TimerType.GameMode&&__instance.Pointer==retiredModePointer)return false;
        if(type==TimerType.GameMode&&continuousModePointer==__instance.Pointer&&(faulted||terminalStarted))
        {UpdateInvalidMatchClock(timer);return false;}
        if(type==TimerType.GameMode&&__instance.Pointer==endingModePointer)return false;
        try
        {
            if(type!=TimerType.GameMode)return true;
            var candidate=new View(__instance);
            bool observed=Observe(candidate,timer);
            if(!observed)
            {
                if(continuousModePointer==__instance.Pointer)throw new InvalidOperationException("Continuous mode lost its guard; native phases remain blocked for this invalid match");
                return true;
            }
            if(config.PhasePolicy!="continuous")return true;
            continuousModePointer=__instance.Pointer;
            // Audited GameMode branch updates phase UI/audio, awards and phase-end events.
            // Keep deployment/other timers and the native service clock/result path intact.
            var panel=candidate.Panel;if(panel!=null)panel.SetTime(Math.Max(0,timer));
            continuousTimerCalls++;
            return false;
        }
        catch(Exception e){Fail(e);return continuousModePointer!=__instance.Pointer;}
    }
    public static void WarTimerAfter(WarGoalsMode __instance) => Restore(new View(__instance));
    public static void ConquestTimerAfter(ConquestMode __instance) => Restore(new View(__instance));
    public static void PhaseBefore()
    { if (ready && !faulted && ledger != null && view != null && Guarded(view.Service)) { nativePhaseCalls++;Log("native_phase_begin", new { customAlpha = ledger.Alpha, customBravo = ledger.Bravo }); } }
    public static void WarPhaseAfter(WarGoalsMode __instance) => Restore(new View(__instance), true);
    public static void ConquestPhaseAfter(ConquestMode __instance) => Restore(new View(__instance), true);
    static void Restore(View candidate, bool phase = false)
    {
        try
        {
            if (view == null || view.Pointer != candidate.Pointer || !Guarded(candidate.Service)) return;
            if (phase) Log("native_phase_awards_replaced", new { native = candidate.ReadPoints(), customAlpha = ledger!.Alpha, customBravo = ledger.Bravo });
            Publish();
        }
        catch (Exception e) { Fail(e); }
    }
    // Keep the native terminal calculation (including its draw and result/stat callbacks).
    // ConquestMode can otherwise finish by a native threshold; this prototype uses time-limit ending.
    static bool Winner(View candidate, bool timeEnd, ref TeamSide result)
    {
        if(dispatching||candidate.Pointer==retiredModePointer||candidate.Pointer==endingModePointer)
        {result=TeamSide.NotDefined;Log("winner_evaluation_suppressed",new{timeEnd,dispatching,reason="terminal or retired mode"});return false;}
        try
        {
            if (!Prepare(candidate)) return true;
            if (!candidate.Service.Timers.TryGetValue(TimerType.GameMode, out float remaining))
                throw new InvalidOperationException("GameMode timer missing at winner evaluation");
            Observe(candidate, remaining);
            if (!timeEnd || remaining > 0) { result = TeamSide.NotDefined; return false; }
            terminalStarted=true;pendingEnding=null;endingModePointer=candidate.Pointer;nativeResultStarted=true;
            Publish(); Log("native_final_evaluation", new { alpha = ledger!.Alpha, bravo = ledger.Bravo, remaining, synthetic=fixtureUsedThisMatch });
            return true;
        }
        catch (Exception e) { Fail(e); return true; }
    }
    public static bool WarWinner(WarGoalsMode __instance, bool timeEnd, ref TeamSide __result) => Winner(new View(__instance), timeEnd, ref __result);
    public static bool ConquestWinner(ConquestMode __instance, bool timeEnd, ref TeamSide __result) => Winner(new View(__instance), timeEnd, ref __result);
    public static void Stopped(GameModeService __instance)
    {
        if(view==null||modeServicePointer!=__instance.Pointer)return;
        retiredModePointer=view.Pointer;
        try{Log("match_stopped",new{alpha=ledger?.Alpha,bravo=ledger?.Bravo,elapsed=ledger?.Elapsed,invalid=faulted,
            winnerEvaluations,winnerFoundCalls,stoppedCalls=++stoppedCalls});}
        catch(Exception e){Fail(e);}
        finally{try{Reset("match stopped");}catch(Exception e){Fail(e);}}
    }
    static void Reset(string reason)
    { DiscardModeFixture(reason);pendingEnding=null;terminalStarted=false;fixtureUsedThisMatch=false;nativePhaseCalls=0;continuousTimerCalls=0;lastModeSample=-1;uiEnabled=false;RestoreNativeUi();uiFault=false;view = null;ledger = null;zones.Clear();lastTelemetry = -10;match++;status = "Waiting for combat timer";Log("reset",new{reason}); }
    static void Fail(Exception e)
    {
        if (faulted) return;
        faulted = true; ready = false;
        pendingEnding=null;terminalStarted=true;config.ShowOverlay=true;
        InvalidateHudPresentation();
        status = "PROTOTYPE INACTIVE / RESULT INVALID: " + e.Message;
        Log("prototype_fault", new { error = e.ToString(), action = "No further custom writes; abandon this experiment match" });
        MelonLogger.Error(status);
    }
    static void Log(string kind, object data)
    {
        if (string.IsNullOrEmpty(logPath)) return;
        try { File.AppendAllText(logPath, JsonSerializer.Serialize(new { sequence = ++sequence, match, ledgerEpoch, requestedProfile, synthetic=fixtureUsedThisMatch, kind, utc = DateTime.UtcNow, data }) + "\n"); }
        catch (Exception e)
        {
            faulted = true; ready = false;
            pendingEnding=null;terminalStarted=true;
            InvalidateHudPresentation();
            status = "PROTOTYPE INACTIVE / RESULT INVALID: evidence log failed";
            MelonLogger.Error(status + ": " + e.Message);
        }
    }
    // Typed adapters keep native access explicit and compilation checks the real generated interfaces.
    sealed class View
    {
        readonly WarGoalsMode war;
        readonly ConquestMode conquest;
        public ConquestMode Conquest => conquest;
        public NativeZones LiveZones => Zones;
        public NativeOwners CapturedOwners => Owners;
        public View(WarGoalsMode mode) { war = mode; }
        public View(ConquestMode mode) { conquest = mode; }
        public IntPtr Pointer => war != null ? war.Pointer : conquest!.Pointer;
        public string Name => war != null ? "WarGoalsMode" : "ConquestMode";
        public GameModeService Service => war != null ? war._gameModeService : conquest!._gameModeService;
        public double Duration => war != null ? war._initData.TimeLimitSec : conquest!._initData.TimeLimitInSec;
        public NativeScores Points => war != null ? war._victoryPoints : conquest!._victoryPoints;
        public NativeScores Destruction => war != null ? war._destructionPoints : conquest!._destructionPoints;
        public WarGoalsPanel Panel => war != null ? war._uiPanel : conquest!._uiPanel;
        NativeZones Zones => war != null ? war._zones : conquest!._zones;
        NativeOwners Owners => war != null ? war._capturedZones : conquest!._capturedZones;
        public object ReadPoints() => new { alpha = Points[TeamSide.Alpha], bravo = Points[TeamSide.Bravo] };
        public object Geometry()
        {
            var result=new List<object>();
            foreach(var zone in Zones)
            {
                var p=zone.transform.position;
                result.Add(new{id=zone.Data.UID,x=p.x,y=p.y,z=p.z});
            }
            return result;
        }
        public void DrawWeights(string map,Settings config)
        {
            var camera=Camera.main;if(camera==null||Zones==null)return;
            foreach(var zone in Zones)
            {
                var screen=camera.WorldToScreenPoint(zone.transform.position);
                if(screen.z<=0)continue;
                float x=screen.x*1920f/Screen.width,y=(Screen.height-screen.y)*1080f/Screen.height;
                if(x<0||x>1920||y<0||y>1080)continue;
                GUI.Label(new Rect(x-25,y-25,80,25),config.Weight(map,zone.Data.UID)+"/tick");
            }
        }
        public List<Zone> ReadZones()
        {
            if (Zones == null || Owners == null) throw new InvalidOperationException("Native zones/owners missing");
            var result = new List<Zone>();
            foreach (var zone in Zones)
            {
                if (zone == null || zone.Data == null) throw new InvalidOperationException("Invalid native zone");
                int id = zone.Data.UID;
                bool a = Owners.TryGetValue(TeamSide.Alpha, out var aa) && aa != null && aa.Contains(id);
                bool b = Owners.TryGetValue(TeamSide.Bravo, out var bb) && bb != null && bb.Contains(id);
                if (a && b) throw new InvalidOperationException("Zone belongs to both teams");
                bool insideA = false, insideB = false;
                if (zone.TeamsInside != null) foreach (var team in zone.TeamsInside)
                {
                    if (team.Value <= 0 || team.Key == null) continue;
                    insideA |= team.Key.TeamSide == TeamSide.Alpha;
                    insideB |= team.Key.TeamSide == TeamSide.Bravo;
                }
                result.Add(new Zone(id, a ? 0 : b ? 1 : 101, insideA && insideB));
            }
            return result;
        }
    }
}

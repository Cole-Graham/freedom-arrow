using UnityEngine;
using Il2CppBrokenArrow.Client.Ecs.Controllers;
using Il2CppBrokenArrow.Client.Ecs.GameMode;
using Il2CppBrokenArrow.MissionEditor.Components;
using Il2CppBrokenArrow.MissionEditor.Data.Meta;
using Il2CppBrokenArrow.MissionEditor.Data.ObjectiveZone;
using Il2CppNetworkCommon.Enums;

namespace FreedomArrow.Conquest;
public sealed partial class Prototype
{
    sealed class PendingEnding
    {
        public View View;
        public long Epoch;
        public TeamSide Winner;
        public int Alpha,Bravo;
        public double Elapsed;
        public bool Synthetic;
    }
    sealed class ZoneState
    {
        public ObjectiveZoneScript Zone;
        public TeamData Owner,Trying;
        public CaptureStatus Status;
        public int DictionaryOwner;
    }
    static PendingEnding pendingEnding;
    static long ledgerEpoch,continuousTimerCalls,nativePhaseCalls;
    static IntPtr continuousModePointer;
    // Tombstones outlive Reset: late native callbacks must not recreate a ledger or end twice.
    // Only an explicit native mode setup clears them, including pointer reuse.
    static IntPtr retiredModePointer,endingModePointer,modeServicePointer;
    static bool dispatching,nativeResultStarted;
    static long winnerEvaluations,winnerFoundCalls,stoppedCalls;
    static bool terminalStarted,fixtureUsedThisMatch;
    static string requestedProfile="packaged settings";
    static int lastModeSample=-1;
    static List<ZoneState> fixtureOriginal;
    static readonly Dictionary<int,int> expectedFixtureOwners=new();
    static bool FixtureActive => fixtureOriginal!=null;
    static long fixtureZoneUpdatesSkipped;
    public static bool FixtureZonesBefore()
    {
        // Developer-only ownership fixture: freeze capture-progress updates rather than fake units.
        // The native updater otherwise removes manually assigned owners whose ECS progress is zero.
        if(!FixtureActive||faulted)return true;
        try
        {
            if(!config.EnableDeveloperFixtures||view==null||!Guarded(view.Service))
                throw new InvalidOperationException("Ownership fixture lost its offline guard");
            if(ModeZoneArray().Any(HasActualOccupants))
                throw new InvalidOperationException("Actual units entered a pinned ownership fixture; abandon match");
            fixtureZoneUpdatesSkipped++;
            return false;
        }
        catch(Exception e){Fail(e);return true;}
    }
    static void BeginModeLifetime()
    {
        // A fault ends one match, not the game session.
        if(faulted&&initialized){faulted=false;ready=true;Log("fault_cleared",new{status});}
        retiredModePointer=IntPtr.Zero;endingModePointer=IntPtr.Zero;continuousModePointer=IntPtr.Zero;
        modeServicePointer=IntPtr.Zero;dispatching=false;nativeResultStarted=false;winnerEvaluations=0;winnerFoundCalls=0;stoppedCalls=0;
    }
    static void UpdateInvalidMatchClock(float remaining)
    {
        try{if(view!=null){var panel=view.Panel;if(panel!=null)panel.SetTime(Math.Max(0,remaining));}}
        catch(Exception e){Log("invalid_match_clock_unavailable",new{message=e.Message});}
    }
    public static bool OfflineTickBefore(GameModeService __instance)
    {
        // GetWinner(NotDefined) alone cannot suppress the direct result delegate in OfflineTick.
        // Once a terminal route begins, refuse a later whole tick for that service lifetime.
        return __instance.Pointer!=modeServicePointer||(endingModePointer==IntPtr.Zero&&retiredModePointer==IntPtr.Zero);
    }
    public static bool WinnerFoundBefore(GameModeService __instance,TeamSide __0)
    {
        if(__instance.Pointer!=modeServicePointer)return true;
        if(nativeResultStarted){Log("native_winner_found_suppressed",new{winner=__0.ToString(),dispatching});return false;}
        nativeResultStarted=true;
        if(view!=null)endingModePointer=view.Pointer;
        Log("native_winner_found_call",new{winner=__0.ToString(),calls=++winnerFoundCalls,dispatching});
        return true;
    }
    public static void ConquestWinnerAfter(ConquestMode __instance,bool timeEnd,TeamSide __result,bool __runOriginal)
        => RecordWinnerReturn(__instance.Pointer,timeEnd,__result,__runOriginal);
    public static void WarWinnerAfter(WarGoalsMode __instance,bool timeEnd,TeamSide __result,bool __runOriginal)
        => RecordWinnerReturn(__instance.Pointer,timeEnd,__result,__runOriginal);
    static void RecordWinnerReturn(IntPtr mode,bool timeEnd,TeamSide result,bool originalRan)
    {
        // This records GetWinner returns, not a count of the result delegate's invocations.
        if(view==null||view.Pointer!=mode)return;
        Log("native_winner_return",new{timeEnd,result=result.ToString(),resultValue=(int)result,originalRan,
            calls=++winnerEvaluations,dispatching,alpha=ledger?.Alpha,bravo=ledger?.Bravo});
    }
    public static void ConfigureNextMode(string profile)
    {
        if(!config.EnableDeveloperFixtures||faulted||!ready)throw new InvalidOperationException("Developer mode profiles are disabled or faulted");
        GameModeService service=null;
        Il2CppBrokenArrow.Shared.Ecs.Services.Session.TryGetService<GameModeService>(out service,false);
        if(view!=null||pendingEnding!=null||dispatching||(service!=null&&service._gameModeIsActive))throw new InvalidOperationException("Choose mode profile in the menu after prior mode teardown, before a battle");
        if(profile is not ("native_control" or "continuous_score" or "continuous_time"))throw new ArgumentException("Unknown mode profile");
        config.PhasePolicy=profile=="native_control"?"native":"continuous";
        config.Ending=profile=="continuous_time"?"time_limit":"score_or_time";
        config.ScoreLimit=profile=="continuous_time"?0:6;config.Validate();requestedProfile=profile;
        Log("mode_profile_ready",new{profile,config.PhasePolicy,config.Ending,config.ScoreLimit,persistence="current process only; packaged defaults unchanged"});
    }
    static ObjectiveZoneScript[] ModeZoneArray()
    {
        var result=new List<ObjectiveZoneScript>();foreach(var zone in view.LiveZones)result.Add(zone);return result.ToArray();
    }
    static bool HasActualOccupants(ObjectiveZoneScript zone)
    {
        if(zone.UnitsInside.Count>0)return true;
        foreach(var pair in zone.TeamsInside)if(pair.Value>0)return true;
        return false;
    }

    static void QueueScoreLimitEnding()
    {
        if(terminalStarted||pendingEnding!=null||ledger==null||view==null||ledger.Elapsed>=ledger.Duration)return;
        if(config.Ending!="score_or_time")return;
        if(ledger.ScoreLimitWinner is not int side)return;
        if(view.Conquest==null)throw new InvalidOperationException("Score-limit dispatch requires audited ConquestMode");
        pendingEnding=new PendingEnding {View=view,Epoch=ledgerEpoch,Winner=(TeamSide)side,
            Alpha=ledger.Alpha,Bravo=ledger.Bravo,Elapsed=ledger.Elapsed,Synthetic=fixtureUsedThisMatch};
        Log("score_limit_queued",new{winner=side,ledger.Alpha,ledger.Bravo,ledger.Elapsed,config.ScoreLimit,epoch=ledgerEpoch,synthetic=fixtureUsedThisMatch});
    }
    static void DispatchPendingEnding()
    {
        var end=pendingEnding;if(end==null)return;
        pendingEnding=null;
        try
        {
            var service=end.View.Service;
            if(terminalStarted||end.Epoch!=ledgerEpoch||view==null||view.Pointer!=end.View.Pointer||
                !Guarded(service)||!service._gameModeIsActive||service.CurrentGameMode?.Pointer!=end.View.Pointer)
            {Log("score_limit_discarded",new{reason="stale or inactive mode",end.Epoch});return;}
            terminalStarted=true;endingModePointer=end.View.Pointer;dispatching=true;Publish();
            Log("score_limit_dispatch",new{winner=end.Winner.ToString(),end.Alpha,end.Bravo,end.Elapsed,synthetic=end.Synthetic,
                route="native GameModeService.OnWinnerFound after timer callback unwinds"});
            // Online, OnWinnerFound only stops the mode on this PC; the server keeps the match running.
            // Send the result the way a scenario End Mission node does: NetworkRoomService.SendEndGame.
            // The game sends it only from the scenario host, and the server then ends the match for everyone.
            if(service._isOnline)
            {
                var room=service._networkRoomService;
                Log("score_limit_online_end",new{winner=end.Winner.ToString(),end.Alpha,end.Bravo,
                    host=Il2CppBrokenArrow.ScriptEngine.Network.NetworkScenarioStorage.IsScenarioHost,
                    slave=Il2CppBrokenArrow.ScriptEngine.Network.NetworkScenarioStorage.IsScenarioSlave,room=room!=null});
                if(room==null)throw new InvalidOperationException("NetworkRoomService missing");
                room.SendEndGame(end.Winner);
                return;
            }
            // Native code stops/releases the mode and emits the ordinary result delegate.
            // The stop hook may clear our global view/ledger; retain only the local snapshot.
            service.OnWinnerFound(end.Winner);
            Log("score_limit_dispatch_returned",new{end.Alpha,end.Bravo,synthetic=end.Synthetic,modeActive=service._gameModeIsActive,
                currentModePresent=service.CurrentGameMode!=null,stoppedHookClearedView=view==null});
        }
        catch(Exception e){Fail(e);}
        finally{dispatching=false;}
    }
    public static void InspectMode()
    {
        if(view==null||!Guarded(view.Service))throw new InvalidOperationException("No guarded local mode");
        LogModeSnapshot(true);
    }
    static void LogModeSnapshot(bool force)
    {
        if(view==null||ledger==null||view.Conquest==null)return;
        int sample=(int)ledger.Elapsed/10;if(!force&&sample==lastModeSample)return;lastModeSample=sample;
        var mode=view.Conquest;
        var phases=new List<float>();if(mode._phasesTime!=null)foreach(var phase in mode._phasesTime)phases.Add(phase);
        Log("mode_snapshot",new{epoch=ledgerEpoch,mode=view.Name,requestedProfile,config.PhasePolicy,config.Ending,config.ScoreLimit,
            ledger.Elapsed,ledger.Duration,ledger.Alpha,ledger.Bravo,ledger.Finished,ledger.ReachedScoreLimit,
            currentPhase=mode._currentPhase,phaseTimes=phases.ToArray(),nativePhaseCalls,continuousTimerCalls,
            mode._initData.DeathByScore,mode._initData.IsDestructionEnabled,mode._initData.IsCompensationEnabled,
            synthetic=fixtureUsedThisMatch,fixtureActive=FixtureActive,terminalStarted,
            fixtureZoneUpdatesSkipped,
            zones=view.ReadZones(),nativeOwners=ModeZoneArray().Select(z=>new{id=z.Data.UID,
                side=z.CapturedBy==null?101:(int)z.CapturedBy.TeamSide,status=z.CaptureStatus.ToString()}).ToArray()});
    }

    static void RequireDeveloperFixture()
    {
        if(!config.EnableDeveloperFixtures||view?.Conquest==null||!Guarded(view.Service))
            throw new InvalidOperationException("Developer fixture disabled or outside audited offline ConquestMode");
        if(terminalStarted||pendingEnding!=null||dispatching||!view.Service._gameModeIsActive||
            view.Service.CurrentGameMode?.Pointer!=view.Pointer||view.Pointer==retiredModePointer||view.Pointer==endingModePointer)
            throw new InvalidOperationException("Cannot mutate fixtures in an inactive or terminal mode");
        if(!GameController.Instance.GameSession.IsPaused)throw new InvalidOperationException("Pause before editing synthetic zone state");
        if(ModeZoneArray().Any(HasActualOccupants))
            throw new InvalidOperationException("Zone contains actual units; refusing synthetic ownership edits");
    }
    public static void SetModeFixture(string name)
    {
        RequireDeveloperFixture();
        if(name is not ("restore" or "net_4v3" or "net_equal" or "bravo_4v3" or "weight2"))throw new ArgumentException("Unknown scoring fixture");
        bool mutationStarted=false;
        try{ApplyModeFixture(name,ref mutationStarted);}
        catch(Exception e)
        {
            if(mutationStarted)Fail(e);
            throw;
        }
    }
    static void ApplyModeFixture(string name,ref bool mutationStarted)
    {
        if(name=="restore"){mutationStarted=FixtureActive;RestoreModeFixture();return;}
        var ordered=ModeZoneArray().OrderBy(z=>z.Data.UID).ToArray();
        if(ordered.Length<5)throw new InvalidOperationException("Scoring fixture requires at least five real native zones");
        var teams=new Dictionary<int,TeamData>();
        foreach(var pair in view.Conquest._scenarioData._allObjects)
        {
            var team=pair.Value.TryCast<TeamData>();
            if(team!=null&&team.TeamSide is TeamSide.Alpha or TeamSide.Bravo)teams[(int)team.TeamSide]=team;
        }
        if(!teams.ContainsKey(0)||!teams.ContainsKey(1))throw new InvalidOperationException("Scenario has no two native team records");
        if(fixtureOriginal==null)
        {
            var current=view.ReadZones().ToDictionary(z=>z.Uid,z=>z.Owner);
            fixtureOriginal=ordered.Select(z=>new ZoneState {Zone=z,Owner=z.CapturedBy,Trying=z.TeamTryingToCapture,
                Status=z.CaptureStatus,DictionaryOwner=current[z.Data.UID]}).ToList();
            if(fixtureOriginal.Any(z=>z.DictionaryOwner!=(z.Owner==null?101:(int)z.Owner.TeamSide)))
            {fixtureOriginal=null;throw new InvalidOperationException("Native zone and captured-zone set disagree before fixture");}
        }
        mutationStarted=true;fixtureUsedThisMatch=true;
        config.FixtureMap=ledger.Map;config.FixtureWeights.Clear();expectedFixtureOwners.Clear();
        foreach(var zone in ordered)
        {
            int owner=101,weight=1,index=Array.IndexOf(ordered,zone);
            if(name is "net_4v3" or "bravo_4v3")
            {
                if(index<2){owner=name=="net_4v3"?0:1;weight=2;}
                else if(index<5)owner=name=="net_4v3"?1:0;
            }
            else if(name=="net_equal"){if(index<2)owner=0;else if(index<4)owner=1;}
            else if(index==0){owner=0;weight=2;}
            SetSyntheticOwner(zone,owner==101?null:teams[owner],owner);
            expectedFixtureOwners[zone.Data.UID]=owner;config.FixtureWeights[zone.Data.UID]=weight;
        }
        fixtureUsedThisMatch=true;ValidateModeFixture();zones=view.ReadZones();
        fixtureZoneUpdatesSkipped=0;
        Log("mode_fixture_applied",new{name,synthetic=true,scope="pinned native owner fields and captured-zone sets; capture-progress updates frozen while empty; not troop capture or capture-event behavior",
            elapsed=ledger.Elapsed,ledger.Alpha,ledger.Bravo,zones,weights=config.FixtureWeights,weightPersistence="in-memory only; never written to defaults/overrides"});
        LogModeSnapshot(true);
    }
    static void SetSyntheticOwner(ObjectiveZoneScript zone,TeamData owner,int side)
    {
        // Remove first so a zone is never scored for both sides.
        view.CapturedOwners[TeamSide.Alpha].Remove(zone.Data.UID);
        view.CapturedOwners[TeamSide.Bravo].Remove(zone.Data.UID);
        if(side is 0 or 1)view.CapturedOwners[(TeamSide)side].Add(zone.Data.UID);
        zone.CapturedBy=owner;zone.TeamTryingToCapture=null;
        zone.CaptureStatus=owner==null?CaptureStatus.Neutral:CaptureStatus.Captured;
        zone.SetColor((TeamSide)side);var panel=view.Panel;if(panel!=null)panel.UpdateObjectiveZoneOwner(zone.Data.UID,(TeamSide)side,false);
    }
    static void ValidateModeFixture()
    {
        if(!FixtureActive)return;
        var actual=view.ReadZones().ToDictionary(z=>z.Uid,z=>z.Owner);
        foreach(var zone in view.LiveZones)
        {
            int expected=expectedFixtureOwners[zone.Data.UID];
            int native=zone.CapturedBy==null?101:(int)zone.CapturedBy.TeamSide;
            var status=expected==101?CaptureStatus.Neutral:CaptureStatus.Captured;
            if(actual[zone.Data.UID]!=expected||native!=expected||zone.CaptureStatus!=status||
                HasActualOccupants(zone))
                throw new InvalidOperationException($"Synthetic/native mismatch zone={zone.Data.UID} expected={expected} dictionary={actual[zone.Data.UID]} native={native} status={zone.CaptureStatus} units={zone.UnitsInside.Count}; abandon fixture match");
        }
    }
    static void RestoreModeFixture()
    {
        if(fixtureOriginal==null){Log("mode_fixture_restore_noop",new{reason="No original snapshot; no writes"});return;}
        foreach(var state in fixtureOriginal)
        {
            SetSyntheticOwner(state.Zone,state.Owner,state.DictionaryOwner);
            state.Zone.TeamTryingToCapture=state.Trying;state.Zone.CaptureStatus=state.Status;
        }
        var actual=view.ReadZones().ToDictionary(z=>z.Uid,z=>z.Owner);
        foreach(var state in fixtureOriginal)
            if(actual[state.Zone.Data.UID]!=state.DictionaryOwner||state.Zone.CapturedBy?.Pointer!=state.Owner?.Pointer||
                state.Zone.TeamTryingToCapture?.Pointer!=state.Trying?.Pointer||state.Zone.CaptureStatus!=state.Status)
                throw new InvalidOperationException("Fixture restore readback mismatch; abandon match");
        Log("mode_fixture_restore_readback",new{verified=true,zones=fixtureOriginal.Count});
        DiscardModeFixture("explicit restoration");zones=view.ReadZones();LogModeSnapshot(true);
    }
    static void DiscardModeFixture(string reason)
    {
        if(fixtureOriginal!=null)Log("mode_fixture_cleared",new{reason,synthetic=true,
            nativeStateRestored=reason=="explicit restoration",note="On match end the native scenario owns teardown; discard references, do not rewrite a released mode"});
        fixtureOriginal=null;expectedFixtureOwners.Clear();config.FixtureMap=null;config.FixtureWeights.Clear();
    }
    public static void InjectModeFault()
    {
        RequireDeveloperFixture();
        if(continuousModePointer==IntPtr.Zero)throw new InvalidOperationException("Continuous branch must have executed before fault test");
        Fail(new InvalidOperationException("Developer-injected fault: result invalid, pending ending cleared, native phase catch-up remains blocked"));
    }
}

using MelonLoader;
using UnityEngine;
using UnityEngine.UI;
using Il2CppTMPro;
using Il2CppBrokenArrow.Client.Ecs.UI.HUD.GameModes.WarGoals;
using Il2CppBrokenArrow.Client.Ecs.Controllers;
using Il2CppNetworkCommon.Enums;

namespace FreedomArrow.Conquest;
public sealed partial class Prototype
{
    static bool updatingHud;
    static bool uiEnabled;
    static View labelView;
    static string labelMap;
    static GUIStyle labelStyle,bannerStyle;
    static bool labelsOff,labelsLogged,barsOff,barsLogged,matchEnded;
    static bool uiFault;
    static UiSnapshot uiSnapshot;
    sealed class UiSnapshot
    {
        public WarGoalsPanel Panel;
        public string Phase,Time;
        public float PhaseSize;
        public Color TimerColor;
        public bool AlphaBar,BravoBar,AlphaConquest,BravoConquest,PhaseActive,ProgressActive,MessageActive;
        public readonly List<(GameObject widget,bool active)> HiddenRoots=new();
        public readonly List<Image> PhaseBoxes=new();
    }
    static void HidePhaseRoot(WarGoalsPanel panel,Transform phasePart)
    {
        // Select only a phase branch. Never hide an ancestor of essential HUD widgets.
        var protectedWidgets=new[]{panel._timeText.transform,panel._alphaVictoryPointsText.transform,
            panel._bravoVictoryPointsText.transform,panel._alphaPlayersContainer,panel._bravoPlayersContainer,
            panel._zonesAlphaContainer,panel._zonesNeutralContainer,panel._zonesBravoContainer};
        var chosen=phasePart;
        for(var parent=phasePart.parent;parent!=null&&parent.Pointer!=panel.transform.Pointer;parent=parent.parent)
        {
            if(protectedWidgets.Any(p=>p!=null&&(p.Pointer==parent.Pointer||p.IsChildOf(parent))))break;
            chosen=parent;
        }
        if(!uiSnapshot.HiddenRoots.Any(x=>x.widget.Pointer==chosen.gameObject.Pointer))
            uiSnapshot.HiddenRoots.Add((chosen.gameObject,chosen.gameObject.activeSelf));
        chosen.gameObject.SetActive(false);
    }
    // The boxes mark the three native phases. Only the fill bar stays. Turn off the Image and not the
    // object, because the fill bar can be a child of a box.
    const float PhaseTextScale=0.75f;
    static void HidePhaseBoxes(WarGoalsPanel panel)
    {
        var fill=panel._phasePeriodProgressImage;
        foreach(var root in uiSnapshot.HiddenRoots)
        {
            if(root.widget==null)continue;
            foreach(var image in root.widget.GetComponentsInChildren<Image>(true))
            {
                bool keep=image.Pointer==fill.Pointer;
                Log("phase_image",new{name=image.name,keep,width=image.rectTransform.rect.width});
                if(keep||!image.enabled)continue;
                image.enabled=false;
                uiSnapshot.PhaseBoxes.Add(image);
            }
        }
    }
    // The green number under each team bar: the points that team gets on the next tick.
    static TextMeshProUGUI alphaNextTick,bravoNextTick;
    static bool nextTickOff;
    static TextMeshProUGUI NextTickText(GoalsBar bar,TextMeshProUGUI label)
    {
        if(label!=null)return label;
        var source=bar._progressText;
        var clone=UnityEngine.Object.Instantiate(source.gameObject,source.transform.parent);
        clone.name="FA_NextTick";
        var text=clone.GetComponent<TextMeshProUGUI>();
        var rect=text.rectTransform;
        rect.anchoredPosition=rect.anchoredPosition-new Vector2(0,rect.rect.height);
        text.color=Color.green;
        return text;
    }
    static void ShowNextTick(WarGoalsPanel panel)
    {
        if(nextTickOff||zones==null)return;
        try
        {
            var next=ledger.Forecast(zones);
            alphaNextTick=NextTickText(panel._alphaConquestBar,alphaNextTick);
            bravoNextTick=NextTickText(panel._bravoConquestBar,bravoNextTick);
            bool bravo=LocalIsBravo(panel);
            alphaNextTick.text=Settings.NextTickLabel(bravo?next.Bravo:next.Alpha);
            bravoNextTick.text=Settings.NextTickLabel(bravo?next.Alpha:next.Bravo);
        }
        catch(Exception e)
        {
            nextTickOff=true;MelonLogger.Error("FREEDOM_ARROW_NEXT_TICK_FAILED: off for this session. "+e.Message);
        }
    }
    public static void SetNativeUi(bool enabled)
    {
        if(view==null||!Guarded(view.Service))throw new InvalidOperationException("Native UI experiment requires guarded local battle");
        if(!enabled&&config.PhasePolicy=="continuous")throw new InvalidOperationException("Continuous policy requires the phase-free HUD; use the native policy to restore phase widgets");
        if(uiFault&&enabled)throw new InvalidOperationException("UI experiment failed; inspect log");
        uiEnabled=enabled;
        if(!enabled)RestoreNativeUi();
        Log("native_ui_mode",new{enabled,scope="native WarGoalsPanel; F10 toggle; does not change scoring state"});
    }
    public static void SetScoringOverlay(bool enabled)
    {
        if(view==null||!Guarded(view.Service))throw new InvalidOperationException("No guarded local battle");
        config.ShowOverlay=enabled;Log("scoring_overlay_mode",new{enabled});
    }
    // Timer ticks also run during deployment, so the labels can show before combat starts.
    static void NoteLabelMode(View candidate)
    {
        if(labelView!=null&&labelView.Pointer==candidate.Pointer)return;
        labelView=candidate;labelMap=null;labelsOff=false;labelsLogged=false;barsLogged=false;matchEnded=false;leaving=false;
    }
    // Osama, 7 November: the zone point labels and round banner go away when the match ends, not when the player leaves.
    static void HideLabels(string reason){if(matchEnded||labelView==null)return;matchEnded=true;Log("zone_labels_hidden",new{reason});}
    // Set when the player confirms leaving (Escape menu); cleared when the next match's mode or preview screen comes up.
    static bool leaving;
    public static void LeavingMatch(){leaving=true;try{Log("leaving_match",new{t=Time.unscaledTime});}catch{}}
    static void ClearLabelMode(){labelView=null;labelMap=null;}
    static double clockOffset=-1;
    static float clockStart;
    static double ShownElapsed()=>Settings.ShownElapsed(ledger.Elapsed,clockOffset,Time.unscaledTime-clockStart);
    // Online, the scenario script pauses the game before the mode exists. There is no match clock or panel yet.
    static float onlineSetupStart=-1;
    static void DrawBanner(string text,int size)
    {
        if(bannerStyle==null||bannerStyle.fontSize!=size)bannerStyle=new GUIStyle(GUI.skin.label){fontSize=size,fontStyle=FontStyle.Bold,alignment=TextAnchor.MiddleCenter};
        float y=Screen.height*0.13f,h=size*1.8f;
        GUI.contentColor=Color.black;GUI.Label(new Rect(2,y+2,Screen.width,h),text,bannerStyle);
        GUI.contentColor=Color.white;GUI.Label(new Rect(0,y,Screen.width,h),text,bannerStyle);
    }
    // Lateralus 16 Nov 2026: the DEPLOYMENT banner started on the "BATTLE STARTS IN" map preview screen, which is paused too. Read from
    // GameAssembly 6000.3.24f1 (GameModeService.OnlineTick 0x441430): the room server's NetworkRoomService.State.Status is 0/1 while players
    // connect, 10 (RoomStatus.DeploymentPhase) on that preview screen, and 20 (InProcess) once the battle runs. Our deployment is the
    // scenario script's pause inside the battle, so the banner runs only at InProcess.
    static string lastRoomStatus;
    // Set on the "BATTLE STARTS IN" preview screen; the online deployment hold starts only after it (not for a player who rejoins mid-match).
    static bool sawPreview;
    static bool BattleRunning()
    {
        Il2CppBrokenArrow.Shared.Ecs.Services.Session.TryGetService<Il2CppBrokenArrow.Client.Ecs.GameMode.GameModeService>(out var service,false);
        var status=service?._networkRoomService?.State?.Status;
        string state=status?.ToString()??"none";
        if(state!=lastRoomStatus){lastRoomStatus=state;Log("online_room_status",new{status=state,t=Time.unscaledTime});if(status==RoomStatus.DeploymentPhase){leaving=false;sawPreview=true;}}
        return status==RoomStatus.InProcess;
    }
    // Seconds of the online deployment pause left, or null. From 16 Nov 2026 the conquest mode starts with the pause (scenarios/common.py
    // conquest_during_deployment), so this also runs while the mode and its labels are up.
    static double? OnlineSetupLeft()
    {
        if(economyOnlineGuard?.Invoke()!=true||GameController.Instance?.GameSession?.IsPaused!=true
            ||!config.MapZoneWeights.ContainsKey(Il2CppBrokenArrow.MissionEditor.MissionResolver.ScenariosService.ActiveScenario?.Name??"")
            ||!BattleRunning()){onlineSetupStart=-1;return null;}
        if(onlineSetupStart<0){onlineSetupStart=Time.unscaledTime;Log("online_setup_banner_started",new{t=onlineSetupStart,config.OnlineDeploySeconds,modeUp=view!=null,
            elapsed=ledger?.Elapsed});}
        double left=config.OnlineDeploySeconds-(Time.unscaledTime-onlineSetupStart);
        return left>0?left:null;
    }
    static void DrawOnlineSetup()
    {
        if(OnlineSetupLeft() is double left)DrawBanner(Settings.SetupBanner(left),Math.Max(16,Screen.height/38));
    }
    static void DrawRoundBanner()
    {
        if(ledger==null||view==null||view.Pointer!=labelView.Pointer)return;
        string setup=setupEnds>=0?Settings.SetupBanner(setupEnds-Time.unscaledTime)
            :view.Service._isOnline&&OnlineSetupLeft() is double left?Settings.SetupBanner(left):null;
        string text=setup??config.RoundAnnouncement(ShownElapsed());
        if(text==null)return;
        DrawBanner(text,Math.Max(setup!=null?16:12,Screen.height/(setup!=null?38:64)));
    }
    // Lateralus 16 Nov 2026: the zone values stayed on screen over the Escape menu. Nothing of ours draws while it (or the settings it
    // opens) is up. EscapeMenu.IsActive is the game's own flag; the settings screen is looked up at most once a second.
    // 0.9.0-dev.37 (Osama 17 Nov 2026, 5v5 FPS test, FREEDOM_ARROW_SLOW_FRAME lines): FindObjectOfType searches every object in the scene and took
    // 7-11 ms in a 5v5 battle, once a second, every second, so it caused most of the >50 ms frames. The settings screen can only be opened from
    // the Escape menu, so the search now runs only while the Escape menu is up, for 10 s after it closes, or while settings is open, and the
    // found screen is kept, so later checks are a cheap activeInHierarchy read. SettingsSearches is in the FREEDOM_ARROW_HOOK_HEALTH line.
    static float menuCheckedAt=-10,escapeSeenAt=-100;static bool settingsOpen,menuLogged;
    static Il2CppBrokenArrow.Client.Ecs.UI.Menu.Settings.SettingsScreen settingsScreen;
    public static int SettingsSearches;
    static bool MenuOpen()
    {
        float now=Time.unscaledTime;
        if(Il2CppBrokenArrow.Client.Ecs.UI.Menu.Profile.EscapeMenu.IsActive){escapeSeenAt=now;return true;}
        if(settingsScreen!=null&&settingsScreen.WasCollected)settingsScreen=null;
        if(settingsScreen!=null){settingsOpen=settingsScreen.gameObject.activeInHierarchy;return settingsOpen;}
        if(!settingsOpen&&now-escapeSeenAt>10f)return false;
        if(now-menuCheckedAt>=1f)
        {
            menuCheckedAt=now;SettingsSearches++;
            settingsScreen=UnityEngine.Object.FindObjectOfType<Il2CppBrokenArrow.Client.Ecs.UI.Menu.Settings.SettingsScreen>();
            settingsOpen=settingsScreen!=null&&settingsScreen.gameObject.activeInHierarchy;
        }
        return settingsOpen;
    }
    public void OnGUI()
    {
        DrawVersionLabel();
        if(leaving)return;
        try{if(MenuOpen()){if(!menuLogged){menuLogged=true;Log("overlay_hidden_for_menu",new{});}return;}}
        catch(Exception e){MelonLogger.Error("FREEDOM_ARROW_MENU_CHECK_FAILED: "+e.Message);}
        if(!labelsOff&&config.ShowOverlay&&Event.current.type==EventType.Repaint&&labelView==null)
        {
            // A banner fault must not stop the match.
            try{DrawOnlineSetup();}catch(Exception e){labelsOff=true;MelonLogger.Error("FREEDOM_ARROW_ONLINE_SETUP_FAILED: off for this session. "+e.Message);}
            return;
        }
        if(labelsOff||matchEnded||labelView==null||!config.ShowOverlay||Event.current.type!=EventType.Repaint)return;
        try
        {
            if(!Guarded(labelView.Service))return;
            if(labelMap==null)
            {
                if(labelView.ZoneIds().Count==0)return;
                labelMap=MapName(labelView);
            }
            int size=Math.Max(12,Screen.height/56);
            if(labelStyle==null||labelStyle.fontSize!=size)labelStyle=new GUIStyle(GUI.skin.label){fontSize=size,fontStyle=FontStyle.Bold,alignment=TextAnchor.MiddleLeft};
            var color=GUI.contentColor;
            DrawRoundBanner();
            int drawn=labelView.DrawWeights(labelMap,config,labelStyle);
            GUI.contentColor=color;
            if(!labelsLogged){labelsLogged=true;Log("zone_labels",new{map=labelMap,drawn,camera=drawn>=0});}
        }
        catch(Exception e)
        {
            // A label fault must not stop scoring.
            labelsOff=true;MelonLogger.Error("FREEDOM_ARROW_ZONE_LABELS_FAILED: off for this match. "+e.Message);
        }
    }
    // F8 only. Vanilla pauses the session for its deployment phase; online, the room server controls that phase.
    static float setupEnds=-1;
    static IntPtr setupSession;
    static void StartSetup(View candidate)
    {
        if(candidate.Service._isOnline||config.SetupSeconds<=0)return;
        // A setup fault must not stop scoring.
        try
        {
            var session=GameController.Instance.GameSession;
            session.IsPaused=true;
            setupSession=session.Pointer;
            setupEnds=Time.unscaledTime+config.SetupSeconds;
            Log("setup_started",new{config.SetupSeconds});
        }
        catch(Exception e){setupEnds=-1;MelonLogger.Error("FREEDOM_ARROW_SETUP_FAILED: setup phase off. "+e.Message);}
    }
    static void EndSetup(string reason)
    {
        if(setupEnds<0)return;
        setupEnds=-1;
        var session=GameController.Instance?.GameSession;
        if(session!=null&&session.Pointer==setupSession)session.IsPaused=false;
        Log("setup_ended",new{reason});
    }
    static void SetupFrame()
    {
        if(setupEnds<0)return;
        try
        {
            var session=GameController.Instance?.GameSession;
            if(session==null||session.Pointer!=setupSession||view==null){EndSetup("session closed");return;}
            if(Time.unscaledTime>=setupEnds){EndSetup("time");return;}
            // The pause button must not end the setup phase early.
            if(!session.IsPaused)session.IsPaused=true;
        }
        catch(Exception e){setupEnds=-1;MelonLogger.Error("FREEDOM_ARROW_SETUP_FAILED: setup phase off. "+e.Message);}
    }
    // Online deployment hold (Osama 22 Nov 2026: "we had a person spawn before the game started"). Every online FA map's script pauses
    // each player's own game for OnlineDeploySeconds at battle start (scenarios/common.py add_deployment: pauseGame true, delay,
    // pauseGame false); Skirmish copies have no pause. The pause is local (GameSessionContext.IsPaused, game speed 0 on this PC only), so
    // a client whose pause does not hold keeps its purchase timers and income running while the others wait. R2 logs 21-22 Nov 2026:
    // 11 matches had one or two such players (0.9.3 and 0.9.4); in match 9851894 TNTScientist's first unit was on the map 12 s into the
    // pause, he had 19 units and +733 points at the end of it, the other five players none and +0. This holds the pause on this client
    // from its first battle frame until HoldMargin before the window ends; the script's own pauseGame(false) then ends deployment. If this
    // hold had to restore the pause and the game is still paused HoldMargin after the window, the hold releases it itself. A player who
    // rejoins a running match (no preview screen first) gets no hold.
    const double HoldMargin=5;
    static float onlineHoldStart=-1;
    static IntPtr onlineHoldSession;
    static int onlineHoldRestores;
    static bool onlineHoldDone,onlineHoldFailed;
    static bool OnlineDeployMap(string name)=>name!=null&&config.MapZoneWeights.ContainsKey(name)&&!name.Contains(" Skirmish ");
    static void OnlineDeployFrame()
    {
        if(onlineHoldFailed)return;
        try
        {
            var session=GameController.Instance?.GameSession;
            if(session==null||economyOnlineGuard?.Invoke()!=true
                ||!OnlineDeployMap(Il2CppBrokenArrow.MissionEditor.MissionResolver.ScenariosService.ActiveScenario?.Name)||!BattleRunning())
            {
                onlineHoldStart=-1;onlineHoldDone=false;onlineHoldRestores=0;return;
            }
            if(onlineHoldStart<0||session.Pointer!=onlineHoldSession)
            {
                if(!sawPreview){onlineHoldDone=true;onlineHoldStart=Time.unscaledTime;onlineHoldSession=session.Pointer;return;}
                sawPreview=false;
                onlineHoldStart=Time.unscaledTime;onlineHoldSession=session.Pointer;onlineHoldRestores=0;onlineHoldDone=false;
                Log("online_deploy_hold_started",new{paused=session.IsPaused,config.OnlineDeploySeconds});
                MelonLogger.Msg($"FREEDOM_ARROW_DEPLOY_HOLD started: {config.OnlineDeploySeconds} s, game paused {session.IsPaused}");
            }
            if(onlineHoldDone)return;
            double left=config.OnlineDeploySeconds-(Time.unscaledTime-onlineHoldStart);
            if(left>HoldMargin)
            {
                if(!session.IsPaused)
                {
                    session.IsPaused=true;
                    if(++onlineHoldRestores==1)MelonLogger.Warning($"FREEDOM_ARROW_DEPLOY_HOLD this game was not paused {Time.unscaledTime-onlineHoldStart:0.0} s into deployment; pause restored");
                }
                return;
            }
            if(left>-HoldMargin)return;
            onlineHoldDone=true;
            bool released=onlineHoldRestores>0&&session.IsPaused;
            if(released)session.IsPaused=false;
            Log("online_deploy_hold_ended",new{restores=onlineHoldRestores,released});
            MelonLogger.Msg($"FREEDOM_ARROW_DEPLOY_HOLD ended: pause restored {onlineHoldRestores} time(s){(released?", released by the hold":"")}");
        }
        catch(Exception e){onlineHoldFailed=true;MelonLogger.Error("FREEDOM_ARROW_DEPLOY_HOLD_FAILED: off for this session. "+e.Message);}
    }
    public void OnUpdate()
    {
        SetupFrame();
        OnlineDeployFrame();
        StateFrame();
        CombatFrame();
        EconomyFrame();
        DispatchPendingEnding();
        if(uiSnapshot!=null&&uiSnapshot.Panel==null){uiEnabled=false;RestoreNativeUi();}
        bool retainContinuousUi=view!=null&&continuousModePointer==view.Pointer;
        if(uiSnapshot!=null&&!retainContinuousUi&&(view==null||!Guarded(view.Service))) {uiEnabled=false;RestoreNativeUi();}
        if(config.EnableDeveloperFixtures&&view!=null&&Guarded(view.Service)&&Input.GetKeyDown(KeyCode.F10))
        {
            if(config.PhasePolicy=="continuous"||uiFault)Log("native_ui_toggle_refused",new{reason="Continuous policy or UI fault requires retained HUD state"});
            else SetNativeUi(!uiEnabled);
        }
        if(config.EnableDeveloperFixtures&&view!=null&&Guarded(view.Service)&&Input.GetKeyDown(KeyCode.F11))SetScoringOverlay(!config.ShowOverlay);
    }
    // The panel's "alpha" widgets show the local player's own team, as the native UpdateConquestPoints does
    // (it reads _session.CurrentPlayer.TeamSide). A Bravo player sees Bravo on the "alpha" bar.
    static bool LocalIsBravo(WarGoalsPanel panel)=>panel._session?.CurrentPlayer?.TeamSide==TeamSide.Bravo;
    // Native conquest bars show points out of the score limit. A bar fault turns off the bars, not the scoring.
    static bool ShowScoreBars(WarGoalsPanel panel)
    {
        if(barsOff||ledger.ScoreLimit<=0)return false;
        try
        {
            bool bravo=LocalIsBravo(panel);
            ShowScoreBar(panel._alphaConquestBar,bravo?ledger.Bravo:ledger.Alpha);
            ShowScoreBar(panel._bravoConquestBar,bravo?ledger.Alpha:ledger.Bravo);
            if(!barsLogged)
            {
                barsLogged=true;
                Log("score_bars",new{limit=ledger.ScoreLimit,alphaVisible=panel._alphaConquestBar.gameObject.activeInHierarchy,bravoVisible=panel._bravoConquestBar.gameObject.activeInHierarchy});
            }
            return true;
        }
        catch(Exception e)
        {
            barsOff=true;MelonLogger.Error("FREEDOM_ARROW_SCORE_BARS_FAILED: off for this session. "+e.Message);
            return false;
        }
    }
    static void ShowScoreBar(GoalsBar bar,int points)
    {
        bar.gameObject.SetActive(true);
        bar._progress.fillAmount=Mathf.Clamp01(points/(float)ledger.ScoreLimit);
        // Auto-size so that three digit scores stay in the box and are not cut off.
        var text=bar._progressText;
        if(!text.enableAutoSizing)
        {
            text.fontSizeMax=text.fontSize;
            text.fontSizeMin=text.fontSize*0.4f;
            text.enableAutoSizing=true;
        }
        text.text=$"{points}/{ledger.ScoreLimit}";
        // The stars and markers belong to the native three-goal mode.
        foreach(var marker in new Component[]{bar._goalPointA,bar._goalPointB,bar._goalPointC,bar._goalIconA,bar._goalIconB,bar._goalIconC,bar._progressLineMain,bar._limiterParent})
            if(marker!=null&&marker.gameObject.activeSelf)marker.gameObject.SetActive(false);
    }
    public static void UpdateNativeUi(WarGoalsPanel __instance)
    {
        if(updatingHud||!uiEnabled||uiFault||ledger==null||view==null||!Guarded(view.Service))return;
        if(view.Panel==null||view.Panel.Pointer!=__instance.Pointer)return;
        if(!__instance.isActiveAndEnabled)return;
        try
        {
            updatingHud=true;
            if(uiSnapshot!=null&&(uiSnapshot.Panel==null||uiSnapshot.Panel.Pointer!=__instance.Pointer))RestoreNativeUi();
            if(uiSnapshot==null)
            {
                lastUiSecond=-1;
                uiSnapshot=new UiSnapshot {Panel=__instance,Phase=__instance._phaseText.text,Time=__instance._timeText.text,
                    PhaseSize=__instance._phaseText.fontSize,TimerColor=__instance._timeText.color,
                    AlphaBar=__instance._alphaDestructionBar.gameObject.activeSelf,BravoBar=__instance._bravoDestructionBar.gameObject.activeSelf,
                    AlphaConquest=__instance._alphaConquestBar.gameObject.activeSelf,BravoConquest=__instance._bravoConquestBar.gameObject.activeSelf,
                    PhaseActive=__instance._phaseText.gameObject.activeSelf,ProgressActive=__instance._phasePeriodProgressImage.gameObject.activeSelf,
                    MessageActive=__instance._message.gameObject.activeSelf};
                Log("native_ui_before",new{uiSnapshot.Phase,uiSnapshot.Time,uiSnapshot.PhaseSize,uiSnapshot.AlphaBar,uiSnapshot.BravoBar});
                HidePhaseRoot(__instance,__instance._phasePeriodProgressImage.transform);
                HidePhaseRoot(__instance,__instance._phaseText.transform);
                HidePhaseBoxes(__instance);
                __instance._phaseText.fontSize=uiSnapshot.PhaseSize*PhaseTextScale;
            }
            double shown=ShownElapsed();
            int remaining=(int)Math.Ceiling(Math.Max(0,ledger.Duration-shown));
            __instance._timeText.text=$"{remaining/60:00}:{remaining%60:00}";
            __instance._timeText.color=Color.cyan;
            // The native phase bar shows the rounds. It stays hidden during the setup phase, which has the large banner.
            bool showRound=setupEnds<0&&!(view.Service._isOnline&&OnlineSetupLeft()!=null);   // online deployment has the banner too
            foreach(var root in uiSnapshot.HiddenRoots)if(root.widget!=null&&root.widget.activeSelf!=showRound)root.widget.SetActive(showRound);
            __instance._phaseText.gameObject.SetActive(showRound);
            __instance._phasePeriodProgressImage.gameObject.SetActive(showRound);
            if(showRound)
            {
                var round=config.RoundBar(shown,ledger.Duration);
                __instance._phaseText.text=round.Text;
                __instance._phasePeriodProgressImage.fillAmount=round.Progress;
            }
            __instance._message.gameObject.SetActive(false);
            if(ShowScoreBars(__instance))ShowNextTick(__instance);
            else
            {
                __instance._alphaConquestBar.gameObject.SetActive(false);
                __instance._bravoConquestBar.gameObject.SetActive(false);
            }
            __instance._alphaDestructionBar.gameObject.SetActive(false);
            __instance._bravoDestructionBar.gameObject.SetActive(false);
            int second=(int)ledger.Elapsed;
            if(second!=lastUiSecond||Time.unscaledTime-lastUiWallTime>=2)
            {
                lastUiSecond=second;lastUiWallTime=Time.unscaledTime;
                Log("native_ui_readback",new{phase=__instance._phaseText.text,time=__instance._timeText.text,
                    phaseFontSize=__instance._phaseText.fontSize,
                    phaseVisible=__instance._phaseText.gameObject.activeSelf,phaseProgressVisible=__instance._phasePeriodProgressImage.gameObject.activeSelf,
                    phaseProgress=__instance._phasePeriodProgressImage.fillAmount,
                    modeBannerVisible=__instance._message.gameObject.activeSelf,alphaConquestVisible=__instance._alphaConquestBar.gameObject.activeSelf,
                    hiddenPhaseRoots=uiSnapshot.HiddenRoots.Select(x=>new{name=x.widget.name,visible=x.widget.activeSelf}).ToArray(),
                    timerVisible=__instance._timeText.gameObject.activeInHierarchy,
                    alphaScoreVisible=__instance._alphaVictoryPointsText.gameObject.activeInHierarchy,
                    bravoScoreVisible=__instance._bravoVictoryPointsText.gameObject.activeInHierarchy,
                    bravoConquestVisible=__instance._bravoConquestBar.gameObject.activeSelf,alphaDestructionVisible=__instance._alphaDestructionBar.gameObject.activeSelf,
                    bravoDestructionVisible=__instance._bravoDestructionBar.gameObject.activeSelf});
                Log("native_scoreboard_readback",new{
                    alpha=__instance._alphaVictoryPointsText.text,bravo=__instance._bravoVictoryPointsText.text,
                    time=__instance._timeText.text,ledger.Alpha,ledger.Bravo,ledger.Elapsed,
                    customHudPresent=GameObject.Find("FA_ConquestMatchHud")!=null,
                    alphaPlayersActive=__instance._alphaPlayersContainer.gameObject.activeInHierarchy,
                    bravoPlayersActive=__instance._bravoPlayersContainer.gameObject.activeInHierarchy,
                    alphaZonesActive=__instance._zonesAlphaContainer.gameObject.activeInHierarchy,
                    neutralZonesActive=__instance._zonesNeutralContainer.gameObject.activeInHierarchy,
                    bravoZonesActive=__instance._zonesBravoContainer.gameObject.activeInHierarchy});
            }
        }
        catch(Exception e){uiFault=true;uiEnabled=false;if(config.PhasePolicy=="continuous")Fail(e);else RestoreNativeUi();Log("native_ui_failed",new{error=e.ToString()});}
        finally{updatingHud=false;}
    }
    static void InvalidateHudPresentation() { config.ShowOverlay=true; }
    static int lastUiSecond=-1;
    static float lastUiWallTime=-100;
    static void RestoreUiPart(Action action,string part)
    {try{action();}catch(Exception e){Log("native_ui_part_restore_unavailable",new{part,message=e.Message});}}
    static void RestoreNativeUi()
    {
        var s=uiSnapshot;uiSnapshot=null;
        if(s==null)return;
        try
        {
            if(s.Panel==null)return;
            // Do not replay stale phase/time strings after the native phase or clock changed.
            RestoreUiPart(()=>s.Panel._phaseText.fontSize=s.PhaseSize,"phase font");
            foreach(var image in s.PhaseBoxes)if(image!=null)RestoreUiPart(()=>image.enabled=true,"phase box");
            RestoreUiPart(()=>{if(alphaNextTick!=null)UnityEngine.Object.Destroy(alphaNextTick.gameObject);if(bravoNextTick!=null)UnityEngine.Object.Destroy(bravoNextTick.gameObject);},"next tick");
            RestoreUiPart(()=>s.Panel._timeText.color=s.TimerColor,"timer color");
            RestoreUiPart(()=>s.Panel._phaseText.gameObject.SetActive(s.PhaseActive),"phase label");
            RestoreUiPart(()=>s.Panel._phasePeriodProgressImage.gameObject.SetActive(s.ProgressActive),"phase progress");
            RestoreUiPart(()=>s.Panel._message.gameObject.SetActive(s.MessageActive),"message");
            RestoreUiPart(()=>s.Panel._alphaConquestBar.gameObject.SetActive(s.AlphaConquest),"Alpha conquest");
            RestoreUiPart(()=>s.Panel._bravoConquestBar.gameObject.SetActive(s.BravoConquest),"Bravo conquest");
            RestoreUiPart(()=>s.Panel._alphaDestructionBar.gameObject.SetActive(s.AlphaBar),"Alpha destruction");
            RestoreUiPart(()=>s.Panel._bravoDestructionBar.gameObject.SetActive(s.BravoBar),"Bravo destruction");
            foreach(var root in s.HiddenRoots)if(root.widget!=null)RestoreUiPart(()=>root.widget.SetActive(root.active),"phase parent");
            Log("native_ui_restored",new{phaseFontSize=s.Panel._phaseText.fontSize,alphaBar=s.Panel._alphaDestructionBar.gameObject.activeSelf,bravoBar=s.Panel._bravoDestructionBar.gameObject.activeSelf});
        }
        catch(Exception e){Log("native_ui_restore_unavailable",new{message=e.Message,scope="panel may already be destroyed"});}
    }
}

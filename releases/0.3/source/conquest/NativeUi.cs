using UnityEngine;
using Il2CppBrokenArrow.Client.Ecs.UI.HUD.GameModes.WarGoals;
using Il2CppBrokenArrow.Client.Ecs.Controllers;

namespace FreedomArrow.Conquest;
public sealed partial class Prototype
{
    static bool updatingHud;
    static bool uiEnabled;
    static View labelView;
    static string labelMap;
    static GUIStyle labelStyle;
    static bool labelsOff,labelsLogged;
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
        labelView=candidate;labelMap=null;labelsOff=false;labelsLogged=false;
    }
    static void ClearLabelMode(){labelView=null;labelMap=null;}
    public override void OnGUI()
    {
        if(labelsOff||labelView==null||!config.ShowOverlay||Event.current.type!=EventType.Repaint)return;
        try
        {
            if(!Guarded(labelView.Service))return;
            if(labelMap==null)
            {
                if(labelView.ZoneIds().Count==0)return;
                labelMap=MapName(labelView);
            }
            int size=Math.Max(14,Screen.height/40);
            if(labelStyle==null||labelStyle.fontSize!=size)labelStyle=new GUIStyle(GUI.skin.label){fontSize=size,fontStyle=FontStyle.Bold,alignment=TextAnchor.MiddleCenter};
            var color=GUI.contentColor;
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
    public override void OnUpdate()
    {
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
            }
            int remaining=(int)Math.Ceiling(Math.Max(0,ledger.Duration-ledger.Elapsed));
            __instance._timeText.text=$"{remaining/60:00}:{remaining%60:00}";
            __instance._timeText.color=Color.cyan;
            foreach(var root in uiSnapshot.HiddenRoots)if(root.widget!=null&&root.widget.activeSelf)root.widget.SetActive(false);
            // Hide only mode widgets, preserving timer, VP stars, portraits and zone ownership.
            __instance._phaseText.gameObject.SetActive(false);
            __instance._phasePeriodProgressImage.gameObject.SetActive(false);
            __instance._message.gameObject.SetActive(false);
            __instance._alphaConquestBar.gameObject.SetActive(false);
            __instance._bravoConquestBar.gameObject.SetActive(false);
            __instance._alphaDestructionBar.gameObject.SetActive(false);
            __instance._bravoDestructionBar.gameObject.SetActive(false);
            int second=(int)ledger.Elapsed;
            if(second!=lastUiSecond||Time.unscaledTime-lastUiWallTime>=2)
            {
                lastUiSecond=second;lastUiWallTime=Time.unscaledTime;
                Log("native_ui_readback",new{phase=__instance._phaseText.text,time=__instance._timeText.text,
                    phaseFontSize=__instance._phaseText.fontSize,
                    phaseVisible=__instance._phaseText.gameObject.activeSelf,phaseProgressVisible=__instance._phasePeriodProgressImage.gameObject.activeSelf,
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

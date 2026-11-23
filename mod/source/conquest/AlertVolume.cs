using System.Reflection;
using System.Reflection.Emit;
using HarmonyLib;
using MelonLoader;
using UnityEngine;
using Il2CppBrokenArrow.Client.Ecs.UI.AlertsPanel;
using Il2CppBrokenArrow.Client.Ecs.UI.AlertsPanel.Systems;
using Il2CppPlugins.FMOD.Bridge;
using Il2CppFMODUnity;

namespace FreedomArrow.Conquest;
// 0.6 dev.47 (Osama, 7 November 2026): the aircraft and missile warning alarms play at half their old volume.
// Read from the game code (GameAssembly 6000.3.24f1): AlertsSystem.PlayAlertSound (RVA 0x5AD330) sends the "plane
// spotted" sound to UiEffects.PlayEvent, which calls FmodController.PlayOneShot (RVA 0xB39730): TryGetEvent, then
// RuntimeManager.PlayOneShot(guid, position). For a SpottedPlane alert we play the same event the same way, at half volume.
// The missile alarm is FlatIncomeMod's (AlarmSound.Play sets channel volume Clamp01(MissileSoundVolume)); its volume is
// multiplied by 0.5 in the code, so the player's own setting is not changed.
public sealed partial class Prototype
{
    const float AlarmScale=0.5f;
    static bool planeAlert,alertOff,alertLogged;
    static void InstallAlertVolume()
    {
        Patch(typeof(AlertsSystem),"PlayAlertSound",nameof(AlertSoundBefore),nameof(AlertSoundAfter));
        Patch(typeof(FmodController),"PlayOneShot",nameof(OneShotBefore),null);
        MelonLogger.Msg($"FREEDOM_ARROW_ALERT_VOLUME installed: the plane spotted alert plays at {AlarmScale:0.##} volume");
        var alarm=AccessTools.Method("FlatIncomeMod.AlarmSound:Play");
        if(alarm==null){MelonLogger.Msg("FREEDOM_ARROW_ALERT_VOLUME: FlatIncomeMod not loaded; no missile alarm to change");return;}
        instance!.HarmonyInstance.Patch(alarm,transpiler:new HarmonyMethod(typeof(Prototype),nameof(AlarmTranspiler)));
        MelonLogger.Msg($"FREEDOM_ARROW_ALERT_VOLUME: FlatIncomeMod missile alarm plays at {AlarmScale:0.##} of its volume setting");
    }
    public static void AlertSoundBefore(AlertType __0)=>planeAlert=__0==AlertType.SpottedPlane;
    public static void AlertSoundAfter()=>planeAlert=false;
    public static bool OneShotBefore(FmodController __instance,string __0,in Vector3 __1)
    {
        if(!planeAlert||alertOff)return true;
        planeAlert=false;
        try
        {
            if(!__instance.TryGetEvent(__0,out var guid))return true;
            var sound=RuntimeManager.CreateInstance(guid);
            sound.set3DAttributes(RuntimeUtils.To3DAttributes(__1));
            sound.setVolume(AlarmScale);
            sound.start();
            sound.release();
            if(!alertLogged){alertLogged=true;MelonLogger.Msg($"FREEDOM_ARROW_ALERT_VOLUME: plane spotted alert '{__0}' played at {AlarmScale:0.##} volume");}
            return false;
        }
        catch(Exception e)
        {
            alertOff=true;
            MelonLogger.Error("FREEDOM_ARROW_ALERT_VOLUME_FAILED: "+e.Message+"; the alert plays at full volume");
            return true;
        }
    }
    // After the Mathf.Clamp01 call that makes the channel volume, multiply the result by AlarmScale.
    static IEnumerable<CodeInstruction> AlarmTranspiler(IEnumerable<CodeInstruction> code)
    {
        int found=0;
        foreach(var c in code)
        {
            yield return c;
            if(c.opcode==OpCodes.Call&&c.operand is MethodInfo m&&m.Name=="Clamp01")
            {
                found++;
                yield return new CodeInstruction(OpCodes.Ldc_R4,AlarmScale);
                yield return new CodeInstruction(OpCodes.Mul);
            }
        }
        if(found!=1)MelonLogger.Error($"FREEDOM_ARROW_ALERT_VOLUME: FlatIncomeMod alarm volume call found {found} times (expected 1); check its volume");
    }
}

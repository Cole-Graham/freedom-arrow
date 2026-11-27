using HarmonyLib;
using MelonLoader;
using UnityEngine;
using Il2CppBrokenArrow.Client.Ecs.UI;
namespace FAModels;
// native-preload branch (Osama 27 Nov 2026 02:1x: "make a version of the game that preloads models natively like we do in vanilla").
// Vanilla units are in the game's own asset bundles, so nothing is built in the match. FA models are built by this mod. While the loading
// screen (SceneTransition) is still up, the preload works with a 40 ms frame budget instead of one blocking burst, and when the game asks the
// loading screen to fade out (CompleteLoading), the fade waits until every queued model, detail level, body and weapon is built, for at most
// MaxHoldSeconds. The game keeps running under the loading screen, so an online deployment clock keeps counting during the hold.
public partial class Mod
{
    internal static bool curtainUp;
    const double CurtainBudgetMs = 40;
    const float MaxHoldSeconds = 20f;
    static float holdStart = -1f;
    static bool holdDone, curtainBroken;
    static void InstallCurtain(HarmonyLib.Harmony h)
    {
        h.Patch(AccessTools.Method(typeof(SceneTransition), "Update"), prefix: new HarmonyMethod(typeof(Mod), nameof(CurtainBefore)));
        MelonLogger.Msg($"FAMODELS loading-screen hold installed: up to {MaxHoldSeconds:g} s while models build ({CurtainBudgetMs:g} ms per frame)");
    }
    static bool PreloadPending => preload.Count > 0 || (!LowModels && preloadHeavy.Count > 0);
    static bool CurtainBefore(SceneTransition __instance)
    {
        if (curtainBroken) return true;
        try
        {
            var cg = __instance._canvasGroup;
            curtainUp = cg != null && __instance.gameObject.activeInHierarchy && cg.alpha > 0.5f;
            if (holdDone || !curtainUp || !__instance._completionRequested) return true;
            if (!PreloadPending)
            {
                if (holdStart >= 0) MelonLogger.Msg($"FAMODELS loading-screen hold ended: all models built after {Time.realtimeSinceStartup - holdStart:F1} s");
                holdDone = true; return true;
            }
            if (holdStart < 0) { holdStart = Time.realtimeSinceStartup; MelonLogger.Msg($"FAMODELS loading-screen hold started: {preload.Count} model(s) and {preloadHeavy.Count} detail level(s) left"); }
            if (Time.realtimeSinceStartup - holdStart > MaxHoldSeconds)
            {
                MelonLogger.Warning($"FAMODELS loading-screen hold gave up after {MaxHoldSeconds:g} s: {preload.Count} model(s) and {preloadHeavy.Count} detail level(s) build in the match");
                holdDone = true; return true;
            }
            cg.alpha = 1f;
            return false;   // the loading screen stays fully opaque this frame
        }
        catch (Exception ex) { curtainBroken = true; curtainUp = false; MelonLogger.Error("FAMODELS loading-screen hold off: " + ex.Message); return true; }
    }
    // A new match (decks set again) re-arms the hold.
    static void ResetCurtainHold() { holdStart = -1f; holdDone = false; }
}

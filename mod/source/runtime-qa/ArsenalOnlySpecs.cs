using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.Decks_v2.UI;
using Il2CppBrokenArrow.Client.Ecs.UI;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.ArmyBuilder;
using MelonLoader;
namespace FreedomArrow;
// 0.9.4 (Osama, 21 November 2026, thread 1567745029781454889): "Make sure blue dragons is not playable in the deck creation but shows in the armory".
// The spec data has no Arsenal-only switch (ShowInHangar / ContentMembership also drive the Arsenal and DLC ownership), so the deck creation
// popup hides the spec buttons listed here after it renders them (DeckCreationPopup.RenderSpecs postfix, like ChinaUi.DeckCountries).
// The Arsenal spec filter and the unit cards are not touched. Spec 23 = Blue Dragon (Testing Preview).
static class ArsenalOnlySpecs
{
    static readonly int[] Ids = { 23 };
    static bool logged;
    public static void Install(HarmonyLib.Harmony h)
    {
        h.Patch(AccessTools.Method(typeof(DeckCreationPopup), "RenderSpecs"), postfix: new HarmonyMethod(typeof(ArsenalOnlySpecs), nameof(HideSpecs)));
        MelonLogger.Msg("FREEDOM_ARROW_ARSENAL_ONLY_SPECS installed: deck creation hides spec " + string.Join(",", Ids));
    }
    static void HideSpecs(DeckCreationPopup __instance)
    {
        var specs = __instance._specs; var buttons = __instance._specButtons;
        if (specs == null || buttons == null) return;
        int hidden = 0;
        for (int i = 0; i < specs.Length && i < buttons.Length; i++)
        {
            if (specs[i] == null || buttons[i] == null || System.Array.IndexOf(Ids, specs[i].Id) < 0) continue;
            buttons[i].gameObject.SetActive(false); hidden++;
        }
        if (!logged && hidden > 0) { logged = true; MelonLogger.Msg($"FREEDOM_ARROW_ARSENAL_ONLY_SPECS deck creation: {hidden} spec button(s) hidden"); }
    }
}

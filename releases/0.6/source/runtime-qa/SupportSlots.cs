using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.Decks;
using Il2CppNetworkCommon.Enums.Common;
using MelonLoader;
namespace FreedomArrow;
// 0.6 dev.21 (Osama, 7 November 2026): the SUP tab gets 2 more slots.
// Deck.GetMaxCategoryPointsOrSlots adds the slots of the deck's two specializations and then clamps the total to 7
// (cmp eax,7; cmovg at RVA 0x6F339B). The deck builder, deck preview, deck creation popup, ValidateDeck and TryFixDeck
// all read the slot count from this one method, so +2 here moves all of them together. Point caps are not changed.
static class SupportSlots
{
    const int Extra=2;
    static bool said;
    public static void Install(HarmonyLib.Harmony h)
    {
        h.Patch(AccessTools.Method(typeof(Deck),nameof(Deck.GetMaxCategoryPointsOrSlots)),postfix:new HarmonyMethod(typeof(SupportSlots),nameof(After)));
        MelonLogger.Msg($"FREEDOM_ARROW_SUPPORT_SLOTS: SUP tab +{Extra} slots (vanilla limit 7)");
    }
    static void After(UnitCategoryType categoryType,bool slots,ref int __result)
    {
        // A tab with no support slots in either specialization stays closed.
        if(!slots||categoryType!=UnitCategoryType.Support||__result<=0)return;
        __result+=Extra;
        if(!said){said=true;MelonLogger.Msg($"FREEDOM_ARROW_SUPPORT_SLOTS: first SUP tab read {__result-Extra} -> {__result}");}
    }
}

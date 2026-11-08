using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.Decks;
using Il2CppBrokenArrow.Client.Ecs.Decks.Models;
using Il2CppNetworkCommon.Enums.Common;
using MelonLoader;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
namespace FreedomArrow;
// 0.6 dev.21 (Osama, 7 November 2026): the SUP tab gets 2 more slots. dev.22 (Osama): the RECON tab gets 2 more slots too.
// Deck.GetMaxCategoryPointsOrSlots adds the slots of the deck's two specializations and then clamps the total to 7
// (cmp eax,7; cmovg at RVA 0x6F339B). The deck builder, deck preview, deck creation popup, ValidateDeck and TryFixDeck
// all read the slot count from this one method, so +2 here moves all of them together. Point caps are not changed.
static class SupportSlots
{
    const int Extra=2;
    static bool said,saidRecon;
    public static void Install(HarmonyLib.Harmony h)
    {
        h.Patch(AccessTools.Method(typeof(Deck),nameof(Deck.GetMaxCategoryPointsOrSlots)),postfix:new HarmonyMethod(typeof(SupportSlots),nameof(After)));
        h.Patch(AccessTools.Constructor(typeof(Deck),new[]{typeof(DeckDataModel)}),postfix:new HarmonyMethod(typeof(SupportSlots),nameof(Grow)));
        MelonLogger.Msg($"FREEDOM_ARROW_SUPPORT_SLOTS: SUP and RECON tabs +{Extra} slots (vanilla limit 7)");
    }
    // dev.30 (Osama, 7 November 2026): a saved deck keeps the slot arrays in its file (DeckDataModel "set2"), so decks
    // saved before dev.21 still showed 7 RECON and SUP slots. When a deck opens, a tab with fewer slots than the current
    // count gets empty slots at the end (new DeckSlotModel with only Category and SlotIndex, as CreateDeckDataModel makes
    // them), through the game's own Deck.ApplyResize. Cards and their order are not touched; a tab is never shortened.
    static int grown;
    static void Grow(Deck __instance)
    {
        try
        {
            foreach(var cat in Deck.GetCategories())
            {
                int max=Deck.GetMaxCategoryPointsOrSlots(__instance.Specs,cat,true);
                var data=__instance.Data.Cast<IDeckDataModel>();
                var cur=Deck.GetCategorySlots(data,cat);
                int have=cur==null?0:cur.Length;
                if(max<=have)continue;
                var arr=new Il2CppReferenceArray<DeckSlotModel>(max);
                for(int i=0;i<max;i++)arr[i]=i<have?cur[i]:new DeckSlotModel{Category=cat,SlotIndex=i};
                Deck.ApplyResize(data,cat,arr);
                if(++grown<=20)MelonLogger.Msg($"FREEDOM_ARROW_SUPPORT_SLOTS: deck '{__instance.Name}' {cat} {have} -> {max} slots");
            }
        }
        catch(System.Exception e){MelonLogger.Error("FREEDOM_ARROW_SUPPORT_SLOTS deck grow failed: "+e.Message);}
    }
    static void After(UnitCategoryType categoryType,bool slots,ref int __result)
    {
        // A tab with no slots in either specialization stays closed.
        if(!slots||(categoryType!=UnitCategoryType.Support&&categoryType!=UnitCategoryType.Recon)||__result<=0)return;
        __result+=Extra;
        bool recon=categoryType==UnitCategoryType.Recon;
        if(recon?saidRecon:said)return;
        if(recon)saidRecon=true;else said=true;
        MelonLogger.Msg($"FREEDOM_ARROW_SUPPORT_SLOTS: first {(recon?"RECON":"SUP")} tab read {__result-Extra} -> {__result}");
    }
}

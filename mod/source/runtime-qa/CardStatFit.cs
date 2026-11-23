using System;
using System.Collections.Generic;
using HarmonyLib;
using Il2CppTMPro;
using MelonLoader;
namespace FreedomArrow;
// 0.9.0-dev.4 (Osama, 14 November 2026: "unit stat card for numbers have second rows, we need everything to fit on one row").
// The armory card's bottom stat row (UnitInfoCard.SetUnitStatistic fills pooled UnitStatisticItem texts) wraps 5-digit
// values such as supply 15000 or weight 24000 and "1000 m" onto a second line. Each text now stays on one line and shrinks
// to fit its box (TextMeshPro auto-size, down to half its size). Vanilla-length values keep their normal size.
// 0.9.0-dev.8 (Osama, 14 November 2026: "can you just bring it back to vanilla but make it like 10% smaller?"): every stat number
// is 90 % of its vanilla size, all the same size, on one line. dev.7 shrank only the wide ones, so the row had mixed sizes.
static class CardStatFit
{
    static readonly Dictionary<IntPtr,float> size=new();
    static bool broken;
    public static void Install(HarmonyLib.Harmony h)
    {
        h.Patch(AccessTools.Method(typeof(Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.InfoCard.UnitInfoCard),"SetUnitStatistic"),
            postfix:new HarmonyMethod(typeof(CardStatFit),nameof(After)){priority=Priority.Last});
        MelonLogger.Msg("FREEDOM_ARROW_CARD_STAT_FIT installed: card stat numbers at 90 % of vanilla size, one line");
    }
    static void After(Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.InfoCard.UnitInfoCard __instance)
    {
        if(broken||__instance==null)return;
        try
        {
            // Pooled texts are reused across cards; remember each one's first (vanilla) size and use the largest on the card for all.
            var texts=new List<Il2CppTMPro.TextMeshProUGUI>();float full=0;
            foreach(var item in __instance.GetComponentsInChildren<Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.InfoCard.UnitStatisticItem>(true))
            {
                var t=item?.Text;
                if(t==null)continue;
                if(!size.TryGetValue(t.Pointer,out float f)){f=t.fontSize;size[t.Pointer]=f;t.textWrappingMode=TextWrappingModes.NoWrap;t.enableAutoSizing=false;t.overflowMode=TextOverflowModes.Overflow;}
                texts.Add(t);full=Math.Max(full,f);
            }
            foreach(var t in texts)t.fontSize=full*0.9f;
        }
        catch(Exception e){broken=true;MelonLogger.Error("FREEDOM_ARROW_CARD_STAT_FIT_FAILED: vanilla wrapping kept. "+e.Message);}
    }
}

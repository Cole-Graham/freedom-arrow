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
// 0.9.0-dev.7 (Osama, 14 November 2026: "unit card text is way too small"): TextMeshPro auto-size also fits the text box's
// height, and these boxes are shorter than a line, so every number dropped to half size. Now each text keeps its vanilla
// size and is scaled down only when its one-line width is wider than its box (not below half size).
static class CardStatFit
{
    static readonly Dictionary<IntPtr,float> size=new();
    static bool broken;
    public static void Install(HarmonyLib.Harmony h)
    {
        h.Patch(AccessTools.Method(typeof(Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.InfoCard.UnitInfoCard),"SetUnitStatistic"),
            postfix:new HarmonyMethod(typeof(CardStatFit),nameof(After)){priority=Priority.Last});
        MelonLogger.Msg("FREEDOM_ARROW_CARD_STAT_FIT installed: card stat numbers stay on one line at vanilla size unless too wide");
    }
    static void After(Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.InfoCard.UnitInfoCard __instance)
    {
        if(broken||__instance==null)return;
        try
        {
            foreach(var item in __instance.GetComponentsInChildren<Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.InfoCard.UnitStatisticItem>(true))
            {
                var t=item?.Text;
                if(t==null)continue;
                if(!size.TryGetValue(t.Pointer,out float full)){full=t.fontSize;size[t.Pointer]=full;t.textWrappingMode=TextWrappingModes.NoWrap;t.enableAutoSizing=false;}
                t.fontSize=full;
                float box=t.rectTransform.rect.width,need=t.GetPreferredValues(t.text).x;
                if(box>0&&need>box)t.fontSize=full*Math.Max(0.5f,box/need);
            }
        }
        catch(Exception e){broken=true;MelonLogger.Error("FREEDOM_ARROW_CARD_STAT_FIT_FAILED: vanilla wrapping kept. "+e.Message);}
    }
}

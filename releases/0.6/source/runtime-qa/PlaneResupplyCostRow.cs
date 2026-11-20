using System;
using HarmonyLib;
using MelonLoader;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.InfoCard;
namespace FreedomArrow;
// 0.9.2-dev.8 (Lateralus, 20 November 2026: "remove the "Resupply Cost" row from weapons on planes so players don't get confused ... that
// whole row should just be removed from all plane weapons"). For planes the ammunition SupplyCost only reduces the refund, and Freedom Arrow
// refunds planes in full, so the "Resupply cost NN pts" line on a plane weapon's ammo panel means nothing. The game builds that line inline in
// AmmoInfoExpansionPanel.SetMainAmmoStats(weapon, ammo, isAircraft); isAircraft is true only for planes (Units.Type 16, UnitInfoCard.
// OnWeaponButtonSelected), so helicopters and ground units keep it. This postfix hides that one pooled line; the pool shows it again when it
// is reused (OnGetItem sets the item active). Game data and the refund code are unchanged.
static class PlaneResupplyCostRow
{
    static bool broken,logged;
    public static void Install(HarmonyLib.Harmony h)
    {
        h.Patch(AccessTools.Method(typeof(AmmoInfoExpansionPanel),"SetMainAmmoStats"),
            postfix:new HarmonyMethod(typeof(PlaneResupplyCostRow),nameof(After)));
        MelonLogger.Msg("FREEDOM_ARROW_PLANE_RESUPPLY_COST installed: the Resupply cost line is hidden on plane weapon cards");
    }
    static void After(AmmoInfoExpansionPanel __instance,bool isAircraft)
    {
        if(broken||!isAircraft||__instance==null)return;
        try
        {
            string title=InfoCardLocalization.TextAmmoResupplyCost;
            var items=__instance._activeStatisticItems;
            if(string.IsNullOrEmpty(title)||items==null)return;
            for(int i=0;i<items.Count;i++)
            {
                var item=items[i];var t=item?.TitleText;
                if(t==null||t.text!=title)continue;
                item.gameObject.SetActive(false);
                if(!logged){logged=true;MelonLogger.Msg($"FREEDOM_ARROW_PLANE_RESUPPLY_COST hid '{title}' on a plane weapon card");}
            }
        }
        catch(Exception e){broken=true;MelonLogger.Error("FREEDOM_ARROW_PLANE_RESUPPLY_COST_FAILED: the line stays visible. "+e.Message);}
    }
}

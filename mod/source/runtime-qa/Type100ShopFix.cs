using System;
using HarmonyLib;
using MelonLoader;
using Il2CppBrokenArrow.Client.Ecs.Controllers;
using Il2CppBrokenArrow.DataBase.Models;
namespace FreedomArrow;
// Type 100 CSV transport fix. Root cause and fix by focolate (26 Nov 2026, thread 1575040931457929327, tested in an isolated client);
// ported on Osama's go ("Definitely port it", 26 Nov 10:2x). UnitsInfoService.ApplyReplaceModification takes the cached, already-resolved
// template of the swap unit (GetCachedUnit), writes the base unit into its BaseUnit and gives that same object to the base unit as
// ReplaceUnit. So the shop card and every spawned vehicle share one Units object. SpawnService.SpawnUnit then writes the carried
// squad's id into UnitToSpawn.OwnerInfantryID, and the independent shop card now looks like an attached transport: the next order asks
// the card's empty transport slot ("Deck has no transport ID!") and the card can no longer deploy. focolate's measurement: map counts
// 2,1,1,2 before, 2,2,2,2 after. This prefix gives each caller its own copy of the resolved template (MemberwiseClone keeps the
// resolved APS and weapons), only for the Type 100 transport (unit 1416) with one of its three swap loadouts. Everything else, and
// the 40 mm CT default (option 31360), stays on the game's own path. Data: options 31361/31362/31363 -> units 1417/1418/1419.
static class Type100ShopFix
{
    const int Transport=1416;
    static readonly (int option,int unit)[] Loadouts={(31361,1417),(31362,1418),(31363,1419)};
    static bool broken,logged;
    public static void Install(HarmonyLib.Harmony h)
    {
        h.Patch(AccessTools.Method(typeof(UnitsInfoService),"ApplyReplaceModification"),
            prefix:new HarmonyMethod(typeof(Type100ShopFix),nameof(Before)));
        MelonLogger.Msg("FREEDOM_ARROW_TYPE100_SHOP_FIX installed: Type 100 CSV transport loadouts get their own unit copy");
    }
    static bool Before(Il2CppSystem.Collections.Generic.ICollection<int> __0,Units __1)
    {
        if(broken||__1==null||__1.Id!=Transport||__0==null||__0.Count!=1)return true;
        try
        {
            int id=0;
            foreach(var (option,unit) in Loadouts) if(__0.Contains(option)){id=unit;break;}
            if(id==0)return true;
            var template=UnitsInfoService.GetCachedUnit(id)?.Cast<Units>();
            if(template==null||template.Id!=id)return true;
            var variant=template.MemberwiseClone().Cast<Units>();
            variant.BaseUnit=__1;
            __1.ReplaceUnit=variant;
            if(!logged){logged=true;MelonLogger.Msg($"FREEDOM_ARROW_TYPE100_SHOP_FIX gave transport {Transport} its own copy of unit {id}");}
            return false;
        }
        catch(Exception e){broken=true;MelonLogger.Error("FREEDOM_ARROW_TYPE100_SHOP_FIX_FAILED: the game's own swap is used. "+e.Message);return true;}
    }
}

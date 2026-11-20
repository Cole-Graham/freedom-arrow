using System;
using System.IO;
using System.Text.Json.Nodes;
using HarmonyLib;
using MelonLoader;
using Il2CppBrokenArrow.Client.Ecs.Configs;
using Il2CppBrokenArrow.Client.Ecs.Controllers;
namespace FreedomArrow;
// 0.9.2-dev.8 (Lateralus, 20 November 2026: "Yes go with option 1 and compensate the nukes"). A plane's return delay is PlanesRefundFloor + base +
// K x (sum of shots x ResupplyTime^P)^(1/P) (RefundSystem.GetPurchaseDelay, 1.2.2.1). Vanilla K 1, P 5 makes 1 missile cost most of the time
// of 16; option 1 sets K 0.3, P 1.6 (game-config.json PlanesRefundAmmoCoeff_K/_P). The card timer and the battle refund both read
// GameConfig.Instance, so the values are set before each unit card is filled and before each battle loads its players.
static class PlaneReturnCurve
{
    static float k,p;static (float k,float p)? vanilla;static bool broken,logged;
    public static void Install(HarmonyLib.Harmony h,string root)
    {
        var game=JsonNode.Parse(File.ReadAllText(Path.Combine(root,"game-config.json")));
        k=game["PlanesRefundAmmoCoeff_K"].GetValue<float>();p=game["PlanesRefundAmmoCoeff_P"].GetValue<float>();
        if(!(k>0&&k<=2&&p>=1&&p<=10))throw new InvalidDataException("PlanesRefundAmmoCoeff_K/P out of range");
        var pre=new HarmonyMethod(typeof(PlaneReturnCurve),nameof(Apply));
        h.Patch(AccessTools.Method(typeof(Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.InfoCard.UnitInfoCard),"SetUnitStatistic"),prefix:pre);
        h.Patch(AccessTools.Method(typeof(ScenarioController),"LoadTeamsAndPlayers"),prefix:pre);
        MelonLogger.Msg($"FREEDOM_ARROW_PLANE_RETURN installed: plane return ammo curve K {k} P {p} (vanilla 1 / 5)");
    }
    static void Apply()
    {
        if(broken)return;
        try
        {
            var g=GameConfig.Instance;if(g==null)return;
            vanilla??=(g.PlanesRefundAmmoCoeff_K,g.PlanesRefundAmmoCoeff_P);
            (g.PlanesRefundAmmoCoeff_K,g.PlanesRefundAmmoCoeff_P)=Runtime.IsApplied?(k,p):vanilla.Value;
            if(!logged){logged=true;MelonLogger.Msg($"FREEDOM_ARROW_PLANE_RETURN K {g.PlanesRefundAmmoCoeff_K} P {g.PlanesRefundAmmoCoeff_P} (vanilla {vanilla.Value.k} / {vanilla.Value.p})");}
        }
        catch(Exception e){broken=true;MelonLogger.Error("FREEDOM_ARROW_PLANE_RETURN_FAILED: vanilla plane return times. "+e.Message);}
    }
}

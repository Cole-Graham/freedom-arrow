using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.GNetwork.Services.Room;
using Il2CppBrokenArrow.Client.Ecs.Shop.UI;
using Il2CppBrokenArrow.Client.Ecs.Utils;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;
// Server points overwrite log (Lateralus 16 Nov 2026 04:1x PST, thread 1571554273639006392: "Yes add the log line on a test build").
// Read from GameAssembly 6000.3.24f1: every 10 s the client sends its PlayerInfo.Points to the server (NetworkUserRoomStateHandler.
// SendClientPointsValidation), and the server can answer with a message that NetworkUserRoomStateHandler.OnClientGetMoney(BitGalaxy) reads as
// one float, clamps and writes straight into the local PlayerInfo.Points. When the server sends it is server code we cannot read. This logs
// each call with the points before and after, so a reset of mod-paid points (plane sale, fixed income) shows in the log. A 60 s heartbeat
// records that the hook was live, so "no server_money_set lines" means the server did not overwrite the points.
static class ServerMoney
{
    const int MaxLog=500;
    static PlayerInfo me;static float before=float.NaN,nextBeat;static int calls,logged;static bool on;
    public static void Install(HarmonyLib.Harmony harmony)
    {
        var m=AccessTools.Method(typeof(NetworkUserRoomStateHandler),"OnClientGetMoney")??throw new MissingMethodException("NetworkUserRoomStateHandler.OnClientGetMoney");
        harmony.Patch(m,prefix:new HarmonyMethod(typeof(ServerMoney),nameof(Before)),postfix:new HarmonyMethod(typeof(ServerMoney),nameof(After)));
        var ui=AccessTools.Method(typeof(MainShopButtonUI),"GameUpdate")??throw new MissingMethodException("MainShopButtonUI.GameUpdate");
        harmony.Patch(ui,postfix:new HarmonyMethod(typeof(ServerMoney),nameof(Hud)));
        on=true;
        MelonLogger.Msg("FREEDOM_ARROW_SERVER_MONEY installed: logs every server points overwrite (OnClientGetMoney)");
        DiagnosticLog.Write("server_money_installed",new{hook="NetworkUserRoomStateHandler.OnClientGetMoney"});
    }
    static void Hud(PlayerInfo __0){if(__0!=null)me=__0;}
    static float Points(){try{return me==null?float.NaN:me.Points.Value;}catch{return float.NaN;}}
    static void Before(){before=Points();}
    static void After()
    {
        calls++;
        try
        {
            float after=Points();
            if(logged<MaxLog){logged++;DiagnosticLog.Write("server_money_set",new{t=Time.time,before,after,delta=after-before,calls,planeSalesPaying=PlaneSale.Active});}
            MelonLogger.Msg($"FREEDOM_ARROW_SERVER_MONEY set by server: {before:0.#} -> {after:0.#} (call {calls})");
        }
        catch(Exception x){MelonLogger.Error("FREEDOM_ARROW_SERVER_MONEY log failed: "+x.Message);}
    }
    public static void LateUpdate()
    {
        if(!on||me==null||Time.time<nextBeat)return;
        nextBeat=Time.time+60;
        if(logged<MaxLog){logged++;DiagnosticLog.Write("server_money_watch",new{t=Time.time,points=Points(),serverSets=calls,planeSalesPaying=PlaneSale.Active});}
    }
    public static void SceneChanged(){me=null;nextBeat=0;}
}

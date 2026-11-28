using HarmonyLib;
using MelonLoader;
namespace FreedomArrow;
// Osama 27 Nov 2026 20:0x PST (bugs thread): "remove the ban risk warning". ArrowQueue (third-party, shipped unchanged) shows
// "An AI bot in the lobby — a ban risk with mods!" on its lobby card whenever ArrowQueue.Game.HasBots() is true (LobbyCard.Pump, 0.10.31).
// The claim has no source, and our PvE / vs-AI maps use bot slots on purpose (26-27 Nov logs: ~140 online bot matches). HasBots has
// no other caller in ArrowQueue 0.10.31, so answering false only removes that line. Nothing else about bots or lobbies changes.
static class BotWarningOff
{
    public static void Install(HarmonyLib.Harmony h)
    {
        var m=AccessTools.Method(AccessTools.TypeByName("ArrowQueue.Game"),"HasBots");
        if(m==null){MelonLogger.Warning("FREEDOM_ARROW_BOT_WARNING_OFF: ArrowQueue.Game.HasBots not found; the warning stays");return;}
        h.Patch(m,prefix:new HarmonyMethod(typeof(BotWarningOff),nameof(NoBots)));
        MelonLogger.Msg("FREEDOM_ARROW_BOT_WARNING_OFF installed: no ArrowQueue \"AI bot in the lobby\" ban-risk warning");
    }
    static bool NoBots(ref bool __result){__result=false;return false;}
}

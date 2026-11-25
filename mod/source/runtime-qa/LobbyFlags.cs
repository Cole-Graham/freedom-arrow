using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Network.Lobby;
using MelonLoader;
namespace FreedomArrow;
// Lobby country flags (Osama 25 Nov 2026 01:4x PST, thread 1567745029781454889: "Please remove the EU flag from the lobby please for the time
// being"). LobbyForcesSettings makes one button per country for each team's allowed-forces row; _countryButtons maps each button to the
// country's flag name. The Eurocorp button (FA_EUROCORP_FLAG, country 5 "Eurocorp (Preview)") is switched off there only, so the Arsenal
// and deck creation still show the Eurocorp preview. To show it again, remove its name from Hidden.
static class LobbyFlags
{
    static readonly HashSet<string> Hidden = new() { "FA_EUROCORP_FLAG" };
    static bool logged;
    public static void Install(HarmonyLib.Harmony h)
    {
        var post = new HarmonyMethod(typeof(LobbyFlags), nameof(Hide));
        h.Patch(AccessTools.Method(typeof(LobbyForcesSettings), "Init") ?? throw new MissingMethodException("LobbyForcesSettings.Init"), postfix: post);
        h.Patch(AccessTools.Method(typeof(LobbyForcesSettings), "UpdateAllowedCountries") ?? throw new MissingMethodException("LobbyForcesSettings.UpdateAllowedCountries"), postfix: post);
    }
    static void Hide(LobbyForcesSettings __instance)
    {
        try
        {
            var buttons = __instance._countryButtons; if (buttons == null) return;
            int hidden = 0;
            foreach (var kv in buttons)
                if (kv.Key != null && kv.Value != null && Hidden.Contains(kv.Value) && kv.Key.gameObject.activeSelf) { kv.Key.gameObject.SetActive(false); hidden++; }
            if (!logged && hidden > 0) { logged = true; MelonLogger.Msg($"FREEDOM_ARROW_LOBBY_FLAGS: {hidden} lobby flag button(s) hidden ({string.Join(", ", Hidden)})"); }
        }
        catch (Exception e) { MelonLogger.Warning("FREEDOM_ARROW_LOBBY_FLAGS: not applied (" + e.Message + ")"); }
    }
}

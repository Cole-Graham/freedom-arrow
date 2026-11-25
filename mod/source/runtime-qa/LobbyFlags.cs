using Il2CppBrokenArrow.Client.Ecs.GNetwork.Services.Lobby;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Network.Lobby;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;
// Lobby country flags (Osama 25 Nov 2026 01:4x PST, thread 1567745029781454889: "Please remove the EU flag from the lobby please for the time
// being"). LobbyForcesSettings makes one button per country for each team's allowed-forces row; _countryButtons maps each button to the
// country's flag name. The Eurocorp button (FA_EUROCORP_FLAG, country 5 "Eurocorp (Preview)") is switched off there only, so the Arsenal
// and deck creation still show the Eurocorp preview. To show it again, remove its name from Hidden.
// No Harmony patch on LobbyForcesSettings (25 Nov 10:3x): the 0.9.7-dev.9..dev.15 postfix on LobbyForcesSettings.Init(TeamSide, ...) threw a
// NullReferenceException in the Il2CppInterop trampoline for both teams, the forces rows were never set up and every new lobby stayed on the
// loading screen (Osama: "I'm stuck at an infinite loading screen whenever I try to make a lobby"). A menu tick (every 15 frames, only while
// in a lobby) hides the button instead; the game's own Init and UpdateAllowedCountries run untouched.
static class LobbyFlags
{
    static readonly HashSet<string> Hidden = new() { "FA_EUROCORP_FLAG" };
    static bool inMenu, logged, failed;
    public static void SceneChanged(string scene) => inMenu = scene == "Hangar_Scene";
    public static void Tick()
    {
        if (!inMenu || failed || Time.frameCount % 15 != 0) return;
        try
        {
            Il2CppBrokenArrow.Shared.Ecs.Services.Session.TryGetService<NetworkLobbyService>(out var lobby, false);
            if (lobby == null || lobby.LobbyId == 0) return;
            int hidden = 0;
            foreach (var s in UnityEngine.Object.FindObjectsOfType<LobbyForcesSettings>())
            {
                var buttons = s?._countryButtons; if (buttons == null) continue;
                foreach (var kv in buttons)
                    if (kv.Key != null && kv.Value != null && Hidden.Contains(kv.Value) && kv.Key.gameObject.activeSelf) { kv.Key.gameObject.SetActive(false); hidden++; }
            }
            if (!logged && hidden > 0) { logged = true; MelonLogger.Msg($"FREEDOM_ARROW_LOBBY_FLAGS: {hidden} lobby flag button(s) hidden ({string.Join(", ", Hidden)})"); }
        }
        catch (Exception e) { failed = true; MelonLogger.Warning("FREEDOM_ARROW_LOBBY_FLAGS: off for this session (" + e.Message + ")"); }
    }
}

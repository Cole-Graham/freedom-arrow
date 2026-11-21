using System;
using System.Diagnostics;
using System.Reflection;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.UI.MainMenu;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Network.Lobby;
using MelonLoader;
namespace FreedomArrow;
// 0.9.4 (Osama, 21 November 2026, thread 1573561286803980289): "make the play button open up the current Mod Lobbies section of the menu.
// Keep it simple and clean. So there's no way to play online skirmish or normal lobby."
// The main menu's Play tab is the MainMenuButton whose content holds the game's LobbyScreen (ArrowQueue finds it the same way,
// ModTab.ShowLobbyTab). A player's click on it opens ArrowQueue's Mod Lobbies page (ModTab.Open) instead of the native play tab.
// The native tab still opens when ArrowQueue itself selects it (it shows a joined mod lobby there) and while the player is in a lobby.
// ArrowQueue's own postfix on the same click (GameTabClicked) hides its page, so the page is opened one frame later.
// If ArrowQueue's methods are missing, the click goes to the native tab; BALocalSkirmish still refuses every non-scenario online lobby.
static class PlayToModLobbies
{
    static MethodInfo open, inLobby;
    static bool pending;
    public static void Install(HarmonyLib.Harmony h)
    {
        open=AccessTools.Method(AccessTools.TypeByName("ArrowQueue.ModTab"),"Open");
        var game=AccessTools.TypeByName("ArrowQueue.Game");
        inLobby=game==null?null:AccessTools.PropertyGetter(game,"InLobby");
        if(open==null||inLobby==null){MelonLogger.Error("FREEDOM_ARROW_PLAY_MENU: ArrowQueue ModTab.Open or Game.InLobby not found; Play keeps the game's own tab");return;}
        h.Patch(AccessTools.Method(typeof(MainMenuButtonControling),"OnMainMenuButtonClick"),prefix:new HarmonyMethod(typeof(PlayToModLobbies),nameof(Before)){priority=Priority.First});
        MelonLogger.Msg("FREEDOM_ARROW_PLAY_MENU: Play opens Mod Lobbies");
    }
    static bool Before(MainMenuButton __0)
    {
        try
        {
            var content=__0?._showTargetContent;
            if(content==null||content.GetComponentInChildren<LobbyScreen>(true)==null)return true;   // not the Play tab
            if(FromArrowQueue())return true;                                                            // ArrowQueue showing a mod lobby
            if(inLobby.Invoke(null,null) is true)return true;                                          // already in a lobby: show it
            pending=true;
            MelonLogger.Msg("FREEDOM_ARROW_PLAY_MENU: Play -> Mod Lobbies");
            return false;
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_PLAY_MENU: "+e.Message);return true;}
    }
    static bool FromArrowQueue()
    {
        foreach(var f in new StackTrace().GetFrames()??Array.Empty<StackFrame>())
            if(f.GetMethod()?.DeclaringType?.Namespace=="ArrowQueue")return true;
        return false;
    }
    public static void Tick()
    {
        if(!pending)return;
        pending=false;
        try{open.Invoke(null,null);}
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_PLAY_MENU: open failed: "+e.Message);}
    }
}

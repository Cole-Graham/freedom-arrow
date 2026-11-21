using System;
using System.Diagnostics;
using System.Reflection;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.UI;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Network.Lobby;
using MelonLoader;
namespace FreedomArrow;
// 0.9.4 (Osama, 21 November 2026, thread 1573561286803980289): "let's change it so the mod lobbies opens when you press the Multiplayer button
// in the Play section. Not the play button itself" / "so they can play the other modes in play". Play keeps its own tab (Skirmish vs AI,
// Scenarios, Campaign). Multiplayer opens the game's online lobby list (LobbyList, child of NetworkScreen); when that list opens because of
// the player, it is closed with its own back button (_backToPlayTabButton) and ArrowQueue's Mod Lobbies page (ModTab.Open) opens one frame
// later. The list still opens when ArrowQueue opens it (stack has an ArrowQueue frame) or while the player is in a lobby (Game.InLobby).
// If ArrowQueue's methods are missing, the list opens as before; BALocalSkirmish still refuses every non-scenario online lobby.
// The first run logs the Play section's buttons (FREEDOM_ARROW_PLAY_MENU buttons: ...) so the in-game test can confirm which is Multiplayer.
static class MultiplayerToModLobbies
{
    static MethodInfo open, inLobby;
    static bool pending, logged;
    public static void Install(HarmonyLib.Harmony h)
    {
        open=AccessTools.Method(AccessTools.TypeByName("ArrowQueue.ModTab"),"Open");
        var game=AccessTools.TypeByName("ArrowQueue.Game");
        inLobby=game==null?null:AccessTools.PropertyGetter(game,"InLobby");
        h.Patch(AccessTools.Method(typeof(PlayTab),nameof(PlayTab.Initialize)),postfix:new HarmonyMethod(typeof(MultiplayerToModLobbies),nameof(LogButtons)));
        if(open==null||inLobby==null){MelonLogger.Error("FREEDOM_ARROW_PLAY_MENU: ArrowQueue ModTab.Open or Game.InLobby not found; Multiplayer keeps the game's lobby list");return;}
        h.Patch(AccessTools.Method(typeof(LobbyList),"OnEnable"),postfix:new HarmonyMethod(typeof(MultiplayerToModLobbies),nameof(Opened)));
        MelonLogger.Msg("FREEDOM_ARROW_PLAY_MENU: Multiplayer opens Mod Lobbies");
    }
    static void LogButtons(PlayTab __instance)
    {
        if(logged)return;
        try
        {
            var c=__instance._buttonsContainer;if(c==null)return;logged=true;
            var names=new System.Collections.Generic.List<string>();
            for(int i=0;i<c.transform.childCount;i++){var t=c.transform.GetChild(i);names.Add(t.name+(t.gameObject.activeSelf?"":" (hidden)"));}
            MelonLogger.Msg("FREEDOM_ARROW_PLAY_MENU buttons: "+string.Join(", ",names));
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_PLAY_MENU: "+e.Message);}
    }
    static void Opened(LobbyList __instance)
    {
        try
        {
            if(FromArrowQueue()||inLobby.Invoke(null,null) is true)return;
            var back=__instance._backToPlayTabButton;
            if(back==null){MelonLogger.Warning("FREEDOM_ARROW_PLAY_MENU: lobby list has no back button; list left open");return;}
            back.onClick.Invoke();
            pending=true;
            MelonLogger.Msg("FREEDOM_ARROW_PLAY_MENU: Multiplayer -> Mod Lobbies");
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_PLAY_MENU: "+e.Message);}
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

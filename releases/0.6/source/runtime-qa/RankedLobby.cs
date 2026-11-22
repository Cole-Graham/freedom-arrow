using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.Decks;
using Il2CppBrokenArrow.Client.Ecs.Decks.Models;
using Il2CppBrokenArrow.Client.Ecs.GNetwork.Services.Lobby;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Network.TeamPanel;
using Il2CppNetworkCommon.Enums;
using MelonLoader;
using System.Reflection;
using System.Text.Json;
using UnityEngine;
namespace FreedomArrow;
// Ranked match flow (Lateralus 22 Nov 2026, "go" on the proposal):
// 1. A default deck chosen in the ranked menu; the client reports whether it is valid (hub SetRankedDeck). The hub refuses a search
//    while any group member has no valid deck; the GROUP slots show a warning and FIND MATCH is disabled with the reason.
// 2-3. Match found: ArrowQueue's normal flow builds the native lobby (host creates it with the hub's map, everyone joins, teams set).
// 4. Hub phase "deck" (60 s, server clock): my default deck is selected once; enemy deck info is hidden in the lobby's player panels
//    (TeamPanelPlayerInfo.ToggleDeckInfo forced off for the other side). At the end, no deck -> default deck, then ready.
// 5. "reveal" (5 s): enemy decks shown. "launch": the host's game starts the match with the vanilla start call
//    (NetworkLobbyService.ChangeLobbyStatus(Launching)) once every client is ready.
static partial class RankedMenu
{
    static string deckName="";
    static float nextDeckReport;static string lastDeckReport="";
    static DeckService DeckSvc(){Il2CppBrokenArrow.Shared.Ecs.Services.Session.TryGetService<DeckService>(out var d,false);return d;}
    static NetworkLobbyService LobbySvc(){Il2CppBrokenArrow.Shared.Ecs.Services.Session.TryGetService<NetworkLobbyService>(out var l,false);return l;}
    static List<DeckDataModel> validCache=new();static float validAt=-100f;
    static List<DeckDataModel> ValidDecks()
    {
        if(Time.unscaledTime-validAt<3f)return validCache;   // validation walks every deck: at most every 3 s
        validAt=Time.unscaledTime;
        var res=new List<DeckDataModel>();validCache=res;
        try
        {
            var ds=DeckSvc();var all=ds?.AllValidDecks;if(all==null)return res;
            foreach(var d in all){if(d==null)continue;bool nonFull;if(ds.ValidateDeck(d.Cast<IDeckDataModel>(),out nonFull))res.Add(d);}
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_RANKED decks: "+e.Message);}
        return res;
    }
    static DeckDataModel DefaultDeck(){if(deckName.Length==0)return null;foreach(var d in ValidDecks())if(d.Name==deckName)return d;return null;}
    // every 10 s, and at once when the choice changes
    static void ReportDeck(float now)
    {
        var d=DefaultDeck();var key=(d!=null)+"|"+deckName;
        if(key==lastDeckReport&&now<nextDeckReport)return;
        nextDeckReport=now+10f;lastDeckReport=key;
        Call("SetRankedDeck",_=>{},d!=null,deckName);
    }

    // ---------- in the ranked lobby ----------
    static string lobbyMatch="",phase="";static float phaseEndAt,launchTry;static bool deckApplied,finalized,launched,hidingDecks;
    static TeamSide myTeam=TeamSide.Alpha;
    static PropertyInfo pGameMe;
    static int MyClientId(){try{pGameMe??=AccessTools.Property(tGame,"Me");var me=pGameMe?.GetValue(null);return me==null?-1:Traverse.Create(me).Property("Id").GetValue<int>();}catch{return -1;}}
    public static void InstallLobby(HarmonyLib.Harmony h)
    {
        h.Patch(AccessTools.Method(typeof(TeamPanelPlayerInfo),nameof(TeamPanelPlayerInfo.ToggleDeckInfo)),prefix:new HarmonyMethod(typeof(RankedMenu),nameof(DeckInfoShown)));
        h.Patch(AccessTools.Method(typeof(TeamPanelPlayerInfo),nameof(TeamPanelPlayerInfo.SetDeckInfo)),postfix:new HarmonyMethod(typeof(RankedMenu),nameof(DeckInfoSet)));
    }
    static bool Enemy(TeamPanelPlayerInfo p){try{var ci=p._clientInfo;return ci!=null&&!ci.IsBot&&(ci.TeamSide==TeamSide.Alpha||ci.TeamSide==TeamSide.Bravo)&&ci.TeamSide!=myTeam;}catch{return false;}}
    static void DeckInfoShown(TeamPanelPlayerInfo __instance,ref bool on){if(hidingDecks&&on&&Enemy(__instance))on=false;}
    static void DeckInfoSet(TeamPanelPlayerInfo __instance){if(hidingDecks&&Enemy(__instance))__instance.ToggleDeckInfo(false);}
    static void RefreshPanels(bool show)
    {
        foreach(var p in UnityEngine.Object.FindObjectsOfType<TeamPanelPlayerInfo>())
            try{if(p._clientInfo==null||p._clientInfo.IsBot)continue;if(show){p.ToggleDeckInfo(true);p.SetDeckInfo();}else if(Enemy(p))p.ToggleDeckInfo(false);}catch{}
    }

    static float nextLobbyTick,nextLobbyAsk;
    static void LobbyTick(float now)
    {
        if(now<nextLobbyTick)return;nextLobbyTick=now+0.25f;
        bool inLobby=false;try{inLobby=pInLobby.GetValue(null) is true;}catch{}
        if(inLobby&&now>=nextLobbyAsk){nextLobbyAsk=now+1f;Ask();}   // the hub's phase clock, every second while in a lobby
        JsonElement m=default;bool inMatch=false;
        try{if(meJson.Length>0){var r=JsonDocument.Parse(meJson).RootElement;if(r.TryGetProperty("match",out m)&&m.ValueKind==JsonValueKind.Object)inMatch=true;}}catch{}
        if(!inMatch||!inLobby)
        {
            if(lobbyMatch.Length>0){if(hidingDecks){hidingDecks=false;RefreshPanels(true);}MelonLogger.Msg("FREEDOM_ARROW_RANKED_LOBBY left "+lobbyMatch);}
            lobbyMatch="";phase="";return;
        }
        var id=m.GetProperty("id").GetString()??"";
        if(id!=lobbyMatch){lobbyMatch=id;deckApplied=finalized=launched=false;launchTry=0;MelonLogger.Msg($"FREEDOM_ARROW_RANKED_LOBBY {id} on {m.GetProperty("map").GetString()}");}
        var ph=m.GetProperty("phase").GetString()??"";
        phaseEndAt=now+m.GetProperty("phaseLeftMs").GetInt32()/1000f;
        if(ph!=phase){MelonLogger.Msg($"FREEDOM_ARROW_RANKED_LOBBY phase {ph}");phase=ph;}
        var lobby=LobbySvc();var st=lobby?.State;int meId=MyClientId();
        Il2CppNetworkCommon.Messages.Clients.ClientInfo ci=null;
        if(st!=null&&meId>=0)st.TryGetClientById(meId,out ci);
        if(ci!=null&&(ci.TeamSide==TeamSide.Alpha||ci.TeamSide==TeamSide.Bravo))myTeam=ci.TeamSide;
        bool hide=phase is "join" or "deck";
        if(hide!=hidingDecks){hidingDecks=hide;RefreshPanels(!hide);}
        else if(hide)RefreshPanels(false);
        try
        {
            if(phase=="deck"&&!deckApplied&&ci!=null&&lobby!=null)
            {
                deckApplied=true;var d=DefaultDeck();
                if(d!=null){lobby.ChangeClientDeck(d);MelonLogger.Msg("FREEDOM_ARROW_RANKED_LOBBY default deck "+d.Name);}
            }
            if(phase is "reveal" or "launch"&&!finalized&&ci!=null&&lobby!=null)
            {
                finalized=true;
                if(ci.ShortDeck==null){var d=DefaultDeck();if(d!=null){lobby.ChangeClientDeck(d);MelonLogger.Msg("FREEDOM_ARROW_RANKED_LOBBY no deck at the end: default "+d.Name);}}
                if(ci.Status!=ClientLobbyStatus.Ready&&!lobby.IsHost){lobby.ChangeClientReadyStatus(meId);MelonLogger.Msg("FREEDOM_ARROW_RANKED_LOBBY ready");}
            }
            if(phase=="launch"&&!launched&&lobby!=null&&lobby.IsHost&&now>=launchTry)
            {
                launchTry=now+1f;
                if(lobby.AllClientsReady()){launched=true;lobby.ChangeLobbyStatus(LobbyStatus.Launching);MelonLogger.Msg("FREEDOM_ARROW_RANKED_LOBBY host launched the match");}
            }
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_RANKED_LOBBY: "+e.Message);}
    }
    // small banner over the lobby while the phases run
    static void LobbyBanner()
    {
        if(lobbyMatch.Length==0||phase.Length==0)return;
        int left=Mathf.Max(0,Mathf.CeilToInt(phaseEndAt-Time.unscaledTime));
        string text=phase switch{"join"=>"RANKED · waiting for every player to join the lobby",
            "deck"=>$"RANKED · pick your deck: {left} s · enemy decks are hidden",
            "reveal"=>$"RANKED · decks revealed · launching in {left} s",_=>"RANKED · launching"};
        float w=Screen.height*0.62f,h=Screen.height*0.045f;var r=new Rect((Screen.width-w)/2,Screen.height*0.105f,w,h);
        var o=GUI.color;GUI.color=new Color(0.06f,0.07f,0.08f,0.92f);GUI.DrawTexture(r,Texture2D.whiteTexture);
        GUI.color=phase=="deck"?Red:Green;GUI.DrawTexture(new Rect(r.x,r.yMax-3,r.width,3),Texture2D.whiteTexture);GUI.color=o;
        var s=new GUIStyle(GUI.skin.label){fontSize=Mathf.RoundToInt(h*0.42f),fontStyle=FontStyle.Bold,alignment=TextAnchor.MiddleCenter};s.normal.textColor=Color.white;
        GUI.Label(r,text,s);
    }
}

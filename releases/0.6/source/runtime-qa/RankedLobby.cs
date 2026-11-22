using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.Decks;
using Il2CppBrokenArrow.Client.Ecs.Decks.Models;
using Il2CppBrokenArrow.Client.Ecs.GNetwork.Services.Lobby;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Network;
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
    static string lobbyMatch="",phase="";static float phaseEndAt,launchTry,readyTry,deckTry,deckFirst=-1f;static bool deckApplied,finalized,launched,hidingDecks;
    static TeamSide myTeam=TeamSide.Alpha;
    static PropertyInfo pGameMe;
    static int MyClientId(){try{pGameMe??=AccessTools.Property(tGame,"Me");var me=pGameMe?.GetValue(null);return me==null?-1:Traverse.Create(me).Property("Id").GetValue<int>();}catch{return -1;}}
    public static void InstallLobby(HarmonyLib.Harmony h)
    {
        h.Patch(AccessTools.Method(typeof(TeamPanelPlayerInfo),nameof(TeamPanelPlayerInfo.ToggleDeckInfo)),prefix:new HarmonyMethod(typeof(RankedMenu),nameof(DeckInfoShown)));
        h.Patch(AccessTools.Method(typeof(TeamPanelPlayerInfo),nameof(TeamPanelPlayerInfo.SetDeckInfo)),postfix:new HarmonyMethod(typeof(RankedMenu),nameof(DeckInfoSet)));
        // Lateralus 22 Nov test: launch and ready are automatic in a ranked lobby; a player who un-readied stopped the auto launch
        h.Patch(AccessTools.Method(typeof(NetworkStatusTopPanel),"OnButtonClick"),prefix:new HarmonyMethod(typeof(RankedMenu),nameof(RankedBlocks)));
        h.Patch(AccessTools.Method(typeof(TeamPanelPlayerInfo),"OnReadyButtonSelected"),prefix:new HarmonyMethod(typeof(RankedMenu),nameof(RankedBlocks)));
    
    // ArrowQueue's lobby card ("EVERYONE IS HERE · CLOSE THE SEARCH") becomes the ranked status card in a ranked lobby
        var pump=AccessTools.Method(AccessTools.TypeByName("ArrowQueue.LobbyCard"),"Pump");
        if(pump!=null)h.Patch(pump,postfix:new HarmonyMethod(typeof(RankedMenu),nameof(CardPumped)));else MelonLogger.Warning("FREEDOM_ARROW_RANKED_LOBBY no ArrowQueue LobbyCard.Pump: the banner is used");
    }
    static bool InRankedLobby=>lobbyMatch.Length>0&&phase.Length>0;
    static bool RankedBlocks(){if(!InRankedLobby)return true;MelonLogger.Msg("FREEDOM_ARROW_RANKED_LOBBY launch/ready button ignored: automatic in ranked");return false;}
    // the card's fields (ArrowQueue 0.10.31 LobbyCard): _card, _small, _big, _details, _btn
    static FieldInfo fCard,fSmall,fBig,fDetails,fBtn;static bool cardShown;
    static void CardPumped()
    {
        cardShown=false;
        if(!InRankedLobby)return;
        try
        {
            var t=AccessTools.TypeByName("ArrowQueue.LobbyCard");
            fCard??=AccessTools.Field(t,"_card");fSmall??=AccessTools.Field(t,"_small");fBig??=AccessTools.Field(t,"_big");fDetails??=AccessTools.Field(t,"_details");fBtn??=AccessTools.Field(t,"_btn");
            var card=fCard.GetValue(null) as GameObject;if(card==null||card.WasCollected||!card.activeInHierarchy)return;
            int left=Mathf.Max(0,Mathf.CeilToInt(phaseEndAt-Time.unscaledTime));
            (fSmall.GetValue(null) as Il2CppTMPro.TextMeshProUGUI)?.SetText("RANKED "+rankedFormat.ToUpperInvariant());
            (fBig.GetValue(null) as Il2CppTMPro.TextMeshProUGUI)?.SetText(phase switch{"join"=>"PLAYERS JOINING","deck"=>"PICK YOUR DECK","reveal"=>"DECKS REVEALED",_=>"LAUNCHING"});
            (fDetails.GetValue(null) as Il2CppTMPro.TextMeshProUGUI)?.SetText(phase switch{"join"=>"waiting for every player","deck"=>$"{left} s left · enemy decks are hidden","reveal"=>$"launching in {left} s",_=>"the match starts automatically"});
            var btn=fBtn.GetValue(null) as GameObject;if(btn!=null&&btn.activeSelf)btn.SetActive(false);
            cardShown=true;
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_RANKED_LOBBY card: "+e.Message);fCard=null;}
    }
    static string rankedFormat="1v1";
    // the vanilla top panel (LAUNCH / ready, "Players ready n/n") and the per-player ready toggles are hidden in a ranked lobby
    static readonly List<GameObject> hiddenUi=new();
    static void HideManual()
    {
        try
        {
            void Hide(GameObject g){if(g!=null&&g.activeSelf){g.SetActive(false);hiddenUi.Add(g);}}
            foreach(var tp in UnityEngine.Object.FindObjectsOfType<NetworkStatusTopPanel>())Hide(tp._button?.gameObject);
            foreach(var p in UnityEngine.Object.FindObjectsOfType<TeamPanelPlayerInfo>())Hide(p._readyButton?.gameObject);
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_RANKED_LOBBY hide buttons: "+e.Message);}
    }
    static void ShowManual(){foreach(var g in hiddenUi)try{if(g!=null&&!g.WasCollected)g.SetActive(true);}catch{}hiddenUi.Clear();}
    // enemy flag and spec icons (the deck's nation and specs) stay hidden with the deck until the reveal
    static readonly List<GameObject> hiddenFlags=new();
    static void HideEnemyMarks(TeamPanelPlayerInfo p)
    {
        foreach(var img in new[]{p._country,p._spec1,p._spec2})
        {var g=img?.gameObject;if(g!=null&&g.activeSelf){g.SetActive(false);hiddenFlags.Add(g);}}
    }
    static void ShowEnemyMarks(){foreach(var g in hiddenFlags)try{if(g!=null&&!g.WasCollected)g.SetActive(true);}catch{}hiddenFlags.Clear();}
    static bool Enemy(TeamPanelPlayerInfo p){try{var ci=p._clientInfo;return ci!=null&&!ci.IsBot&&(ci.TeamSide==TeamSide.Alpha||ci.TeamSide==TeamSide.Bravo)&&ci.TeamSide!=myTeam;}catch{return false;}}
    static void DeckInfoShown(TeamPanelPlayerInfo __instance,ref bool on){if(hidingDecks&&on&&Enemy(__instance))on=false;}
    static void DeckInfoSet(TeamPanelPlayerInfo __instance){if(hidingDecks&&Enemy(__instance)){__instance.ToggleDeckInfo(false);HideEnemyMarks(__instance);}}
    static void RefreshPanels(bool show)
    {
        foreach(var p in UnityEngine.Object.FindObjectsOfType<TeamPanelPlayerInfo>())
            try{if(p._clientInfo==null||p._clientInfo.IsBot)continue;if(show){p.ToggleDeckInfo(true);p.SetDeckInfo();}else if(Enemy(p)){p.ToggleDeckInfo(false);HideEnemyMarks(p);}}catch{}
        if(show)ShowEnemyMarks();
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
            if(lobbyMatch.Length>0){if(hidingDecks){hidingDecks=false;RefreshPanels(true);}ShowEnemyMarks();ShowManual();MelonLogger.Msg("FREEDOM_ARROW_RANKED_LOBBY left "+lobbyMatch);}
            lobbyMatch="";phase="";return;
        }
        var id=m.GetProperty("id").GetString()??"";
        if(id!=lobbyMatch){lobbyMatch=id;deckApplied=finalized=launched=false;launchTry=readyTry=deckTry=0;deckFirst=-1f;try{rankedFormat=m.GetProperty("format").GetString()??"1v1";}catch{}MelonLogger.Msg($"FREEDOM_ARROW_RANKED_LOBBY {id} on {m.GetProperty("map").GetString()}");}
        var ph=m.GetProperty("phase").GetString()??"";
        // Lateralus 22 Nov: the countdown went 17, 16, 17, 16 - each reply arrives with a different delay. Within a phase the end time
        // only moves earlier, so the shown seconds never go up.
        var est=now+m.GetProperty("phaseLeftMs").GetInt32()/1000f;
        if(ph!=phase){MelonLogger.Msg($"FREEDOM_ARROW_RANKED_LOBBY phase {ph}");phase=ph;phaseEndAt=est;if(ph=="launch"){resultMatch=id;resultShown="";}}   // the end screen waits for this match's result
        else phaseEndAt=Mathf.Min(phaseEndAt,est);
        HideManual();
        var lobby=LobbySvc();var st=lobby?.State;int meId=MyClientId();
        Il2CppNetworkCommon.Messages.Clients.ClientInfo ci=null;
        if(st!=null&&meId>=0)st.TryGetClientById(meId,out ci);
        if(ci!=null&&(ci.TeamSide==TeamSide.Alpha||ci.TeamSide==TeamSide.Bravo))myTeam=ci.TeamSide;
        bool hide=phase is "join" or "deck";
        if(hide!=hidingDecks){hidingDecks=hide;RefreshPanels(!hide);}
        else if(hide)RefreshPanels(false);
        try
        {
            // Default deck as soon as my own player card is in the lobby (Lateralus 22 Nov: "the selected default decks should be chosen
            // by default when the players load into the lobby"). Picked through the card's own deck dropdown, like a click, so the
            // card, the dropdown and the lobby server agree. The game may set its own last-used deck while the card initialises, so the
            // choice is checked again for the first 4 s; after that the player's own picks are left alone.
            if(phase is "join" or "deck"&&!deckApplied&&ci!=null)
            {
                var card=MyCard(meId);var d=DefaultDeck();
                if(d==null){deckApplied=true;MelonLogger.Msg("FREEDOM_ARROW_RANKED_LOBBY no valid default deck to select");}
                else if(card!=null&&card._deckList!=null&&card._deckList.Count>0&&now>=deckTry)
                {
                    if(deckFirst<0)deckFirst=now;
                    deckTry=now+1f;
                    if(SelectedName(card)!=d.Name)SelectDeck(card,d.Name,lobby,"default deck");
                    else if(now-deckFirst>=4f){deckApplied=true;MelonLogger.Msg("FREEDOM_ARROW_RANKED_LOBBY default deck selected: "+d.Name);}
                }
            }
            // End of the 60 s: no deck, an unknown one or an invalid one -> the default deck (checked on the real selection, not just "any")
            if(phase is "reveal" or "launch"&&!finalized&&ci!=null&&lobby!=null)
            {
                finalized=true;
                var card=MyCard(meId);var sel=card!=null?SelectedDeck(card):null;var d=DefaultDeck();
                string why=ci.ShortDeck==null?"no deck":sel==null?"selection unknown":!DeckValid(sel)?"invalid deck "+SelectedName(card):null;
                if(why!=null&&d!=null){SelectDeck(card,d.Name,lobby,$"{why} at the end of the deck pick: default");}
                else if(why!=null)MelonLogger.Warning("FREEDOM_ARROW_RANKED_LOBBY "+why+" and no valid default deck");
                else MelonLogger.Msg("FREEDOM_ARROW_RANKED_LOBBY deck kept: "+SelectedName(card));
            }
            // ready, and again if anything un-readied (checked every 3 s so a slow status echo is never toggled twice)
            if(phase is "reveal" or "launch"&&ci!=null&&lobby!=null&&!lobby.IsHost&&ci.Status!=ClientLobbyStatus.Ready&&now>=readyTry)
            {readyTry=now+3f;lobby.ChangeClientReadyStatus(meId);MelonLogger.Msg("FREEDOM_ARROW_RANKED_LOBBY ready");}
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
        if(lobbyMatch.Length==0||phase.Length==0||cardShown)return;
        int left=Mathf.Max(0,Mathf.CeilToInt(phaseEndAt-Time.unscaledTime));
        string text=phase switch{"join"=>"RANKED · waiting for every player to join the lobby",
            "deck"=>$"RANKED · pick your deck: {left} s · enemy decks are hidden",
            "reveal"=>$"RANKED · decks revealed · launching in {left} s",_=>"RANKED · launching"};
        float w=Screen.height*0.62f,h=Screen.height*0.045f;var r=new Rect((Screen.width-w)/2,Screen.height*0.90f,w,h);   // fallback only (no ArrowQueue card): bottom, clear of the top panel
        var o=GUI.color;GUI.color=new Color(0.06f,0.07f,0.08f,0.92f);GUI.DrawTexture(r,Texture2D.whiteTexture);
        GUI.color=phase=="deck"?Red:Green;GUI.DrawTexture(new Rect(r.x,r.yMax-3,r.width,3),Texture2D.whiteTexture);GUI.color=o;
        var s=new GUIStyle(GUI.skin.label){fontSize=Mathf.RoundToInt(h*0.42f),fontStyle=FontStyle.Bold,alignment=TextAnchor.MiddleCenter};s.normal.textColor=Color.white;
        GUI.Label(r,text,s);
    }
    static TeamPanelPlayerInfo MyCard(int meId)
    {
        if(meId<0)return null;
        foreach(var p in UnityEngine.Object.FindObjectsOfType<TeamPanelPlayerInfo>())try{if(p._clientInfo!=null&&p._clientInfo.Id==meId)return p;}catch{}
        return null;
    }
    static IDeckDataModel SelectedDeck(TeamPanelPlayerInfo card)
    {
        try{var l=card._deckList;int i=card.SelectedDeckListID;return l!=null&&i>=0&&i<l.Count?l[i]:null;}catch{return null;}
    }
    static string SelectedName(TeamPanelPlayerInfo card){try{return SelectedDeck(card)?.TryCast<DeckDataModel>()?.Name??"";}catch{return "";}}
    static bool DeckValid(IDeckDataModel d){try{var ds=DeckSvc();return ds!=null&&ds.ValidateDeck(d,out bool nonFull);}catch{return false;}}
    // select by name through the card's dropdown (as a click: card, dropdown and lobby server all follow); fallback: the lobby call
    static void SelectDeck(TeamPanelPlayerInfo card,string name,NetworkLobbyService lobby,string why)
    {
        try
        {
            var l=card?._deckList;int idx=-1;
            for(int i=0;l!=null&&i<l.Count;i++)if(l[i]?.TryCast<DeckDataModel>()?.Name==name){idx=i;break;}
            if(idx>=0&&card._decksDropdown!=null){card._decksDropdown.SetValue(idx,false);MelonLogger.Msg($"FREEDOM_ARROW_RANKED_LOBBY {why}: {name} (dropdown item {idx})");return;}
            if(idx>=0){card.OnDeckSelected(idx);MelonLogger.Msg($"FREEDOM_ARROW_RANKED_LOBBY {why}: {name} (card item {idx})");return;}
            var d=DefaultDeck();if(d!=null&&lobby!=null){lobby.ChangeClientDeck(d);MelonLogger.Msg($"FREEDOM_ARROW_RANKED_LOBBY {why}: {name} (lobby call; not in the card's list)");}
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_RANKED_LOBBY select deck: "+e.Message);}
    }
}

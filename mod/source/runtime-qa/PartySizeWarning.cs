using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.GNetwork.Services.Lobby;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Network;
using Il2CppNetworkCommon.Enums;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;
// Oversized-party warning (Osama 22 Nov 2026 00:40 PST, thread 1573561286803980289: "our game should have a big warning pop up whenever the
// players play a larger party compared to the map. for example when they play 5v5 on a 2v2 map, there should be a popup warning that covers the
// ready button and there's a button to remove the popup"). In a lobby on an [FA] [NvN] map, when a team has more than N players (humans and
// bots), a large English + 中文 panel is drawn over the top-centre Ready / Launch button (NetworkStatusTopPanel._button), and Ready and Launch
// are blocked (NetworkStatusTopPanel.OnButtonClick, NetworkLobbyService.ChangeClientReadyStatus) until the player presses Dismiss. It shows
// again if the map changes or the party grows. Other players' lobbies and maps without an [NvN] tag are not affected.
static class PartySizeWarning
{
    static readonly (string Tag,int Size)[] Sizes={("[1v1]",1),("[2v2]",2),("[3v3]",3),("[5v5]",5)};
    static bool inMenu;
    static string active,dismissed,map;
    static int mapSize,party;
    static RectTransform readyButton;
    static GUIStyle titleStyle,bodyStyle,buttonStyle;
    static bool failed;
    static bool Showing=>inMenu&&active!=null&&active!=dismissed;

    public static void Install(HarmonyLib.Harmony h)
    {
        h.Patch(AccessTools.Method(typeof(NetworkStatusTopPanel),"OnButtonClick")??throw new MissingMethodException("NetworkStatusTopPanel.OnButtonClick"),
            prefix:new HarmonyMethod(typeof(PartySizeWarning),nameof(BlockClick)));
        h.Patch(AccessTools.Method(typeof(NetworkStatusTopPanel),"OnInitialize")??throw new MissingMethodException("NetworkStatusTopPanel.OnInitialize"),
            postfix:new HarmonyMethod(typeof(PartySizeWarning),nameof(TopPanel)));
        h.Patch(AccessTools.Method(typeof(NetworkLobbyService),nameof(NetworkLobbyService.ChangeClientReadyStatus))??throw new MissingMethodException("NetworkLobbyService.ChangeClientReadyStatus"),
            prefix:new HarmonyMethod(typeof(PartySizeWarning),nameof(BlockReady)));
        MelonLogger.Msg("FREEDOM_ARROW_PARTY_SIZE installed: warning over Ready when a team is larger than the [NvN] map");
    }

    public static void SceneChanged(string scene){inMenu=scene=="Hangar_Scene";if(!inMenu)active=null;}

    static void TopPanel(NetworkStatusTopPanel __instance)
    {
        try{readyButton=__instance._button?.GetComponent<RectTransform>();}catch{readyButton=null;}
    }

    static bool BlockClick()
    {
        if(!Showing)return true;
        MelonLogger.Msg($"FREEDOM_ARROW_PARTY_SIZE Ready/Launch blocked until the warning is dismissed ({map}, {party} per team)");
        return false;
    }

    static bool BlockReady(bool __1)=>!(__1&&Showing);

    public static void Tick()
    {
        if(!inMenu||failed||Time.frameCount%15!=0)return;
        try
        {
            Il2CppBrokenArrow.Shared.Ecs.Services.Session.TryGetService<NetworkLobbyService>(out var lobby,false);
            var st=lobby?.State;
            if(lobby==null||lobby.LobbyId==0||st?.Teams==null){active=null;return;}
            map=st.ScenarioMeta?.Name??"";mapSize=0;
            foreach(var (tag,n) in Sizes)if(map.StartsWith("[FA]")&&map.Contains(tag))mapSize=n;
            if(mapSize==0){active=null;return;}
            party=0;
            foreach(var side in new[]{TeamSide.Alpha,TeamSide.Bravo})
            {
                if(!st.Teams.TryGetValue(side,out var team)||team?.Slots==null)continue;
                int n=0;
                foreach(var s in team.Slots)if(s!=null&&(s.Status==LobbySlotStatus.Occupied||s.Status==LobbySlotStatus.OccupiedByBot))n++;
                party=Math.Max(party,n);
            }
            var key=party>mapSize?$"{lobby.LobbyId}|{map}|{party}":null;
            if(key!=null&&key!=active){PickLanguage();MelonLogger.Msg($"FREEDOM_ARROW_PARTY_SIZE warning: {map} is {mapSize}v{mapSize}, a team has {party}");}
            active=key;
        }
        catch(Exception e){failed=true;active=null;MelonLogger.Error("FREEDOM_ARROW_PARTY_SIZE_FAILED: warning off. "+e.Message);}
    }

    // Osama 22 Nov 16:1x: "Can we make the warning message change based on language selection" / "So we don't have Chinese and English in the
    // same pop up": one language, from the game's own language setting (LocalizationService.CurrentLanguage, as ArrowQueue and HudQuick read it).
    // A Chinese setting (code starting "zh" or containing "chin") shows Chinese; every other language shows English. Read each time the warning
    // appears; the code is logged once per change.
    static readonly string[] En={"WARNING: TOO MANY PLAYERS FOR THIS MAP","Oversized teams cause balance issues. We encourage playing maps at their recommended size.","Dismiss and play anyway"};
    static readonly string[] Zh={"警告：玩家人数超过地图设计","超出人数会导致平衡问题。我们鼓励按地图推荐人数进行游戏。","关闭并继续"};
    static string lang="";static string[] text=En;
    static void PickLanguage()
    {
        string code="";
        try
        {
            Il2CppBrokenArrow.Shared.Ecs.Services.Session.TryGetService<Il2CppBrokenArrow.Shared.Ecs.Localization.LocalizationService>(out var loc,false);
            code=loc?.CurrentLanguage??"";
        }
        catch{code="";}
        if(code==lang)return;
        lang=code;var c=code.Trim().ToLowerInvariant();
        text=c.StartsWith("zh")||c.Contains("chin")?Zh:En;
        titleStyle=null;   // the title size is fitted to this language's title
        MelonLogger.Msg($"FREEDOM_ARROW_PARTY_SIZE language '{code}': {(text==Zh?"Chinese":"English")}");
    }
    // Osama 22 Nov 15:3x: "make the warning a little bit smaller it takes up a massive portion of the screen": about two thirds of the
    // approved size (860 px wide, body 24 px, title 34 px, button 560x46 at 1080p); wording and colours unchanged.
    // Seen in game 22 Nov 15:22 (1920x1080): the 53 px English title wrapped to two lines, so the title block overflowed the fixed 128 px row and
    // its top was cut off at the screen edge. The panel is now sized to its text: the English title shrinks (not below the body size) until it
    // fits one line, and every row's height is measured (GUIStyle.CalcHeight) before the panel is placed.
    public static void OnGUI()
    {
        if(!Showing)return;
        float k=Screen.height/1080f;
        float w=Mathf.Min(860*k,Screen.width-20),pad=16*k;
        int fs=Mathf.Max(12,Mathf.RoundToInt(24*k));
        if(titleStyle==null||bodyStyle.fontSize!=fs)
        {
            titleStyle=new GUIStyle(GUI.skin.label){normal={textColor=Color.white},fontSize=Mathf.RoundToInt(fs*1.4f),fontStyle=FontStyle.Bold,alignment=TextAnchor.MiddleCenter,wordWrap=false};
            bodyStyle=new GUIStyle(GUI.skin.label){normal={textColor=Color.white},fontSize=fs,alignment=TextAnchor.UpperCenter,wordWrap=true};
            buttonStyle=new GUIStyle(GUI.skin.button){fontSize=Mathf.RoundToInt(fs*1.1f),fontStyle=FontStyle.Bold};
            var en=new GUIContent(text[0]);
            while(titleStyle.fontSize>fs&&titleStyle.CalcSize(en).x>w-2*pad)titleStyle.fontSize--;
        }
        float tw=w-2*pad,hEn=titleStyle.CalcHeight(new GUIContent(text[0]),tw),
            hBody=bodyStyle.CalcHeight(new GUIContent(text[1]),tw),hBtn=46*k;
        float h=pad+hEn+8*k+hBody+12*k+hBtn+pad;
        float cx=Screen.width/2f,top=30*k;
        try
        {
            if(readyButton!=null&&readyButton.gameObject.activeInHierarchy)
            {
                var p=readyButton.position;   // screen-space overlay canvas: position is in screen pixels
                cx=p.x;top=Screen.height-p.y-60*k;
            }
        }
        catch{readyButton=null;}
        var r=new Rect(Mathf.Clamp(cx-w/2,10,Screen.width-w-10),Mathf.Clamp(top,8*k,Mathf.Max(8*k,Screen.height-h-8*k)),w,h);
        var old=GUI.color;
        // Large red panel (Osama 22 Nov 00:52): bright red border, solid red body, white text.
        GUI.color=new Color(1f,0.42f,0.42f,1f);GUI.DrawTexture(new Rect(r.x-5,r.y-5,r.width+10,r.height+10),Texture2D.whiteTexture);
        GUI.color=new Color(0.70f,0.06f,0.08f,0.98f);GUI.DrawTexture(r,Texture2D.whiteTexture);
        GUI.color=old;
        float y=r.y+pad;
        GUI.Label(new Rect(r.x+pad,y,tw,hEn),text[0],titleStyle);y+=hEn+8*k;
        GUI.Label(new Rect(r.x+pad,y,tw,hBody),text[1],bodyStyle);y+=hBody+12*k;
        if(GUI.Button(new Rect(r.x+r.width/2-280*k,y,560*k,hBtn),text[2],buttonStyle))
        {
            dismissed=active;
            MelonLogger.Msg($"FREEDOM_ARROW_PARTY_SIZE dismissed ({map}, {party} per team)");
        }
    }
}

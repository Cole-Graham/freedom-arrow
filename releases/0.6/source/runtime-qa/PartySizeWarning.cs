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
            if(key!=null&&key!=active)MelonLogger.Msg($"FREEDOM_ARROW_PARTY_SIZE warning: {map} is {mapSize}v{mapSize}, a team has {party}");
            active=key;
        }
        catch(Exception e){failed=true;active=null;MelonLogger.Error("FREEDOM_ARROW_PARTY_SIZE_FAILED: warning off. "+e.Message);}
    }

    static int Recommended()
    {
        foreach(var (_,n) in Sizes)if(n>=party)return n;
        return Sizes[^1].Size;
    }

    public static void OnGUI()
    {
        if(!Showing)return;
        float k=Screen.height/1080f;
        float w=Mathf.Min(980*k,Screen.width-20),h=420*k;
        float cx=Screen.width/2f,top=30*k;
        try
        {
            if(readyButton!=null&&readyButton.gameObject.activeInHierarchy)
            {
                var p=readyButton.position;   // screen-space overlay canvas: position is in screen pixels
                cx=p.x;top=Screen.height-p.y-90*k;
            }
        }
        catch{readyButton=null;}
        var r=new Rect(Mathf.Clamp(cx-w/2,10,Screen.width-w-10),Mathf.Clamp(top,0,Screen.height-h),w,h);
        int fs=Mathf.Max(12,Mathf.RoundToInt(22*k));
        if(titleStyle==null||bodyStyle.fontSize!=fs)
        {
            titleStyle=new GUIStyle(GUI.skin.label){fontSize=Mathf.RoundToInt(fs*1.45f),fontStyle=FontStyle.Bold,alignment=TextAnchor.MiddleCenter,wordWrap=true};
            bodyStyle=new GUIStyle(GUI.skin.label){fontSize=fs,alignment=TextAnchor.UpperCenter,wordWrap=true};
            buttonStyle=new GUIStyle(GUI.skin.button){fontSize=Mathf.RoundToInt(fs*1.1f),fontStyle=FontStyle.Bold};
        }
        var old=GUI.color;
        GUI.color=new Color(0.89f,0.21f,0.24f,1f);GUI.DrawTexture(new Rect(r.x-4,r.y-4,r.width+8,r.height+8),Texture2D.whiteTexture);
        GUI.color=new Color(0.05f,0.05f,0.06f,0.97f);GUI.DrawTexture(r,Texture2D.whiteTexture);
        GUI.color=old;
        int rec=Recommended();
        GUI.Label(new Rect(r.x+20,r.y+12*k,r.width-40,60*k),"WARNING: TOO MANY PLAYERS FOR THIS MAP\n警告：玩家人数超过地图设计",titleStyle);
        GUI.Label(new Rect(r.x+30,r.y+95*k,r.width-60,230*k),
            $"This is a {mapSize}v{mapSize} map, but a team has {party} players. Playing with more players than a map is made for causes balance problems: crowded front lines, too many units for the space and scoring tuned for {mapSize}v{mapSize}. Pick a {rec}v{rec} map, or dismiss this warning to play anyway.\n\n"+
            $"这是一张 {mapSize}v{mapSize} 地图，但有一方有 {party} 名玩家。玩家人数超过地图设计会导致平衡问题：前线拥挤、单位过多、计分按 {mapSize}v{mapSize} 设计。请选择 {rec}v{rec} 地图，或关闭此警告后继续。",bodyStyle);
        if(GUI.Button(new Rect(r.x+r.width/2-230*k,r.y+r.height-70*k,460*k,52*k),"Dismiss and play anyway / 关闭并继续",buttonStyle))
        {
            dismissed=active;
            MelonLogger.Msg($"FREEDOM_ARROW_PARTY_SIZE dismissed ({map}, {party} per team)");
        }
    }
}

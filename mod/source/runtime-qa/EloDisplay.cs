using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.BattleEnd;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Network.TeamPanel;
using Il2CppNetworkCommon.Enums;
using Il2CppNetworkCommon.Messages.Clients;
using Il2CppTMPro;
using MelonLoader;
using System.Globalization;
using System.Reflection;
using System.Text;
using System.Text.Json;
using UnityEngine;
namespace FreedomArrow;
// Vanilla, FA 1v1 and FA Team Elo everywhere (Lateralus 22 Nov 2026 16:56: "change player cards in all menus to show seperate vanilla BA and
// the FA mod ELO ... For the mod lobbies and anywhere else that average elo is calculated, I would also want seperate avg ELOs"; mock-up v2
// 17:36; 27 Nov 2026: "I want vanilla, FA 1v1, and FA Team average and individual elo's displayed in all lobby and match result screens,
// for both ranked and regular mod lobbies").
// - Ratings: the FA 1v1 and Team leaderboards from the FA lobby server (GetRankedLeaderboard, all rated players), asked every 60 s while in a
//   lobby or on the end screen. A player with no FA rating shows "–". Vanilla Elo is ArrowQueue's Game.RatingOfClient.
// - Lobby player card: "FA 1523 | 1702" (FA 1v1 | FA Team) on the name line, right of the name, shrunk to fit before the country flag.
// - Team header: ArrowQueue's "avg Elo 2140" label (TeamElo) gets a second line "FA avg 1v1 1391 · Team 1488" (averages of the rated players).
// - End screen (ranked and mod games): a block over the empty medals/objectives area, per team the three averages and per player the three
//   ratings; in a ranked match the ladder played shows before → after and the change (RankedResult.cs).
static partial class RankedMenu
{
    sealed class Seat{public string Name="",Steam="";public TeamSide Side;public double Ba;}
    static readonly Dictionary<string,double> fa1=new(),faT=new();
    static string parsed1="",parsedT="";
    static float nextEloBoards=-100f,nextEloPump;
    static MethodInfo mLobbyClients,mSteamOfClient,mRatingOfClient;static FieldInfo fTeamEloLabels;
    static List<Seat> roster=new();static bool eloBroken,rosterPlayed;static float menuSince=-1f;
    static readonly Dictionary<IntPtr,TextMeshProUGUI> cardLabels=new();
    static readonly Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppStructArray<Vector3> corners=new(4L);

    static void EloInstall(HarmonyLib.Harmony h)
    {
        mLobbyClients=AccessTools.Method(tGame,"LobbyClients");mSteamOfClient=AccessTools.Method(tGame,"SteamIdOfClient");mRatingOfClient=AccessTools.Method(tGame,"RatingOfClient");
        var teamElo=AccessTools.TypeByName("ArrowQueue.TeamElo");var pump=teamElo==null?null:AccessTools.Method(teamElo,"Pump");fTeamEloLabels=teamElo==null?null:AccessTools.Field(teamElo,"_labels");
        if(pump!=null&&fTeamEloLabels!=null)h.Patch(pump,postfix:new HarmonyMethod(typeof(RankedMenu),nameof(AfterTeamElo)));
        MelonLogger.Msg($"FREEDOM_ARROW_ELO installed: lobby clients {mLobbyClients!=null}, steam ids {mSteamOfClient!=null}, vanilla Elo {mRatingOfClient!=null}, team averages {pump!=null&&fTeamEloLabels!=null}");
    }
    static string Steam(ClientInfo c){try{var id=(ulong)mSteamOfClient.Invoke(null,new object[]{c.Id});return id==0?"":id.ToString(CultureInfo.InvariantCulture);}catch{return "";}}
    static double Ba(ClientInfo c){try{return (float)mRatingOfClient.Invoke(null,new object[]{c.Id});}catch{return 0;}}
    static double? Fa(Dictionary<string,double> d,string steam)=>steam.Length>0&&d.TryGetValue(steam,out var r)?r:null;
    static string R(double? v)=>v is double d&&d>0?d.ToString("0",CultureInfo.InvariantCulture):"–";
    static double? Avg(IEnumerable<double?> v){var l=v.Where(x=>x is double d&&d>0).Select(x=>x!.Value).ToList();return l.Count==0?null:l.Average();}

    static void ParseBoards()
    {
        void One(string json,ref string last,Dictionary<string,double> d)
        {
            if(json.Length==0||json==last)return;last=json;d.Clear();
            try{foreach(var r in JsonDocument.Parse(json).RootElement.GetProperty("rows").EnumerateArray())d[r.GetProperty("steamId").GetString()??""]=r.GetProperty("rating").GetDouble();}
            catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_ELO leaderboard: "+e.Message);}
        }
        One(board1,ref parsed1,fa1);One(boardT,ref parsedT,faT);
    }

    // every frame from Tick: in a lobby the roster, cards and boards; on the end screen the boards for the result block
    static void EloTick(float now)
    {
        if(eloBroken||mLobbyClients==null)return;
        bool inLobby=false;try{inLobby=pInLobby.GetValue(null) is true;}catch{}
        bool endUp=false;try{endUp=BattleEndScreen.Active;}catch{}
        if(!inLobby&&!endUp)
        {
            cardLabels.Clear();
            // back in the menus without a lobby for 5 s: the last roster belongs to no coming match (a Skirmish end screen shows no block)
            bool hangar=UnityEngine.SceneManagement.SceneManager.GetActiveScene().name=="Hangar_Scene";
            if(!hangar)menuSince=-1f;else if(menuSince<0)menuSince=now;else if(now-menuSince>5f&&roster.Count>0&&!rosterPlayed)roster=new();
            return;
        }
        menuSince=-1f;if(inLobby)rosterPlayed=false;
        if(now>=nextEloBoards){nextEloBoards=now+60f;AskBoards();}
        ParseBoards();
        if(!inLobby||now<nextEloPump)return;
        nextEloPump=now+1f;
        try
        {
            var seats=new List<Seat>();
            if(mLobbyClients.Invoke(null,null) is System.Collections.IEnumerable list)
                foreach(var o in list)
                    if(o is ClientInfo c&&!c.IsBot&&(c.TeamSide==TeamSide.Alpha||c.TeamSide==TeamSide.Bravo))
                        seats.Add(new Seat{Name=c.Name??"",Steam=Steam(c),Side=c.TeamSide,Ba=Ba(c)});
            if(seats.Count>0)roster=seats;   // the last lobby's players, for that match's end screen
            foreach(var p in UnityEngine.Object.FindObjectsOfType<TeamPanelPlayerInfo>())Card(p);
        }
        catch(Exception e){eloBroken=true;MelonLogger.Error("FREEDOM_ARROW_ELO_FAILED: no FA Elo in lobbies from now on. "+e.Message);}
    }

    static void Card(TeamPanelPlayerInfo p)
    {
        var ci=p._clientInfo;var name=p._playerName;
        if(ci==null||ci.IsBot||name==null||!name.gameObject.activeInHierarchy)return;
        var steam=Steam(ci);
        var text=$"<color=#E8574B>FA</color> {R(Fa(fa1,steam))} | {R(Fa(faT,steam))}";   // FA 1v1 | FA Team
        if(!cardLabels.TryGetValue(p.Pointer,out var l)||l==null||l.WasCollected)
        {
            var parent=name.transform.parent;
            for(int i=parent.childCount-1;i>=0;i--)if(parent.GetChild(i).name=="FA_CardElo")UnityEngine.Object.Destroy(parent.GetChild(i).gameObject);
            var go=new GameObject("FA_CardElo");var rt=go.AddComponent<RectTransform>();rt.SetParent(parent,false);
            go.AddComponent<UnityEngine.UI.LayoutElement>().ignoreLayout=true;
            l=go.AddComponent<TextMeshProUGUI>();l.font=name.font;l.color=Color.white;l.richText=true;l.raycastTarget=false;
            l.enableAutoSizing=true;l.fontSizeMax=name.fontSize*0.8f;l.fontSizeMin=8f;
            l.alignment=TextAlignmentOptions.MidlineLeft;l.enableWordWrapping=false;l.overflowMode=TextOverflowModes.Ellipsis;
            var prt=parent.GetComponent<RectTransform>();var a=prt!=null?prt.pivot:new Vector2(0.5f,0.5f);rt.anchorMin=rt.anchorMax=a;rt.pivot=new Vector2(0f,0.5f);
            cardLabels[p.Pointer]=l;
        }
        if(l.text!=text)l.SetText(text);
        // on the name line, right of the name, up to the country flag (the line under it has no room: Elo, flag and spec icons)
        var parentT=l.transform.parent;float start=Right(name,parentT,out var mid)+12f,end=start+170f;
        var flag=p._country;
        if(flag!=null&&flag.gameObject.activeInHierarchy){flag.rectTransform.GetWorldCorners(corners);var fl=parentT.InverseTransformPoint(corners[0]).x;if(fl>start)end=fl-6f;}
        var want=new Vector2(start,mid);if((l.rectTransform.anchoredPosition-want).sqrMagnitude>0.25f)l.rectTransform.anchoredPosition=want;
        var size=new Vector2(Mathf.Max(30f,end-start),name.rectTransform.rect.height);if((l.rectTransform.sizeDelta-size).sqrMagnitude>0.25f)l.rectTransform.sizeDelta=size;
    }
    static float Right(TextMeshProUGUI t,Transform parent,out float mid)
    {
        var b=t.textBounds;var rt=t.rectTransform;Vector3 v=parent.InverseTransformPoint(rt.TransformPoint(new Vector3(b.max.x,b.center.y,0f)));
        if(b.size.x<0.5f){rt.GetWorldCorners(corners);v=parent.InverseTransformPoint((corners[2]+corners[3])*0.5f);}
        mid=v.y;return v.x;
    }

    // ArrowQueue writes "avg Elo N" next to each team title once a second; the FA averages are added after it every call
    static void AfterTeamElo()
    {
        if(eloBroken||roster.Count==0)return;
        try
        {
            if(fTeamEloLabels.GetValue(null) is not System.Collections.IDictionary labels||labels.Count==0)return;
            var side=new Dictionary<IntPtr,TeamSide>();
            foreach(var ti in UnityEngine.Object.FindObjectsOfType<TeamIdentifier>())if(ti!=null&&!ti.WasCollected)side[ti.Pointer]=ti.TeamSide;
            foreach(System.Collections.DictionaryEntry e in labels)
            {
                if(e.Value is not TextMeshProUGUI l||l.WasCollected||!l.gameObject.activeSelf||!side.TryGetValue((IntPtr)e.Key,out var s))continue;
                var team=roster.Where(x=>x.Side==s).ToList();
                // a second, smaller line under ArrowQueue's "avg Elo N": one line would run into the other team's header
                var add=$"\n<size=85%><color=#E8574B>FA</color> avg 1v1 {R(Avg(team.Select(x=>Fa(fa1,x.Steam))))} · Team {R(Avg(team.Select(x=>Fa(faT,x.Steam))))}</size>";
                var t=l.text??"";if(t.EndsWith(add))continue;
                var cut=t.IndexOf("\n<size=85%><color=#E8574B>FA",StringComparison.Ordinal);if(cut>=0)t=t.Substring(0,cut);
                l.SetText(t+add);
                var sz=l.rectTransform.sizeDelta;l.rectTransform.sizeDelta=new Vector2(l.GetPreferredValues(l.text).x+4f,sz.y);
            }
        }
        catch(Exception x){eloBroken=true;MelonLogger.Error("FREEDOM_ARROW_ELO_FAILED: no FA team averages from now on. "+x.Message);}
    }

    // the end screen block: per team the three averages, per player the three ratings; ranked: the ladder played shows before → after
    static string EloBlock(string title,Dictionary<string,(double before,double after,double change)> result,string ladder)
    {
        if(roster.Count==0&&result.Count==0)return null;
        var me=MySteam();var sb=new StringBuilder(title);
        foreach(var s in new[]{TeamSide.Alpha,TeamSide.Bravo})
        {
            var team=roster.Where(x=>x.Side==s).ToList();if(team.Count==0)continue;
            sb.Append($"\n<b>{(s==TeamSide.Alpha?"TEAM A":"TEAM B")}</b>   avg  BA {R(Avg(team.Select(x=>(double?)x.Ba)))}  ·  FA 1v1 {R(Avg(team.Select(x=>Fa(fa1,x.Steam))))}  ·  FA Team {R(Avg(team.Select(x=>Fa(faT,x.Steam))))}");
            foreach(var p in team)
            {
                string one(string lad,Dictionary<string,double> d)
                {
                    if(ladder==lad&&result.TryGetValue(p.Steam,out var r))
                    {
                        string col=r.change>0.05?"#7CFF81":r.change<-0.05?"#FF6A5E":"#BBBBBB";
                        return $"{r.before:0} → {r.after:0} <color={col}>{(r.change>0?"+":r.change<0?"−":"±")}{Math.Abs(r.change):0.0}</color>";
                    }
                    return R(Fa(d,p.Steam));
                }
                bool mine=p.Steam.Length>0&&p.Steam==me;
                sb.Append($"\n{(mine?"<b>":"")}{p.Name}{(mine?"</b>":"")}    BA {R(p.Ba)}  ·  1v1 {one("1v1",fa1)}  ·  Team {one("team",faT)}");
            }
        }
        return sb.ToString();
    }
}

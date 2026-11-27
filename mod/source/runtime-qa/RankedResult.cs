using Il2CppBrokenArrow.Client.Ecs.UI.Menu.BattleEnd;
using Il2CppTMPro;
using MelonLoader;
using System.Text;
using System.Text.Json;
using UnityEngine;
namespace FreedomArrow;
// Elo change on the end screen (Lateralus 22 Nov: "end of match screens don't show any ELO gain or Loss for each player"). After a
// ranked match the hub keeps every player's before/after/change (GetRanked extra.lastResult). While the game's BattleEndScreen is up,
// the result is asked for every 2 s and written under the game's result title, one line per player.
static partial class RankedMenu
{
    static string resultMatch="",resultShown="";static float nextResultAsk,resultWaitFrom=-1f;static GameObject resultGo;
    static void ResultTick(float now)
    {
        bool endUp=false;try{endUp=BattleEndScreen.Active;}catch{}
        if(!endUp){if(resultGo!=null){try{UnityEngine.Object.Destroy(resultGo);}catch{}resultGo=null;if(roster.Count>0)rosterPlayed=true;if(resultMatch.Length>0&&resultShown==resultMatch)resultMatch="";}resultWaitFrom=-1f;return;}
        if(resultMatch.Length==0)
        {
            // a mod lobby game (not ranked): the lobby's players with BA, FA 1v1 and FA Team Elo (EloDisplay.cs), redrawn every 2 s as the boards arrive
            if(roster.Count==0||rosterPlayed||now<nextResultAsk)return;nextResultAsk=now+2f;
            var block=EloBlock("<b>MOD GAME</b>  ·  Elo",new(),"");if(block!=null)Draw(block);
            return;
        }
        if(resultShown==resultMatch)return;
        if(resultWaitFrom<0)resultWaitFrom=now;
        if(now>=nextResultAsk){nextResultAsk=now+2f;Ask();}
        string text=null;
        try
        {
            if(meJson.Length>0)
            {
                var r=JsonDocument.Parse(meJson).RootElement;
                if(r.TryGetProperty("extra",out var x)&&x.TryGetProperty("lastResult",out var lr)&&lr.ValueKind==JsonValueKind.Object&&lr.GetProperty("matchId").GetString()==resultMatch)
                    text=ResultText(lr);
            }
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_RANKED result: "+e.Message);}
        if(text==null)text=now-resultWaitFrom<120?"<b>RANKED</b>  ·  waiting for both teams' results…":"<b>RANKED</b>  ·  result not received yet: see Recent matches in the ranked menu";
        else{resultShown=resultMatch;MelonLogger.Msg("FREEDOM_ARROW_RANKED result shown on the end screen: "+resultMatch);}
        Draw(text);
    }
    static string ResultText(JsonElement lr)
    {
        var sb=new StringBuilder();var outcome=lr.GetProperty("outcome").GetString();var format=lr.GetProperty("format").GetString()??"";
        sb.Append($"<b>RANKED {format.ToUpperInvariant()}</b>  ·  {lr.GetProperty("map").GetString()}");
        if(outcome!="rated")
        {
            string why="";try{why=lr.GetProperty("detail").GetProperty("reason").GetString()??"";}catch{}
            sb.Append(why=="draw"?"  ·  draw: no rating change":$"  ·  not rated ({(why.Length>0?why:outcome)})");
        }
        // 27 Nov 2026 (Lateralus): BA, FA 1v1 and FA Team for every player and team, the ladder played as before → after (EloDisplay.cs)
        var res=new Dictionary<string,(double,double,double)>();
        foreach(var p in lr.GetProperty("players").EnumerateArray())
            res[p.GetProperty("steamId").GetString()??""]=(p.GetProperty("before").GetDouble(),p.GetProperty("after").GetDouble(),outcome=="rated"?p.GetProperty("change").GetDouble():0);
        if(roster.Count>0&&EloBlock(sb.ToString(),res,format=="1v1"?"1v1":"team") is {} block)return block;
        var me=MySteam();
        foreach(var p in lr.GetProperty("players").EnumerateArray())
        {
            double b=p.GetProperty("before").GetDouble(),a=p.GetProperty("after").GetDouble(),c=p.GetProperty("change").GetDouble();
            string col=c>0.05?"#7CFF81":c<-0.05?"#FF6A5E":"#BBBBBB";string name=p.GetProperty("name").GetString()??"";
            bool mine=p.GetProperty("steamId").GetString()==me;
            sb.Append($"\n{(mine?"<b>":"")}{name}{(mine?"</b>":"")}   {b:0} → {a:0}   <color={col}>{(c>0?"+":c<0?"−":"±")}{Math.Abs(c):0.0}</color>");
        }
        return sb.ToString();
    }
    static void Draw(string text)
    {
        try
        {
            if(resultGo==null||resultGo.WasCollected)
            {
                var scr=UnityEngine.Object.FindObjectOfType<BattleEndScreen>();var extra=scr?._battleResultTextExtra;
                if(extra==null)return;
                resultGo=new GameObject("FA_RankedResult");var rt=resultGo.AddComponent<RectTransform>();
                // 27 Nov 2026: below the Objectives row, over the empty medals / objectives placeholders (under the map name it ran into the
                // Level progression column; a 4v4 block has up to 13 lines). Falls back to under the result text without a full-screen root.
                if(scr.GetComponent<RectTransform>() is RectTransform root)
                {rt.SetParent(root,false);rt.anchorMin=rt.anchorMax=new Vector2(0.5f,0.47f);rt.pivot=new Vector2(0.5f,1f);rt.sizeDelta=new Vector2(1300,440);rt.anchoredPosition=Vector2.zero;}
                else
                {
                    rt.SetParent(extra.transform.parent,false);var ert=extra.rectTransform;rt.anchorMin=ert.anchorMin;rt.anchorMax=ert.anchorMax;rt.pivot=new Vector2(0.5f,1f);
                    rt.sizeDelta=new Vector2(Mathf.Max(ert.rect.width,900),220);rt.anchoredPosition=ert.anchoredPosition+new Vector2(0,-ert.rect.height*(1-ert.pivot.y)-12);
                }
                var t=resultGo.AddComponent<TextMeshProUGUI>();t.font=extra.font;t.fontSize=Mathf.Max(16,extra.fontSize*0.5f);t.richText=true;t.raycastTarget=false;
                t.alignment=TextAlignmentOptions.Top;t.color=Color.white;t.enableWordWrapping=false;t.overflowMode=TextOverflowModes.Overflow;
                MelonLogger.Msg("FREEDOM_ARROW_RANKED result panel placed under the end screen's result text");
            }
            var tmp=resultGo.GetComponent<TextMeshProUGUI>();if(tmp!=null&&tmp.text!=text)tmp.SetText(text);
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_RANKED result panel: "+e.Message);}
    }
}

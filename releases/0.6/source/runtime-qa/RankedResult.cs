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
        if(!endUp){if(resultGo!=null){try{UnityEngine.Object.Destroy(resultGo);}catch{}resultGo=null;}resultWaitFrom=-1f;return;}
        if(resultMatch.Length==0||resultShown==resultMatch)return;
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
        var sb=new StringBuilder();var outcome=lr.GetProperty("outcome").GetString();
        sb.Append($"<b>RANKED {lr.GetProperty("format").GetString()?.ToUpperInvariant()}</b>  ·  {lr.GetProperty("map").GetString()}");
        if(outcome!="rated")
        {
            string why="";try{why=lr.GetProperty("detail").GetProperty("reason").GetString()??"";}catch{}
            sb.Append(why=="draw"?"  ·  draw: no rating change":$"  ·  not rated ({(why.Length>0?why:outcome)})");
        }
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
                resultGo=new GameObject("FA_RankedResult");var rt=resultGo.AddComponent<RectTransform>();rt.SetParent(extra.transform.parent,false);
                var ert=extra.rectTransform;rt.anchorMin=ert.anchorMin;rt.anchorMax=ert.anchorMax;rt.pivot=new Vector2(0.5f,1f);
                rt.sizeDelta=new Vector2(Mathf.Max(ert.rect.width,900),220);rt.anchoredPosition=ert.anchoredPosition+new Vector2(0,-ert.rect.height*(1-ert.pivot.y)-12);
                var t=resultGo.AddComponent<TextMeshProUGUI>();t.font=extra.font;t.fontSize=Mathf.Max(18,extra.fontSize*0.62f);t.richText=true;t.raycastTarget=false;
                t.alignment=TextAlignmentOptions.Top;t.color=Color.white;t.enableWordWrapping=false;t.overflowMode=TextOverflowModes.Overflow;
                MelonLogger.Msg("FREEDOM_ARROW_RANKED result panel placed under the end screen's result text");
            }
            var tmp=resultGo.GetComponent<TextMeshProUGUI>();if(tmp!=null&&tmp.text!=text)tmp.SetText(text);
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_RANKED result panel: "+e.Message);}
    }
}

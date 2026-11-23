using HarmonyLib;
using MelonLoader;
using System.Reflection;
using UnityEngine;
using UnityEngine.UI;
namespace FreedomArrow;
// Play tab layout (Lateralus 22 Nov 2026, picked from the previews): Campaign and Scenarios hidden; the row (Multiplayer, Skirmish and
// our Ranked card) centred; Multiplayer art = PLA flag raising (FA_CN_LOADING_33), Skirmish art = Russian assault troops
// (FA_RU_LOADING_09), both baked 600x1200 with the cards' top fade (UserData/FreedomArrow/ranked/menu/). ArrowQueue's 'Mod game'
// header tab is hidden outside lobbies (the Multiplayer card opens the same page); ArrowQueue still shows it in a lobby.
static partial class RankedMenu
{
    static float nextPlayLayout;static Sprite artMp,artSk;static bool artLoaded,loggedLayout;
    static RectTransform rowContent;static Vector2 rowAnchorMin,rowAnchorMax,rowPivot,rowPos;static bool rowSaved;
    static Sprite ArtSprite(string file)
    {
        var t=Load(Path.Combine(dir,"menu",file),"FA_play_"+file);if(t==null){MelonLogger.Warning("FREEDOM_ARROW_PLAY_TAB missing "+file);return null;}
        var s=Sprite.Create(t,new Rect(0,0,t.width,t.height),new Vector2(0.5f,0.5f));s.hideFlags=HideFlags.DontUnloadUnusedAsset;return s;
    }
    static void PlayLayoutTick(float now)
    {
        if(now<nextPlayLayout)return;nextPlayLayout=now+0.5f;
        try
        {
            if(play==null||play.WasCollected||!play.isActiveAndEnabled)return;
            var c=play._buttonsContainer;if(c==null)return;
            Transform mp=null,sk=null,camp=null,scen=null;
            foreach(var t in c.GetComponentsInChildren<Transform>(true))
            {
                var n=t.name;
                if(n=="Menu Picture Button - Multiplayer")mp=t;else if(n=="Menu Picture Button - Skirmish")sk=t;
                else if(n=="Menu Picture Button - Campaign")camp=t;else if(n=="Menu Picture Button - Scenarios")scen=t;
            }
            if(mp==null||sk==null)return;
            if(camp!=null&&camp.gameObject.activeSelf)camp.gameObject.SetActive(false);
            if(scen!=null&&scen.gameObject.activeSelf)scen.gameObject.SetActive(false);
            if(!artLoaded){artLoaded=true;artMp=ArtSprite("multiplayer.png");artSk=ArtSprite("skirmish.png");}
            SetArt(mp,artMp);SetArt(sk,artSk);
            // centre the row: Multiplayer, Skirmish and the Ranked card drawn one card pitch right of Skirmish
            var content=mp.parent.GetComponent<RectTransform>();var hlg=content.GetComponent<HorizontalLayoutGroup>();
            float pitch=mp.GetComponent<RectTransform>().rect.width+(hlg!=null?hlg.spacing:0);
            if(rowContent==null||rowContent.WasCollected||rowContent.Pointer!=content.Pointer){rowContent=content;rowAnchorMin=content.anchorMin;rowAnchorMax=content.anchorMax;rowPivot=content.pivot;rowPos=content.anchoredPosition;rowSaved=true;}
            var want=new Vector2(-pitch/2f,content.anchoredPosition.y);
            if(content.anchorMin.x!=0.5f||content.anchorMax.x!=0.5f||content.pivot.x!=0.5f||Mathf.Abs(content.anchoredPosition.x-want.x)>0.5f)
            {
                content.anchorMin=new Vector2(0.5f,content.anchorMin.y);content.anchorMax=new Vector2(0.5f,content.anchorMax.y);content.pivot=new Vector2(0.5f,content.pivot.y);content.anchoredPosition=want;
                if(!loggedLayout){loggedLayout=true;MelonLogger.Msg($"FREEDOM_ARROW_PLAY_TAB Campaign/Scenarios hidden, row centred (pitch {pitch:0}, was anchors {rowAnchorMin}-{rowAnchorMax} pivot {rowPivot} pos {rowPos}), art {(artMp!=null?"MP ok":"MP missing")} {(artSk!=null?"Skirmish ok":"Skirmish missing")}");}
            }
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_PLAY_TAB: "+e.Message);nextPlayLayout=now+10f;}
    }
    static void SetArt(Transform card,Sprite s)
    {
        if(s==null)return;
        var img=card.Find("image")?.GetComponent<Image>();
        if(img!=null&&(img.sprite==null||img.sprite.Pointer!=s.Pointer)){img.sprite=s;img.preserveAspect=false;}
    }
    // ArrowQueue's 'Mod game' header tab: skip its layout and keep it hidden while not in a lobby (its own Layout re-shows it)
    static FieldInfo fModTab;static MethodInfo mRestoreLine;
    public static void InstallPlayTab(HarmonyLib.Harmony h)
    {
        var t=AccessTools.TypeByName("ArrowQueue.ModTab");var lay=t==null?null:AccessTools.Method(t,"Layout");
        if(lay==null){MelonLogger.Warning("FREEDOM_ARROW_PLAY_TAB no ArrowQueue ModTab.Layout: the Mod game tab stays");return;}
        fModTab=AccessTools.Field(t,"_tab");mRestoreLine=AccessTools.Method(t,"RestoreLine");
        h.Patch(lay,prefix:new HarmonyMethod(typeof(RankedMenu),nameof(ModTabLayout)));
    }
    static bool loggedModTab;
    static bool ModTabLayout()
    {
        try
        {
            if(pInLobby?.GetValue(null) is true)return true;
            var tab=fModTab?.GetValue(null) as GameObject;
            if(tab!=null&&!tab.WasCollected&&tab.activeSelf){tab.SetActive(false);mRestoreLine?.Invoke(null,null);if(!loggedModTab){loggedModTab=true;MelonLogger.Msg("FREEDOM_ARROW_PLAY_TAB ArrowQueue 'Mod game' tab hidden (Multiplayer opens the same page)");}}
            return false;
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_PLAY_TAB mod tab: "+e.Message);return true;}
    }
}

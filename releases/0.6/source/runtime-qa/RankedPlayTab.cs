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
    static RectTransform rowContent;static int rowPad;static Transform fadeCard;
    // left edge and width of a card in its row's parent space (world corners: the hover grow may scale the card instead of resizing it)
    static (float left,float width) InParent(RectTransform r,RectTransform parent)
    {
        var c=new Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppStructArray<Vector3>(4);r.GetWorldCorners(c);
        float l=parent.InverseTransformPoint(c[0]).x,rr=parent.InverseTransformPoint(c[3]).x;
        return (l-parent.rect.xMin,rr-l);
    }
    // The vanilla cards fade in through their CanvasGroups (GalaxyUiBase); the Ranked card (drawn with IMGUI) copies Skirmish's
    // effective alpha (Lateralus 22 Nov 2026: Ranked appeared at once while Multiplayer and Skirmish faded in).
    public static float CardAlpha()
    {
        try
        {
            if(fadeCard==null||fadeCard.WasCollected)return 1f;
            float a=1f;var t=fadeCard;
            while(t!=null){var g=t.GetComponent<CanvasGroup>();if(g!=null){a*=g.alpha;if(g.ignoreParentGroups)break;}t=t.parent;}
            return Mathf.Clamp01(a);
        }
        catch{return 1f;}
    }
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
            fadeCard=sk;
            // Centre the row (Multiplayer, Skirmish and the Ranked card drawn one pitch right of Skirmish) with the layout's left padding.
            // Lateralus 22 Nov 2026 (dev.34): hovering a card sometimes threw the whole row to the right, Ranked partly off screen. The
            // first version moved the Content's anchors, pivot and position every 0.5 s and measured the card width while the vanilla
            // hover tween was growing it, which fought the game's own layout. Now the Content keeps the game's anchors and pivot; only
            // HorizontalLayoutGroup.padding.left changes, measured only at rest (both cards the same width, nothing hovered).
            var content=mp.parent.GetComponent<RectTransform>();var hlg=content.GetComponent<HorizontalLayoutGroup>();
            var parent=content.parent as RectTransform;if(hlg==null||parent==null)return;
            if(rowContent==null||rowContent.WasCollected||rowContent.Pointer!=content.Pointer){rowContent=content;rowPad=hlg.padding.left;}
            var mr=mp.GetComponent<RectTransform>();var sr=sk.GetComponent<RectTransform>();
            var (firstLeft,w)=InParent(mr,parent);var (_,ws)=InParent(sr,parent);
            if(w<20f||Mathf.Abs(ws-w)>0.5f)return;   // a card is hovered (it grows alone): keep the padding
            float rowW=3f*w+2f*hlg.spacing;
            float want=hlg.padding.left+((parent.rect.width-rowW)/2f-firstLeft);
            int pad=Mathf.Max(0,Mathf.RoundToInt(want));
            if(Mathf.Abs(pad-hlg.padding.left)>1)
            {
                hlg.padding.left=pad;LayoutRebuilder.MarkLayoutForRebuild(content);
                if(!loggedLayout){loggedLayout=true;MelonLogger.Msg($"FREEDOM_ARROW_PLAY_TAB Campaign/Scenarios hidden, row centred by padding {rowPad} -> {pad} (card {w:0}, spacing {hlg.spacing:0}, parent {parent.rect.width:0}), art {(artMp!=null?"MP ok":"MP missing")} {(artSk!=null?"Skirmish ok":"Skirmish missing")}");}
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

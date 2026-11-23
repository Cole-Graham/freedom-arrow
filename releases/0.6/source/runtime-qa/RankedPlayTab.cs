using HarmonyLib;
using MelonLoader;
using System.Reflection;
using UnityEngine;
using UnityEngine.UI;
using Il2CppBrokenArrow.Client.Ecs.UI;
namespace FreedomArrow;
// Play tab layout (Lateralus 22 Nov 2026, picked from the previews): Campaign and Scenarios hidden; the row (Multiplayer, Skirmish and
// our Ranked card) centred; Multiplayer art = PLA flag raising (FA_CN_LOADING_33), Skirmish art = Russian assault troops
// (FA_RU_LOADING_09), both baked 600x1200 with the cards' top fade (UserData/FreedomArrow/ranked/menu/). ArrowQueue's 'Mod game'
// header tab is hidden outside lobbies (the Multiplayer card opens the same page); ArrowQueue still shows it in a lobby.
static partial class RankedMenu
{
    static Sprite artMp,artSk;static bool artLoaded;
    static Transform fadeCard;
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
    // Lateralus 22 Nov 2026 (dev.35): at the first opening the vanilla cards (Campaign, Scenarios, old art) showed before ours, the row
    // ended off centre, and on every re-opening it started left and slid right while flashing. Causes: the fix-up ran every 0.5 s and the
    // game re-enables Campaign/Scenarios each time the tab opens; the centring measured cards during the game's opening animation.
    // Now: the Play tab is prepared while it is still closed (FindObjectsOfTypeAll) and checked every frame; Campaign and Scenarios move
    // into an inactive holder (the game can switch them on, they stay invisible and out of the layout); the centring padding is
    // computed from the layout values (card LayoutElement width, spacing, the Content's anchor/pivot/position), not from card positions.
    static RectTransform cContent;static HorizontalLayoutGroup cHlg;static Transform cMp,cSk;static float nextLayoutScan,restL=-1f;static int origPad;
    static bool loggedFormula;
    static void PlayLayoutTick(float now)
    {
        try
        {
            if(cContent==null||cContent.WasCollected||cMp==null||cMp.WasCollected||cSk==null||cSk.WasCollected||cHlg==null||cHlg.WasCollected)
            {
                cContent=null;
                if(now<nextLayoutScan)return;nextLayoutScan=now+0.25f;
                if(UnityEngine.SceneManagement.SceneManager.GetActiveScene().name!="Hangar_Scene")return;
                PlayTab p=null;foreach(var x in Resources.FindObjectsOfTypeAll<PlayTab>())if(x!=null&&x.gameObject.scene.IsValid()){p=x;break;}
                if(p==null)return;
                var c=p._buttonsContainer;if(c==null)return;
                Transform mp=null,sk=null,camp=null,scen=null;
                foreach(var t in c.GetComponentsInChildren<Transform>(true))
                {
                    var n=t.name;
                    if(n=="Menu Picture Button - Multiplayer")mp=t;else if(n=="Menu Picture Button - Skirmish")sk=t;
                    else if(n=="Menu Picture Button - Campaign")camp=t;else if(n=="Menu Picture Button - Scenarios")scen=t;
                }
                if(mp==null||sk==null)return;
                var content=mp.parent.GetComponent<RectTransform>();var hlg=content==null?null:content.GetComponent<HorizontalLayoutGroup>();if(hlg==null)return;
                var holder=new GameObject("FA hidden play cards");holder.SetActive(false);holder.transform.SetParent(p.transform,false);
                if(camp!=null)camp.SetParent(holder.transform,false);
                if(scen!=null)scen.SetParent(holder.transform,false);
                if(!artLoaded){artLoaded=true;artMp=ArtSprite("multiplayer.png");artSk=ArtSprite("skirmish.png");}
                cContent=content;cHlg=hlg;cMp=mp;cSk=sk;restL=-1f;origPad=hlg.padding.left;fadeCard=sk;
                MelonLogger.Msg($"FREEDOM_ARROW_PLAY_TAB prepared ({(p.isActiveAndEnabled?"open":"closed")}): Campaign/Scenarios moved to a hidden holder ({camp!=null}/{scen!=null}), art {(artMp!=null?"MP ok":"MP missing")} {(artSk!=null?"Skirmish ok":"Skirmish missing")}");
            }
            SetArt(cMp,artMp);SetArt(cSk,artSk);
            Centre();
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_PLAY_TAB: "+e.Message);cContent=null;nextLayoutScan=now+10f;}
    }
    static float LayoutWidth(Transform card)
    {
        var le=card.GetComponent<LayoutElement>();
        if(le!=null&&le.preferredWidth>0f)return le.preferredWidth;
        return card.GetComponent<RectTransform>().rect.width;
    }
    // first card's left edge in the parent = ax*W + pos.x + scale*(P - pivot.x*contentWidth), contentWidth = P + padR + 2L + spacing
    // (ContentSizeFitter); solve for the left padding P that puts the 3-card row (Ranked drawn one pitch right) in the middle.
    static void Centre()
    {
        var parent=cContent.parent as RectTransform;if(parent==null)return;
        float l=Math.Min(LayoutWidth(cMp),LayoutWidth(cSk));if(l<20f)return;
        if(restL<0f||l<restL)restL=l;   // a hovered card grows; keep the rest width
        float L=restL,W=parent.rect.width,sp=cHlg.spacing,ax=cContent.anchorMin.x,px=cContent.pivot.x,sc=cContent.localScale.x,pos=cContent.anchoredPosition.x;
        if(Mathf.Abs(cContent.anchorMax.x-ax)>0.001f){if(!loggedFormula){loggedFormula=true;MelonLogger.Warning($"FREEDOM_ARROW_PLAY_TAB row not centred: stretched anchors {cContent.anchorMin}-{cContent.anchorMax}");}return;}
        float denom=sc*(1f-px);if(denom<0.01f)return;
        float target=(W-(3f*L+2f*sp))/2f;
        float P=(target-ax*W-pos+sc*px*(cHlg.padding.right+2f*L+sp))/denom;
        int pad=Mathf.Max(0,Mathf.RoundToInt(P));
        if(pad==cHlg.padding.left)return;
        cHlg.padding.left=pad;LayoutRebuilder.MarkLayoutForRebuild(cContent);
        if(!loggedFormula){loggedFormula=true;MelonLogger.Msg($"FREEDOM_ARROW_PLAY_TAB row centred: padding {origPad} -> {pad} (card {L:0}, spacing {sp:0}, parent {W:0}, anchor {ax:0.00}, pivot {px:0.00}, pos {pos:0}, scale {sc:0.00})");}
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

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
    // Osama 22 Nov 2026 20:0x (dev.36 live check, 3840x2160): the row still sat right of centre. Measured in game: Multiplayer at screen
    // x 1472 (of 3840) with the Content at anchoredPosition.x 72, anchor/pivot 0; changing the HorizontalLayoutGroup padding (0 -> 406 with
    // the layout formula, or a +/-258 left/right pair) did not move the cards at all. Moving the Content itself does: the row is measured on
    // the screen (ScreenRect) and the Content shifted by the difference (Content x 72 -> -186 at 4K, then centred). It is measured only when
    // both cards have the same width (nothing hovered) and their position has held for 0.3 s after the cards have fully faded in (measured in game: during the
    // opening animation the cards sit elsewhere, x 144 or -372 at 4K, and correcting there made the row jump twice per opening).
    static float stableX=float.NaN,stableSince;
    static void Centre()
    {
        if(!cContent.gameObject.activeInHierarchy||CardAlpha()<0.99f){stableX=float.NaN;return;}   // closed or still fading in (cards move during the opening animation)
        var mr=cMp.GetComponent<RectTransform>();var sr=cSk.GetComponent<RectTransform>();
        var rm=ScreenRect(mr);var rs=ScreenRect(sr);
        if(rm.width<20f||Mathf.Abs(rs.width-rm.width)>1f||mr.rect.width<1f){stableX=float.NaN;return;}   // a card is hovered or not laid out
        float now=Time.unscaledTime;
        if(float.IsNaN(stableX)||Mathf.Abs(rm.x-stableX)>1f){stableX=rm.x;stableSince=now;return;}
        if(now-stableSince<0.3f)return;
        float unitsPerPx=mr.rect.width/rm.width;
        float rowWpx=3f*rm.width+2f*cHlg.spacing/unitsPerPx;
        int sh=Mathf.RoundToInt(((Screen.width-rowWpx)/2f-rm.x)*unitsPerPx);
        if(Mathf.Abs(sh)<=1)return;
        var ap=cContent.anchoredPosition;cContent.anchoredPosition=new Vector2(ap.x+sh,ap.y);stableX=float.NaN;
        MelonLogger.Msg($"FREEDOM_ARROW_PLAY_TAB row centred on screen: Content x {ap.x:0} -> {ap.x+sh:0} (card {rm.width:0} px at x {rm.x:0}, row {rowWpx:0} px, screen {Screen.width})");
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

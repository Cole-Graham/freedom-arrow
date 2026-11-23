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
    // Lateralus 22 Nov 2026 20:5x (dev.37, 2560x1440): "they are starting halfway off the left side of the screen and then suddenly pop into
    // the center ... every time I go in and out of the play menu". Cause (il2cpp dump): each card's GalaxyUiBase plays a FlyFadeIn on enable,
    // which places the card at its remembered _startPosition + _startValue and flies it to _startPosition. That position is the card's slot in
    // the vanilla 4-card row, so layout padding never moved the cards (dev.35/36), and dev.37's fix (moving the whole Content left by 258
    // units) moved the fly-in start half off the screen as well. Now the Content stays where the game puts it; once the cards are at rest,
    // the two cards themselves (localPosition) and their FlyFadeIn target (_startPosition) move by the measured offset, so every later
    // opening flies straight to the centred slots. The row is measured on the screen (ScreenRect) only when both cards have the same width
    // (nothing hovered), have fully faded in and have not moved for 0.3 s.
    static float stableX=float.NaN,stableSince;static float contentX0=float.NaN;
    static void Centre()
    {
        if(!cContent.gameObject.activeInHierarchy||CardAlpha()<0.99f){stableX=float.NaN;return;}
        if(float.IsNaN(contentX0))contentX0=cContent.anchoredPosition.x;
        var mr=cMp.GetComponent<RectTransform>();var sr=cSk.GetComponent<RectTransform>();
        var rm=ScreenRect(mr);var rs=ScreenRect(sr);
        if(rm.width<20f||Mathf.Abs(rs.width-rm.width)>1f||mr.rect.width<1f){stableX=float.NaN;return;}   // a card is hovered or not laid out
        float now=Time.unscaledTime;
        if(float.IsNaN(stableX)||Mathf.Abs(rm.x-stableX)>1f){stableX=rm.x;stableSince=now;return;}
        if(now-stableSince<0.3f)return;
        float unitsPerPx=mr.rect.width/rm.width;
        float rowWpx=3f*rm.width+2f*cHlg.spacing/unitsPerPx;
        float dx=((Screen.width-rowWpx)/2f-rm.x)*unitsPerPx;
        if(Mathf.Abs(dx)<=1f)return;
        int flies=MoveCard(cMp,dx)+MoveCard(cSk,dx);stableX=float.NaN;
        MelonLogger.Msg($"FREEDOM_ARROW_PLAY_TAB cards centred: moved {dx:0} units, {flies} fly-in target(s) moved (card {rm.width:0} px at x {rm.x:0}, row {rowWpx:0} px, screen {Screen.width}, Content x {cContent.anchoredPosition.x:0})");
    }
    static int MoveCard(Transform card,float dx)
    {
        var lp=card.localPosition;card.localPosition=new Vector3(lp.x+dx,lp.y,lp.z);
        int n=0;
        try
        {
            var gb=card.GetComponent<Il2CppBrokenArrow.Client.Ecs.UI.Galaxy.GalaxyUiBase>();
            var stack=new List<Il2CppBrokenArrow.Client.Ecs.UI.Galaxy.GalaxyUiAnimation>();
            if(gb?._onEnabled?.Animation!=null)stack.Add(gb._onEnabled.Animation);
            while(stack.Count>0)
            {
                var a=stack[stack.Count-1];stack.RemoveAt(stack.Count-1);
                var pc=a.TryCast<Il2CppPlugins.GalaxyUI.Runtime.Animations.ParallelCollection>();
                if(pc?._collection!=null){foreach(var c in pc._collection)if(c!=null)stack.Add(c);continue;}
                var f=a.TryCast<Il2CppPlugins.GalaxyUI.Runtime.Animations.FlyFadeIn>();
                if(f!=null){var sp=f._startPosition;f._startPosition=new Vector3(sp.x+dx,sp.y,sp.z);n++;}
            }
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_PLAY_TAB fly-in target: "+e.Message);}
        return n;
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

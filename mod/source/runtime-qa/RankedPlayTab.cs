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
    static Sprite artMp,artSk,artRk;static bool artLoaded;
    // Native Ranked card (Lateralus 24 Nov 2026, thread 1568104480459722894: proposal A, "queue it"). It replaces the IMGUI card, which was drawn
    // over the menu and copied the vanilla cards' fade, position and hover: it showed up late (Play tab and Play button searches every 1-2 s, a
    // cover check cached for 0.25 s) and snapped to the hovered size when the pointer crossed from Multiplayer to Skirmish. Now the Ranked card
    // is a copy of the Skirmish card inside the same HorizontalLayoutGroup, made while the Play tab is still closed, so the game's own GalaxyUiBase
    // plays its fade/fly-in and hover, AudioUiEffect its sounds, and the layout places it. The copy loses PlayTabSkirmishButton (it adds the
    // Skirmish click listener in its Start, which never runs on the copy) and the two TextTarget components (each re-reads its localization key
    // at Start and on every language change, so the copy would say "Skirmish"; see docs/engine/ui-fly-in-animation.md). Its button gets a new
    // click event that opens the Ranked page; its title and description are set here (English, or Chinese when the game is in Chinese) at every
    // opening of the Play tab.
    const string RankedCardName="Menu Picture Button - Ranked";
    static readonly List<UnityEngine.Events.UnityAction> rankedClick=new();
    static Transform MakeRanked(Transform sk)
    {
        var content=sk.parent;
        for(int i=0;i<content.childCount;i++)if(content.GetChild(i).name==RankedCardName)return content.GetChild(i);
        var go=UnityEngine.Object.Instantiate(sk.gameObject,content,false);go.name=RankedCardName;
        var skb=go.GetComponent<Il2CppBrokenArrow.BrokenArrow.Client.Ecs.UI.Menu.PlayTabSkirmishButton>();if(skb!=null)UnityEngine.Object.DestroyImmediate(skb);
        foreach(var tt in go.GetComponentsInChildren<Il2CppBrokenArrow.Shared.Ecs.Localization.TextTarget>(true))UnityEngine.Object.DestroyImmediate(tt);
        var b=go.GetComponent<Button>();
        b.onClick=new Button.ButtonClickedEvent();
        var ua=Il2CppInterop.Runtime.DelegateSupport.ConvertDelegate<UnityEngine.Events.UnityAction>(new Action(()=>
        {
            try{PlaySelected();Open();}catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_PLAY_TAB Ranked click: "+e.Message);}
        }));
        rankedClick.Add(ua);b.onClick.AddListener(ua);
        go.transform.SetSiblingIndex(sk.GetSiblingIndex()+1);
        MelonLogger.Msg($"FREEDOM_ARROW_PLAY_TAB native Ranked card made from Skirmish: Skirmish click script {(skb!=null?"removed":"not found")}, text sources removed, sibling {go.transform.GetSiblingIndex()}");
        return go.transform;
    }
    static void RankedTexts()
    {
        bool zh=HeliRangeCard.Chinese();
        var title=cRk.Find("Title")?.GetComponent<Il2CppTMPro.TextMeshProUGUI>();var desc=cRk.Find("Description")?.GetComponent<Il2CppTMPro.TextMeshProUGUI>();
        if(title!=null)title.text=zh?"排位赛":"Ranked";
        if(desc!=null)desc.text=zh?"与其他玩家较量，检验你的实力":"Test your skill against other players";
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
    static RectTransform cContent;static HorizontalLayoutGroup cHlg;static Transform cMp,cSk,cRk;static float nextLayoutScan,restL=-1f;static int origPad;
    static bool loggedFormula;
    static void PlayLayoutTick(float now)
    {
        try
        {
            if(cContent==null||cContent.WasCollected||cMp==null||cMp.WasCollected||cSk==null||cSk.WasCollected||cRk==null||cRk.WasCollected||cHlg==null||cHlg.WasCollected)
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
                if(!artLoaded){artLoaded=true;artMp=ArtSprite("multiplayer.png");artSk=ArtSprite("skirmish.png");artRk=ArtSprite("ranked.png");}
                var rk=MakeRanked(sk);
                cContent=content;cHlg=hlg;cMp=mp;cSk=sk;cRk=rk;restL=-1f;origPad=hlg.padding.left;padL=float.NaN;placed=false;flyMp=flySk=flyRk=null;wasOpen=false;fixes=0;
                RankedTexts();
                MelonLogger.Msg($"FREEDOM_ARROW_PLAY_TAB prepared ({(p.isActiveAndEnabled?"open":"closed")}): Campaign/Scenarios moved to a hidden holder ({camp!=null}/{scen!=null}), art {(artMp!=null?"MP ok":"MP missing")} {(artSk!=null?"Skirmish ok":"Skirmish missing")}");
            }
            SetArt(cMp,artMp);SetArt(cSk,artSk);SetArt(cRk,artRk);
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
    // Lateralus 22 Nov 2026 21:0x (dev.38): "THEY STILL START LEFT ALIGNED AND THEN SUDDENLY POP INTO THE MIDDLE ... actually investigate".
    // Cause, read from GameAssembly 1.2.2.1 (FlyFadeIn RVA 0x5B20/0x5BC0/0x5AC0, GalaxyUiAnimation.PlayAnimation 0x49D050): on every
    // opening each card's GalaxyUiBase.OnEnable plays a FlyFadeIn.
    //   OnPreStart (at once, in OnEnable, before the layout runs): _startPosition = card.anchoredPosition.
    //   OnStart (after the random Delay, so after the HorizontalLayoutGroup has re-laid the row): flies from the layout's position minus
    //     _startValue to the layout's position (_currentPosition).
    //   OnComplete: card.anchoredPosition = _startPosition, the position from before the layout.
    // So the card flies to where the layout puts it, then snaps back to where it was before. With the vanilla prefab the two agree. With
    // Campaign/Scenarios gone, padding alone (dev.35/36) only moved the flight: the snap kept returning the cards to their prefab slots
    // (measured: padding 0 -> 406, cards still at x 1472 px of 3840). dev.37 moved the whole Content, dev.38 moved only the resting
    // position: in both the layout still said left, so the cards flew left and popped to the centre at the end.
    // Now both agree, set while the Play tab is still closed: the layout padding puts the 3-card row (Multiplayer, Skirmish, our Ranked)
    // in the centre, and each card's resting anchoredPosition is set to the position that layout gives it. The fly-in then lands where
    // it started and there is nothing to snap. Each opening is checked once at rest (flight target vs resting position vs the screen
    // centre) and logged; if they still disagree the card is put on the layout position once (logged), so a wrong guess costs one pop,
    // not one per opening.
    static List<Il2CppPlugins.GalaxyUI.Runtime.Animations.FlyFadeIn> flyMp,flySk,flyRk;static bool wasOpen,checkedOpen;static int openings,fixes;
    static float padL=float.NaN;static bool placed;
    static void Place()
    {
        placed=true;
        var mr=cMp.GetComponent<RectTransform>();var sr=cSk.GetComponent<RectTransform>();var kr=cRk.GetComponent<RectTransform>();var par=cContent.parent?.GetComponent<RectTransform>();
        if(par==null)return;
        float w=LayoutWidth(cMp),sp=cHlg.spacing,W=par.rect.width;
        float ax=cContent.anchorMin.x;
        float left=Mathf.Abs(cContent.anchorMax.x-ax)<1e-4f?ax*W+cContent.anchoredPosition.x-cContent.pivot.x*cContent.rect.width:float.NaN;
        if(float.IsNaN(left)){MelonLogger.Warning($"FREEDOM_ARROW_PLAY_TAB Content has stretched anchors {cContent.anchorMin}-{cContent.anchorMax}: cards left where the game puts them");return;}
        if(float.IsNaN(padL))padL=Mathf.Round((W-(3f*w+2f*sp))/2f-left);
        cHlg.padding.left=(int)padL;
        var order=new[]{cMp,cSk,cRk}.OrderBy(t=>t.GetSiblingIndex()).ToList();   // the layout's order: Multiplayer, Skirmish, Ranked
        foreach(var t in order)SetRest(t.GetComponent<RectTransform>(),padL+order.IndexOf(t)*(w+sp),w);
        LayoutRebuilder.MarkLayoutForRebuild(cContent);
        flyMp=Flies(cMp,mr);flySk=Flies(cSk,sr);flyRk=Flies(cRk,kr);
        MelonLogger.Msg($"FREEDOM_ARROW_PLAY_TAB Ranked card x {kr.anchoredPosition.x:0}, fly-ins on its own card: {flyRk.Count}");
        MelonLogger.Msg($"FREEDOM_ARROW_PLAY_TAB row placed: padding {origPad} -> {padL:0}, Multiplayer x {mr.anchoredPosition.x:0}, Skirmish x {sr.anchoredPosition.x:0} (card {w:0}, spacing {sp:0}, parent {W:0}, Content left {left:0}, align {cHlg.childAlignment}, fly-ins {flyMp.Count}/{flySk.Count})");
    }
    // the position HorizontalLayoutGroup gives a child at inset x from the Content's left edge (SetInsetAndSizeFromParentEdge, Left)
    static void SetRest(RectTransform rt,float x,float w)
    {
        rt.anchorMin=new Vector2(0f,rt.anchorMin.y);rt.anchorMax=new Vector2(0f,rt.anchorMax.y);
        var ap=rt.anchoredPosition;rt.anchoredPosition=new Vector2(x+w*rt.pivot.x,ap.y);
    }
    static List<Il2CppPlugins.GalaxyUI.Runtime.Animations.FlyFadeIn> Flies(Transform card,RectTransform rt)
    {
        var l=new List<Il2CppPlugins.GalaxyUI.Runtime.Animations.FlyFadeIn>();
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
                if(f!=null&&f._target!=null&&f._target.Pointer==rt.Pointer)l.Add(f);
            }
        }
        catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_PLAY_TAB fly-in: "+e.Message);}
        return l;
    }
    static void Centre()
    {
        if(!placed)Place();
        if(flyMp==null)return;
        bool open=cContent.gameObject.activeInHierarchy;
        if(open&&!wasOpen){openings++;checkedOpen=false;RankedTexts();}
        wasOpen=open;
        if(!open||checkedOpen)return;
        if(!Done(flyMp)||!Done(flySk)||!Done(flyRk))return;
        var mr=cMp.GetComponent<RectTransform>();var sr=cSk.GetComponent<RectTransform>();var kr=cRk.GetComponent<RectTransform>();
        var rm=ScreenRect(mr);var rs=ScreenRect(sr);var rk=ScreenRect(kr);
        if(rm.width<20f||Mathf.Abs(rs.width-rm.width)>1f||Mathf.Abs(rk.width-rm.width)>1f||mr.rect.width<1f)return;   // a card is hovered or not laid out
        checkedOpen=true;
        float flewMp=Target(flyMp,mr),flewSk=Target(flySk,sr),flewRk=Target(flyRk,kr);
        float unitsPerPx=mr.rect.width/rm.width,rowWpx=3f*rm.width+2f*cHlg.spacing/unitsPerPx,want=(Screen.width-rowWpx)/2f;
        string msg=$"opening {openings}: Multiplayer flew to x {flewMp:0} and rests at x {mr.anchoredPosition.x:0}, Skirmish flew to x {flewSk:0} and rests at x {sr.anchoredPosition.x:0}, Ranked flew to x {flewRk:0} and rests at x {kr.anchoredPosition.x:0}; row starts at {rm.x:0} px, centre {want:0} px, screen {Screen.width}";
        bool snap=Mathf.Abs(flewMp-mr.anchoredPosition.x)>1f||Mathf.Abs(flewSk-sr.anchoredPosition.x)>1f||Mathf.Abs(flewRk-kr.anchoredPosition.x)>1f;
        // dev.39 logs (Lateralus 22 Nov, 2560 px): the layout values put the row at 637 px, the exact centre, but the screen check measured the
        // centre as 626 and 607 px (a card still slightly scaled), moved the padding 6 and 15 units and so made a small jump. The screen check
        // now only logs; only a flight target / resting spot mismatch is corrected (once).
        if(fixes<1&&snap)
        {
            fixes++;SetRestX(mr,flewMp);SetRestX(sr,flewSk);SetRestX(kr,flewRk);
            MelonLogger.Warning($"FREEDOM_ARROW_PLAY_TAB {msg}: corrected (rest put on the flight target)");
        }
        else MelonLogger.Msg($"FREEDOM_ARROW_PLAY_TAB {msg}");
    }
    static bool Done(List<Il2CppPlugins.GalaxyUI.Runtime.Animations.FlyFadeIn> l){foreach(var f in l)if(!f.Completed)return false;return true;}
    static float Target(List<Il2CppPlugins.GalaxyUI.Runtime.Animations.FlyFadeIn> l,RectTransform rt)=>l.Count>0?l[0]._currentPosition.x:rt.anchoredPosition.x;
    static void SetRestX(RectTransform rt,float x){var ap=rt.anchoredPosition;rt.anchoredPosition=new Vector2(x,ap.y);}
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

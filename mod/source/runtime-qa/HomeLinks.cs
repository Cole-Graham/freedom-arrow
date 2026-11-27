using MelonLoader;
using MelonLoader.Utils;
using UnityEngine;
using UnityEngine.UI;
namespace FreedomArrow;
// Home page left column links (Osama 27 Nov 2026 13:2x PST, #Website thread: "leave the BA news alone, let's touch the left side buttons.
// Let's change the war in the Baltic to the guide button and the trick or treat to the tools website link").
// Read on Osama's PC (dev.6, FA_HOME_TREE dump): "Home menu content/Left Side Bar" (VerticalLayoutGroup) holds "QuickSearch Button",
// "Play Campaign Button" (War in the Baltic, 512x288), "ScenariosButton" (PvE carousel, 512x288) and two hidden vanilla cards of the same
// style, "HotKeys" and "Feedback"; Feedback carries the game's own OpenURL component (Link, ExtraPopup, AutoInit) on a UiButton. Each FA
// card is a copy of Feedback (vanilla look and hover), its OpenURL removed and its UiButton given our own click that opens our page, our picture on its "image",
// its TextTarget components removed (they would re-read the localization key) and our texts set. The copies take the Campaign and
// Scenarios places in the layout; those two are hidden, and kept hidden if the game switches them back on.
// Under each title a smaller line says what the page covers (Osama 27 Nov 13:4x: "add more description about what the guides cover and tools cover").
// Guides title (Osama 27 Nov 13:5x): "say learn what's different with FA along that line".
static class HomeLinks
{
    sealed class Card{public string Name,Replaces,Link,Pic,Kick,KickZh,Title,TitleZh,Desc,DescZh;public Sprite Sprite;}
    static readonly Card[] cards={
        new Card{Name="FA Guides Card",Replaces="Play Campaign Button",Link="https://freedomarrow.app/#guides",Pic="home-guides.png",Kick="Guides",KickZh="指南",Title="Learn what's different in Freedom Arrow",TitleZh="了解自由之箭的不同之处",
            Desc="Vehicle damage, penetration, HEAT, cover, income, scoring, coordinated strikes, ECM and flares",
            DescZh="载具伤害、穿深、破甲、掩体、收入、计分、协同打击、电子干扰与干扰弹"},
        new Card{Name="FA Tools Card",Replaces="ScenariosButton",Link="https://freedomarrow.app/#tools",Pic="home-tools.png",Kick="Tools",KickZh="工具",Title="Armory, DPM and price check",TitleZh="军械库、DPM 与价格查询",
            Desc="Every unit vs vanilla, DPM by range, damage and crit calculator, price check, maps and build changelog",
            DescZh="全部单位与原版对比、按距离的 DPM、伤害与暴击计算器、价格对比、地图和版本更新记录"}};
    static readonly List<Il2CppSystem.Action<GameObject,UnityEngine.EventSystems.PointerEventData.InputButton>> keep=new();
    static Transform bar; static float next;
    public static void Install()
    {
        var dir=Path.Combine(MelonEnvironment.GameRootDirectory,"UserData","FreedomArrow","menu-art");
        foreach(var c in cards)
        {
            var t=new Texture2D(2,2,TextureFormat.RGBA32,false){name="FA_"+c.Pic,hideFlags=HideFlags.DontUnloadUnusedAsset};
            if(!ImageConversion.LoadImage(t,File.ReadAllBytes(Path.Combine(dir,c.Pic)),true))throw new InvalidDataException(c.Pic+" did not load");
            c.Sprite=Sprite.Create(t,new Rect(0,0,t.width,t.height),new Vector2(0.5f,0.5f),100f);c.Sprite.hideFlags=HideFlags.DontUnloadUnusedAsset;
        }
        MelonLogger.Msg("FREEDOM_ARROW_HOME_LINKS installed: Campaign -> Guides, Scenarios -> Tools on the Home page");
    }
    // From WebsiteButton.Build (the Home page was just found) and every second from Tick while that page lives.
    public static void Apply(Transform page)
    {
        bar=null;
        for(int i=0;i<page.childCount;i++)if(page.GetChild(i).name=="Left Side Bar")bar=page.GetChild(i);
        if(bar==null){MelonLogger.Warning("FREEDOM_ARROW_HOME_LINKS: no Left Side Bar");return;}
        Keep();
    }
    public static void Tick()
    {
        if(bar==null||Time.unscaledTime<next)return;
        next=Time.unscaledTime+1f;
        try{if(bar.WasCollected){bar=null;return;}Keep();}catch(Exception e){bar=null;MelonLogger.Warning("FREEDOM_ARROW_HOME_LINKS: "+e.Message);}
    }
    static void Keep()
    {
        var tpl=bar.Find("Feedback");
        foreach(var c in cards)
        {
            var old=bar.Find(c.Replaces);
            var mine=bar.Find(c.Name);
            if(mine==null&&tpl!=null&&old!=null)mine=Make(c,tpl,old);
            if(old!=null&&old.gameObject.activeSelf&&mine!=null)old.gameObject.SetActive(false);
        }
    }
    static Transform Make(Card c,Transform tpl,Transform old)
    {
        bool zh=false;try{zh=HeliRangeCard.Chinese();}catch{}
        var go=UnityEngine.Object.Instantiate(tpl.gameObject,bar,false);go.name=c.Name;
        foreach(var tt in go.GetComponentsInChildren<Il2CppBrokenArrow.Shared.Ecs.Localization.TextTarget>(true))UnityEngine.Object.DestroyImmediate(tt);
        // Our own click (logged, testable) instead of the copied OpenURL component, which is removed so a click never opens two pages.
        var url=go.GetComponent<Il2CppBrokenArrow.ScriptEngine.UI.OpenURL>();if(url!=null)UnityEngine.Object.DestroyImmediate(url);
        var btn=go.GetComponent<Il2CppBrokenArrow.Client.Ecs.UI.BaseElements.UiButton>();
        if(btn!=null){var link=c.Link;var d=Il2CppInterop.Runtime.DelegateSupport.ConvertDelegate<Il2CppSystem.Action<GameObject,UnityEngine.EventSystems.PointerEventData.InputButton>>(
            new Action<GameObject,UnityEngine.EventSystems.PointerEventData.InputButton>((o,b)=>{if(b!=UnityEngine.EventSystems.PointerEventData.InputButton.Left)return;Application.OpenURL(link);MelonLogger.Msg("FREEDOM_ARROW_HOME_LINKS opened "+link);}));
            keep.Add(d);btn.add_ClickEvent(d);}
        var img=go.transform.Find("image")?.GetComponent<Image>();
        if(img!=null){img.sprite=c.Sprite;img.color=Color.white;img.preserveAspect=false;}
        var kick=go.transform.Find("Texts/GUIDE")?.GetComponent<Il2CppTMPro.TextMeshProUGUI>();if(kick!=null)kick.SetText(zh?c.KickZh:c.Kick);
        var title=go.transform.Find("Texts/Text")?.GetComponent<Il2CppTMPro.TextMeshProUGUI>();if(title!=null){title.enableWordWrapping=true;title.richText=true;title.SetText((zh?c.TitleZh:c.Title)+"\n<size=58%><color=#C4C9D0>"+(zh?c.DescZh:c.Desc)+"</color></size>");var trt=title.rectTransform;MelonLogger.Msg($"FREEDOM_ARROW_HOME_LINKS text rect {trt.rect.width:0}x{trt.rect.height:0} font {title.fontSize:0} auto {title.enableAutoSizing} overflow {title.overflowMode} align {title.alignment}");}
        var ort=old.GetComponent<RectTransform>();var rt=go.GetComponent<RectTransform>();
        // The hidden Feedback card is placed by hand (the layout group skips it), so the copy takes the replaced card's exact rect.
        if(ort!=null&&rt!=null){rt.anchorMin=ort.anchorMin;rt.anchorMax=ort.anchorMax;rt.pivot=ort.pivot;rt.sizeDelta=ort.sizeDelta;rt.anchoredPosition=ort.anchoredPosition;}
        var le=go.GetComponent<LayoutElement>()??go.AddComponent<LayoutElement>();le.ignoreLayout=true;
        go.transform.SetSiblingIndex(old.GetSiblingIndex());
        go.SetActive(true);
        MelonLogger.Msg($"FREEDOM_ARROW_HOME_LINKS: '{c.Name}' made from Feedback in place of '{c.Replaces}' (click {(btn!=null?"set":"missing")}, picture {(img!=null?"set":"missing")}, texts {(kick!=null&&title!=null?"set":"missing")}) -> {c.Link}");
        return go.transform;
    }
}

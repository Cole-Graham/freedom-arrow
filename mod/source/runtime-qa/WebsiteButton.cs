using HarmonyLib;
using Il2CppInterop.Runtime;
using Il2CppBrokenArrow.Client.Ecs.UI.MainMenu;
using MelonLoader;
using MelonLoader.Utils;
using UnityEngine;
using UnityEngine.UI;
namespace FreedomArrow;
// Website button (Osama 22 Nov 2026 01:42 PST, thread 1573561286803980289: "in this new version in the main menu we need a button with our art
// that opens our website"). A banner (UserData/FreedomArrow/menu-art/website-button.png: approved FA patch, menu art, "freedomarrow.app",
// "WEBSITE · 访问官网") drawn on the Home tab in the top centre, between the Quick match tile and Server status, and a click on it opens
// https://freedomarrow.app/.
//
// Native UI (Lateralus 23 Nov 2026, thread 1573505321010331651: "include the website banner fix, make sure its display follows the vanilla
// menu asset design architecture"). Until 0.9.5b-dev.1 the banner was IMGUI, drawn over everything, so it needed its own show rules (Home
// tab button selected, title-screen check, 2 s settle, FA Music selector state) and still drew over the main-menu loading screen. Now it is
// an Image + Button inside the game's own Home page, "Home menu content" (1920x1080, no layout group; ArrowQueue's server status copy sits in
// the same page). The page is found by its object name, which is the same in every language; no label text, scene name or timer is read.
// The game shows and hides it with the Home page, fades it with the page's CanvasGroups, scales it with the menu's CanvasScaler, and the
// title and loading screens cover it the same way they cover the vanilla Home tiles.
//
// Old-launcher warning (Osama 22 Nov 2026 02:0x PST, thread 1573505321010331651: "an in game warning that their launcher is out of date should
// pop up on the main menu and disappear after dismissal, it should link to our website. make it a art based button"). Launchers older than
// 1.1.9 cannot update themselves. Launcher 1.1.9+ keeps the last verified signed version list in
// %AppData%\FreedomArrowLauncherDev45\downloads\live-manifest.signed.json (written at every PLAY); older launchers use the same AppData folder
// but never write that file. So: launcher folder present + no signed list = old launcher. Then this banner shows menu-art/launcher-update.png
// ("LAUNCHER OUT OF DATE", EN + 中文) instead of the website art; a click opens the install page, the ✕ dismisses it for this session (the
// normal website banner shows after that). Mod Manager installs (no launcher folder) and Proton (the launcher runs in its own prefix) see nothing.
static class WebsiteButton
{
    const string Url="https://freedomarrow.app/";
    const string InstallUrl="https://freedomarrow.app/#install";
    static Texture2D art,updateArt;
    static bool launcherOld,updateDismissed;

    public static void Install(HarmonyLib.Harmony h)
    {
        var file=Path.Combine(MelonEnvironment.GameRootDirectory,"UserData","FreedomArrow","menu-art","website-button.png");
        art=new Texture2D(2,2,TextureFormat.RGBA32,false){name="FA_website_button",hideFlags=HideFlags.DontUnloadUnusedAsset};
        if(!ImageConversion.LoadImage(art,File.ReadAllBytes(file),true))throw new InvalidDataException("website-button.png did not load");
        try
        {
            var dir=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),"FreedomArrowLauncherDev45");
            launcherOld=Directory.Exists(dir)&&!File.Exists(Path.Combine(dir,"downloads","live-manifest.signed.json"));
            if(launcherOld)
            {
                updateArt=new Texture2D(2,2,TextureFormat.RGBA32,false){name="FA_launcher_update",hideFlags=HideFlags.DontUnloadUnusedAsset};
                if(!ImageConversion.LoadImage(updateArt,File.ReadAllBytes(Path.Combine(Path.GetDirectoryName(file),"launcher-update.png")),true))updateArt=null;
            }
            MelonLogger.Msg($"FREEDOM_ARROW_LAUNCHER_NOTICE launcher folder {(Directory.Exists(dir)?"found":"not found")}, "+
                (launcherOld?(updateArt!=null?"old launcher (no signed version list): out-of-date banner shown":"old launcher, art missing: no banner"):"no notice"));
        }
        catch(Exception ex){launcherOld=false;MelonLogger.Msg("FREEDOM_ARROW_LAUNCHER_NOTICE off: "+ex.GetType().Name);}
        MelonLogger.Msg($"FREEDOM_ARROW_WEBSITE_BUTTON installed ({art.width}x{art.height}): Home tab banner opens {Url}");
    }


    // Osama 22 Nov 01:56: "take the top and central area between quick match and server status". Measured on a 1568x882 Home screenshot:
    // Quick match tile right edge 0.304 (gear icon to 0.324), Server status left edge 0.725, tile tops at 0.122. As anchors in the page:
    // x 0.335-0.715, top edge 0.122 below the page top; the height follows the art's aspect ratio.
    const float Left=0.335f,Right=0.715f,Top=0.122f;
    static GameObject banner;static Image image,closeImage;static Sprite siteSprite,updateSprite;
    static readonly List<UnityEngine.Events.UnityAction> keep=new();
    static float nextScan;static string waitWhy="";
    static void Wait(string why){if(why!=waitWhy){waitWhy=why;MelonLogger.Msg("FREEDOM_ARROW_WEBSITE_BUTTON wait: "+why);}}

    // Called every frame from Runtime.OnUpdate. While the banner exists this is one null check; when the menu is rebuilt (a new Hangar
    // scene) the old page and banner are destroyed with it, and the next scan (at most every 2 s) builds a new one.
    public static void Tick()
    {
        if(art==null)return;
        if(banner!=null&&!banner.WasCollected)return;
        banner=null;
        if(Time.unscaledTime<nextScan)return;
        nextScan=Time.unscaledTime+2f;
        try
        {
            var page=HomePage();
            if(page==null){Wait("no Home menu content page");return;}
            Build(page);
        }
        catch(Exception ex){banner=null;MelonLogger.Warning("FREEDOM_ARROW_WEBSITE_BUTTON not built: "+ex.Message);}
    }

    // The Home tab's page: the MainMenuButton whose target page is, or holds, "Home menu content". Inactive objects count (the Home page
    // is built while another page or the loading screen is up).
    static Transform HomePage()
    {
        foreach(var b in Resources.FindObjectsOfTypeAll<MainMenuButton>())
        {
            if(b==null||!b.gameObject.scene.IsValid())continue;
            var p=b._showTargetContent;if(p==null)continue;
            if(p.name=="Home menu content")return p.transform;
            foreach(var t in p.GetComponentsInChildren<Transform>(true))if(t.name=="Home menu content")return t;
        }
        return null;
    }

    static Sprite Spr(Texture2D t){var s=Sprite.Create(t,new Rect(0,0,t.width,t.height),new Vector2(0.5f,0.5f),100f);s.name=t.name;s.hideFlags=HideFlags.DontUnloadUnusedAsset;return s;}
    static RectTransform Node(string name,Transform parent)
    {
        var g=new GameObject(name);g.layer=parent.gameObject.layer;
        var rt=g.AddComponent<RectTransform>();rt.SetParent(parent,false);return rt;
    }
    static void OnClick(Button b,Action a)
    {
        var ua=DelegateSupport.ConvertDelegate<UnityEngine.Events.UnityAction>(new Action(()=>{try{a();}catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_WEBSITE_BUTTON click: "+e.Message);}}));
        keep.Add(ua);b.onClick.AddListener(ua);
    }
    static void Tint(Button b,Graphic g)
    {
        b.targetGraphic=g;b.transition=Selectable.Transition.ColorTint;
        var cb=b.colors;cb.normalColor=Color.white;cb.highlightedColor=new Color(1.25f,1.25f,1.25f,1f);cb.pressedColor=new Color(0.8f,0.8f,0.8f,1f);
        cb.selectedColor=Color.white;cb.fadeDuration=0.1f;b.colors=cb;
        var nav=b.navigation;nav.mode=Navigation.Mode.None;b.navigation=nav;   // no keyboard/gamepad focus taken from the vanilla menu
    }

    static void Build(Transform page)
    {
        siteSprite??=Spr(art);
        if(launcherOld&&updateArt!=null)updateSprite??=Spr(updateArt);
        var rt=Node("FA Website Banner",page);
        rt.anchorMin=new Vector2(Left,1f-Top);rt.anchorMax=new Vector2(Right,1f-Top);rt.pivot=new Vector2(0.5f,1f);
        rt.anchoredPosition=Vector2.zero;rt.sizeDelta=Vector2.zero;
        rt.gameObject.AddComponent<LayoutElement>().ignoreLayout=true;
        image=rt.gameObject.AddComponent<Image>();image.raycastTarget=true;image.preserveAspect=true;
        var fit=rt.gameObject.AddComponent<AspectRatioFitter>();fit.aspectMode=AspectRatioFitter.AspectMode.WidthControlsHeight;
        var btn=rt.gameObject.AddComponent<Button>();Tint(btn,image);
        OnClick(btn,()=>{var url=Warning()?InstallUrl:Url;Application.OpenURL(url);MelonLogger.Msg((Warning()?"FREEDOM_ARROW_LAUNCHER_NOTICE":"FREEDOM_ARROW_WEBSITE_BUTTON")+" opened "+url);});
        // The old-launcher warning's dismiss X, top right of the banner (same place as before).
        var x=Node("FA Launcher Notice Close",rt);
        x.anchorMin=x.anchorMax=new Vector2(1f,1f);x.pivot=new Vector2(1f,1f);
        x.anchoredPosition=new Vector2(-6f,-6f);x.sizeDelta=new Vector2(30f,30f);
        closeImage=x.gameObject.AddComponent<Image>();closeImage.color=new Color(0f,0f,0f,0.6f);closeImage.raycastTarget=true;
        var xt=Node("X",x);xt.anchorMin=Vector2.zero;xt.anchorMax=Vector2.one;xt.sizeDelta=Vector2.zero;
        var label=xt.gameObject.AddComponent<Il2CppTMPro.TextMeshProUGUI>();
        var vf=page.GetComponentInChildren<Il2CppTMPro.TextMeshProUGUI>(true);if(vf!=null&&vf.font!=null)label.font=vf.font;   // the Home page's own font
        label.text="X";label.fontSize=20;label.fontStyle=Il2CppTMPro.FontStyles.Bold;
        label.alignment=Il2CppTMPro.TextAlignmentOptions.Center;label.color=Color.white;label.raycastTarget=false;
        var xb=x.gameObject.AddComponent<Button>();Tint(xb,closeImage);
        var cb=xb.colors;cb.highlightedColor=new Color(0.89f,0.21f,0.24f,0.95f)*1.6f;xb.colors=cb;
        OnClick(xb,()=>{updateDismissed=true;MelonLogger.Msg("FREEDOM_ARROW_LAUNCHER_NOTICE dismissed");Show();});
        banner=rt.gameObject;
        Show();
        var prt=page.GetComponent<RectTransform>();
        MelonLogger.Msg($"FREEDOM_ARROW_WEBSITE_BUTTON built in '{page.name}' ({(prt!=null?$"{prt.rect.width:0}x{prt.rect.height:0}":"no RectTransform")}, active {page.gameObject.activeInHierarchy}): {(Warning()?"launcher warning":"website")} art, anchors x {Left}-{Right}, top {Top}");
        waitWhy="";
    }
    static bool Warning()=>launcherOld&&!updateDismissed&&updateSprite!=null;
    static void Show()
    {
        var w=Warning();var sp=w?updateSprite:siteSprite;
        image.sprite=sp;image.GetComponent<AspectRatioFitter>().aspectRatio=(float)sp.texture.width/sp.texture.height;
        closeImage.gameObject.SetActive(w);
    }
}

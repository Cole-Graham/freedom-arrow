using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.UI.MainMenu;
using MelonLoader;
using MelonLoader.Utils;
using UnityEngine;
namespace FreedomArrow;
// Website button (Osama 22 Nov 2026 01:42 PST, thread 1573561286803980289: "in this new version in the main menu we need a button with our art
// that opens our website"). A banner (UserData/FreedomArrow/menu-art/website-button.png: approved FA patch, menu art, "freedomarrow.app",
// "WEBSITE · 访问官网") drawn on the Home tab in the top centre, between the Quick match tile and Server status, and a click on it opens
// https://freedomarrow.app/. Osama 22 Nov 02:37 ("just tie it with the music pack selector"): it uses the music pack selector's rule
// (tools/music-player/MusicMenu.cs) - shown while the menu scene is Hangar_Scene and the Home tab button is selected, hidden otherwise.
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
    static MainMenuButton home;
    static Texture2D art,updateArt;
    static bool failed,launcherOld,updateDismissed;

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


    // Osama 22 Nov 01:56: "take the top and central area between quick match and server status, it goes away after someone clicks play,
    // arsenal, editor, mod game, settings and etc". Measured on a 1568x882 Home screenshot: Quick match tile right edge 0.304 (its gear icon
    // to 0.324), Server status left edge 0.725, tile tops at 0.122. It hides when another tab is selected and comes back the next time the
    // Home tab is selected again (a return to the Home tab or a new menu scene).
    static bool dismissed,wasActive;
    // Osama 22 Nov 02:11: "the website button showed up in our loading screen and then dissappeared before going into the main menu".
    // The Home menu is built behind the loading screen, and IMGUI draws over it; a click during loading then
    // counted as "clicked elsewhere". So the banner waits until the Home tab has been selected for 2 s with no loading hitch
    // (a frame over 0.25 s), and only clicks after it is on screen can dismiss it.
    const float SettleSeconds=2f,HitchSeconds=0.25f;
    static float settledFrom=-1f;
    // Osama 22 Nov 02:28 (dev.17): "website button only shows in the loading screen not main menu". Every show/hide is logged
    // (FREEDOM_ARROW_WEBSITE_BUTTON shown / hidden: reason), and clicks in its first 0.75 s on screen don't hide it.
    static float shownAt=-1f;
    static string hiddenWhy="";

    // Same rule as the music pack selector: menu scene + Home tab button selected. The Home button is looked up at most every 2 s.
    static float nextHomeScan;
    static bool HomeSelected()
    {
        if(UnityEngine.SceneManagement.SceneManager.GetActiveScene().name!="Hangar_Scene"){home=null;return false;}
        if(home==null||home.WasCollected)
        {
            home=null;
            if(Time.unscaledTime<nextHomeScan)return false;
            nextHomeScan=Time.unscaledTime+2f;
            foreach(var b in Resources.FindObjectsOfTypeAll<MainMenuButton>())
            {
                if(!b.gameObject.scene.IsValid()||b._buttonText==null)continue;
                if(!b._buttonText.text.Trim().Equals("Home",StringComparison.OrdinalIgnoreCase))continue;
                home=b;break;
            }
            if(home==null)return false;
        }
        return home.isActiveAndEnabled&&home.Selected;
    }

    // Osama 22 Nov 13:2x (dev.29): "The website banner please fix it now" - it drew over the "Press any key" title screen. The Home menu is
    // built (Home tab selected) behind the title, and this banner is IMGUI, which draws over everything; the music pack selector is native
    // UI under the title, so it never showed there. The title is the active "Parallax Keyart" object (MenuArt.cs); checked at most twice a second.
    static float nextTitleCheck;static bool titleUp;
    static bool TitleScreenUp()
    {
        if(Time.unscaledTime<nextTitleCheck)return titleUp;
        nextTitleCheck=Time.unscaledTime+0.5f;
        var g=GameObject.Find("Parallax Keyart");
        titleUp=g!=null&&g.activeInHierarchy;
        return titleUp;
    }

    static void Hide(string why)
    {
        if(shownAt>=0f&&why!=hiddenWhy)MelonLogger.Msg("FREEDOM_ARROW_WEBSITE_BUTTON hidden: "+why);
        shownAt=-1f;hiddenWhy=why;
    }

    public static void OnGUI()
    {
        if(failed||art==null)return;
        try
        {
            bool title=TitleScreenUp();
            bool active=!title&&HomeSelected();
            if(!active)Hide(title?"title screen (Press any key)":"not on the Home tab");
            if(active&&!wasActive){dismissed=false;settledFrom=Time.realtimeSinceStartup;}
            wasActive=active;
            if(!active||dismissed)return;
            if(Time.unscaledDeltaTime>HitchSeconds)settledFrom=Time.realtimeSinceStartup;   // still loading
            if(Time.realtimeSinceStartup-settledFrom<SettleSeconds)return;
            if(shownAt<0f){shownAt=Time.realtimeSinceStartup;hiddenWhy="";MelonLogger.Msg("FREEDOM_ARROW_WEBSITE_BUTTON shown on the Home tab");}
            bool warn=launcherOld&&!updateDismissed&&updateArt!=null;
            var tex=warn?updateArt:art;
            float left=Screen.width*0.335f,right=Screen.width*0.715f;
            float w=right-left,h=w*tex.height/tex.width;
            var r=new Rect(left,Screen.height*0.122f,w,h);
            float cs=Mathf.Max(22f,h*0.13f);
            var close=new Rect(r.xMax-cs-h*0.03f,r.y+h*0.05f,cs,cs);   // the warning's dismiss ✕, top right
            var e=Event.current;
            // Osama 22 Nov 03:07: "the website button dissappears when you click anywhere on the menu ... let its presence be tied to the
            // same logic that has the music pack button". No click-outside hiding: it shows exactly while the music pack selector would.
            GUI.DrawTexture(r,tex,ScaleMode.StretchToFill);
            if(r.Contains(e.mousePosition)&&!(warn&&close.Contains(e.mousePosition)))
            {
                var old=GUI.color;GUI.color=new Color(1f,1f,1f,0.12f);GUI.DrawTexture(r,Texture2D.whiteTexture);GUI.color=old;
            }
            if(warn)
            {
                var old=GUI.color;GUI.color=close.Contains(e.mousePosition)?new Color(0.89f,0.21f,0.24f,0.95f):new Color(0f,0f,0f,0.6f);
                GUI.DrawTexture(close,Texture2D.whiteTexture);GUI.color=old;
                var st=new GUIStyle(GUI.skin.label){alignment=TextAnchor.MiddleCenter,fontSize=Mathf.RoundToInt(cs*0.62f),fontStyle=FontStyle.Bold};
                st.normal.textColor=Color.white;
                GUI.Label(close,"X",st);
                if(GUI.Button(close,GUIContent.none,GUIStyle.none))
                {
                    updateDismissed=true;
                    MelonLogger.Msg("FREEDOM_ARROW_LAUNCHER_NOTICE dismissed");
                    return;
                }
            }
            if(GUI.Button(r,GUIContent.none,GUIStyle.none))
            {
                var url=warn?InstallUrl:Url;
                Application.OpenURL(url);
                MelonLogger.Msg((warn?"FREEDOM_ARROW_LAUNCHER_NOTICE":"FREEDOM_ARROW_WEBSITE_BUTTON")+" opened "+url);
            }
        }
        catch(Exception ex){home=null;MelonLogger.Warning("FREEDOM_ARROW_WEBSITE_BUTTON hidden until the Home tab reopens: "+ex.Message);}
    }
}

using HarmonyLib;
using Il2CppBrokenArrow.BrokenArrow.Client.Ecs.UI.Menu.News;
using MelonLoader;
using MelonLoader.Utils;
using UnityEngine;
namespace FreedomArrow;
// Website button (Osama 22 Nov 2026 01:42 PST, thread 1573561286803980289: "in this new version in the main menu we need a button with our art
// that opens our website"). A banner (UserData/FreedomArrow/menu-art/website-button.png: approved FA patch, menu art, "freedomarrow.app",
// "WEBSITE · 访问官网") drawn on the Home tab in the top centre, between the Quick match tile and Server status. It shows only while the
// Home tab's news panel (NewsWindow) is on screen, hides after any other click, and a click on it opens https://freedomarrow.app/.
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
    static NewsWindow news;
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
        h.Patch(AccessTools.Method(typeof(NewsWindow),"Start")??throw new MissingMethodException("NewsWindow.Start"),
            postfix:new HarmonyMethod(typeof(WebsiteButton),nameof(Started)));
        MelonLogger.Msg($"FREEDOM_ARROW_WEBSITE_BUTTON installed ({art.width}x{art.height}): Home tab banner opens {Url}");
    }

    static void Started(NewsWindow __instance)=>news=__instance;

    // Osama 22 Nov 01:56: "take the top and central area between quick match and server status, it goes away after someone clicks play,
    // arsenal, editor, mod game, settings and etc". Measured on a 1568x882 Home screenshot: Quick match tile right edge 0.304 (its gear icon
    // to 0.324), Server status left edge 0.725, tile tops at 0.122. Any click outside the banner hides it; it comes back the next time the
    // Home news panel opens (a return to the Home tab or a new menu scene).
    static bool dismissed,wasActive;
    public static void OnGUI()
    {
        if(failed||art==null||news==null)return;
        try
        {
            bool active=!news.WasCollected&&news.gameObject.activeInHierarchy;
            if(active&&!wasActive)dismissed=false;
            wasActive=active;
            if(!active||dismissed)return;
            bool warn=launcherOld&&!updateDismissed&&updateArt!=null;
            var tex=warn?updateArt:art;
            float left=Screen.width*0.335f,right=Screen.width*0.715f;
            float w=right-left,h=w*tex.height/tex.width;
            var r=new Rect(left,Screen.height*0.122f,w,h);
            float cs=Mathf.Max(22f,h*0.13f);
            var close=new Rect(r.xMax-cs-h*0.03f,r.y+h*0.05f,cs,cs);   // the warning's dismiss ✕, top right
            var e=Event.current;
            if(e.type==EventType.MouseDown&&!r.Contains(e.mousePosition)){dismissed=true;return;}
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
        catch(Exception ex){news=null;MelonLogger.Warning("FREEDOM_ARROW_WEBSITE_BUTTON hidden until the Home tab reopens: "+ex.Message);}
    }
}

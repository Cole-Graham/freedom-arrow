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
static class WebsiteButton
{
    const string Url="https://freedomarrow.app/";
    static NewsWindow news;
    static Texture2D art;
    static bool failed;

    public static void Install(HarmonyLib.Harmony h)
    {
        var file=Path.Combine(MelonEnvironment.GameRootDirectory,"UserData","FreedomArrow","menu-art","website-button.png");
        art=new Texture2D(2,2,TextureFormat.RGBA32,false){name="FA_website_button",hideFlags=HideFlags.DontUnloadUnusedAsset};
        if(!ImageConversion.LoadImage(art,File.ReadAllBytes(file),true))throw new InvalidDataException("website-button.png did not load");
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
            float left=Screen.width*0.335f,right=Screen.width*0.715f;
            float w=right-left,h=w*art.height/art.width;
            var r=new Rect(left,Screen.height*0.122f,w,h);
            var e=Event.current;
            if(e.type==EventType.MouseDown&&!r.Contains(e.mousePosition)){dismissed=true;return;}
            GUI.DrawTexture(r,art,ScaleMode.StretchToFill);
            if(r.Contains(e.mousePosition))
            {
                var old=GUI.color;GUI.color=new Color(1f,1f,1f,0.12f);GUI.DrawTexture(r,Texture2D.whiteTexture);GUI.color=old;
            }
            if(GUI.Button(r,GUIContent.none,GUIStyle.none))
            {
                Application.OpenURL(Url);
                MelonLogger.Msg("FREEDOM_ARROW_WEBSITE_BUTTON opened "+Url);
            }
        }
        catch(Exception ex){news=null;MelonLogger.Warning("FREEDOM_ARROW_WEBSITE_BUTTON hidden until the Home tab reopens: "+ex.Message);}
    }
}

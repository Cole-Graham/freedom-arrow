using HarmonyLib;
using Il2CppBrokenArrow.BrokenArrow.Client.Ecs.UI.Menu.News;
using MelonLoader;
using MelonLoader.Utils;
using UnityEngine;
namespace FreedomArrow;
// Website button (Osama 22 Nov 2026 01:42 PST, thread 1573561286803980289: "in this new version in the main menu we need a button with our art
// that opens our website"). A banner (UserData/FreedomArrow/menu-art/website-button.png: approved FA patch, menu art, "freedomarrow.app",
// "WEBSITE · 访问官网") drawn on the Home tab just left of the game's Steam Workshop banner, the same size. It shows only while the Home
// tab's news panel (NewsWindow) is on screen, and a click opens https://freedomarrow.app/ in the browser.
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

    public static void OnGUI()
    {
        if(failed||art==null||news==null)return;
        try
        {
            if(news.WasCollected||!news.gameObject.activeInHierarchy)return;
            // Placed by the Steam Workshop banner on the Home tab (measured on a 1568x882 menu screenshot: Workshop x 0.812-0.979, y 0.850-0.955).
            float h=Screen.height*0.104f,w=h*art.width/art.height;
            var r=new Rect(Screen.width*0.8017f-w,Screen.height*0.955f-h,w,h);
            GUI.DrawTexture(r,art,ScaleMode.StretchToFill);
            if(r.Contains(Event.current.mousePosition))
            {
                var old=GUI.color;GUI.color=new Color(1f,1f,1f,0.12f);GUI.DrawTexture(r,Texture2D.whiteTexture);GUI.color=old;
            }
            if(GUI.Button(r,GUIContent.none,GUIStyle.none))
            {
                Application.OpenURL(Url);
                MelonLogger.Msg("FREEDOM_ARROW_WEBSITE_BUTTON opened "+Url);
            }
        }
        catch(Exception e){news=null;MelonLogger.Warning("FREEDOM_ARROW_WEBSITE_BUTTON hidden until the Home tab reopens: "+e.Message);}
    }
}

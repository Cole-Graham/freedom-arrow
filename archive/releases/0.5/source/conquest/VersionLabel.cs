using MelonLoader;
using UnityEngine;
using Il2CppBrokenArrow.AudioSystem;

namespace FreedomArrow.Conquest;
// 0.5 dev.43: the main menu shows the Freedom Arrow version (Osama, 7 November 2026).
// 0.5 dev.45: bottom middle, because the game shows its own build number at the bottom right.
// The game's music type tells menu screens from battles: Intro 2, Hangar 20, Campaign 30, MiniGames 100.
public sealed partial class Prototype
{
    static int menuMusicType=2;
    static GUIStyle versionStyle;
    static bool versionOff;
    static void InstallVersionLabel()
    {
        Patch(typeof(Il2Cpp.MusicService),"PlayByType",null,nameof(MusicTypeAfter));
        MelonLogger.Msg("FREEDOM_ARROW_VERSION_LABEL installed: "+instance.Info.Version);
    }
    public static void MusicTypeAfter(MusicType musicType){menuMusicType=(int)musicType;}
    static void DrawVersionLabel()
    {
        if(versionOff||Event.current.type!=EventType.Repaint||menuMusicType is not (2 or 20 or 30 or 100))return;
        try
        {
            int size=Math.Max(12,Screen.height/60);
            if(versionStyle==null||versionStyle.fontSize!=size)versionStyle=new GUIStyle(GUI.skin.label){fontSize=size,alignment=TextAnchor.LowerCenter};
            GUI.Label(new Rect(0,0,Screen.width,Screen.height-10),"Freedom Arrow "+instance.Info.Version,versionStyle);
        }
        catch(Exception e){versionOff=true;MelonLogger.Error("FREEDOM_ARROW_VERSION_LABEL_FAILED: off for this session. "+e.Message);}
    }
}

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
    static GUIStyle versionStyle,noticeStyle;
    static bool versionOff;
    static void InstallVersionLabel()
    {
        Patch(typeof(Il2Cpp.MusicService),"PlayByType",null,nameof(MusicTypeAfter));
        MelonLogger.Msg("FREEDOM_ARROW_VERSION_LABEL installed; uses verified loaded package identity");
    }
    public static void MusicTypeAfter(MusicType musicType){menuMusicType=(int)musicType;}
    static void DrawVersionLabel()
    {
        if(versionOff||Event.current.type!=EventType.Repaint||menuMusicType is not (2 or 20 or 30 or 100))return;
        try
        {
            int size=Math.Max(12,Screen.height/60);
            if(versionStyle==null||versionStyle.fontSize!=size)versionStyle=new GUIStyle(GUI.skin.label){fontSize=size,alignment=TextAnchor.LowerCenter};
            GUI.Label(new Rect(0,0,Screen.width,Screen.height-10),FreedomArrow.Runtime.DisplayLabel,versionStyle);
            // Osama 21 Nov 2026: tell players on an old version to update through the launcher (runtime-qa/UpdateNotice.cs).
            if(FreedomArrow.UpdateNotice.Text is string notice)
            {
                int big=Math.Max(16,Screen.height/40);
                if(noticeStyle==null||noticeStyle.fontSize!=big)noticeStyle=new GUIStyle(GUI.skin.label){fontSize=big,fontStyle=FontStyle.Bold,alignment=TextAnchor.LowerCenter};
                var r=new Rect(0,0,Screen.width,Screen.height-10-size*2);
                GUI.contentColor=Color.black;GUI.Label(new Rect(r.x+2,r.y+2,r.width,r.height),notice,noticeStyle);
                GUI.contentColor=new Color(1f,0.82f,0.2f);GUI.Label(r,notice,noticeStyle);
                GUI.contentColor=Color.white;
            }
        }
        catch(Exception e){versionOff=true;MelonLogger.Error("FREEDOM_ARROW_VERSION_LABEL_FAILED: off for this session. "+e.Message);}
    }
}

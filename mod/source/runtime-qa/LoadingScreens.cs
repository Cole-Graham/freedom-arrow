using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.UI;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;
// Freedom Arrow loading screens (Osama 18 Nov 2026, thread 1572407822849810463: "I want to replace ALL loading screens", "I want to remove the
// vanilla loading screens"). The game picks the loading background in SceneTransitionDecorConfig.GetRandomBackground (one native caller,
// SceneTransition.Load). This postfix returns one of our pictures instead: every UserData/FreedomArrow/loading/*.png (2048x857, the vanilla size,
// with the vanilla side fade baked in), random, never the same one twice in a row. The vanilla pictures are never shown while at least one of ours
// loads. If the folder is empty or every picture fails, the game keeps its own picture (logged).
static class LoadingScreens
{
    static readonly List<Sprite> sprites=new();static readonly System.Random rng=new();static int last=-1,logs;
    public static void Install(HarmonyLib.Harmony harmony,string root)
    {
        var dir=Path.Combine(root,"loading");
        var files=Directory.Exists(dir)?Directory.GetFiles(dir,"*.png").OrderBy(f=>f).ToArray():Array.Empty<string>();
        foreach(var f in files)
        {
            try
            {
                var t=new Texture2D(2,2,TextureFormat.RGBA32,false){name=Path.GetFileNameWithoutExtension(f),wrapMode=TextureWrapMode.Clamp};
                if(!ImageConversion.LoadImage(t,(Il2CppStructArray<byte>)File.ReadAllBytes(f),true))throw new InvalidDataException("did not decode");
                t.hideFlags=HideFlags.HideAndDontSave;
                var s=Sprite.Create(t,new Rect(0,0,t.width,t.height),new Vector2(.5f,.5f),100f);s.name=t.name;s.hideFlags=HideFlags.HideAndDontSave;sprites.Add(s);
            }
            catch(Exception e){MelonLogger.Error($"FREEDOM_ARROW_LOADING_SCREEN_BAD {Path.GetFileName(f)}: {e.Message}");}
        }
        if(sprites.Count==0){MelonLogger.Msg($"FREEDOM_ARROW_LOADING_SCREENS none in {dir}; vanilla loading screens stay");return;}
        harmony.Patch(AccessTools.Method(typeof(SceneTransitionDecorConfig),nameof(SceneTransitionDecorConfig.GetRandomBackground)),postfix:new HarmonyMethod(typeof(LoadingScreens),nameof(After)));
        MelonLogger.Msg($"FREEDOM_ARROW_LOADING_SCREENS installed: {sprites.Count} picture(s), vanilla pictures off");
        DiagnosticLog.Write("loading_screens_installed",new{count=sprites.Count,files=files.Select(Path.GetFileName).ToArray()});
    }
    static void After(ref Sprite __result)
    {
        try
        {
            int i;if(sprites.Count==1||last<0)i=rng.Next(sprites.Count);else{i=rng.Next(sprites.Count-1);if(i>=last)i++;}   // never the same picture twice in a row
            last=i;__result=sprites[i];
            if(logs++<20)MelonLogger.Msg($"FREEDOM_ARROW_LOADING_SCREEN {sprites[i].name}");
        }
        catch(Exception e){if(logs++<20)MelonLogger.Error("FREEDOM_ARROW_LOADING_SCREEN_FAILED: vanilla picture used. "+e.Message);}
    }
}

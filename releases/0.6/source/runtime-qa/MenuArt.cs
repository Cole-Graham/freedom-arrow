using System.Text.Json;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using Il2CppPlugins.GalaxyUI.Runtime;
using MelonLoader;
using UnityEngine;
using UnityEngine.UI;
namespace FreedomArrow;
// Freedom Arrow title screen (Osama 18 Nov 2026 03:1x PST, thread 1567745029781454889: "finalize this image as our main menu, you break it up into
// various layers, add the freedom arrow logo that's in broken arrow's style ... make sure the parallax effect works"). The "Press any key" screen
// is the game's UiParallax on EntryPointLogicLoader/StartParalax/Start screen/Parallax Keyart: a static Background image plus 24 layers (a1..a11,
// s1..s4, ef*, ground, logo, abrams, stones) that each move toward the mouse within their LimitPosition. We keep the component and its motion and
// only swap the pictures: menu-art/menu-art.json maps layer names to our PNGs, sizes, positions (1920x1080 canvas units, centre origin) and limits;
// every other layer is switched off. Each layer's _startPosition is reset after the move, because ParallaxLayer.OnScreenUpdate places the layer at
// _startPosition + offset. No game files change; with no menu-art folder the vanilla screen stays. Finds the object by name at most twice a second,
// and only in the first 90 s after a scene loads, never in battle (the object only exists on the start screen).
static class MenuArt
{
    sealed class LayerSpec { public string image=""; public float w,h,x,y; public float[] limit=new float[2]; public float[] rot=new float[2]; }
    sealed class Spec { public string background=""; public Dictionary<string,LayerSpec> layers=new(); public bool hide_other_layers=true; public string[] hide_paths=Array.Empty<string>(); public string[] order=Array.Empty<string>(); }
    static Spec spec; static readonly Dictionary<string,Sprite> sprites=new(); static string dir;
    static float deadline=-1, nextTry; static int applied; static IntPtr appliedTo;
    public static void Install(string root)
    {
        dir=Path.Combine(root,"menu-art");var json=Path.Combine(dir,"menu-art.json");
        if(!File.Exists(json)){MelonLogger.Msg("FREEDOM_ARROW_MENU_ART none; vanilla start screen stays");return;}
        spec=JsonSerializer.Deserialize<Spec>(File.ReadAllText(json),new JsonSerializerOptions{IncludeFields=true})!;
        foreach(var name in spec.layers.Values.Select(l=>l.image).Append(spec.background).Where(n=>n.Length>0).Distinct())
        {
            var f=Path.Combine(dir,name);
            var t=new Texture2D(2,2,TextureFormat.RGBA32,false){name="FA_"+Path.GetFileNameWithoutExtension(f),wrapMode=TextureWrapMode.Clamp};
            if(!ImageConversion.LoadImage(t,(Il2CppStructArray<byte>)File.ReadAllBytes(f),true))throw new InvalidDataException(name+" did not decode");
            t.hideFlags=HideFlags.HideAndDontSave;
            var s=Sprite.Create(t,new Rect(0,0,t.width,t.height),new Vector2(.5f,.5f),100f);s.name=t.name;s.hideFlags=HideFlags.HideAndDontSave;sprites[name]=s;
        }
        deadline=Time.realtimeSinceStartup+90;
        MelonLogger.Msg($"FREEDOM_ARROW_MENU_ART loaded: {sprites.Count} picture(s), {spec.layers.Count} layer(s)");
    }
    public static void SceneChanged(){ if(spec!=null)deadline=Time.realtimeSinceStartup+90; }
    public static void Tick()
    {
        if(spec==null||deadline<0)return;
        float now=Time.realtimeSinceStartup;if(now>deadline||now<nextTry)return;nextTry=now+0.5f;
        try
        {
            var go=GameObject.Find("Parallax Keyart");if(go==null||go.Pointer==appliedTo)return;
            var px=go.GetComponent<UiParallax>();if(px==null)return;
            Apply(go,px);appliedTo=go.Pointer;deadline=-1;
        }
        catch(Exception e){MelonLogger.Error("FREEDOM_ARROW_MENU_ART_FAILED: vanilla start screen. "+e);deadline=-1;}
    }
    static void Apply(GameObject root,UiParallax px)
    {
        var bg=root.transform.Find("Background");
        if(bg!=null&&spec.background.Length>0)
        {
            var img=bg.GetComponent<Image>();var rt=bg.GetComponent<RectTransform>();
            img.sprite=sprites[spec.background];img.color=Color.white;img.preserveAspect=false;
            rt.anchorMin=Vector2.zero;rt.anchorMax=Vector2.one;rt.offsetMin=Vector2.zero;rt.offsetMax=Vector2.zero;bg.SetSiblingIndex(0);
        }
        var layers=px._layers;int used=0,hidden=0,order=1;
        var byName=new Dictionary<string,ParallaxLayer>();
        for(int i=0;i<layers.Length;i++){var l=layers[i];if(l?.Layer!=null)byName[l.Layer.gameObject.name]=l;}
        foreach(var (name,l) in byName)
        {
            var t=l.Layer;
            if(!spec.layers.TryGetValue(name,out var s)){if(spec.hide_other_layers){t.gameObject.SetActive(false);hidden++;}continue;}
            var img=t.GetComponent<Image>()??t.gameObject.AddComponent<Image>();
            img.sprite=sprites[s.image];img.color=Color.white;img.preserveAspect=false;img.raycastTarget=false;
            for(int c=0;c<t.childCount;c++)t.GetChild(c).gameObject.SetActive(false);
            var rt=t.Cast<RectTransform>();rt.anchorMin=rt.anchorMax=new Vector2(.5f,.5f);rt.pivot=new Vector2(.5f,.5f);
            rt.sizeDelta=new Vector2(s.w,s.h);rt.anchoredPosition=new Vector2(s.x,s.y);rt.localRotation=Quaternion.identity;rt.localScale=Vector3.one;
            l.LimitPosition=new Vector2(s.limit[0],s.limit[1]);l.RotationLimit=new Vector2(s.rot[0],s.rot[1]);l._startPosition=rt.localPosition;
            t.gameObject.SetActive(true);used++;
        }
        // Start-screen UI the game draws over the art, by path under "Start screen". GameObject/bg is the dark 611 px "menu news bg" bar behind
        // "Press any key": made for the bright vanilla sunset, it shows as a grey haze over our night scene (Osama 18 Nov 10:0x: "why is there a glow").
        int off=0;var screen=root.transform.parent;
        foreach(var path in spec.hide_paths){var h=screen!=null?screen.Find(path):null;if(h!=null){h.gameObject.SetActive(false);off++;}else MelonLogger.Warning("FREEDOM_ARROW_MENU_ART hide path not found: "+path);}
        // Draw order back to front: menu-art.json "order" (Osama 18 Nov 10:4x: the hill with the soldiers as its own parallax layer, in front of
        // the aircraft and behind the title); older files without it keep ground, a1, logo.
        foreach(var name in spec.order.Length>0?spec.order:new[]{"ground","a1","logo"})if(byName.TryGetValue(name,out var l)&&spec.layers.ContainsKey(name))l.Layer.SetSiblingIndex(order++);
        applied++;
        MelonLogger.Msg($"FREEDOM_ARROW_MENU_ART applied: {used} layer(s) ours, {hidden} vanilla layer(s) off, background {(bg!=null?"ours":"not found")}, {off} screen element(s) hidden");
        DiagnosticLog.Write("menu_art_applied",new{used,hidden,background=bg!=null});
    }
}

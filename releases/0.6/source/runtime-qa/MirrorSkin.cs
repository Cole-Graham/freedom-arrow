using System.Text.Json.Nodes;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.Spawn;
using Il2CppBrokenArrow.DataBase.Models;
using Il2CppBrokenArrow.Shared.Ecs.MemoryController;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;
// Mirror-finish skin chosen by a loadout option (Osama 16 Nov 2026, F-22 "symbiote" / Vanguard Edition: "all the white areas, we turn into a
// mirror finish and leave the rest ... +20 point stealth coating loadout option"). The game's unit shader (Shader Graphs/UnitV3) has a mask-map
// slot (Layer_4C4561B0) that the F-22 materials leave empty, so the shader uses its default white mask everywhere. For a unit whose current
// options include the configured option, every renderer material whose name starts with the configured prefix is replaced by a copy with the
// configured albedo (the Vanguard skin) and a mask that is mirror in the white paint only; the material floats in the config scale the mask.
// UserData/FreedomArrow/mirror-skins.json; edits are read again while the game runs (every 2 s), for tuning.
static class MirrorSkin
{
    sealed class Entry
    {
        public string unit="",prefix="",albedo="",mask="";public string[] options=Array.Empty<string>(),exclude=Array.Empty<string>();
        public Dictionary<string,float> floats=new();public bool all;
    }
    sealed class View{public GameObject root=null!;public Units data=null!;public Entry e=null!;public bool on;public float until;public Dictionary<IntPtr,Material[]> orig=new();}
    static string dir="";static List<Entry> entries=new();static DateTime stamp;static float nextLoad,nextTick;static int logs;
    static readonly List<View> views=new();static readonly Dictionary<string,Texture2D> texs=new();static readonly Dictionary<(Entry,IntPtr),Material> mats=new();
    public static void Install(HarmonyLib.Harmony harmony,string root)
    {
        dir=root;Load();if(entries.Count==0&&!File.Exists(Path.Combine(dir,"mirror-skins.json")))return;
        var m=typeof(UnitBuilder).GetMethods().First(x=>x.Name=="InitView"&&x.GetParameters().Length==4&&x.GetParameters()[1].ParameterType==typeof(Units));
        harmony.Patch(m,postfix:new HarmonyMethod(typeof(MirrorSkin),nameof(After)));
        MelonLogger.Msg($"FREEDOM_ARROW_MIRROR_SKIN installed: {entries.Count} skin(s)");DiagnosticLog.Write("mirror_skin_installed",new{skins=entries.Select(e=>new{e.unit,e.options,e.all}).ToArray()});
    }
    static void Load()
    {
        var f=Path.Combine(dir,"mirror-skins.json");if(!File.Exists(f)){entries=new();return;}
        var t=File.GetLastWriteTimeUtc(f);if(t==stamp)return;stamp=t;
        var list=new List<Entry>();
        foreach(var n in JsonNode.Parse(File.ReadAllText(f))!["skins"]!.AsArray())
        {
            var e=new Entry{unit=(string)n!["unit"]!,prefix=(string)n["prefix"]!,albedo=(string?)n["albedo"]??"",mask=(string)n["mask"]!,all=(bool?)n["all"]??false};
            e.options=n["options"]?.AsArray().Select(x=>(string)x!).ToArray()??Array.Empty<string>();
            e.exclude=n["exclude"]?.AsArray().Select(x=>(string)x!).ToArray()??Array.Empty<string>();
            if(n["floats"] is JsonObject fl)foreach(var kv in fl)e.floats[kv.Key]=(float)kv.Value!;
            list.Add(e);
        }
        entries=list;texs.Clear();mats.Clear();
        foreach(var v in views)v.e=entries.FirstOrDefault(e=>e.unit==v.e.unit)??v.e;
        foreach(var v in views)if(v.on){Restore(v);v.on=false;}
        if(logs++<20)DiagnosticLog.Write("mirror_skin_config",new{skins=list.Count});
    }
    static void After(UnitModelInfo unitModel,Units unitData,IUnitLoadScope scope)
    {
        try
        {
            if(unitData==null||unitModel?.PrefabRootScript==null)return;
            var e=entries.FirstOrDefault(x=>x.unit==unitData.Name);if(e==null)return;
            views.Add(new View{root=unitModel.PrefabRootScript.gameObject,data=unitData,e=e,until=Time.realtimeSinceStartup+5f});
        }
        catch(Exception x){if(logs++<20)DiagnosticLog.Write("mirror_skin_failed",new{where="hook",error=x.Message});}
    }
    static bool Wants(View v)
    {
        if(v.e.all)return true;
        var o=v.data.CurrentOptions;if(o==null)return false;
        for(int i=0;i<o.Count;i++){var x=o[i];if(x!=null&&(v.e.options.Contains(x.Name)||v.e.options.Contains(x.Id.ToString())))return true;}
        return false;
    }
    public static void Tick()
    {
        if(views.Count==0&&entries.Count==0)return;
        float now=Time.realtimeSinceStartup;
        if(now>nextLoad){nextLoad=now+2f;try{Load();}catch(Exception x){if(logs++<20)DiagnosticLog.Write("mirror_skin_failed",new{where="config",error=x.Message});}}
        if(now<nextTick)return;nextTick=now+0.25f;
        for(int i=views.Count-1;i>=0;i--)
        {
            var v=views[i];
            try
            {
                if(v.root==null||!v.root){views.RemoveAt(i);continue;}
                bool want=Wants(v);
                // Late renderers (LODs, gear, bays) appear after InitView: keep applying for the first 5 s.
                if(want&&(!v.on||now<v.until)){Apply(v);v.on=true;}
                else if(!want&&v.on){Restore(v);v.on=false;}
            }
            catch(Exception x){views.RemoveAt(i);if(logs++<20)DiagnosticLog.Write("mirror_skin_failed",new{where="tick",error=x.Message});}
        }
    }
    static Texture2D Tex(string png,bool linear)
    {
        string key=png+(linear?":lin":"");if(texs.TryGetValue(key,out var t)&&t)return t;
        t=new Texture2D(2,2,TextureFormat.RGBA32,true,linear){name="FA_"+png,wrapMode=TextureWrapMode.Repeat,filterMode=FilterMode.Trilinear,anisoLevel=4,hideFlags=HideFlags.HideAndDontSave};
        if(!ImageConversion.LoadImage(t,(Il2CppStructArray<byte>)File.ReadAllBytes(Path.Combine(dir,png)),true))throw new InvalidDataException(png);
        return texs[key]=t;
    }
    static void Apply(View v)
    {
        int swapped=0;
        foreach(var r in v.root.GetComponentsInChildren<Renderer>(true))
        {
            var ms=r.sharedMaterials;bool any=false;
            for(int k=0;k<ms.Length;k++)
            {
                var m=ms[k];if(m==null)continue;string n=m.name;
                if(!n.StartsWith(v.e.prefix)||v.e.exclude.Any(x=>n.Contains(x))||n.StartsWith("FA_MIRROR"))continue;
                if(!mats.TryGetValue((v.e,m.Pointer),out var c)||!c)
                {
                    c=new Material(m){name="FA_MIRROR "+n,hideFlags=HideFlags.HideAndDontSave};
                    if(v.e.albedo!="")c.SetTexture("Layer_A97CDC25",Tex(v.e.albedo,false));
                    c.SetTexture("Layer_4C4561B0",Tex(v.e.mask,true));
                    foreach(var kv in v.e.floats)c.SetFloat(kv.Key,kv.Value);
                    mats[(v.e,m.Pointer)]=c;
                }
                if(!v.orig.ContainsKey(r.Pointer))v.orig[r.Pointer]=r.sharedMaterials;
                ms[k]=c;any=true;swapped++;
            }
            if(any)r.sharedMaterials=ms;
        }
        if(swapped>0&&logs++<200)DiagnosticLog.Write("mirror_skin_applied",new{unit=v.data.Name,id=v.data.Id,materials=swapped});
    }
    static void Restore(View v)
    {
        if(v.root==null||!v.root)return;
        foreach(var r in v.root.GetComponentsInChildren<Renderer>(true))if(v.orig.TryGetValue(r.Pointer,out var o))r.sharedMaterials=o;
        v.orig.Clear();if(logs++<200)DiagnosticLog.Write("mirror_skin_restored",new{unit=v.data.Name,id=v.data.Id});
    }
}

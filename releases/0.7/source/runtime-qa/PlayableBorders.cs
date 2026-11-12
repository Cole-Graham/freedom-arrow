using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.Controllers;
using Il2CppInterop.Runtime;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using MelonLoader;
using UnityEngine;
using UnityEngine.Rendering;
namespace FreedomArrow;

// Draw the native active play area (PlayZoneBounds, including ResetToFull and scripted switches) as a line in the 3D scene.
// lat.21 drew a screen overlay; Lateralus found it aliased and drawn over trees, units and the HUD, and asked for a plain,
// slightly transparent white line (12 November 2026). lat.22 renders a camera-facing strip of constant screen width with a
// copy of the objective-border material (ObjZone_Border: HDRP/Unlit, transparent, depth test LessEqual), so terrain, trees
// and units hide it, the HUD covers it, and a soft-edged texture smooths its edges.
// It changes no bounds, native materials, objective outlines, orders or collision.
internal static class PlayableBorders
{
    const float Spacing=10,Pixels=4,RetrySeconds=5;
    const int MaxSteps=1024;
    const string SourceMaterial="ObjZone_Border";
    static readonly Color LineColor=new(1,1,1,.8f);
    static PlayableZone zone;
    static Bounds cached;
    static Vector3[][] edges=Array.Empty<Vector3[]>();
    static float next,nextSearch;
    static bool off,waitLogged,searchLogged;
    static Material material;
    static Texture2D texture;
    static int layer;
    static GameObject strip;
    static Mesh mesh;
    static Il2CppStructArray<Vector3> vertices;
    static System.Numerics.Vector3[] points=Array.Empty<System.Numerics.Vector3>(),ribbon=Array.Empty<System.Numerics.Vector3>();
    static Vector3 lastEye;
    static float lastPixel;
    public static void Install(HarmonyLib.Harmony h)
    {
        // lat.18-20 hooked the PlayableZone constructor. GameAssembly has no direct call to it (the
        // constructor is inlined), so the hook never ran and nothing was drawn (Lateralus, 12 November 2026).
        // These methods have direct native callers: the minimap subscribes at mission load
        // (MiniMapBehaviour.OnMissionLoaded), and the scenario script switches zones with SetPlayZone.
        // ContainsForPlayer is not used: target search calls it often.
        var seen=new HarmonyMethod(typeof(PlayableBorders),nameof(Seen));
        foreach(var name in new[]{"add_OnZoneBoundsChanged","SetPlayZone"})
            h.Patch(AccessTools.Method(typeof(PlayableZone),name)??throw new MissingMethodException("PlayableZone."+name),postfix:seen);
        h.Patch(AccessTools.Method(typeof(GameController),nameof(GameController.Dispose)),
            prefix:new HarmonyMethod(typeof(PlayableBorders),nameof(Disposed)));
        DiagnosticLog.Write("playable_borders_installed",new{pixels=Pixels,alpha=LineColor.a,sampleSpacing=Spacing,maxSamplesPerEdge=MaxSteps+1,material=SourceMaterial,
            hooks="add_OnZoneBoundsChanged,SetPlayZone"});
    }
    static void Seen(PlayableZone __instance)
    {
        if(zone!=null&&zone.Pointer==__instance.Pointer)return;
        zone=__instance;edges=Array.Empty<Vector3[]>();next=0;off=false;waitLogged=false;
        DiagnosticLog.Write("playable_borders_zone",new{});
    }
    static void Disposed(){Clear();}
    public static void Clear(){zone=null;edges=Array.Empty<Vector3[]>();DestroyStrip();}
    public static void SceneChanged(){edges=Array.Empty<Vector3[]>();next=0;DestroyStrip();}
    static void DestroyStrip()
    {
        if(strip!=null)UnityEngine.Object.Destroy(strip);
        if(mesh!=null)UnityEngine.Object.Destroy(mesh);
        strip=null;mesh=null;vertices=null;
    }
    static bool Active=>!off&&Runtime.IsApplied&&zone!=null&&!zone.WasCollected&&GameController.IsInstanceAlive
        &&!GameController.Instance._disposed;
    // Camera.main needs the MainCamera tag. Otherwise use the enabled screen camera with the highest depth.
    static Camera View()
    {
        var main=Camera.main;if(main!=null)return main;
        Camera best=null;
        foreach(var c in Camera.allCameras)
            if(c!=null&&c.isActiveAndEnabled&&c.targetTexture==null&&(best==null||c.depth>best.depth))best=c;
        return best;
    }
    public static void Update()
    {
        try
        {
            if(!Active){Hide();return;}
            if(Time.unscaledTime>=next){next=Time.unscaledTime+.5f;Sample();}
            if(edges.Length==0||strip==null){Hide();return;}
            Render();
        }
        catch(Exception e){Fail(e);}
    }
    static void Hide(){if(strip!=null&&strip.activeSelf)strip.SetActive(false);}
    static void Sample()
    {
        var game=GameController.Instance;
        if(game.MapMetaData==null||game.MapSettings==null||View()==null)
        {
            if(!waitLogged){waitLogged=true;DiagnosticLog.Write("playable_borders_waiting",new{metadata=game.MapMetaData!=null,settings=game.MapSettings!=null,camera=View()!=null});}
            return;
        }
        if(!EnsureMaterial())return;
        var bounds=zone.PlayZoneBounds;
        if(edges.Length!=0&&bounds==cached&&strip!=null)return;
        var lo=bounds.min;var hi=bounds.max;
        if(!float.IsFinite(lo.x)||!float.IsFinite(lo.z)||!float.IsFinite(hi.x)||!float.IsFinite(hi.z)
            ||hi.x-lo.x<1||hi.z-lo.z<1) {edges=Array.Empty<Vector3[]>();return;}
        var corners=new[]{new Vector3(lo.x,0,lo.z),new Vector3(hi.x,0,lo.z),new Vector3(hi.x,0,hi.z),new Vector3(lo.x,0,hi.z)};
        var sampled=new Vector3[4][];
        for(int edge=0;edge<4;edge++)
        {
            var a=corners[edge];var b=corners[(edge+1)%4];
            int steps=Math.Clamp((int)Math.Ceiling(Vector3.Distance(a,b)/Spacing),1,MaxSteps);
            var line=new Vector3[steps+1];
            for(int i=0;i<=steps;i++)
            {
                var p=Vector3.Lerp(a,b,(float)i/steps);
                // This native API returns height by value/out parameter. Do not use the
                // generated GetPixelSafe proxy: its native ref MapPixel is not a boxed object.
                var query=new Vector3(p.x,game.MapMetaData.MaxMapHeight+100,p.z);
                game.MapMetaData.GetTerrainAtHeight(ref query,out var terrain,out float y);
                if(!float.IsFinite(y))throw new InvalidDataException("Non-finite border height");
                p.y=y;line[i]=p;
            }
            sampled[edge]=line;
        }
        cached=bounds;edges=sampled;BuildStrip(lo,hi);
        var view=View();
        DiagnosticLog.Write("playable_borders_bounds",new{minX=lo.x,minZ=lo.z,maxX=hi.x,maxZ=hi.z,samples=edges.Sum(e=>e.Length),camera=view.name,mainTag=Camera.main!=null});
    }
    // The objective-border material is loaded with the scenario's objectives. Search again every few seconds until it is.
    static bool EnsureMaterial()
    {
        if(material!=null&&texture!=null)return true;
        if(Time.unscaledTime<nextSearch)return false;
        nextSearch=Time.unscaledTime+RetrySeconds;
        Material source=null;
        foreach(var o in Resources.FindObjectsOfTypeAll(Il2CppType.Of<Material>()))
        {
            var m=o.TryCast<Material>();
            if(m!=null&&m.name==SourceMaterial&&m.shader!=null&&m.shader.name=="HDRP/Unlit"){source=m;break;}
        }
        if(source==null)
        {
            if(!searchLogged){searchLogged=true;DiagnosticLog.Write("playable_borders_waiting",new{material=SourceMaterial});}
            return false;
        }
        layer=0;
        foreach(var o in Resources.FindObjectsOfTypeAll(Il2CppType.Of<Renderer>()))
        {
            var r=o.TryCast<Renderer>();
            if(r!=null&&r.sharedMaterial!=null&&r.sharedMaterial.name==SourceMaterial&&r.gameObject.scene.IsValid()){layer=r.gameObject.layer;break;}
        }
        // Alpha across the strip: opaque in the middle 60%, smooth fall to zero at both edges.
        texture=new Texture2D(1,32,TextureFormat.RGBA32,false,true){wrapMode=TextureWrapMode.Clamp,filterMode=FilterMode.Bilinear,hideFlags=HideFlags.HideAndDontSave};
        for(int y=0;y<32;y++)
        {
            float edge=Math.Clamp((.5f-Math.Abs((y+.5f)/32-.5f))/.2f,0,1);
            texture.SetPixel(0,y,new Color(1,1,1,edge*edge*(3-2*edge)));
        }
        texture.Apply(false);
        material=new Material(source){hideFlags=HideFlags.HideAndDontSave,name="FreedomArrow playable border"};
        material.SetTexture("_UnlitColorMap",texture);material.SetTexture("_MainTex",texture);
        material.SetColor("_UnlitColor",LineColor);
        material.SetFloat("_CullMode",0);material.SetFloat("_CullModeForward",0);
        DiagnosticLog.Write("playable_borders_material",new{source=SourceMaterial,shader=material.shader.name,queue=material.renderQueue,layer});
        return true;
    }
    static void BuildStrip(Vector3 lo,Vector3 hi)
    {
        DestroyStrip();
        int count=edges.Sum(e=>e.Length);
        var uv=new Il2CppStructArray<Vector2>(2*count);
        var triangles=new Il2CppStructArray<int>(6*(count-edges.Length));
        float low=float.MaxValue,high=float.MinValue;
        int v=0,t=0;
        foreach(var line in edges)
        {
            for(int i=0;i<line.Length;i++)
            {
                uv[v+2*i]=new Vector2(0,0);uv[v+2*i+1]=new Vector2(0,1);
                low=Math.Min(low,line[i].y);high=Math.Max(high,line[i].y);
                if(i==0)continue;
                int a=v+2*i-2;
                triangles[t++]=a;triangles[t++]=a+1;triangles[t++]=a+2;
                triangles[t++]=a+1;triangles[t++]=a+3;triangles[t++]=a+2;
            }
            v+=2*line.Length;
        }
        points=new System.Numerics.Vector3[count];ribbon=new System.Numerics.Vector3[2*count];
        vertices=new Il2CppStructArray<Vector3>(2*count);
        mesh=new Mesh{hideFlags=HideFlags.HideAndDontSave,name="FreedomArrow playable border"};
        mesh.MarkDynamic();
        mesh.vertices=vertices;mesh.uv=uv;mesh.triangles=triangles;
        // Fixed bounds: the strip moves with the camera, but stays within the play area and a margin above its terrain.
        mesh.bounds=new Bounds((lo+hi)/2+new Vector3(0,(low+high)/2,0),new Vector3(hi.x-lo.x+200,high-low+2000,hi.z-lo.z+200));
        strip=new GameObject("FreedomArrow playable border"){layer=layer};
        strip.AddComponent<MeshFilter>().sharedMesh=mesh;
        var renderer=strip.AddComponent<MeshRenderer>();
        renderer.sharedMaterial=material;
        renderer.shadowCastingMode=ShadowCastingMode.Off;renderer.receiveShadows=false;
        renderer.motionVectorGenerationMode=MotionVectorGenerationMode.ForceNoMotion;
        renderer.lightProbeUsage=LightProbeUsage.Off;renderer.reflectionProbeUsage=ReflectionProbeUsage.Off;
        lastPixel=-1;
    }
    // Rebuild the strip only when the camera position or the pixel size changes.
    static void Render()
    {
        var camera=View();if(camera==null){Hide();return;}
        var eye=camera.transform.position;
        float pixel=2*MathF.Tan(camera.fieldOfView*Mathf.Deg2Rad/2)/Math.Max(1,camera.pixelHeight);
        if(!strip.activeSelf)strip.SetActive(true);
        if(eye==lastEye&&pixel==lastPixel)return;
        lastEye=eye;lastPixel=pixel;
        var e=new System.Numerics.Vector3(eye.x,eye.y,eye.z);
        int start=0;
        foreach(var line in edges)
        {
            for(int i=0;i<line.Length;i++)points[start+i]=new(line[i].x,line[i].y,line[i].z);
            BorderGeometry.Ribbon(points.AsSpan(start,line.Length),e,pixel,Pixels,ribbon.AsSpan(2*start,2*line.Length));
            start+=line.Length;
        }
        for(int i=0;i<ribbon.Length;i++)vertices[i]=new Vector3(ribbon[i].X,ribbon[i].Y,ribbon[i].Z);
        mesh.vertices=vertices;
    }
    static void Fail(Exception e)
    {
        off=true;edges=Array.Empty<Vector3[]>();
        try{DestroyStrip();}catch{}
        DiagnosticLog.Write("playable_borders_failed",new{error=e.ToString()});
        MelonLogger.Warning("FREEDOM_ARROW_PLAYABLE_BORDERS_FAILED: "+e.Message);
    }
}

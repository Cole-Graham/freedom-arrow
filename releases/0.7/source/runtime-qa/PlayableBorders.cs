using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.Controllers;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;

// Read the native active bounds, including ResetToFull and scripted zone switches.
// A screen overlay keeps its width and contrast when zooming/looking straight down.
// It changes no bounds, materials, objective outlines, orders or collision.
internal static class PlayableBorders
{
    static PlayableZone zone;
    static Bounds cached;
    static Vector3[][] edges=Array.Empty<Vector3[]>();
    static float next;
    static bool off,waitLogged;
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
        DiagnosticLog.Write("playable_borders_installed",new{innerPixels=3,outlinePixels=7,sampleSpacing=50,maxSamplesPerEdge=192,
            hooks="add_OnZoneBoundsChanged,SetPlayZone"});
    }
    static void Seen(PlayableZone __instance)
    {
        if(zone!=null&&zone.Pointer==__instance.Pointer)return;
        zone=__instance;edges=Array.Empty<Vector3[]>();next=0;off=false;waitLogged=false;
        DiagnosticLog.Write("playable_borders_zone",new{});
    }
    static void Disposed(){Clear();}
    public static void Clear(){zone=null;edges=Array.Empty<Vector3[]>();}
    public static void SceneChanged(){edges=Array.Empty<Vector3[]>();next=0;}
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
            if(!Active||Time.unscaledTime<next)return;
            next=Time.unscaledTime+.5f;
            var game=GameController.Instance;
            if(game.MapMetaData==null||game.MapSettings==null||View()==null)
            {
                if(!waitLogged){waitLogged=true;DiagnosticLog.Write("playable_borders_waiting",new{metadata=game.MapMetaData!=null,settings=game.MapSettings!=null,camera=View()!=null});}
                return;
            }
            var bounds=zone.PlayZoneBounds;
            if(edges.Length!=0&&bounds==cached)return;
            var lo=bounds.min;var hi=bounds.max;
            if(!float.IsFinite(lo.x)||!float.IsFinite(lo.z)||!float.IsFinite(hi.x)||!float.IsFinite(hi.z)
                ||hi.x-lo.x<1||hi.z-lo.z<1) {edges=Array.Empty<Vector3[]>();return;}
            var corners=new[]{new Vector3(lo.x,0,lo.z),new Vector3(hi.x,0,lo.z),new Vector3(hi.x,0,hi.z),new Vector3(lo.x,0,hi.z)};
            var sampled=new Vector3[4][];
            for(int edge=0;edge<4;edge++)
            {
                var a=corners[edge];var b=corners[(edge+1)%4];
                int steps=Math.Clamp((int)Math.Ceiling(Vector3.Distance(a,b)/50),1,191);
                var points=new Vector3[steps+1];
                for(int i=0;i<=steps;i++)
                {
                    var p=Vector3.Lerp(a,b,(float)i/steps);
                    // This native API returns height by value/out parameter. Do not use the
                    // generated GetPixelSafe proxy: its native ref MapPixel is not a boxed object.
                    var query=new Vector3(p.x,game.MapMetaData.MaxMapHeight+100,p.z);
                    game.MapMetaData.GetTerrainAtHeight(ref query,out var terrain,out float y);
                    if(!float.IsFinite(y))throw new InvalidDataException("Non-finite border height");
                    p.y=y+1;points[i]=p;
                }
                sampled[edge]=points;
            }
            cached=bounds;edges=sampled;
            var view=View();
            DiagnosticLog.Write("playable_borders_bounds",new{minX=lo.x,minZ=lo.z,maxX=hi.x,maxZ=hi.z,samples=edges.Sum(e=>e.Length),camera=view.name,mainTag=Camera.main!=null});
        }
        catch(Exception e){Fail(e);}
    }
    public static void Draw()
    {
        if(Event.current?.type!=EventType.Repaint)return;
        try
        {
            if(!Active||edges.Length==0)return;
            var camera=View();if(camera==null)return;
            var oldColor=GUI.color;var oldMatrix=GUI.matrix;int depth=GUI.depth;
            try
            {
                GUI.depth=100; // The existing HUD draws over the map border.
                foreach(var points in edges)for(int i=1;i<points.Length;i++)Segment(camera,points[i-1],points[i]);
            }
            finally {GUI.color=oldColor;GUI.matrix=oldMatrix;GUI.depth=depth;}
        }
        catch(Exception e){Fail(e);}
    }
    static void Segment(Camera camera,Vector3 a,Vector3 b)
    {
        var pa=camera.WorldToScreenPoint(a);var pb=camera.WorldToScreenPoint(b);float near=Math.Max(.01f,camera.nearClipPlane+.01f);
        if(pa.z<near&&pb.z<near)return;
        if(pa.z<near){a=Vector3.Lerp(a,b,(near-pa.z)/(pb.z-pa.z));pa=camera.WorldToScreenPoint(a);}
        if(pb.z<near){b=Vector3.Lerp(b,a,(near-pb.z)/(pa.z-pb.z));pb=camera.WorldToScreenPoint(b);}
        var rect=camera.pixelRect;
        float ax=pa.x-rect.x,ay=pa.y-rect.y,bx=pb.x-rect.x,by=pb.y-rect.y;
        if(!BorderGeometry.Clip(ref ax,ref ay,ref bx,ref by,rect.width,rect.height))return;
        ax+=rect.x;bx+=rect.x;ay=Screen.height-(ay+rect.y);by=Screen.height-(by+rect.y);
        float dx=bx-ax,dy=by-ay,len=MathF.Sqrt(dx*dx+dy*dy);if(len<.1f)return;
        var matrix=GUI.matrix;
        try
        {
            GUIUtility.RotateAroundPivot(MathF.Atan2(dy,dx)*Mathf.Rad2Deg,new Vector2(ax,ay));
            GUI.color=new Color(.05f,.025f,0,1);GUI.DrawTexture(new Rect(ax,ay-3.5f,len,7),Texture2D.whiteTexture);
            GUI.color=new Color(1,.62f,.04f,1);GUI.DrawTexture(new Rect(ax,ay-1.5f,len,3),Texture2D.whiteTexture);
        }
        finally{GUI.matrix=matrix;}
    }
    static void Fail(Exception e)
    {
        off=true;edges=Array.Empty<Vector3[]>();
        DiagnosticLog.Write("playable_borders_failed",new{error=e.ToString()});
        MelonLogger.Warning("FREEDOM_ARROW_PLAYABLE_BORDERS_FAILED: "+e.Message);
    }
}

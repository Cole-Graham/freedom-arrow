using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.UI.Labels.Components;
using Il2CppBrokenArrow.Client.Ecs.UI.Labels.Systems;
using Il2CppBrokenArrow.Client.Ecs.Utils;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppBrokenArrow.Shared.Ecs;
using Il2CppBrokenArrow.Client.Ecs.Planes.Components;
using Il2CppBrokenArrow.Client.Ecs.UI.Labels;
using Il2CppDefaultEcs;
using MelonLoader;
using UnityEngine;
using UnityEngine.UI;
namespace FreedomArrow;
// Altitude intent on plane labels (Lateralus 16 Nov 2026, thread 1571554273639006392): "if the low altitude hotkey is toggled on, the same
// indicator in a yellow color will be displayed until either the plane reaches low altitude or the player toggles the low altitude hotkey
// off"; 06:19 PST: "when a plane is transition back to high it would show the yellow version as well but with the arrow facing up ... prioritize
// displaying the current intent to transition altitude up or down, whereas displaying the actual state of being at low altitude becomes a
// secondary priority".
// Read from GameAssembly 6000.3.24f1: the label's orange arrow is LabelView.LowAltitudeIcon, switched by LabelFacade.SetLowAltitudeState from
// LabelDataComponent.IsLowAltitude (actual altitude only). The hotkey writes PlaneAltitudeSwitchComponent {IsChangePending, TargetAltitude};
// AltitudeComponent.GlobalAltitudeLevel is the current level (Ground 0, Low 1, High 2). After LabelSystem.Update, for the local player's own planes:
// ordered Low and not yet Low -> the arrow, yellow; ordered High and not yet High -> the arrow, yellow, turned to point up; otherwise the
// game's own icon (orange, shown only at low altitude) with the original colours and rotation. Display only: no orders, data or network.
static class AltitudeIntent
{
    const byte Low=1,High=2;
    static readonly Color Yellow=new(1f,0.85f,0.1f,1f);
    sealed class Saved{public GameObject Icon;public Image[] Images;public Color[] Colors;public Quaternion Rotation;}
    static readonly Dictionary<ulong,byte> intent=new();
    static readonly Dictionary<ulong,Saved> changed=new();
    static EntitySet planes;static IntPtr planesWorld;static bool on,broken,loggedDown,loggedUp;static int shown;
    public static void Install(HarmonyLib.Harmony harmony)
    {
        var m=AccessTools.Method(typeof(LabelSystem),"Update")??throw new MissingMethodException("LabelSystem.Update");
        harmony.Patch(m,postfix:new HarmonyMethod(typeof(AltitudeIntent),nameof(After)));
        on=true;
        MelonLogger.Msg("FREEDOM_ARROW_ALTITUDE_INTENT installed: own planes show a yellow altitude arrow (down or up) while an altitude change is ordered");
        DiagnosticLog.Write("altitude_intent_installed",new{hook="LabelSystem.Update postfix"});
    }
    static ulong Key(Entity e)=>System.Runtime.CompilerServices.Unsafe.As<Entity,ulong>(ref e);
    static void After(LabelSystem __instance)
    {
        if(!on||broken)return;
        try
        {
            var me=__instance._sessionContext?.CurrentPlayer;if(me==null)return;
            var world=Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems.ShootingSystem._gameContext;if(world==null||world._isDisposed)return;
            if(planesWorld!=world.Pointer)
            {
                try{planes?.Dispose();}catch{}
                planes=world.GetEntities().With<PlaneAltitudeSwitchComponent>().With<AltitudeComponent>().With<UnitLabelComponent>().With<UnitComponent>().AsSet();
                planesWorld=world.Pointer;intent.Clear();changed.Clear();
            }
            var list=planes._entities;int count=Math.Min(planes.Count,list?.Length??0);
            var seen=new HashSet<ulong>();
            for(int i=0;i<count;i++)
            {
                var e=list[i];if(!e.IsAlive)continue;ulong k=Key(e);seen.Add(k);
                var owner=NativeEcs.Read<UnitComponent>(e).Owner?.TryCast<PlayerInfo>();
                if(owner==null||owner.Pointer!=me.Pointer)continue;   // own planes only: an enemy's order must not show
                var sw=NativeEcs.ReadValue<PlaneAltitudeSwitchComponent>(e);
                byte level=NativeEcs.Field<AltitudeComponent,byte>(e,"GlobalAltitudeLevel");
                byte target=(byte)sw.TargetAltitude;
                if(sw.IsChangePending&&(target==Low||target==High))intent[k]=target;
                if(intent.TryGetValue(k,out var want)&&want==level)intent.Remove(k);
                intent.TryGetValue(k,out want);
                var facade=NativeEcs.Read<UnitLabelComponent>(e).Label;var view=facade?._label;var icon=view?.LowAltitudeIcon;
                if(icon==null)continue;
                if(want==Low||want==High)Show(k,icon,want==High,e);
                else if(changed.ContainsKey(k))Restore(k,e);
            }
            foreach(var k in changed.Keys.Where(k=>!seen.Contains(k)).ToArray()){changed.Remove(k);intent.Remove(k);}
        }
        catch(Exception x){Fail(x);}
    }
    static void Show(ulong k,GameObject icon,bool up,Entity e)
    {
        if(!changed.TryGetValue(k,out var s))
        {
            var imgs=icon.GetComponentsInChildren<Image>(true).ToArray();
            s=new Saved{Icon=icon,Images=imgs,Colors=imgs.Select(x=>x.color).ToArray(),Rotation=icon.transform.localRotation};changed[k]=s;
        }
        if(!icon.activeSelf)icon.SetActive(true);
        // Tint the coloured part (the orange disc); keep near-white/near-black parts (the arrow) as they are.
        bool any=false;
        for(int i=0;i<s.Images.Length;i++)
        {
            var c=s.Colors[i];float max=Mathf.Max(c.r,Mathf.Max(c.g,c.b)),min=Mathf.Min(c.r,Mathf.Min(c.g,c.b));
            if(max-min>0.25f){s.Images[i].color=new Color(Yellow.r,Yellow.g,Yellow.b,c.a);any=true;}
        }
        if(!any&&s.Images.Length>0)s.Images[0].color=new Color(Yellow.r,Yellow.g,Yellow.b,s.Colors[0].a);
        icon.transform.localRotation=up?s.Rotation*Quaternion.Euler(0,0,180):s.Rotation;
        shown++;
        if(up?!loggedUp:!loggedDown)
        {
            if(up)loggedUp=true;else loggedDown=true;
            DiagnosticLog.Write("altitude_intent_shown",new{direction=up?"up":"down",images=s.Images.Select((x,i)=>new{name=x.name,color=s.Colors[i].ToString()}).ToArray()});
        }
    }
    static void Restore(ulong k,Entity e)
    {
        var s=changed[k];changed.Remove(k);
        for(int i=0;i<s.Images.Length;i++)if(s.Images[i]!=null)s.Images[i].color=s.Colors[i];
        if(s.Icon==null)return;
        s.Icon.transform.localRotation=s.Rotation;
        bool low=false;
        try{low=NativeEcs.Field<LabelDataComponent,bool>(e,"IsLowAltitude");}
        catch{low=NativeEcs.Field<AltitudeComponent,byte>(e,"GlobalAltitudeLevel")==Low;}
        if(s.Icon.activeSelf!=low)s.Icon.SetActive(low);   // hand back to the game's own state
    }
    public static void SceneChanged(){intent.Clear();changed.Clear();try{planes?.Dispose();}catch{}planes=null;planesWorld=IntPtr.Zero;}
    static void Fail(Exception x)
    {
        if(broken)return;broken=true;
        DiagnosticLog.Write("altitude_intent_failed",new{error=x.ToString()});
        MelonLogger.Error("FREEDOM_ARROW_ALTITUDE_INTENT_FAILED: the game's own altitude icon from now on. "+x.Message);
    }
}

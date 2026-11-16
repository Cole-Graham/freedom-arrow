using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.UI.Labels;
using Il2CppBrokenArrow.Client.Ecs.UI.Labels.Components;
using Il2CppBrokenArrow.Client.Ecs.UI.Labels.Systems;
using Il2CppBrokenArrow.Client.Ecs.Utils;
using Il2CppBrokenArrow.Client.Ecs.Planes.Components;
using Il2CppBrokenArrow.Client.Ecs.Navigation.Components;
using Il2CppBrokenArrow.Shared.Ecs;
using Il2CppBrokenArrow.Shared.Ecs.Components;
using Il2CppDefaultEcs;
using MelonLoader;
using UnityEngine;
using UnityEngine.UI;
namespace FreedomArrow;
// Altitude intent on plane and helicopter labels (Lateralus 16 Nov 2026, thread 1571554273639006392): "if the low altitude hotkey is toggled
// on, the same indicator in a yellow color will be displayed until either the plane reaches low altitude or the player toggles the low altitude
// hotkey off"; 06:19 PST: yellow arrow facing up while going back to high; "prioritize displaying the current intent to transition altitude up or
// down"; 06:38 PST (sead3 test): "The arrow gets stuck on yellow down when cancelling the order mid-descent" and "make sure altitude intent works
// for helicopters as well".
// Read from GameAssembly 6000.3.24f1:
// - The label arrow is LabelView.LowAltitudeIcon (one image, Icon_LowAltitude, orange RGBA 0.965/0.522/0.200), shown from
//   LabelDataComponent.IsLowAltitude: the game's own "is low" state, used here as the actual state for planes and helicopters alike.
// - Planes: the hotkey calls AltitudeChangeAbilitySystem.ChangeAltitudeForPlane, which writes PlaneAltitudeSwitchComponent
//   {IsChangePending = (AltitudeComponent.GlobalAltitudeLevel != target), TargetAltitude = target}. Cancelling mid-descent writes target High
//   with IsChangePending false (the level is still High), so sead3, which only took orders from IsChangePending, kept the old Low order.
// - Helicopters: the ordered mode is HelicopterNavDataComponent.FlyMode (HighAltitude 0, LowAltitude 1), set by AltitudeChangeCommandSystem.
// Rule (the same for both): every change of the ordered value is a new order. Ordered low but not yet low -> yellow arrow down; ordered high
// but still low -> yellow arrow up; the order is dropped when the actual state matches it or the order is taken back. Otherwise the game's
// own icon, original colour and rotation. Local player's own units only. Display only: no orders, data or network.
static class AltitudeIntent
{
    const byte PlaneLow=1,HeliLow=1;
    static readonly Color Yellow=new(1f,0.85f,0.1f,1f);
    sealed class Saved{public GameObject Icon;public Image[] Images;public Color[] Colors;public Quaternion Rotation;}
    sealed class Track{public byte LastOrder;public sbyte Intent;}   // Intent: +1 down (to low), -1 up (to high), 0 none
    static readonly Dictionary<ulong,Track> tracks=new();
    static readonly Dictionary<ulong,Saved> changed=new();
    static EntitySet planes,helis;static IntPtr setsWorld;static bool on,broken;static readonly HashSet<string> logged=new();
    public static void Install(HarmonyLib.Harmony harmony)
    {
        var m=AccessTools.Method(typeof(LabelSystem),"Update")??throw new MissingMethodException("LabelSystem.Update");
        harmony.Patch(m,postfix:new HarmonyMethod(typeof(AltitudeIntent),nameof(After)));
        on=true;
        MelonLogger.Msg("FREEDOM_ARROW_ALTITUDE_INTENT installed: own planes and helicopters show a yellow altitude arrow (down or up) while an altitude order is under way");
        DiagnosticLog.Write("altitude_intent_installed",new{hook="LabelSystem.Update postfix",units="planes (PlaneAltitudeSwitchComponent) and helicopters (HelicopterNavDataComponent.FlyMode)"});
    }
    static ulong Key(Entity e)=>System.Runtime.CompilerServices.Unsafe.As<Entity,ulong>(ref e);
    static void Log(string kind,object data){if(logged.Count<200&&logged.Add(kind))DiagnosticLog.Write("altitude_intent_"+kind,data);}
    static void After(LabelSystem __instance)
    {
        if(!on||broken)return;
        try
        {
            var me=__instance._sessionContext?.CurrentPlayer;if(me==null)return;
            var world=Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems.ShootingSystem._gameContext;if(world==null||world._isDisposed)return;
            if(setsWorld!=world.Pointer)
            {
                try{planes?.Dispose();helis?.Dispose();}catch{}
                planes=world.GetEntities().With<PlaneAltitudeSwitchComponent>().With<UnitLabelComponent>().With<UnitComponent>().AsSet();
                helis=world.GetEntities().With<HelicopterNavDataComponent>().With<UnitLabelComponent>().With<UnitComponent>().AsSet();
                setsWorld=world.Pointer;tracks.Clear();changed.Clear();
            }
            var seen=new HashSet<ulong>();
            Pass(planes,true,me,seen);Pass(helis,false,me,seen);
            foreach(var k in tracks.Keys.Where(k=>!seen.Contains(k)).ToArray()){tracks.Remove(k);changed.Remove(k);}
        }
        catch(Exception x){Fail(x);}
    }
    static void Pass(EntitySet set,bool plane,PlayerInfo me,HashSet<ulong> seen)
    {
        var list=set._entities;int count=Math.Min(set.Count,list?.Length??0);
        for(int i=0;i<count;i++)
        {
            var e=list[i];if(!e.IsAlive)continue;
            var owner=NativeEcs.Read<UnitComponent>(e).Owner?.TryCast<PlayerInfo>();
            if(owner==null||owner.Pointer!=me.Pointer)continue;   // own units only: an enemy's order must not show
            ulong k=Key(e);seen.Add(k);
            byte order;bool pending=false;
            if(plane){var sw=NativeEcs.ReadValue<PlaneAltitudeSwitchComponent>(e);order=(byte)sw.TargetAltitude;pending=sw.IsChangePending;}
            else order=NativeEcs.Field<HelicopterNavDataComponent,byte>(e,"FlyMode");
            bool orderedLow=plane?order==PlaneLow:order==HeliLow;
            bool actualLow=ActualLow(e);
            if(!tracks.TryGetValue(k,out var t))
            {
                // First sight: only a plane's still-pending order counts; a helicopter's standing fly mode is not a new order.
                t=new Track{LastOrder=order,Intent=(sbyte)(plane&&pending&&orderedLow!=actualLow?(orderedLow?1:-1):0)};tracks[k]=t;
            }
            else if(order!=t.LastOrder)
            {
                t.LastOrder=order;t.Intent=(sbyte)(orderedLow!=actualLow?(orderedLow?1:-1):0);
                Log((plane?"plane":"heli")+"_order_"+(t.Intent>0?"down":t.Intent<0?"up":"none"),new{order,actualLow,pending});
            }
            if(t.Intent>0&&actualLow||t.Intent<0&&!actualLow)t.Intent=0;   // arrived
            var icon=NativeEcs.Read<UnitLabelComponent>(e).Label?._label?.LowAltitudeIcon;if(icon==null)continue;
            if(t.Intent!=0)Show(k,icon,t.Intent<0,plane);
            else if(changed.ContainsKey(k))Restore(k,actualLow);
        }
    }
    static bool ActualLow(Entity e)
    {
        try{return NativeEcs.Field<LabelDataComponent,bool>(e,"IsLowAltitude");}
        catch(Exception x){Log("state_fallback",new{error=x.Message});return NativeEcs.Field<AltitudeComponent,byte>(e,"GlobalAltitudeLevel")==1;}
    }
    static void Show(ulong k,GameObject icon,bool up,bool plane)
    {
        if(!changed.TryGetValue(k,out var s))
        {
            var imgs=icon.GetComponentsInChildren<Image>(true).ToArray();
            s=new Saved{Icon=icon,Images=imgs,Colors=imgs.Select(x=>x.color).ToArray(),Rotation=icon.transform.localRotation};changed[k]=s;
        }
        if(!icon.activeSelf)icon.SetActive(true);
        bool any=false;
        for(int i=0;i<s.Images.Length;i++)
        {
            var c=s.Colors[i];float max=Mathf.Max(c.r,Mathf.Max(c.g,c.b)),min=Mathf.Min(c.r,Mathf.Min(c.g,c.b));
            if(max-min>0.25f){s.Images[i].color=new Color(Yellow.r,Yellow.g,Yellow.b,c.a);any=true;}
        }
        if(!any&&s.Images.Length>0)s.Images[0].color=new Color(Yellow.r,Yellow.g,Yellow.b,s.Colors[0].a);
        icon.transform.localRotation=up?s.Rotation*Quaternion.Euler(0,0,180):s.Rotation;
        Log("shown_"+(plane?"plane_":"heli_")+(up?"up":"down"),new{images=s.Images.Select((x,i)=>new{name=x.name,color=s.Colors[i].ToString()}).ToArray()});
    }
    static void Restore(ulong k,bool actualLow)
    {
        var s=changed[k];changed.Remove(k);
        for(int i=0;i<s.Images.Length;i++)if(s.Images[i]!=null)s.Images[i].color=s.Colors[i];
        if(s.Icon==null)return;
        s.Icon.transform.localRotation=s.Rotation;
        if(s.Icon.activeSelf!=actualLow)s.Icon.SetActive(actualLow);   // hand back to the game's own state
    }
    public static void SceneChanged(){tracks.Clear();changed.Clear();try{planes?.Dispose();helis?.Dispose();}catch{}planes=helis=null;setsWorld=IntPtr.Zero;}
    static void Fail(Exception x)
    {
        if(broken)return;broken=true;
        DiagnosticLog.Write("altitude_intent_failed",new{error=x.ToString()});
        MelonLogger.Error("FREEDOM_ARROW_ALTITUDE_INTENT_FAILED: the game's own altitude icon from now on. "+x.Message);
    }
}

using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.UI.Labels;
using Il2CppBrokenArrow.Client.Ecs.UI.Labels.Components;
using Il2CppBrokenArrow.Client.Ecs.UI.Labels.Systems;
using Il2CppBrokenArrow.Client.Ecs.Utils;
using Il2CppBrokenArrow.Client.Ecs.Planes.Components;
using Il2CppBrokenArrow.Client.Ecs.Navigation.Components;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
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
// Rule (the same for both): once a unit has an order (a change of the ordered value; a plane's pending order at first sight), the arrow
// follows ordered vs actual: ordered low but not low -> yellow arrow down; ordered high but still low -> yellow arrow up; when they
// match, the game's own icon, original colour and rotation. Planes keep following (momentum can carry them out of the low band after
// a cancelled climb); a helicopter's order ends at its first arrival. Local player's own units only. Display only: no orders, data or network.
// Lateralus 17 Nov 2026 (dev.32 logs): "the yellow altitude change intention indicator we added can still get stuck in the wrong position, is
// there diagnostics that can tell you why?" No: Log wrote each kind once per session (6 lines in 4.5 h). Two ways the code itself could leave
// an icon yellow or turned over were found: (1) a unit that left the plane/helicopter set while its arrow showed was dropped without putting
// its icon back; (2) the "original" colour and rotation were read per unit when the arrow was first shown, so an icon already left turned
// over was saved as its own original and could never be put right. Now: originals are kept per icon object, read the first time this code
// touches that icon (before any change); an icon is put back before its unit is dropped or its label changes to another icon; an icon
// that this code is not showing but is still yellow or turned over is put back and logged (icon_left_modified). Every arrow event is written
// to the diagnostics log (up to 3000 per session), with a state snapshot every 10 s while an arrow has shown for 20 s or more.
// Lateralus 22 Nov 2026 (ranked13 logs, 23 Nov 02:08-02:30 UTC): the arrow still stuck. All 7 arrows that showed 7-48 s started after the
// plane had reached low, when it climbed for an AGM-84 / YJ-15 launch. Game code: PrecisionStrikeCommand.UpdateSteeringPoint (RVA 0x77BDB0)
// flies the firing point at PlaneHighAltOverride or PlanesConfig.HighAltitude, whatever the hotkey says, and the plane holds High after
// the strike (docs/engine/low-altitude-and-air-sight.md, 1b). He kept the 16 Nov momentum arrow, so the rule is: while a plane has
// PrecisionStrikeComponent no arrow shows, and the start of a strike ends the order. An order given during the strike counts again
// once the strike is over.
static class AltitudeIntent
{
    const byte PlaneLow=1,HeliLow=1;
    static readonly Color Yellow=new(1f,0.85f,0.1f,1f);
    sealed class Saved{public GameObject Icon;public Image[] Images;public Color[] Colors;public Quaternion Rotation;}
    // Intent: +1 down (to low), -1 up (to high), 0 none. Ordered: an altitude order has been seen for this unit.
    sealed class Track{public byte LastOrder;public sbyte Intent;public bool Ordered;public bool Strike;public float Since;public float NextSnapshot;}
    static readonly Dictionary<ulong,Track> tracks=new();
    static readonly Dictionary<IntPtr,Saved> originals=new();   // per icon object, read before this code changes it
    static readonly Dictionary<ulong,IntPtr> changed=new();     // unit -> icon this code has changed
    static int traced;
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
    static void Trace(string kind,object data){if(traced<3000){traced++;DiagnosticLog.Write("altitude_intent_"+kind,data);}}
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
                setsWorld=world.Pointer;tracks.Clear();changed.Clear();originals.Clear();
            }
            var seen=new HashSet<ulong>();
            Pass(planes,true,me,seen);Pass(helis,false,me,seen);
            foreach(var k in tracks.Keys.Where(k=>!seen.Contains(k)).ToArray())
            {
                if(changed.TryGetValue(k,out var icon)){Put(icon,null);changed.Remove(k);Trace("dropped_while_shown",new{unit=k,intent=tracks[k].Intent});}
                tracks.Remove(k);
            }
            LeftModified();
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
                t=new Track{LastOrder=order,Ordered=plane&&pending};tracks[k]=t;
                if(t.Ordered)Trace("first_sight_pending",new{unit=k,order,actualLow});
            }
            else if(order!=t.LastOrder)
            {
                t.LastOrder=order;t.Ordered=true;
                Log((plane?"plane":"heli")+"_order_"+(orderedLow!=actualLow?(orderedLow?"down":"up"):"none"),new{order,actualLow,pending});
                Trace("order",new{unit=k,plane,order,orderedLow,actualLow,pending});
            }
            // A precision strike flies high whatever the hotkey says: its start ends the order, and no arrow shows while it lasts.
            bool strike=plane&&e.Has<PrecisionStrikeComponent>();
            if(strike!=t.Strike)
            {
                t.Strike=strike;
                if(strike&&t.Ordered){t.Ordered=false;Trace("strike_ends_order",new{unit=k,order,orderedLow,actualLow,pending,level=Level(e)});}
                else Trace(strike?"strike_start":"strike_end",new{unit=k,order,orderedLow,actualLow,pending,level=Level(e)});
            }
            sbyte before=t.Intent;
            // Lateralus 16 Nov 2026 (dev.26): a climb cancelled while still low showed the orange icon (ordered low, is low), then momentum
            // carried the plane above the low band and no arrow showed. Once a unit has an order, the arrow follows ordered vs actual all
            // the time: whenever they differ, the yellow arrow points to the ordered altitude.
            // Helicopters stop at the first arrival: a landed helicopter can read as low while its fly mode is high.
            t.Intent=(sbyte)(t.Ordered&&!strike&&orderedLow!=actualLow?(orderedLow?1:-1):0);
            if(!plane&&t.Ordered&&orderedLow==actualLow)t.Ordered=false;
            float now=Time.unscaledTime;
            if(t.Intent!=before)
            {
                t.Since=now;t.NextSnapshot=now+20f;
                Trace("intent",new{unit=k,plane,from=before,to=t.Intent,order,orderedLow,actualLow,pending,strike,level=Level(e)});
            }
            else if(t.Intent!=0&&now>=t.NextSnapshot)
            {
                t.NextSnapshot=now+10f;
                Trace("still_shown",new{unit=k,plane,intent=t.Intent,seconds=(int)(now-t.Since),order,orderedLow,actualLow,pending,level=Level(e)});
            }
            var icon=NativeEcs.Read<UnitLabelComponent>(e).Label?._label?.LowAltitudeIcon;
            if(icon==null){if(t.Intent!=0)Log("no_icon",new{unit=k,plane});continue;}
            if(changed.TryGetValue(k,out var was)&&was!=icon.Pointer)
            {
                Put(was,null);changed.Remove(k);Trace("icon_swapped",new{unit=k,plane,intent=t.Intent});
            }
            if(t.Intent!=0)Show(k,icon,t.Intent<0,plane);
            else if(changed.ContainsKey(k))Restore(k,actualLow);
        }
    }
    static int Level(Entity e){try{return NativeEcs.Field<AltitudeComponent,byte>(e,"GlobalAltitudeLevel");}catch{return -1;}}
    static bool ActualLow(Entity e)
    {
        try{return NativeEcs.Field<LabelDataComponent,bool>(e,"IsLowAltitude");}
        catch(Exception x){Log("state_fallback",new{error=x.Message});return NativeEcs.Field<AltitudeComponent,byte>(e,"GlobalAltitudeLevel")==1;}
    }
    static Saved Original(GameObject icon)
    {
        if(originals.TryGetValue(icon.Pointer,out var s)&&s.Icon!=null)return s;
        var imgs=icon.GetComponentsInChildren<Image>(true).ToArray();
        return originals[icon.Pointer]=new Saved{Icon=icon,Images=imgs,Colors=imgs.Select(x=>x.color).ToArray(),Rotation=icon.transform.localRotation};
    }
    static void Show(ulong k,GameObject icon,bool up,bool plane)
    {
        var s=Original(icon);changed[k]=icon.Pointer;
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
        var icon=changed[k];changed.Remove(k);
        Put(icon,actualLow);
        Trace("restored",new{unit=k,actualLow});
    }
    // Back to the game's colour and rotation. active: the game's own low state, or null to leave it (unit gone or label changed).
    static void Put(IntPtr icon,bool? active)
    {
        if(!originals.TryGetValue(icon,out var s))return;
        for(int i=0;i<s.Images.Length;i++)if(s.Images[i]!=null)s.Images[i].color=s.Colors[i];
        if(s.Icon==null)return;
        s.Icon.transform.localRotation=s.Rotation;
        if(active is bool a&&s.Icon.activeSelf!=a)s.Icon.SetActive(a);   // hand back to the game's own state
    }
    // An icon this code changed once but is not showing now must not keep this code's marks. If it does, say so and put it back.
    static void LeftModified()
    {
        var shown=new HashSet<IntPtr>(changed.Values);
        foreach(var (ptr,s) in originals.ToArray())
        {
            if(shown.Contains(ptr))continue;
            if(s.Icon==null){originals.Remove(ptr);continue;}
            // Only this code's own marks: the yellow colour, or the icon turned over. Other changes belong to the game.
            bool turned=Quaternion.Angle(s.Icon.transform.localRotation,s.Rotation)>170f;
            bool yellow=s.Images.Any(x=>x!=null&&Mathf.Abs(x.color.r-Yellow.r)<0.01f&&Mathf.Abs(x.color.g-Yellow.g)<0.01f&&Mathf.Abs(x.color.b-Yellow.b)<0.01f);
            if(!turned&&!yellow)continue;
            Trace("icon_left_modified",new{turned,yellow,rotation=s.Icon.transform.localEulerAngles.z,original=s.Rotation.eulerAngles.z});
            Put(ptr,null);
        }
    }
    public static void SceneChanged(){tracks.Clear();changed.Clear();originals.Clear();try{planes?.Dispose();helis?.Dispose();}catch{}planes=helis=null;setsWorld=IntPtr.Zero;}
    static void Fail(Exception x)
    {
        if(broken)return;broken=true;
        DiagnosticLog.Write("altitude_intent_failed",new{error=x.ToString()});
        MelonLogger.Error("FREEDOM_ARROW_ALTITUDE_INTENT_FAILED: the game's own altitude icon from now on. "+x.Message);
    }
}

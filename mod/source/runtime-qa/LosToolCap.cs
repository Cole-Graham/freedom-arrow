using System.Runtime.InteropServices;
using Il2CppBrokenArrow.Client.Ecs.FogOfWar.VisualTools;
using Il2CppInterop.Runtime;
using MelonLoader;
using MelonLoader.NativeUtils;

namespace FreedomArrow;

// LoS tool shows the ground spotting cap (Lateralus 28 Nov 2026 11:5x, Proposal W: "the LOS tool would tell them they can spot to 3900m
// in the open... but that isn't actually true because we introduced a wargame-style cap"). FOWToolService.Filter(ref FowToolTask) walks
// one ray of the tool (1.2.2.1 RVA 0x6BBFB0, docs/engine/low-altitude-and-air-sight.md 3f): the red line ends where the walk cost passes
// MaxVisionDistance (+0x1C, the unit's raw ground optics); the green line where it passes MaxVisionDistance / LosToolDefaultStealthMax
// (+0x28, the stealth the player picked, FOWToolConfig.StealthMinMax.y). Real spotting caps the budget (SpottingCap.cs), so in ground mode:
//   red   = min(optics, cap)            (a stealth-1 target)
//   green = min(optics / stealth, cap)  (a target at the picked stealth)
// written as MaxVisionDistance = red and stealth = red / green. Optics with no cap entry (or air mode) are left alone. A native detour with
// an explicit pointer ABI, like InterceptLead: FowToolTask holds an int[] and Harmony ref-struct patches have crashed the game before.
// Filter has one direct native caller (the tool's UpdateTools state machine, 1.2.2.1 0x6C6B6B), so the detour is reached; that caller runs on
// a thread-pool thread, so the thunk only reads and writes the task.
internal static unsafe class LosToolCap
{
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    delegate void FilterNative(IntPtr service,IntPtr task,IntPtr method);
    static readonly FilterNative Callback=Thunk;
    static NativeHook<FilterNative> hook;
    static volatile bool off;
    static long rays,capped;
    const int MaxVision=0x1C,StealthMax=0x28,AirMode=0x40;

    public static void Install()
    {
        InterceptLead.CheckGameHash();
        var info=(IntPtr)(typeof(FOWToolService).GetFields(System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Public)
            .Single(f=>f.Name.StartsWith("NativeMethodInfoPtr_Filter_",StringComparison.Ordinal)).GetValue(null)??throw new MissingMethodException("FOWToolService.Filter metadata"));
        if(info==IntPtr.Zero||Marshal.ReadIntPtr(info)==IntPtr.Zero)throw new MissingMethodException("FOWToolService.Filter");
        var service=IL2CPP.il2cpp_method_get_declaring_type(info);
        var task=IL2CPP.il2cpp_class_from_name(IL2CPP.il2cpp_class_get_image(service),"BrokenArrow.Client.Ecs.FogOfWar.VisualTools","FowToolTask");
        if(task==IntPtr.Zero||!IL2CPP.il2cpp_class_is_valuetype(task))throw new InvalidOperationException("FowToolTask missing");
        // Every offset the thunk touches is checked against the game's own metadata (value-type offsets include the 16-byte object header).
        Check(task,"MaxVisionDistance",MaxVision+2*IntPtr.Size);Check(task,"LosToolDefaultStealthMax",StealthMax+2*IntPtr.Size);Check(service,"_airMode",AirMode);
        hook=new NativeHook<FilterNative>(Marshal.ReadIntPtr(info),Marshal.GetFunctionPointerForDelegate(Callback));
        hook.Attach();
        MelonLogger.Msg("FREEDOM_ARROW_LOS_TOOL_CAP installed; ground lines use the spotting cap (red = min(optics, cap), green = min(optics / stealth, cap))");
    }
    static void Check(IntPtr klass,string name,int offset)
    {
        var field=IL2CPP.il2cpp_class_get_field_from_name(klass,name);
        if(field==IntPtr.Zero||IL2CPP.il2cpp_field_get_offset(field)!=offset)throw new InvalidOperationException("LoS tool field mismatch: "+name);
    }
    // Runs on the LoS tool's worker thread: no Unity calls, no allocation, no logging here.
    static void Thunk(IntPtr service,IntPtr task,IntPtr method)
    {
        if(!off&&Runtime.IsApplied&&service!=IntPtr.Zero&&task!=IntPtr.Zero&&*(byte*)(service+AirMode)==0)
        {
            try
            {
                float* max=(float*)(task+MaxVision),stealth=(float*)(task+StealthMax);
                float optics=*max,s=*stealth;
                if(s>=1f&&SpottingCap.GroundCap(optics,out float cap))
                {
                    float red=Math.Min(optics,cap),green=Math.Min(optics/s,cap);
                    if(red<optics||green<optics/s){*max=red;*stealth=red/green;Interlocked.Increment(ref capped);}
                }
                Interlocked.Increment(ref rays);
            }
            catch{off=true;}
        }
        hook.Trampoline(service,task,method);
    }
    // Called from the main thread now and then (Runtime.OnLateUpdate) so the log proves the hook ran.
    internal static void Report()
    {
        if(hook==null)return;
        long r=Interlocked.Read(ref rays);
        if(r>0&&!reported){reported=true;MelonLogger.Msg($"FREEDOM_ARROW_LOS_TOOL_CAP first rays: {r} walked, {Interlocked.Read(ref capped)} capped");}
        if(off&&!offReported){offReported=true;MelonLogger.Error("FREEDOM_ARROW_LOS_TOOL_CAP_FAILED: off for this session; the LoS tool shows uncapped optics");}
    }
    static bool reported,offReported;
}

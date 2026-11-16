using System.Diagnostics;
using System.Reflection;
using HarmonyLib;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;

// 0.9.0-dev.13 (Osama 15 Nov 2026: "can you look at my game and see how we can make it run smoother"). The dev.12 5v5 ran at about
// 25 fps with the main thread at 93% of a core and the GPU at 40%, so the frame time is spent on the main thread. This probe measures
// the main-thread functions that Freedom Arrow hooks: for each one, calls and the time spent in the whole call (the game's own work plus
// every mod patch on it), and the frame rate. One FREEDOM_ARROW_PERF block every 60 s. Only on when UserData/FreedomArrow/perf-probe.txt
// exists: the probe adds its own small cost to every call it measures.
internal static class PerfProbe
{
    static class Probe<T>
    {
        public static long Calls,Ticks;
        public static void Pre(out long __state){__state=Stopwatch.GetTimestamp();}
        public static void Post(long __state){Interlocked.Increment(ref Calls);Interlocked.Add(ref Ticks,Stopwatch.GetTimestamp()-__state);}
    }
    sealed class M0{} sealed class M1{} sealed class M2{} sealed class M3{} sealed class M4{} sealed class M5{} sealed class M6{}
    sealed class M7{} sealed class M8{} sealed class M9{} sealed class M10{} sealed class M11{} sealed class M12{} sealed class M13{}
    sealed class M14{} sealed class M15{} sealed class M16{} sealed class M17{} sealed class M18{}
    static readonly Type[] Markers={typeof(M0),typeof(M1),typeof(M2),typeof(M3),typeof(M4),typeof(M5),typeof(M6),typeof(M7),typeof(M8),typeof(M9),typeof(M10),typeof(M11),typeof(M12),typeof(M13),
        typeof(M14),typeof(M15),typeof(M16),typeof(M17),typeof(M18)};
    static readonly (string type,string method)[] Targets={
        ("BattleSystemHelpers","CalculateHitDamage"),("BattleSystemHelpers","GetArmorSideFromShotVector"),("BattleSystemHelpers","GetPenetrationForShell"),
        ("BattleSystemHelpers","CalculateMissileHitChance"),("BattleSystemHelpers","GetShellMuzzleSpeed"),("FogOfWarUnit","Update"),
        ("FogOfWarUnit","CreateFilterTaskForTarget"),("SeekerSystem","InternalUpdate"),("OverkillScoringSystem","IsTargetOverkilled"),
        ("WeaponHelper","RateOfFire"),("ShootingSystem","WeaponForceFire"),("WeaponComponent","SetRandomParams"),("PlayerEconomyService","Update"),
        ("UnitDeathSystem","TrySpawnPilot"),
        // The mods' own per-frame work: Freedom Arrow's update, late update and on-screen labels, and FAModels' model swaps.
        ("FreedomArrow.Runtime","OnUpdate"),("FreedomArrow.Runtime","OnLateUpdate"),("FreedomArrow.Runtime","OnGUI"),("FAModels.Mod","OnUpdate"),("FAModels.Mod","OnLateUpdate")};
    static readonly List<(string name,FieldInfo calls,FieldInfo ticks)> probes=new();
    static readonly List<float> frames=new();
    static float windowStart=-1;
    public static void Install(HarmonyLib.Harmony harmony,string root)
    {
        if(!File.Exists(Path.Combine(root,"perf-probe.txt")))return;
        for(int i=0;i<Targets.Length;i++)
        {
            var (tn,mn)=Targets[i];
            var type=AccessTools.TypeByName(tn);
            var methods=type==null?new List<MethodInfo>():AccessTools.GetDeclaredMethods(type).Where(m=>m.Name==mn&&!m.IsAbstract).ToList();
            if(methods.Count==0){MelonLogger.Warning($"FREEDOM_ARROW_PERF {tn}.{mn} not found; not measured");continue;}
            var probe=typeof(Probe<>).MakeGenericType(Markers[i]);
            foreach(var m in methods)
                harmony.Patch(m,prefix:new HarmonyMethod(probe.GetMethod("Pre")){priority=Priority.First},postfix:new HarmonyMethod(probe.GetMethod("Post")){priority=Priority.Last});
            probes.Add(($"{tn}.{mn}",probe.GetField("Calls"),probe.GetField("Ticks")));
        }
        MelonEvents.OnUpdate.Subscribe(Frame);
        MelonLogger.Msg($"FREEDOM_ARROW_PERF probe on: {probes.Count} functions measured, one report every 60 s");
    }
    static void Frame()
    {
        float now=Time.realtimeSinceStartup;
        if(windowStart<0){windowStart=now;return;}
        frames.Add(Time.unscaledDeltaTime);
        if(now-windowStart<60f)return;
        float span=now-windowStart;windowStart=now;
        var sorted=frames.OrderBy(f=>f).ToList();int n=sorted.Count;
        float p95=n>0?sorted[Math.Min(n-1,(int)(n*0.95f))]*1000f:0;int slow=sorted.Count(f=>f>0.05f);frames.Clear();
        var lines=new List<string>();
        foreach(var (name,cf,tf) in probes)
        {
            long calls=(long)cf.GetValue(null)!,ticks=(long)tf.GetValue(null)!;cf.SetValue(null,0L);tf.SetValue(null,0L);
            if(calls==0)continue;
            double ms=ticks*1000.0/Stopwatch.Frequency;
            lines.Add($"{name} {calls/span:0} calls/s, {ms/span:0.0} ms/s ({(n>0?ms/n:0):0.00} ms per frame)");
        }
        MelonLogger.Msg($"FREEDOM_ARROW_PERF {span:0} s: {n/span:0.0} fps, 95% of frames under {p95:0} ms, {slow} frames over 50 ms | "+string.Join(" | ",lines));
    }

}

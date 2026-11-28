using MelonLoader;
using UnityEngine;
namespace FAModels;
// 0.3.51 (Osama 27 Nov 2026: "Keep monitoring this models system. We need to make sure we're logging everything going on with performance").
// Always on, in battle scenes, in every player's log (the logs are uploaded): one FAMODELS perf line a minute with the frame times (fps, p50/
// p95/p99/max, frames over 50/100/250 ms), how many slow frames had FAModels work over 10 ms or a garbage collection, FAModels time per frame
// by part, the models built in that minute (in the preload or when a unit first appeared, with their time), the IL2CPP heap and the kept-model
// cache. Each hitch line also says whether a garbage collection ran in that frame. Cost: a float per frame and four counter reads.
public partial class Mod
{
    static readonly List<float> perfFrames = new();
    static readonly long[] secTot = new long[9];
    static float perfStart = -1f; static int perfSlowFam, perfSlowGc, perfSlowNet;
    static long lastIlGc = -1, lastNetGc = -1, frameIlGc, frameNetGc;
    static int famBuiltPre, famBuiltLate; static long famTicksPre, famTicksLate; static bool inPreloadBuild;
    static void PerfFrame()
    {
        long il = -1, net = GC.CollectionCount(0) + GC.CollectionCount(1) + GC.CollectionCount(2);
        try { il = Il2CppSystem.GC.CollectionCount(0); } catch { }
        frameIlGc = lastIlGc >= 0 && il >= 0 ? il - lastIlGc : 0; frameNetGc = lastNetGc >= 0 ? net - lastNetGc : 0; lastIlGc = il; lastNetGc = net;
        if (!battleScene) { perfStart = -1f; return; }
        float now = Time.realtimeSinceStartup, dt = Time.unscaledDeltaTime;
        if (perfStart < 0f) { perfStart = now; perfFrames.Clear(); Array.Clear(secTot, 0, secTot.Length); perfSlowFam = perfSlowGc = perfSlowNet = 0; famBuiltPre = famBuiltLate = 0; famTicksPre = famTicksLate = 0; return; }
        perfFrames.Add(dt);
        if (dt > 0.05f) { if (frameIlGc > 0) perfSlowGc++; if (frameNetGc > 0) perfSlowNet++; if (lastUpdateMs >= 10) perfSlowFam++; }
        if (now - perfStart < 60f) return;
        float span = now - perfStart; perfStart = now;
        var s = perfFrames.OrderBy(f => f).ToList(); int n = s.Count; perfFrames.Clear();
        float P(float q) => n == 0 ? 0 : s[Math.Min(n - 1, (int)(n * q))] * 1000f;
        double tick = 1000.0 / System.Diagnostics.Stopwatch.Frequency, famMs = secTot.Sum() * tick;
        string parts = string.Join(", ", Enumerable.Range(0, secTot.Length).Where(i => secTot[i] * tick >= 1).OrderByDescending(i => secTot[i]).Select(i => $"{secNames[i]} {secTot[i] * tick / Math.Max(1, n):F2}"));
        string heap; try { heap = $"{Il2CppSystem.GC.GetTotalMemory(false) >> 20} MB"; } catch { heap = "n/a"; }
        MelonLogger.Msg($"FAMODELS perf {span:F0} s: {n / span:F1} fps, frame p50 {P(0.5f):F0} / p95 {P(0.95f):F0} / p99 {P(0.99f):F0} / max {(n > 0 ? s[n - 1] * 1000f : 0):F0} ms, "
            + $"over 50 ms {s.Count(f => f > 0.05f)}, over 100 ms {s.Count(f => f > 0.1f)}, over 250 ms {s.Count(f => f > 0.25f)} | slow frames with FAModels over 10 ms {perfSlowFam}, with IL2CPP GC {perfSlowGc}, with .NET GC {perfSlowNet} | "
            + $"FAModels {famMs / Math.Max(1, n):F2} ms per frame ({parts}) | models built: {famBuiltPre} in preload {famTicksPre * tick:F0} ms, {famBuiltLate} at first sight {famTicksLate * tick:F0} ms | "
            + $"kept {famCache.Count} model(s), preload {preload.Count} + {preloadHeavy.Count} left, decks {decksQueued.Count} | il2cpp heap {heap}");
        Array.Clear(secTot, 0, secTot.Length); perfSlowFam = perfSlowGc = perfSlowNet = 0; famBuiltPre = famBuiltLate = 0; famTicksPre = famTicksLate = 0;
    }
    static double lastUpdateMs;
    static void PerfAddUpdate(long start, long end)
    {
        for (int i = 0; i < sec.Length; i++) secTot[i] += sec[i];
        lastUpdateMs = (end - start) * 1000.0 / System.Diagnostics.Stopwatch.Frequency;
    }
    static void PerfBuilt(long ticks)
    {
        if (inPreloadBuild) { famBuiltPre++; famTicksPre += ticks; } else { famBuiltLate++; famTicksLate += ticks; }
    }
}

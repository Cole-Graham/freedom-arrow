using MelonLoader;
using UnityEngine;

namespace FreedomArrow;

/// <summary>
/// Osama 22 Nov 2026 00:05 PST (thread 1573561286803980289): "we need to clear the memory before and after every match".
/// Player logs on 21-22 Nov: private memory about 12 GB at the menu, 18-21 GB in battle, and it stays at 17-20 GB back in
/// the menu, so the next match climbs higher; games that died had 19-21 GB (Dr.bright, 书, 0.9.3 and 0.9.4 alike).
/// On every scene change around a match (Void = the empty scene between menu and map, both ways; Hangar_Scene = back in
/// the menu) run a managed and IL2CPP garbage collection, then Resources.UnloadUnusedAssets, and log memory before and after.
/// The menu pass waits 3 s so FAModels frees its unused models first (Unload.cs). FAModels' kept meshes are
/// DontUnloadUnusedAsset, so this does not touch them.
/// </summary>
static class MemoryCleanup
{
    const float MenuDelay = 3f;
    static float due = -1;
    static string reason = "";
    static AsyncOperation pending;
    static string before;
    static float started;

    public static void SceneChanged(string scene)
    {
        if (scene != "Void" && scene != "Hangar_Scene") return;
        reason = scene;
        due = Time.realtimeSinceStartup + (scene == "Hangar_Scene" ? MenuDelay : 0f);
    }

    public static void Tick()
    {
        try
        {
            if (pending != null)
            {
                if (!pending.isDone) return;
                pending = null;
                Collect();
                MelonLogger.Msg($"FREEDOM_ARROW_MEMORY_CLEANUP {reason}: before [{before}] after [{Snapshot()}], {Time.realtimeSinceStartup - started:0.0} s");
                return;
            }
            if (due < 0 || Time.realtimeSinceStartup < due) return;
            due = -1;
            before = Snapshot();
            started = Time.realtimeSinceStartup;
            Collect();
            pending = Resources.UnloadUnusedAssets();
        }
        catch (Exception e)
        {
            pending = null;
            MelonLogger.Warning("FREEDOM_ARROW_MEMORY_CLEANUP failed: " + e.Message);
        }
    }

    static void Collect()
    {
        GC.Collect();
        GC.WaitForPendingFinalizers();
        Il2CppSystem.GC.Collect();
    }

    // 22 Nov 01:4x: Osama's Linux PC reports private 0, so the first test could not show what a pass frees. Log before and after:
    // process private / working set, Unity's own allocated and reserved memory (works under Proton too) and the IL2CPP GC heap.
    static string Snapshot()
    {
        var p = System.Diagnostics.Process.GetCurrentProcess();
        string unity;
        try { unity = $"unity alloc {UnityEngine.Profiling.Profiler.GetTotalAllocatedMemoryLong() >> 20} MB, reserved {UnityEngine.Profiling.Profiler.GetTotalReservedMemoryLong() >> 20} MB"; }
        catch { unity = "unity n/a"; }
        string heap;
        try { heap = $"il2cpp heap {Il2CppSystem.GC.GetTotalMemory(false) >> 20} MB"; } catch { heap = "il2cpp heap n/a"; }
        return $"private {p.PrivateMemorySize64 >> 20} MB, working set {p.WorkingSet64 >> 20} MB, {unity}, {heap}";
    }
}

using UnityEngine;
using MelonLoader;
namespace FAModels;
// 0.3.45 (End 24 Nov 2026, Linux rejoin freezes): "it should start loading the lowest LOD first and use that until other LODs finished
// loading. a few frames with worse LOD are fine, just prevent blocking and crowding the GPU". His two rejoin logs froze 6-8 s after the
// rejoin while FAModels did up to 78 model swaps in one frame, and 20 model files were read on the game's main thread (1,872 ms), because
// the match-start preload had built only 3 models. Now, from the spawn queue:
// - a model file that is not ready is read on a background thread (Background.cs Prefetch); the unit waits for it hidden, as it already
//   did while a turret bone was missing, instead of the main thread reading it;
// - a unit whose levels are not all built gets only its lightest level first; the other levels are added one per unit per frame,
//   lightest first, each as soon as its file is ready;
// - model swaps and added levels stop for the frame after ModelBudgetMs (infantry bodies already stop after 6 ms, InfantryBodies.cs).
// Models the preload already built still build all levels at once. Infantry weapons (InfantryWeapons.cs) keep building at once.
public partial class Mod
{
    const double ModelBudgetMs = 6;
    static int lodLevelsThisFrame, modelsDeferredThisFrame;
    static double SinceMs(long t0) => (System.Diagnostics.Stopwatch.GetTimestamp() - t0) * 1000.0 / System.Diagnostics.Stopwatch.Frequency;
    static readonly Dictionary<string, Vector3> alignCache = new();
    static bool KeptFam(string file) => famCache.TryGetValue(file, out var c) && c.All(p => p.subs.All(x => x.mesh != null && x.mat != null));
    // True when LoadFam(file) does no file work on the main thread; otherwise starts the background read.
    static bool StreamReady(string file)
    {
        if (KeptFam(file)) return true;
        famCache.Remove(file);   // a cached model whose meshes were unloaded is read again (Prefetch skips cached files)
        Prefetch(file);
        return famJobs.TryGetValue(file, out var t) && t.IsCompleted;
    }
    // One detail level's parts, made under holder (each part on its bone is moved there by the caller). Returns the level's renderers.
    static List<Renderer> BuildLevel(GameObject holder, List<FamPart> fam, int L, List<(GameObject part, string bone)> made, ref int verts)
    {
        var rs = new List<Renderer>();
        foreach (var fp in fam)
        {
            string bone = fp.bone;
            var part = new GameObject(L == 0 ? "FAM_" + bone : $"FAM_{bone}_L{L}");
            part.transform.SetParent(holder.transform, false);
            made.Add((part, bone));
            for (int s = 0; s < fp.subs.Count; s++)
            {
                var go = new GameObject(L == 0 ? $"FAM_{bone}_{s}" : $"FAM_{bone}_{s}_L{L}");
                go.transform.SetParent(part.transform, false);
                go.AddComponent<MeshFilter>().sharedMesh = fp.subs[s].mesh;
                var mr = go.AddComponent<MeshRenderer>(); mr.sharedMaterial = fp.subs[s].mat; rs.Add(mr);
                verts += fp.subs[s].mesh.vertexCount;
            }
        }
        return rs;
    }
    sealed class PartPose { public Transform parent; public Vector3 p, s; public Quaternion r; }
    sealed class LodUpgrade
    {
        public GameObject root, holder; public string unit = ""; public List<string> files = new(); public List<Renderer>[] byLevel = Array.Empty<List<Renderer>>();
        public readonly Dictionary<string, PartPose> poses = new(); public readonly float t = Time.realtimeSinceStartup;
    }
    static readonly List<LodUpgrade> lodUpgrades = new();
    // A later level's part goes on the same bone with the same local pose as the first level's part, so it matches it whatever the
    // turret or wheels are doing by then.
    static void QueueLodUpgrade(GameObject root, GameObject holder, string unit, List<string> files, List<Renderer>[] byLevel, List<(GameObject part, string bone)> made)
    {
        var u = new LodUpgrade { root = root, holder = holder, unit = unit, files = files, byLevel = byLevel };
        foreach (var (part, bone) in made)
            if (part != null && part.transform.parent != holder.transform && !u.poses.ContainsKey(bone))
                u.poses[bone] = new PartPose { parent = part.transform.parent, p = part.transform.localPosition, r = part.transform.localRotation, s = part.transform.localScale };
        lodUpgrades.Add(u);
    }
    static void TickLodUpgrades(long budgetStart)
    {
        for (int i = lodUpgrades.Count - 1; i >= 0; i--)
        {
            var u = lodUpgrades[i];
            // Unit gone, or a loadout variant replaced the model (OptionVariants.cs renames and switches off the old holder before destroying it).
            if (u.root == null || u.holder == null || !u.holder.activeSelf || u.holder.name != "FAM_holder") { lodUpgrades.RemoveAt(i); continue; }
            int L = -1; for (int k = u.files.Count - 1; k >= 0; k--) if (u.byLevel[k] == null) { L = k; break; }
            if (L < 0) { lodUpgrades.RemoveAt(i); continue; }
            if (!StreamReady(u.files[L])) continue;
            if (SinceMs(budgetStart) > ModelBudgetMs) { modelsDeferredThisFrame++; return; }
            var made = new List<(GameObject part, string bone)>();
            try
            {
                int v = 0;
                var rs = BuildLevel(u.holder, LoadFam(u.files[L], out _), L, made, ref v);
                foreach (var (part, bone) in made)
                    if (u.poses.TryGetValue(bone, out var pose) && pose.parent != null)
                    { part.transform.SetParent(pose.parent, false); part.transform.localPosition = pose.p; part.transform.localRotation = pose.r; part.transform.localScale = pose.s; }
                // Same fog-of-war state as the levels already shown; SyncVisibility reads the unit's renderers again at its next check.
                bool vis = true;
                foreach (var lv in u.byLevel) if (lv != null) { var shown = lv.FirstOrDefault(r => r != null); if (shown != null) { vis = shown.enabled; break; } }
                foreach (var r in rs) r.enabled = vis;
                u.byLevel[L] = rs;
                SetLevels(u.root, u.holder, u.byLevel, u.unit);
                famRenderers.Remove(u.root.GetInstanceID());
                try { ApplyPaint(u.root, u.unit); } catch (Exception ex) { MelonLogger.Warning("FAMODELS_PAINT apply: " + ex.Message); }
                NoteUse(u.files[L], u.root);
                lodLevelsThisFrame++;
            }
            catch (Exception ex)
            {
                foreach (var (part, _) in made) if (part != null) { part.SetActive(false); UnityEngine.Object.Destroy(part); }
                MelonLogger.Warning($"FAMODELS {u.unit}: detail level {L} ({u.files[L]}) not added, the lighter level stays: {ex.Message}");
                lodUpgrades.RemoveAt(i); continue;
            }
            if (u.byLevel.All(x => x != null)) { MelonLogger.Msg($"FAMODELS {u.unit}: all {u.files.Count} detail levels in {Time.realtimeSinceStartup - u.t:F2} s after its lightest"); lodUpgrades.RemoveAt(i); }
        }
    }
}

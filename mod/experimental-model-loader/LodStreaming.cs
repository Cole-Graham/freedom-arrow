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
// Models already built still build all levels at once. 0.3.46: the match-start preload (Preload.cs) builds only the lightest
// level and reads the heavier ones in the background, so preloaded units stream their heavier levels too. Infantry weapons (InfantryWeapons.cs) keep building at once.
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
    // 0.3.47 (End 25 Nov 2026: "only load the LOD if the unity game engine actually requests it, so it doesn't fill up all the VRAM";
    // "is there also a method to hook the unity game engine unloading a LOD"; "please do not leave it out"). Unity has no such hook: a
    // LODGroup only picks which already-loaded renderers to draw, inside the native engine, and has no callback or current-level getter.
    // So FAModels works the level out itself, with Unity's formula: screen share = LODGroup.size x scale x lodBias / (2 x distance x
    // tan(fov / 2)). Each unit keeps its lightest level; a heavier level is built only when the camera is close enough to need it
    // (NeedMargin x the share, so it is ready a little before the switch), and its parts are removed after UnloadAfterS seconds without
    // need. A level file no unit has built for UnloadAfterS is freed too (meshes only: the levels share their materials and textures).
    const float LodCheckS = 0.25f, NeedMargin = 1.25f, UnloadAfterS = 30f;
    sealed class LodView
    {
        public GameObject root, holder; public string unit = ""; public List<string> files = new(); public List<Renderer>[] byLevel = Array.Empty<List<Renderer>>();
        public List<GameObject>[] parts = Array.Empty<List<GameObject>>(); public float[] lastNeed = Array.Empty<float>(); public float[] h = Array.Empty<float>();
        public readonly Dictionary<string, PartPose> poses = new(); public LODGroup group; public int need = -1;
    }
    static readonly List<LodView> lodViews = new();
    static float lodCheckT, lodFreeT; static int lodBuilt, lodUnloaded, lodFilesFreed; static long lodBytesFreed;
    // A later level's part goes on the same bone with the same local pose as the first level's part, so it matches it whatever the
    // turret or wheels are doing by then.
    static void QueueLodUpgrade(GameObject root, GameObject holder, string unit, List<string> files, List<Renderer>[] byLevel, List<(GameObject part, string bone)> made)
    {
        int n = files.Count;
        var u = new LodView { root = root, holder = holder, unit = unit, files = files, byLevel = byLevel, parts = new List<GameObject>[n], lastNeed = new float[n], h = LodHeights(root, holder, n) };
        int light = Array.FindIndex(byLevel, x => x != null); if (light >= 0) u.parts[light] = made.Select(m => m.part).ToList();
        foreach (var (part, bone) in made)
            if (part != null && part.transform.parent != holder.transform && !u.poses.ContainsKey(bone))
                u.poses[bone] = new PartPose { parent = part.transform.parent, p = part.transform.localPosition, r = part.transform.localRotation, s = part.transform.localScale };
        lodViews.Add(u);
    }
    static Camera lodCam; static float lodCamT;
    static Camera LodCamera()
    {
        if (lodCam != null && lodCam.isActiveAndEnabled && Time.realtimeSinceStartup - lodCamT < 1f) return lodCam;
        lodCamT = Time.realtimeSinceStartup; lodCam = Camera.main;
        if (lodCam == null) foreach (var c in Camera.allCameras) if (c != null && c.name != "FAM_InspectCam" && (lodCam == null || c.depth > lodCam.depth)) lodCam = c;
        return lodCam;
    }
    // The level Unity would draw at this screen share (-1: culled), as in LODGroup: level i ends at h[i].
    static int LevelFor(float share, float[] h) { for (int i = 0; i < h.Length; i++) if (share >= h[i]) return i; return -1; }
    static float ScreenShare(LodView u, Camera cam)
    {
        var g = u.group; if (g == null) { g = u.group = u.holder.GetComponent<LODGroup>(); if (g == null) return 1f; }
        var ls = u.holder.transform.lossyScale; float scale = Mathf.Max(Mathf.Abs(ls.x), Mathf.Max(Mathf.Abs(ls.y), Mathf.Abs(ls.z)));
        if (cam.orthographic) return g.size * scale * 0.5f / cam.orthographicSize * QualitySettings.lodBias;
        float d = Mathf.Max(0.01f, Vector3.Distance(u.holder.transform.TransformPoint(g.localReferencePoint), cam.transform.position));
        return g.size * scale * QualitySettings.lodBias / (2f * d * Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad));
    }
    static void TickLodUpgrades(long budgetStart)
    {
        float now = Time.realtimeSinceStartup;
        bool check = now - lodCheckT >= LodCheckS; if (check) lodCheckT = now;
        var cam = LodCamera();
        for (int i = lodViews.Count - 1; i >= 0; i--)
        {
            var u = lodViews[i];
            // Unit gone, or a loadout variant replaced the model (OptionVariants.cs renames and switches off the old holder before destroying it).
            if (u.root == null || u.holder == null || !u.holder.activeSelf || u.holder.name != "FAM_holder") { lodViews.RemoveAt(i); continue; }
            int n = u.files.Count, light = n - 1;
            if (check)
            {
                // Without a camera (none found), every level is treated as needed, as in 0.3.45.
                u.need = cam == null ? 0 : LevelFor(ScreenShare(u, cam) * NeedMargin, u.h);
                if (u.need >= 0) { u.need = Math.Max(u.need, QualitySettings.maximumLODLevel); if (u.need < n) u.lastNeed[u.need] = now; }
                for (int L = 0; L < light; L++)
                    if (u.byLevel[L] != null && now - u.lastNeed[L] > UnloadAfterS) UnloadLevel(u, L);
            }
            int need = u.need;
            if (need < 0 || need >= light || u.byLevel[need] != null) continue;
            if (!StreamReady(u.files[need])) continue;
            if (SinceMs(budgetStart) > ModelBudgetMs) { modelsDeferredThisFrame++; continue; }
            BuildLodLevel(u, need);
        }
        if (now - lodFreeT >= 5f) { lodFreeT = now; FreeUnusedLevels(now); }
    }
    static void BuildLodLevel(LodView u, int L)
    {
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
            u.byLevel[L] = rs; u.parts[L] = made.Select(m => m.part).ToList();
            SetLevels(u.root, u.holder, u.byLevel, u.unit);
            famRenderers.Remove(u.root.GetInstanceID());
            try { ApplyPaint(u.root, u.unit); } catch (Exception ex) { MelonLogger.Warning("FAMODELS_PAINT apply: " + ex.Message); }
            NoteUse(u.files[L], u.root);
            lodLevelsThisFrame++; lodBuilt++;
            if (Verbose) MelonLogger.Msg($"FAMODELS {u.unit}: detail level {L} built on demand ({u.files[L]}, {v} vertices)");
        }
        catch (Exception ex)
        {
            foreach (var (part, _) in made) if (part != null) { part.SetActive(false); UnityEngine.Object.Destroy(part); }
            u.byLevel[L] = null; u.parts[L] = null;
            u.lastNeed[L] = float.MaxValue / 2;   // not tried again for this unit
            MelonLogger.Warning($"FAMODELS {u.unit}: detail level {L} ({u.files[L]}) not added, the lighter level stays: {ex.Message}");
        }
    }
    static void UnloadLevel(LodView u, int L)
    {
        if (u.parts[L] != null) foreach (var part in u.parts[L]) if (part != null) { part.SetActive(false); UnityEngine.Object.Destroy(part); }
        u.parts[L] = null; u.byLevel[L] = null;
        SetLevels(u.root, u.holder, u.byLevel, u.unit);
        famRenderers.Remove(u.root.GetInstanceID());
        if (famUsers.TryGetValue(u.files[L], out var users)) users.Remove(u.root);
        lodUnloaded++;
    }
    // A heavier level file that no unit has built for UnloadAfterS is freed: its meshes are destroyed and the file is read again (in the
    // background) when a unit next needs it. Materials and textures stay, because the lightest level of the same model uses them.
    static readonly HashSet<string> lodHeavyFiles = new();
    static void FreeUnusedLevels(float now)
    {
        if (LodPreloadBuild) return;
        foreach (var u in lodViews) for (int L = 0; L < u.files.Count - 1; L++) lodHeavyFiles.Add(u.files[L]);
        foreach (var f in lodHeavyFiles.ToList())
        {
            if (!famCache.TryGetValue(f, out var parts) || InUse(f) || IsWeaponFile(f)) continue;
            if (now - (famUsed.TryGetValue(f, out var t) ? t : 0f) < UnloadAfterS) continue;
            if (lodViews.Any(u => u.files.Count > 0 && u.files[u.files.Count - 1] == f)) continue;   // some unit's lightest level
            foreach (var part in parts) foreach (var sub in part.subs) if (sub.mesh != null) { lodBytesFreed += MeshBytes(sub.mesh); UnityEngine.Object.Destroy(sub.mesh); }
            famCache.Remove(f); famUsers.Remove(f); famUsed.Remove(f); lodFilesFreed++;
            if (Verbose) MelonLogger.Msg($"FAMODELS detail level file {f} freed (no unit needed it for {UnloadAfterS:F0} s)");
        }
    }
}

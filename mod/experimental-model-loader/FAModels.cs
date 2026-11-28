using System.Linq;
using HarmonyLib;
using MelonLoader;
using UnityEngine;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using Il2CppBrokenArrow.Client.Ecs.Spawn;
using Il2CppBrokenArrow.DataBase.Models;
using System.Text.Json;
using Il2CppBrokenArrow.Shared.Ecs.MemoryController;

[assembly: MelonInfo(typeof(FAModels.Mod), "FAModels", "0.3.50", "Freedom Arrow")]
[assembly: MelonGame(null, "BrokenArrow")]
namespace FAModels;

// Replaces the look of chosen units with meshes loaded from UserData/FAModels/*.fam (made by famconv.py from glTF).
// The stand-in unit keeps its own prefab, rig and scripts; only its renderers are hidden and new meshes are added.
// Parts named for a bone (for example turret_0) are reparented to that bone, so they turn with it.
public partial class Mod : MelonMod
{
    class Entry { public string file { get; set; } = ""; public float scale { get; set; } = 1; public float[] offset { get; set; } = new float[3]; public float yaw { get; set; } public bool align { get; set; } = true; public string battle { get; set; } = ""; public string hide { get; set; } = ""; public string[] lods { get; set; } = Array.Empty<string>(); public Variant[] variants { get; set; } = Array.Empty<Variant>(); public float[] dustPoint { get; set; } = Array.Empty<float>(); }
    static Dictionary<string, Entry> map = new();
    static string dir = "";
    static readonly List<(GameObject root, Entry e, string unit, float t, int pass)> queue = new();
    static readonly Dictionary<string, Material> mats = new();
    static string fallbackDonor;
    static float upgradeT;
    static readonly Dictionary<string, List<Material>> fallbackMats = new();
    static readonly Dictionary<Material, float> fallbackAlpha = new();
    static float fallbackDonorAlpha;
    static readonly Dictionary<string, Material> donorTinted = new();
    static void SetDonorAlpha(Material m, float a)
    {
        foreach (var prop in new[] { "_BaseColor", "_Color" }) if (m.HasProperty(prop)) { var c = m.GetColor(prop); c.a = a; m.SetColor(prop, c); }
    }
    static Material DonorTinted(Material donor, string name, float a)
    {
        string k = name + "@" + a.ToString("F3", System.Globalization.CultureInfo.InvariantCulture);
        if (donorTinted.TryGetValue(k, out var t) && t != null) return t;
        t = new Material(donor) { name = "FAM_COCKPIT_" + k, hideFlags = HideFlags.DontUnloadUnusedAsset }; SetDonorAlpha(t, a); donorTinted[k] = t;
        MelonLogger.Msg($"FAMODELS_COCKPIT donor={name} alpha={a:F3} (own copy)");
        return t;
    }
    static readonly HashSet<string> donorFallbacks = new();

    public override void OnInitializeMelon()
    {
        dir = Path.Combine(MelonLoader.Utils.MelonEnvironment.UserDataDirectory, "FAModels");
        var cfg = Path.Combine(dir, "models.json");
        if (File.Exists(cfg)) map = JsonSerializer.Deserialize<Dictionary<string, Entry>>(File.ReadAllText(cfg)) ?? new();
        LoadWeaponRules();
        LoadBodyRules();
        Verbose = File.Exists(Path.Combine(dir, "verbose.txt"));
        try { InstallPreload(); } catch (Exception ex) { MelonLogger.Error("FAMODELS preload not installed: " + ex.Message); }
        try { InstallPaintSchemes(HarmonyInstance); } catch (Exception ex) { MelonLogger.Error("FAMODELS_PAINT not installed; models keep their default colours: " + ex.Message); }
        try { InstallLowSettings(); } catch (Exception ex) { MelonLogger.Error("FAMODELS low-settings switch not installed; armory keeps full models: " + ex.Message); }
        var m = typeof(UnitBuilder).GetMethods().First(x => x.Name == "InitView" && x.GetParameters().Length == 4 && x.GetParameters()[1].ParameterType == typeof(Units));
        HarmonyInstance.Patch(m, postfix: new HarmonyMethod(typeof(Mod), nameof(After)));
        var infantryView = typeof(UnitBuilder).GetMethods().First(x => x.Name == "InitInfantryView" && x.GetParameters().Length == 4);
        HarmonyInstance.Patch(infantryView, postfix: new HarmonyMethod(typeof(Mod), nameof(AfterInfantryWeapons)));
        LoggerInstance.Msg($"FAMODELS ready: {map.Count} unit(s) mapped from {cfg}");
    }

    static void After(UnitModelInfo unitModel, Units unitData, IUnitLoadScope scope)
    {
        try
        {
            if (unitData == null || unitModel?.PrefabRootScript == null) return;
            QueueBodies(unitModel, unitData.Id, LowModels || scope?.TryCast<Il2CppBrokenArrow.Client.Ecs.Controllers.BattleLifetime>() != null);
            QueueWeapons(unitModel, unitData.Id, scope?.TryCast<Il2CppBrokenArrow.Client.Ecs.Controllers.BattleLifetime>() != null);
            if (!map.TryGetValue(unitData.Name, out var e)) return;
            // Osama 13 Nov (Lynx ATV): an entry with no file and a "hide" pattern keeps the stand-in model and only hides
            // its renderers whose object path matches the pattern (for example the seated US soldiers on the M1301 ISV).
            if (e.file == "" && e.hide != "") { HideMatching(unitModel.PrefabRootScript.gameObject, e.hide, unitData.Name); queue.Add((unitModel.PrefabRootScript.gameObject, e, unitData.Name, Time.realtimeSinceStartup, 1)); return; }
            // In a battle, use the entry's low-res copy (smaller textures and mesh; aircraft with the gear up) when it has one.
            // The armory keeps the full-fidelity file, except on Potato or Low models quality (LowSettings.cs, 0.3.28).
            bool battle = LowModels || scope?.TryCast<Il2CppBrokenArrow.Client.Ecs.Controllers.BattleLifetime>() != null;
            // 0.3.39: loadout variants (OptionVariants.cs) pick other files; the view is re-checked while it lives.
            if (e.variants.Length > 0) { int vi = VariantIndex(e, unitData); variantViews.Add((unitModel.PrefabRootScript.gameObject, unitData, e, unitData.Name, battle, vi)); e = Resolve(e, vi, battle); }
            else if (e.battle != "" && battle)
                e = new Entry { file = e.battle, scale = e.scale, offset = e.offset, yaw = e.yaw, align = e.align, lods = e.lods };
            // 0.3.49 (Lateralus 25 Nov 16:4x: "the mod's new custom units pop in at the highest LOD before switching to the lowest LOD, the vanilla
            // units don't do that... Can that be changed only for the armory?"): the armory entry kept the battle detail levels ("lods"), so the
            // full armory model got a LODGroup with the battle copies under it and the armory camera dropped it to the lightest one. The armory
            // (not Potato/Low, which use the battle model) now shows only the full model: one level, no LODGroup (Apply makes one only for 2+).
            else if (!battle && e.lods.Length > 0)
                e = new Entry { file = e.file, scale = e.scale, offset = e.offset, yaw = e.yaw, align = e.align, hide = e.hide };
            // Hide immediately; Apply restores the original and cancels queued re-hides on failure.
            queue.Add((unitModel.PrefabRootScript.gameObject, e, unitData.Name, Time.realtimeSinceStartup, 0));
            Hide(unitModel.PrefabRootScript.gameObject);
        }
        catch (Exception ex) { MelonLogger.Error("FAMODELS hook: " + ex); }
    }

    // Inspection camera: write a unit name (or "off") to UserData/FAModels/cam.txt; a separate camera then
    // follows the first live FAM unit with that name, for close-up screenshots in a battle.
    static Camera cam; static float camCheck, camPicked; static string camWant = ""; static GameObject camTarget;
    static void CamTick()
    {
        if (Time.realtimeSinceStartup - camCheck > 1f)
        {
            camCheck = Time.realtimeSinceStartup;
            var f = Path.Combine(dir, "cam.txt"); var w = File.Exists(f) ? File.ReadAllText(f).Trim() : "off";
            if (w != camWant) { camWant = w; camTarget = null; MelonLogger.Msg($"FAMODELS cam -> {w}"); }
            if (camWant != "off" && Time.realtimeSinceStartup - camPicked > 6f)
            {
                camPicked = Time.realtimeSinceStartup;
                // Prefer the instance whose turret is turned furthest from straight ahead (it is aiming at something).
                float best = -1; GameObject pick = null;
                foreach (var t in live) if (t.root != null && t.unit == camWant)
                {
                    // Living units turn or move; wrecks do neither, so the most recent of the two picks a live one.
                    int k = t.root.GetInstanceID();
                    // Only units the player can see: SyncVisibility switches our renderers off for units hidden by fog of war.
                    var hr = t.root.transform.Find("FAM_holder"); var mr0 = hr == null ? null : hr.GetComponentInChildren<MeshRenderer>(true); if (mr0 == null || !mr0.enabled) continue;
                    float y = Mathf.Max(lastTurn.TryGetValue(k, out var when) ? when : 0, lastMove.TryGetValue(k, out var mv) ? mv : 0);
                    if (y > best) { best = y; pick = t.root; }
                }
                if (pick != null) camTarget = pick;
            }
        }
        bool on = camWant != "off" && camTarget != null;
        if (on && cam == null) { var go = new GameObject("FAM_InspectCam"); UnityEngine.Object.DontDestroyOnLoad(go); cam = go.AddComponent<Camera>(); cam.depth = 100; cam.fieldOfView = 40; cam.nearClipPlane = 0.3f; cam.farClipPlane = 5000; }
        if (cam != null) cam.enabled = on;
        if (!on) return;
        var parts = camWant.Length > 0 ? camWant : "";
        float dist = 14f, h = 5f, yaw = (Time.realtimeSinceStartup * 12f) % 360f;
        var r = camTarget.transform; var c = r.position + Vector3.up * 1.5f;
        cam.transform.position = c + Quaternion.Euler(0, yaw, 0) * new Vector3(0, h, -dist);
        cam.transform.LookAt(c);
    }
    static readonly List<(GameObject root, string unit)> live = new();
    static readonly Dictionary<int, List<Renderer>> origs = new();
    // The game toggles the stand-in's renderers for fog of war and LOD; ours follow whatever the stand-in would show.
    // 0.3.29: the FA renderers of each unit are collected once (they never change after the swap), not by walking the unit's whole
    // object tree 5 times a second for every live unit. The list is refreshed every 5 s, for weapon parts attached later.
    static readonly Dictionary<int, MeshRenderer[]> famRenderers = new();
    static readonly Dictionary<int, Il2CppBrokenArrow.Client.Ecs.Animations.AnimationHub> hubs = new();
    static readonly HashSet<int> deadLogged = new();
    static bool IsDead(GameObject root, int k)
    {
        if (deadLogged.Contains(k)) return true;
        if (!hubs.TryGetValue(k, out var hub) || hub == null) { hub = root.GetComponentInChildren<Il2CppBrokenArrow.Client.Ecs.Animations.AnimationHub>(true); hubs[k] = hub; }
        var dead = hub?.DeadModel;
        return dead != null && dead.activeInHierarchy;
    }
    static readonly Dictionary<int, float> famRenderersT = new();
    static void SyncVisibility()
    {
        // 0.3.34 (5v5 detail log: "visibility sync" 16+ ms frames): units spawned together refreshed their renderer lists in the same check,
        // every 15 s. At most 8 refreshes per check now (0.2 s apart); a unit over the limit keeps its list until a later check.
        int refreshes = 0;
        for (int i = live.Count - 1; i >= 0; i--)
        {
            var (root, unit) = live[i];
            if (root == null) { live.RemoveAt(i); continue; }
            int k = root.GetInstanceID();
            if (!origs.TryGetValue(k, out var os) || os.Count == 0) continue;
            bool vis = false;
            foreach (var o in os) if (o != null && o.enabled && o.gameObject.activeInHierarchy) { vis = true; break; }
            // 0.3.29 (Osama 15 Nov: "clean model dead, we should just remove it so there's no wreck"): when the game switches the unit
            // to its dead model (AnimationHub.DeadModel active), our model goes too. The vanilla wreck stays hidden, so nothing remains.
            if (vis && IsDead(root, k)) { vis = false; if (deadLogged.Add(k)) MelonLogger.Msg($"FAMODELS {unit}: destroyed, model removed (no wreck)"); }
            // 0.3.31: the renderer list is refreshed every 15 s (was: every 5 s, plus a native null check of every renderer every 0.2 s).
            if (!famRenderers.TryGetValue(k, out var rs) || (refreshes < 8 && Time.realtimeSinceStartup - famRenderersT.GetValueOrDefault(k) > 15f))
            {
                refreshes++;
                var list = new List<MeshRenderer>();var h = root.transform.Find("FAM_holder");
                if (h != null) list.AddRange(h.GetComponentsInChildren<MeshRenderer>(true));
                foreach (var t in root.GetComponentsInChildren<Transform>(true)) if (t.name.StartsWith("FAM_") && t.name != "FAM_holder" && t.parent != h) list.AddRange(t.GetComponentsInChildren<MeshRenderer>(true));
                famRenderers[k] = rs = list.Distinct().ToArray(); famRenderersT[k] = Time.realtimeSinceStartup;
            }
            foreach (var fr in rs) if (fr != null && fr.enabled != vis) fr.enabled = vis;
        }
        if (famRenderers.Count > 2000) { famRenderers.Clear(); famRenderersT.Clear(); hubs.Clear(); }
    }
    static float syncT, yawT;
    static readonly Dictionary<int, float> lastYaw = new(), lastTurn = new(), lastMove = new();
    static readonly Dictionary<int, Vector3> lastPos = new();
    // Turret check: every 2 s, log any FAM unit whose turret_0 turned more than 10 degrees since its last report.
    static void YawLog()
    {
        foreach (var (root, unit) in live)
        {
            if (root == null) continue;
            { int k = root.GetInstanceID(); var p = root.transform.position;
              if (lastPos.TryGetValue(k, out var was0) && (p - was0).sqrMagnitude > 0.25f) lastMove[k] = Time.realtimeSinceStartup;
              lastPos[k] = p; }
            var tb = Find(root.transform, "turret_0"); if (tb == null) continue;
            var fam = Find(root.transform, "FAM_turret_0");
            // Yaw of our turret part relative to the hull: this is what the player sees.
            float y = fam == null ? 0 : Mathf.DeltaAngle(root.transform.eulerAngles.y, fam.eulerAngles.y); int id = root.GetInstanceID();
            if (!lastYaw.TryGetValue(id, out var was)) { lastYaw[id] = y; continue; }
            if (Mathf.Abs(Mathf.DeltaAngle(was, y)) > 10f) { lastYaw[id] = y; float gy = float.NaN;
                // Reference: a stand-in mesh that hangs off the same turret_0 bone (not off a second turret such as a commander's MG mount).
                if (origs.TryGetValue(id, out var os)) foreach (var o in os) { if (o == null) continue; var n = o.transform; bool under = false;
                    for (var q = n.parent; q != null && q != root.transform; q = q.parent) { if (q == tb) { under = true; break; } if (q.name.StartsWith("turret_")) break; }
                    if (under) { gy = Mathf.DeltaAngle(root.transform.eulerAngles.y, n.eulerAngles.y); break; } }
                // Skinned stand-ins: the vanilla turret mesh is deformed by the turret_0 bone itself, so the bone's yaw is the vanilla turret's yaw.
                string skin = "";
                if (float.IsNaN(gy) && origs.TryGetValue(id, out var os2)) foreach (var o in os2) { var smr = o == null ? null : o.TryCast<SkinnedMeshRenderer>(); if (smr == null) continue;
                    foreach (var bn in smr.bones) if (bn == tb) { gy = Mathf.DeltaAngle(root.transform.eulerAngles.y, tb.eulerAngles.y); skin = $" (vanilla mesh {smr.name} skinned to turret_0)"; break; }
                    if (!float.IsNaN(gy)) break; }
                MelonLogger.Msg($"FAMODELS turret {unit} #{id}: ours {was:F0} -> {y:F0} deg, game turret mesh {gy:F0} deg{skin} (FAM turret parts {root.GetComponentsInChildren<Transform>(true).Count(x => x.name.StartsWith("FAM_turret"))}) {Vis(fam)}"); }
        }
    }

    // 0.3.29 (Osama 15 Nov: "I'm having frame stutters in game"): every frame over 50 ms in a match is logged with what FAModels did in
    // the frame before it, so a hitch can be blamed on us or ruled out. verbose.txt in UserData/FAModels brings back per-soldier lines.
    static bool Verbose;
    static int bodySwapsThisFrame, modelSwapsThisFrame, hitchCount;
    static float hitchLogT;
    static void HitchLog()
    {
        float dt = Time.unscaledDeltaTime;
        if (dt > 0.05f && Time.realtimeSinceStartup > 30f)
        {
            hitchCount++;
            if (Time.realtimeSinceStartup - hitchLogT > 0.5f || dt > 0.2f)
            { hitchLogT = Time.realtimeSinceStartup; MelonLogger.Msg($"FAMODELS hitch {dt * 1000f:F0} ms (#{hitchCount}): previous frame FAModels did {modelSwapsThisFrame} model swap(s), {lodLevelsThisFrame} later detail level(s), {modelsDeferredThisFrame} deferred, {bodySwapsThisFrame} body swap(s), {preload.Count} preload(s) left"); }
        }
        bodySwapsThisFrame = 0; modelSwapsThisFrame = 0; lodLevelsThisFrame = 0; modelsDeferredThisFrame = 0;
        if (lodLevels.Count > 4000) lodLevels.Clear();
    }

    // 0.3.34 (Osama 17 Nov 2026: "detailed logging and tracking"): each part of the update is timed; an update over 15 ms logs which part
    // took the time (FAMODELS slow update), so a spike in the FREEDOM_ARROW_SLOW_FRAME lines can be traced inside FAModels.
    static readonly long[] sec = new long[9];
    static readonly string[] secNames = { "preload", "body swap", "body poll", "infantry weapons", "visibility sync", "camera", "cockpit upgrade", "camera, cockpits and model swaps", "PLA review" };
    static int slowUpdates;
    static long Mark(int i, long t0) { long t = System.Diagnostics.Stopwatch.GetTimestamp(); sec[i] += t - t0; return t; }
    public override void OnUpdate()
    {
        Array.Clear(sec, 0, sec.Length); long start = System.Diagnostics.Stopwatch.GetTimestamp(), t = start;
        try { HitchLog(); } catch { }
        try { MemoryLog(); } catch (Exception ex) { MelonLogger.Error("FAMODELS memory log: " + ex.Message); }
        try { TickPlaReview(); } catch(Exception e) { MelonLogger.Error("PLA_REVIEW: "+e.Message); }
        t = Mark(8, t);
        try { TickPreload(); } catch (Exception ex) { MelonLogger.Error("FAMODELS preload: " + ex.Message); }
        t = Mark(0, t);
        try { TickInfantryBodies(true); } catch (Exception ex) { MelonLogger.Error("FAMODELS body swap: " + ex.Message); }
        t = Mark(1, t);
        try { TickInfantryBodies(); } catch (Exception ex) { MelonLogger.Error("FAMODELS body poll: " + ex.Message); }
        t = Mark(2, t);
        try { TickInfantryWeapons(); } catch (Exception ex) { MelonLogger.Error("FAMODELS weapon poll: " + ex.Message); }
        t = Mark(3, t);
        if (Time.realtimeSinceStartup - syncT > 0.2f) { syncT = Time.realtimeSinceStartup; try { SyncVisibility(); } catch (Exception ex) { MelonLogger.Error("FAMODELS sync: " + ex.Message); } }
        t = Mark(4, t);
        try { TickVariants(); } catch (Exception ex) { MelonLogger.Error("FAMODELS variants: " + ex.Message); }
        try { UpdateRest(); } finally { t = Mark(7, t); SlowUpdateLog(start, t); }
    }
    static void SlowUpdateLog(long start, long end)
    {
        double ms = (end - start) * 1000.0 / System.Diagnostics.Stopwatch.Frequency;
        if (ms < 15 || slowUpdates++ > 400) return;
        MelonLogger.Msg($"FAMODELS slow update {ms:F0} ms: " + string.Join(", ", Enumerable.Range(0, sec.Length).Where(i => sec[i] * 1000.0 / System.Diagnostics.Stopwatch.Frequency >= 1).OrderByDescending(i => sec[i])
            .Select(i => $"{secNames[i]} {sec[i] * 1000.0 / System.Diagnostics.Stopwatch.Frequency:F0} ms")) + $" | body swaps {bodySwapsThisFrame}, model swaps {modelSwapsThisFrame}");
    }
    // 0.3.34: UpgradeFallbacks searches every loaded material (FindObjectsOfTypeAll, 25-39 ms in a 5v5). With a donor that never loads in a
    // battle it ran every 10 s for the whole match; now at most 3 tries per scene, 10, 20 and 40 s apart, starting again in each new scene.
    static float upgradeGap = 10f; static int upgradeTries;
    static void UpdateRest()
    {
        // 0.3.31: the turret-yaw diagnostic walked every China unit's whole transform tree every 2 s; only with verbose.txt now.
        if (Verbose && Time.realtimeSinceStartup - yawT > 2f) { yawT = Time.realtimeSinceStartup; try { YawLog(); } catch (Exception ex) { MelonLogger.Error("FAMODELS yaw: " + ex.Message); } }
        try { CamTick(); } catch (Exception ex) { MelonLogger.Error("FAMODELS cam: " + ex.Message); camWant = "off"; }
        if (fallbackMats.Count > 0 && upgradeTries < 3 && Time.realtimeSinceStartup - upgradeT > upgradeGap) { upgradeT = Time.realtimeSinceStartup; upgradeGap = Math.Min(upgradeGap * 2f, 320f); upgradeTries++; try { UpgradeFallbacks(false); } catch (Exception ex) { MelonLogger.Error("FAMODELS cockpit upgrade: " + ex.Message); } }
        long budgetStart = System.Diagnostics.Stopwatch.GetTimestamp();
        for (int i = queue.Count - 1; i >= 0; i--)
        {
            var q = queue[i];
            if (q.root == null) { queue.RemoveAt(i); continue; }
            // 0.9.0-dev.13 (perf probe): the 1 s re-hide pass ran for the whole life of every China unit (a full renderer search of
            // the unit each second). Run F's late renderers were each re-hidden once, in the first seconds; stop after 60 passes.
            if (q.pass > 60) { queue.RemoveAt(i); continue; }
            // 0.3.25 (Osama 14 Nov): no fixed 0.5 s wait before the swap. Build on the next frame; Apply waits (up to 0.5 s)
            // only while a turret bone the model needs is not there yet. The 1 s re-hide pass for late renderers stays.
            float wait = q.pass == 0 ? 0f : 1.0f;
            if (Time.realtimeSinceStartup - q.t < wait) continue;
            // 0.3.45: swaps stop for this frame after ModelBudgetMs (LodStreaming.cs); the rest wait hidden, as during the bone wait.
            if (q.pass == 0 && q.e.file != "" && SinceMs(budgetStart) > ModelBudgetMs) { modelsDeferredThisFrame++; continue; }
            try { if (!Apply(q.root, q.e, q.unit, q.pass == 0, Time.realtimeSinceStartup - q.t, stream: true)) continue; }
            catch (Exception ex) { MelonLogger.Error($"FAMODELS {q.unit}: replacement rejected; original retained: {ex}"); queue.RemoveAt(i); continue; }
            queue[i] = (q.root, q.e, q.unit, Time.realtimeSinceStartup, q.pass + 1);
        }
        try { TickLodUpgrades(budgetStart); } catch (Exception ex) { MelonLogger.Error("FAMODELS detail levels: " + ex.Message); }
        try { TickPreloadHeavy(budgetStart); } catch (Exception ex) { MelonLogger.Error("FAMODELS preload levels: " + ex.Message); }
    }

    // 0.3.27 (Osama 14 Nov: "make sure the standin models never pop up"): the game spawns turrets, gunners and LOD children
    // a few frames after InitView. 0.3.26 re-hid those only on the 1 s pass, so the stand-in turret showed for up to a second
    // (log: ZTQ-15 Light 14, ZBD-04A 9, HQ-9B 6 late renderers). Now every frame, after the game's own Update and before the
    // frame is drawn: while the replacement waits, and for 5 s after the swap. The 1 s pass stays as the long-term check.
    // The 1 s pass advances q.pass once a second after the swap, so passes 1-5 are the first 5 s.
    // Called from OnLateUpdate (InfantryBodies.cs).
    static void LateHide()
    {
        try
        {
            foreach (var q in queue)
            {
                if (q.root == null || q.e.file == "" || q.pass > 5) continue;
                int n = Hide(q.root);
                if (n > 0 && q.pass > 0) MelonLogger.Msg($"FAMODELS {q.unit}: hid {n} late renderer(s) on {q.root.name} in the frame they appeared (second {q.pass} after the swap)");
            }
        }
        catch (Exception ex) { MelonLogger.Error("FAMODELS late hide: " + ex.Message); }
    }

    static string Vis(Transform fam)
    {
        var r = fam == null ? null : fam.GetComponentInChildren<MeshRenderer>(true);
        if (r == null) return "no turret renderer";
        var p = fam.parent; return $"turret renderer visible={r.isVisible} enabled={r.enabled} active={r.gameObject.activeInHierarchy} off={r.forceRenderingOff} bone={(p != null ? p.name : "-")} boneActive={(p != null && p.gameObject.activeInHierarchy)}";
    }
    static Transform Find(Transform t, string name)
    {
        if (t.name == name) return t;
        for (int i = 0; i < t.childCount; i++) { var r = Find(t.GetChild(i), name); if (r != null) return r; }
        return null;
    }

    static readonly HashSet<string> hideLogged = new();
    static void HideMatching(GameObject root, string pattern, string unit)
    {
        var rx = new System.Text.RegularExpressions.Regex(pattern, System.Text.RegularExpressions.RegexOptions.IgnoreCase);
        int n = 0, fresh = 0; var names = new List<string>();
        foreach (var r in root.GetComponentsInChildren<Renderer>(true))
        {
            string path = r.gameObject.name; for (var q = r.transform.parent; q != null && q != root.transform; q = q.parent) path = q.name + "/" + path;
            bool hit = rx.IsMatch(path);
            if (hit) { if (!r.forceRenderingOff) fresh++; r.forceRenderingOff = true; n++; }
            if (hideLogged.Add(unit + "|" + path)) names.Add((hit ? "-" : "+") + path);
        }
        if (fresh > 0) MelonLogger.Msg($"FAMODELS {unit}: hid {fresh} new matching renderer(s) ({n} total) for /{pattern}/");
        if (names.Count > 0) MelonLogger.Msg($"FAMODELS {unit} renderers: " + string.Join(" | ", names));
    }

    // Hide the stand-in only after its replacement has loaded completely.
    // ROC 28 Nov 2026 (Shawn: "Fix this strange dust on the wheel", Thunderbolt-2000 on the M270 stand-in): vanilla vehicles spawn their dust
    // effect at child nodes named dust_point_left / dust_point_right, placed inside the vanilla tracks or wheels. On a stand-in with another
    // running gear the dust shows on the new model (TB2000: on the front wheel). An entry's "dustPoint": [x, y, z] (stand-in root space; each node
    // keeps its own side, x sign) moves them inside the new model's wheels.
    static void MoveDustPoints(GameObject root, float[] p, string unit)
    {
        foreach (var t in root.GetComponentsInChildren<Transform>(true))
        {
            if (!t.name.StartsWith("dust_point")) continue;
            var was = root.transform.InverseTransformPoint(t.position);
            t.position = root.transform.TransformPoint(new Vector3(Mathf.Abs(p[0]) * (was.x < 0 ? -1f : 1f), p[1], p[2]));
            MelonLogger.Msg($"FAMODELS {unit}: {t.name} ({was.x:F2},{was.y:F2},{was.z:F2}) -> ({(was.x < 0 ? -1 : 1) * Mathf.Abs(p[0]):F2},{p[1]:F2},{p[2]:F2})");
        }
    }
    static int Hide(GameObject root)
    {
        int hidden = 0;
        foreach (var r in root.GetComponentsInChildren<Renderer>(true))
        {
            if (r.forceRenderingOff || r.gameObject.name.StartsWith("FAM_")) continue;
            if (r.TryCast<MeshRenderer>() != null || r.TryCast<SkinnedMeshRenderer>() != null) { if (!r.forceRenderingOff) { hidden++; r.forceRenderingOff = true; origs.TryAdd(root.GetInstanceID(), new()); origs[root.GetInstanceID()].Add(r); } }
        }
        return hidden;
    }

    // 0.3.25 (Osama 14 Nov): keep each parsed model (meshes and materials) after the first load, as the infantry bodies do.
    // Reopening a card now only creates GameObjects. The game unloads unused assets between scenes, so the kept meshes are
    // flagged DontUnloadUnusedAsset and every entry is checked for destroyed objects before reuse (0.3.17 lesson).
    sealed class FamSub { public Mesh mesh; public Material mat; }
    sealed class FamPart { public string bone = ""; public List<FamSub> subs = new(); }
    static readonly Dictionary<string, List<FamPart>> famCache = new();
    static List<FamPart> LoadFam(string file, out bool kept)
    {
        famUsed[file] = Time.realtimeSinceStartup;   // 0.3.35 (Unload.cs): most recently used models are freed last
        if (famCache.TryGetValue(file, out var c) && c.All(p => p.subs.All(x => x.mesh != null && x.mat != null))) { kept = true; return c; }
        kept = false;
        var mj = Path.Combine(dir, Path.ChangeExtension(file, null) + ".mat.json");
        var mp = File.Exists(mj) ? JsonSerializer.Deserialize<Dictionary<string, MatP>>(File.ReadAllText(mj)) ?? new() : new Dictionary<string, MatP>();
        // 0.3.31: the file was read, converted and given tangents on a background thread (Background.cs); only the Unity objects
        // are made here. Without a prefetch (a unit not in any deck, the armory) the same preparation runs here, as before.
        var data = famJobs.TryRemove(file, out var job) ? job.Result : ParseFamData(file);
        var parts = new List<FamPart>();
        foreach (var pd in data)
        {
            var part = new FamPart { bone = pd.bone };
            for (int s = 0; s < pd.subs.Count; s++)
            {
                var d = pd.subs[s]; var col = new Color(d.col[0], d.col[1], d.col[2], d.col[3]); int nv = d.pos.Length / 3;
                var pos = new Il2CppStructArray<Vector3>(nv); for (int k = 0; k < nv; k++) pos[k] = new Vector3(d.pos[3 * k], d.pos[3 * k + 1], d.pos[3 * k + 2]);
                var uv = new Il2CppStructArray<Vector2>(nv); for (int k = 0; k < nv; k++) uv[k] = new Vector2(d.uv[2 * k], d.uv[2 * k + 1]);
                var idx = new Il2CppStructArray<int>(d.idx.Length); for (int k = 0; k < d.idx.Length; k++) idx[k] = d.idx[k];
                var mesh = new Mesh { name = $"FAM_{file}_{part.bone}_{s}" };
                mesh.hideFlags = HideFlags.DontUnloadUnusedAsset;
                mesh.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;
                mesh.vertices = pos; mesh.uv = uv; mesh.triangles = idx;
                if (d.anyN) { var nrm = new Il2CppStructArray<Vector3>(nv); for (int k = 0; k < nv; k++) nrm[k] = new Vector3(d.nrm[3 * k], d.nrm[3 * k + 1], d.nrm[3 * k + 2]); mesh.normals = nrm; }
                else mesh.RecalculateNormals();
                mesh.RecalculateBounds();
                mp.TryGetValue(MatKey(d.tex, col), out var matp);
                var mat = Mat(d.tex, col, matp);
                mat.hideFlags |= HideFlags.DontUnloadUnusedAsset;
                if (!string.IsNullOrEmpty(matp?.cockpitDonor) || mat.IsKeywordEnabled("_NORMALMAP"))
                {
                    // HDRP normal maps need tangents; the .fam carries none, so they come from the background thread.
                    if (d.tan.Length == 4 * nv) { var tan = new Il2CppStructArray<Vector4>(nv); for (int k = 0; k < nv; k++) tan[k] = new Vector4(d.tan[4 * k], d.tan[4 * k + 1], d.tan[4 * k + 2], d.tan[4 * k + 3]); mesh.tangents = tan; }
                    else mesh.RecalculateTangents();
                }
                part.subs.Add(new FamSub { mesh = mesh, mat = mat });
            }
            parts.Add(part);
        }
        famCache[file] = parts;
        return parts;
    }
    // The stand-in's own LOD switch heights (screen share where each level ends), so our levels change where vanilla's would.
    // Without a stand-in LODGroup: 0.10 / 0.04 / 0.005 of the screen height, the values the vanilla stand-ins use (dev.13 run F log:
    // ZBD-20, Type 59). The earlier 0.25 / 0.10 / 0.02 culled a unit under 2% of the screen height, which is a tank seen from far up.
    // Past the last level the model is culled, as vanilla's is.
    // 0.3.45: levels not built yet (null, LodStreaming.cs) are covered by the next lighter level that is built, so a unit with only its
    // lightest level shows it at every distance and is culled where the full set would be.
    static int lodLogged;
    static void SetLevels(GameObject root, GameObject holder, List<Renderer>[] byLevel, string unit)
    {
        float[] h = { 0.10f, 0.04f, 0.005f };
        var native = root.GetComponentsInChildren<LODGroup>(true).FirstOrDefault(g => g.gameObject != holder);
        if (native != null) { var nl = native.GetLODs(); for (int i = 0; i < Math.Min(nl.Length, h.Length); i++) h[i] = nl[i].screenRelativeTransitionHeight; }
        int n = byLevel.Length; float H(int i) => i < h.Length ? h[i] : h[h.Length - 1] * 0.5f;
        var built = Enumerable.Range(0, n).Where(i => byLevel[i] != null).ToList();
        var lods = new Il2CppReferenceArray<LOD>(built.Count);
        for (int k = 0; k < built.Count; k++) lods[k] = new LOD(H(k + 1 < built.Count ? built[k + 1] - 1 : n - 1), new Il2CppReferenceArray<Renderer>(byLevel[built[k]].ToArray()));
        var g = holder.GetComponent<LODGroup>(); if (g == null) g = holder.AddComponent<LODGroup>();
        g.SetLODs(lods); g.RecalculateBounds();
        // dev.13 LOD test (Osama 15 Nov: "make sure ... the lod models we added actually helped"): the first 20 always, the rest with verbose.
        if (built.Count == n && (Verbose || ++lodLogged <= 20)) MelonLogger.Msg($"FAMODELS {unit}: {n} detail levels at {string.Join("/", h.Take(n).Select(x => x.ToString("F3")))} of the screen ({(native != null ? "stand-in's" : "default")})");
    }
    static float[] Floats(BinaryReader f, int n) { var b = f.ReadBytes(n * 4); var r = new float[n]; Buffer.BlockCopy(b, 0, r, 0, b.Length); return r; }

    // Returns false to try again next frame (pass 0 only): while a needed turret bone is not spawned yet (at most 0.5 s) or, from the
    // spawn queue (stream), while the model file is still being read on a background thread.
    // 0.3.45 (End 24 Nov, rejoin freezes: "it should start loading the lowest LOD first and use that until other LODs finished loading. a few
    // frames with worse LOD are fine, just prevent blocking and crowding the GPU"). His rejoin log had 20 model files read on the main thread
    // (1,872 ms) and up to 78 swaps in one frame. From the spawn queue, a model whose levels are not all built yet has them read in the
    // background, builds only its lightest level once that file is ready, and gets the other levels in later frames (LodStreaming.cs).
    // Models already built still build every level at once. 0.3.46: the match-start burst builds only the lightest level and the
    // heavier levels follow during deployment (TickPreloadHeavy); a unit that spawns before that gets them over later frames.
    static bool Apply(GameObject root, Entry e, string unit, bool build, float age, bool stream = false)
    {
        // Hide-only entries: turrets, gunners and LOD children can be spawned after InitView, so re-check every pass.
        if (e.file == "") { if (e.hide != "") HideMatching(root, e.hide, unit); return true; }
        if (!build) { int late = Hide(root); if (late > 0) MelonLogger.Msg($"FAMODELS {unit}: re-hid {late} late renderer(s) on {root.name}"); return true; }
        var sw = System.Diagnostics.Stopwatch.StartNew();
        // 0.3.31: distance detail levels like vanilla's LOD groups. A battle entry may name lighter copies ("lods": [l1, l2]); each level
        // gets its own parts, and a LODGroup switches between them at the stand-in's own distances (SetLevels). Level 0 is e.file.
        var files = new List<string> { e.file };
        foreach (var lf in e.lods) if (lf != "" && File.Exists(Path.Combine(dir, lf))) files.Add(lf);
        // 0.3.48 (Lateralus 25 Nov 15:3x: "The hitch when zooming in the first time is unacceptable"): back to 0.3.46. 0.3.47 started every
        // model on its lightest level and built heavier levels when the camera came close, which hitched on the first zoom-in.
        bool streamed = stream && !files.All(KeptFam);
        if (streamed) { bool lightReady = false; for (int i = 0; i < files.Count; i++) { bool r = StreamReady(files[i]); if (i == files.Count - 1) lightReady = r; } if (!lightReady) return false; }
        var buildNow = streamed ? new List<int> { files.Count - 1 } : Enumerable.Range(0, files.Count).ToList();
        var fam = LoadFam(files[buildNow[0]], out bool kept);
        float loadMs = (float)sw.Elapsed.TotalMilliseconds;
        if (age < 0.5f && fam.Any(p => p.bone != "root" && Find(root.transform, p.bone) == null)) return false;
        var holder = new GameObject("FAM_holder");
        holder.SetActive(false);
        var made = new List<(GameObject part, string bone)>();
        try
        {
        holder.transform.SetParent(root.transform, false);
        holder.transform.localPosition = new Vector3(e.offset[0], e.offset[1], e.offset[2]);
        holder.transform.localRotation = Quaternion.Euler(0, e.yaw, 0);
        holder.transform.localScale = Vector3.one * e.scale;
        int verts = 0, parts = 0;
        var byLevel = new List<Renderer>[files.Count];
        for (int k = 0; k < buildNow.Count; k++)
        {
            int v = 0, L = buildNow[k];
            byLevel[L] = BuildLevel(holder, k == 0 ? fam : LoadFam(files[L], out _), L, made, ref v);
            if (k == 0) { verts = v; parts = made.Count; }
        }
        // Line the turret up with the stand-in's turret bone (x/z), so it turns about its own ring; then reparent.
        bool aligned = false;
        foreach (var (part, bone) in made)
        {
            if (bone == "root") continue;
            var b = Find(root.transform, bone);
            if (b == null) { MelonLogger.Warning($"FAMODELS {unit}: bone {bone} not found; part stays on the hull"); continue; }
            if (!aligned && e.align)
            {
                // 0.3.45: the shift is the same for every copy of a unit type, so it is worked out once (it copied every turret vertex at each spawn).
                string ak = $"{unit}|{e.file}|{e.offset[0]},{e.offset[1]},{e.offset[2]}|{e.yaw}|{e.scale}";
                bool have = alignCache.TryGetValue(ak, out var d);
                var mfs = have ? null : part.GetComponentsInChildren<MeshFilter>();
                if (!have && mfs.Length > 0)
                {
                    // Turret ring centre: mean x/z of the turret's lowest 0.35 m, in root space (a long barrel would skew a box centre).
                    float minY = float.MaxValue; var pts = new List<Vector3>();
                    foreach (var mf in mfs) { var vs = mf.sharedMesh.vertices; for (int k = 0; k < vs.Length; k += 7) { var w = root.transform.InverseTransformPoint(mf.transform.TransformPoint(vs[k])); pts.Add(w); if (w.y < minY) minY = w.y; } }
                    double sx = 0, sz = 0; int n = 0; foreach (var w in pts) if (w.y < minY + 0.35f) { sx += w.x; sz += w.z; n++; }
                    var c = new Vector3((float)(sx / n), 0, (float)(sz / n)); var bp = root.transform.InverseTransformPoint(b.position);
                    d = new Vector3(bp.x - c.x, 0, bp.z - c.z); alignCache[ak] = d; have = true;
                    MelonLogger.Msg($"FAMODELS {unit}: moved model ({d.x:F2}, {d.z:F2}) m to put the turret on {bone}");
                }
                if (have) holder.transform.localPosition += d;
                aligned = true;
            }
            part.transform.SetParent(b, true);
            { string path = b.name; for (var q = b.parent; q != null && q != root.transform; q = q.parent) path = q.name + "/" + path;
              var rp = root.transform.InverseTransformPoint(part.transform.position); var mr = part.GetComponentInChildren<MeshRenderer>(true);
              MelonLogger.Msg($"FAMODELS {unit}: {bone} -> {path} active={b.gameObject.activeInHierarchy} scale={b.lossyScale} partPos=({rp.x:F2},{rp.y:F2},{rp.z:F2}) bounds={(mr != null ? mr.bounds.center - root.transform.position : Vector3.zero)}"); }
        }
        if (files.Count > 1) SetLevels(root, holder, byLevel, unit);
        int hidden = Hide(root);
        if (e.dustPoint.Length == 3) MoveDustPoints(root, e.dustPoint, unit);
        holder.SetActive(true);
        live.Add((root, unit));
        if (buildNow.Count < files.Count) QueueLodUpgrade(root, holder, unit, files, byLevel, made);
        try { ApplyPaint(root, unit); } catch (Exception ex) { MelonLogger.Warning("FAMODELS_PAINT apply: " + ex.Message); }
        modelSwapsThisFrame++;
        // 0.3.35 (Unload.cs): remember which units use which files; in the menu, free all but the most recent unused models.
        foreach (int L in buildNow) NoteUse(files[L], root);
        if (!kept && inMenu) FreeUnused(MenuKeep, "menu");
        // 0.3.29: infantry weapon swaps log only with UserData/FAModels/verbose.txt (they were ~1,600 lines a session).
        if (Verbose || !kept || !unit.StartsWith("infantry ")) MelonLogger.Msg($"FAMODELS {unit}: hid {hidden} renderer(s), added {parts} part(s), {verts} vertices from {files[buildNow[0]]} in {sw.Elapsed.TotalMilliseconds:F0} ms ({(kept ? "kept model" : $"loaded from file in {loadMs:F0} ms")}, after {age:F2} s){(buildNow.Count < files.Count ? $"; lightest of {files.Count} detail levels first, the others follow" : "")}");
        return true;
        }
        catch
        {
            // Parts may already have been reparented to native bones. Remove those too.
            foreach (var (part, _) in made) if (part != null) { part.SetActive(false); UnityEngine.Object.Destroy(part); }
            holder.SetActive(false);
            UnityEngine.Object.Destroy(holder);
            if (origs.TryGetValue(root.GetInstanceID(), out var original))
                foreach (var renderer in original) if (renderer != null) renderer.forceRenderingOff = false;
            origs.Remove(root.GetInstanceID());
            live.RemoveAll(t => t.root == root);
            throw;
        }
    }

    // 0.3.26 (Osama 14 Nov: "We should be loading models like vanilla"): textures pre-built at package time as X.fat, the
    // graphics card's own compressed format (BC7 colour/mask, BC5 normal) with every mip level, like vanilla's bundles. The bytes
    // go straight to the GPU: no PNG decode and no mip generation on the main thread, a quarter of the video memory, and no
    // CPU-side copy kept (non-readable). A model without .fat files still loads its PNGs, also kept non-readable now.
    // X.fat: "FAT1", int32 width, height, Unity TextureFormat, mip count, linear (0/1), data length, then the mip data.
    static bool TexExists(string png) => File.Exists(Path.Combine(dir, Path.ChangeExtension(png, ".fat"))) || File.Exists(Path.Combine(dir, png));
    static Texture2D Tex(string png, bool linear)
    {
        var fat = Path.Combine(dir, Path.ChangeExtension(png, ".fat"));
        if (File.Exists(fat))
        {
            try
            {
                // 0.3.31: bytes already read on a background thread (Background.cs PrefetchTextures) when the model was prefetched.
                if (!fatReady.TryRemove(fat, out var d))
                {
                    using var r = new BinaryReader(File.OpenRead(fat));
                    if (new string(r.ReadChars(4)) != "FAT1") throw new Exception("not a FAT1 file");
                    d = new FatData { w = r.ReadInt32(), h = r.ReadInt32(), fmt = r.ReadInt32(), mips = r.ReadInt32(), lin = r.ReadInt32() != 0 };
                    int n = r.ReadInt32(); d.data = r.ReadBytes(n);
                }
                var t = new Texture2D(d.w, d.h, (TextureFormat)d.fmt, d.mips, d.lin) { name = "FAM_" + png };
                t.LoadRawTextureData(d.data);
                t.Apply(false, true);
                texBytes[t.name] = d.data.Length; texMade.TryAdd(fat, 0);
                return t;
            }
            catch (Exception ex) { MelonLogger.Warning($"FAMODELS texture {png}: {ex.Message}; using the PNG"); }
        }
        var p = new Texture2D(2, 2, TextureFormat.RGBA32, true, linear) { name = "FAM_" + png };
        ImageConversion.LoadImage(p, File.ReadAllBytes(Path.Combine(dir, png)), true);
        texBytes[p.name] = (long)p.width * p.height * 4 * 4 / 3;
        return p;
    }
    static string Str(BinaryReader f) { int n = f.ReadInt32(); return System.Text.Encoding.UTF8.GetString(f.ReadBytes(n)); }

    public class MatP { public float[] metallicRemap { get; set; } public float[] smoothnessRemap { get; set; } public bool sourceCanopy { get; set; } public string cockpitDonor { get; set; } = ""; public float[] colorScale { get; set; } = new float[] { 1f, 1f, 1f }; public float metallic { get; set; } = 0.1f; public float smoothness { get; set; } = 0.3f; public string alpha { get; set; } = "OPAQUE"; public float cutoff { get; set; } = 0.5f; public float[] emissive { get; set; } = new float[3]; public bool unlit { get; set; } public bool clearGlass { get; set; } public float opacity { get; set; } = 0.025f; public bool preserveSpecular { get; set; } public MatP fallback { get; set; } public float donorAlpha { get; set; } }
    static string MatKey(string tex, Color c) => tex + "|" + string.Join(",", new[] { c.r, c.g, c.b, c.a }.Select(x => x.ToString("F4", System.Globalization.CultureInfo.InvariantCulture)));
    static Material Mat(string tex, Color col, MatP p)
    {
        if (!string.IsNullOrEmpty(p?.cockpitDonor))
        {
            // 0.3.22: the donor (F-16 glass) is only loaded in some scenes (not the editor, not every match). Before this the
            // whole model swap was refused and the stand-in showed (FK-2000, DF-15/17/21, J-jets). Use clear glass until it loads.
            // ROC 28 Nov 2026 (Shawn, F-CK-1: "The front cockpit is too transparent and not visible ... make sure it is visible"): an entry's
            // "donorAlpha" gives its own copy of the donor glass with that base-colour alpha (F-16 glass is 0.05, nearly invisible).
            fallbackDonorAlpha = p.donorAlpha;
            try { var dm = CockpitMaterial(p.cockpitDonor); return p.donorAlpha > 0 ? DonorTinted(dm, p.cockpitDonor, p.donorAlpha) : dm; }
            catch (InvalidDataException e)
            {
                if (donorFallbacks.Add(p.cockpitDonor)) MelonLogger.Warning($"FAMODELS_COCKPIT_FALLBACK {p.cockpitDonor}: {e.Message}; clear glass used until the donor loads");
                // 0.3.23 (Osama 13 Nov): the 0.3 fallback read as frosted white on every jet that uses the F-16 glass. Use the clear
                // value the good-looking canopies use, and upgrade these materials to the donor in place once it loads (UpgradeFallbacks).
                fallbackDonor = p.cockpitDonor;
                // 0.3.43 (Osama 23 Nov 18:4x: KF-21s / F-35B ROKN "should all have the vanilla F-35 canopy textures"): a .mat.json entry may
                // give its own "fallback" look for the time the donor is not loaded (the KF-21s sit on the F-16 body, so the F-35 glass is
                // only in memory once an F-35 has been shown); without one, the clear glass as before. Upgraded to the donor in place later.
                p = p.fallback != null ? new MatP { metallic = p.fallback.metallic, smoothness = p.fallback.smoothness, alpha = p.fallback.alpha, cutoff = p.fallback.cutoff,
                        colorScale = p.fallback.colorScale, clearGlass = p.fallback.clearGlass, opacity = p.fallback.opacity, emissive = p.fallback.emissive ?? new float[3], preserveSpecular = p.fallback.preserveSpecular }
                    : new MatP { clearGlass = true, opacity = 0.025f, alpha = "BLEND", metallic = 0f, smoothness = 0.95f };
            }
        }
        // Canopy policy is opt-in. Its effective texture/colour also belong in the cache key.
        bool clearGlass = p?.clearGlass == true;
        if (clearGlass) { tex = ""; col = new Color(1f, 1f, 1f, Mathf.Clamp01(p.opacity)); }
        // Optional material-only livery adjustment; source textures and UVs stay intact.
        if (!clearGlass && p?.colorScale is { Length: 3 } scale && scale.All(x => float.IsFinite(x) && x >= 0f && x <= 4f))
            col = new Color(col.r * scale[0], col.g * scale[1], col.b * scale[2], col.a);
        string key = tex + col + (p == null ? "" : $"{p.metallic}/{p.smoothness}/{p.alpha}/{p.cutoff}/{string.Join(",", p.emissive)}/{p.clearGlass}/{p.opacity}/{p.sourceCanopy}/{(p.metallicRemap == null ? "" : string.Join(",", p.metallicRemap))}/{(p.smoothnessRemap == null ? "" : string.Join(",", p.smoothnessRemap))}/{p.preserveSpecular}");
        if (mats.TryGetValue(key, out var m) && m != null) { fallbackDonor = null; return m; }
        // Debug: UserData/FAModels/flat.txt present -> every part plain light grey, no textures, to judge geometry alone.
        if (File.Exists(Path.Combine(dir, "flat.txt"))) { tex = ""; col = new Color(0.6f, 0.6f, 0.6f, 1f); key = "FLAT"; if (mats.TryGetValue(key, out var fm) && fm != null) return fm; }
        var sh = Shader.Find("HDRP/Lit");
        m = new Material(sh) { name = "FAM_" + tex };
        m.SetColor("_BaseColor", col.gamma);  // glTF colour factors are linear; SetColor expects sRGB
        if (tex != "")
        {
            m.SetTexture("_BaseColorMap", Tex(tex, false));
        }
        // The model's own surface settings (metallic, smoothness, alpha mode, emission) from famconv's X.mat.json.
        p ??= new MatP();
        m.SetFloat("_Metallic", p.metallic); m.SetFloat("_Smoothness", p.smoothness);
        if (p.alpha == "MASK") { m.SetFloat("_AlphaCutoffEnable", 1f); m.SetFloat("_AlphaCutoff", p.cutoff); m.EnableKeyword("_ALPHATEST_ON"); }
        if (p.alpha == "BLEND" || col.a < 0.99f)
        {
            m.SetFloat("_SurfaceType", 1f); m.SetFloat("_BlendMode", 0f);
            // Osama 9 Nov (F-14 canopy): HDRP keeps full-strength reflections on transparent surfaces by default
            // ("preserve specular lighting"), so clear glass looked milky white. Let reflections fade with alpha.
            // 0.3.50 (Osama 26 Nov 21:3x, J-20 canopy "wasn't reflective" in the Arsenal before an F-35B had loaded its donor glass): a
            // .mat.json entry (or its cockpit "fallback") may set "preserveSpecular": true to keep full reflections on tinted glass.
            if (p.preserveSpecular) { m.SetFloat("_EnableBlendModePreserveSpecularLighting", 1f); m.EnableKeyword("_BLENDMODE_PRESERVE_SPECULAR_LIGHTING"); }
            else { m.SetFloat("_EnableBlendModePreserveSpecularLighting", 0f); m.DisableKeyword("_BLENDMODE_PRESERVE_SPECULAR_LIGHTING"); }
        }
        if (p.emissive != null && p.emissive.Length == 3 && p.emissive.Max() > 0) m.SetColor("_EmissiveColor", new Color(p.emissive[0], p.emissive[1], p.emissive[2]) * 1000f);
        // The source materials are double-sided (thin panels, mirrored halves); single-sided rendering left see-through gaps.
        m.SetFloat("_DoubleSidedEnable", clearGlass ? 0f : 1f); m.SetFloat("_DoubleSidedNormalMode", 0f); m.SetFloat("_CullMode", clearGlass ? 2f : 0f); m.SetFloat("_CullModeForward", clearGlass ? 2f : 0f);
        if (clearGlass) m.DisableKeyword("_DOUBLESIDED_ON"); else m.EnableKeyword("_DOUBLESIDED_ON");
        m.doubleSidedGI = !clearGlass;
        if (clearGlass)
        {
            // Avoid another haze layer or a second rendered face on thin canopy glass.
            m.SetFloat("_EnableFogOnTransparent", 0f); m.DisableKeyword("_ENABLE_FOG_ON_TRANSPARENT");
            m.SetFloat("_TransparentBackfaceEnable", 0f);
        }
        // PBR maps from the source model, written by famconv.py beside the base texture: X_n.png (normal) and X_mask.png
        // (HDRP mask map: R metallic, G occlusion, B detail mask, A smoothness). Both are linear data, not colour.
        string stem = tex.EndsWith(".png") ? tex[..^4] : tex;
        if (tex != "" && TexExists(stem + "_n.png"))
        {
            m.SetTexture("_NormalMap", Tex(stem + "_n.png", true)); m.SetFloat("_NormalScale", 1f); m.EnableKeyword("_NORMALMAP"); m.EnableKeyword("_NORMALMAP_TANGENT_SPACE");
        }
        if (tex != "" && TexExists(stem + "_mask.png"))
        {
            m.SetTexture("_MaskMap", Tex(stem + "_mask.png", true)); m.EnableKeyword("_MASKMAP");
            // 0.9.0-dev.14 (Osama 15 Nov: "X-47B needs a much more metallic skin, right now it's flat"): a model's mat.json can lift the mask's
            // metallic and smoothness ranges (metallicRemap / smoothnessRemap [min, max]); without them the mask is used as painted (0..1).
            var mr = p.metallicRemap is { Length: 2 } ? p.metallicRemap : new[] { 0f, 1f }; var sr = p.smoothnessRemap is { Length: 2 } ? p.smoothnessRemap : new[] { 0f, 1f };
            m.SetFloat("_MetallicRemapMin", mr[0]); m.SetFloat("_MetallicRemapMax", mr[1]); m.SetFloat("_SmoothnessRemapMin", sr[0]); m.SetFloat("_SmoothnessRemapMax", sr[1]);
            m.SetFloat("_AORemapMin", 0f); m.SetFloat("_AORemapMax", 1f);
        }
        ApplyCanopyFinish(m, p.sourceCanopy);
        // Runtime-made materials skip the editor's HDRP setup (render queue, depth/motion-vector passes, keywords).
        // Without it, TAA smears the model with the background and it looks see-through. Run HDRP's own validation.
        bool ok = false; try { ok = UnityEngine.Rendering.HighDefinition.HDMaterial.ValidateMaterial(m); } catch (Exception ex) { MelonLogger.Warning("FAMODELS validate: " + ex.Message); }
        mats[key] = m;
        // 0.3.44: every new stand-in gets the periodic tries again (an AH-1Z stand-in at 21:39 had used up the scene's 3 before the KF-21s at 21:49).
        if (fallbackDonor != null) { if (!fallbackMats.TryGetValue(fallbackDonor, out var fl)) fallbackMats[fallbackDonor] = fl = new List<Material>(); fl.Add(m); if (fallbackDonorAlpha > 0) fallbackAlpha[m] = fallbackDonorAlpha; fallbackDonor = null; upgradeTries = 0; upgradeGap = 10f; }
        MelonLogger.Msg($"FAMODELS material {key}: shader {(sh == null ? "MISSING" : sh.name)} surface={p.alpha} sourceCanopy={p.sourceCanopy} preserveSpecular={m.GetFloat("_EnableBlendModePreserveSpecularLighting"):F0} effectiveMetallic={m.GetFloat("_Metallic"):F2} smoothRange={m.GetFloat("_SmoothnessRemapMin"):F2}..{m.GetFloat("_SmoothnessRemapMax"):F2} clearGlass={clearGlass} opacity={col.a:F3} met={p.metallic:F2} smooth={p.smoothness:F2} normal={m.IsKeywordEnabled("_NORMALMAP")} mask={m.IsKeywordEnabled("_MASKMAP")} validated={ok} queue={m.renderQueue} mv={m.GetShaderPassEnabled("MotionVectors")} depth={m.GetShaderPassEnabled("DepthOnly")}");
        return m;
    }
}

using System.Linq;
using HarmonyLib;
using MelonLoader;
using UnityEngine;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using Il2CppBrokenArrow.Client.Ecs.Spawn;
using Il2CppBrokenArrow.DataBase.Models;
using System.Text.Json;
using Il2CppBrokenArrow.Shared.Ecs.MemoryController;

[assembly: MelonInfo(typeof(FAModels.Mod), "FAModels", "0.3.31", "Freedom Arrow")]
[assembly: MelonGame(null, "BrokenArrow")]
namespace FAModels;

// Replaces the look of chosen units with meshes loaded from UserData/FAModels/*.fam (made by famconv.py from glTF).
// The stand-in unit keeps its own prefab, rig and scripts; only its renderers are hidden and new meshes are added.
// Parts named for a bone (for example turret_0) are reparented to that bone, so they turn with it.
public partial class Mod : MelonMod
{
    class Entry { public string file { get; set; } = ""; public float scale { get; set; } = 1; public float[] offset { get; set; } = new float[3]; public float yaw { get; set; } public bool align { get; set; } = true; public string battle { get; set; } = ""; public string hide { get; set; } = ""; public string[] lods { get; set; } = Array.Empty<string>(); }
    static Dictionary<string, Entry> map = new();
    static string dir = "";
    static readonly List<(GameObject root, Entry e, string unit, float t, int pass)> queue = new();
    static readonly Dictionary<string, Material> mats = new();
    static string fallbackDonor;
    static float upgradeT;
    static readonly Dictionary<string, List<Material>> fallbackMats = new();
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
            if (e.battle != "" && (LowModels || scope?.TryCast<Il2CppBrokenArrow.Client.Ecs.Controllers.BattleLifetime>() != null))
                e = new Entry { file = e.battle, scale = e.scale, offset = e.offset, yaw = e.yaw, align = e.align, lods = e.lods };
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
            if (!famRenderers.TryGetValue(k, out var rs) || Time.realtimeSinceStartup - famRenderersT.GetValueOrDefault(k) > 15f)
            {
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
            { hitchLogT = Time.realtimeSinceStartup; MelonLogger.Msg($"FAMODELS hitch {dt * 1000f:F0} ms (#{hitchCount}): previous frame FAModels did {modelSwapsThisFrame} model swap(s), {bodySwapsThisFrame} body swap(s), {preload.Count} preload(s) left"); }
        }
        bodySwapsThisFrame = 0; modelSwapsThisFrame = 0;
        if (lodLevels.Count > 4000) lodLevels.Clear();
    }

    public override void OnUpdate()
    {
        try { HitchLog(); } catch { }
        try { TickPlaReview(); } catch(Exception e) { MelonLogger.Error("PLA_REVIEW: "+e.Message); }
        try { TickPreload(); } catch (Exception ex) { MelonLogger.Error("FAMODELS preload: " + ex.Message); }
        try { TickInfantryBodies(true); } catch (Exception ex) { MelonLogger.Error("FAMODELS body swap: " + ex.Message); }
        try { TickInfantryBodies(); } catch (Exception ex) { MelonLogger.Error("FAMODELS body poll: " + ex.Message); }
        try { TickInfantryWeapons(); } catch (Exception ex) { MelonLogger.Error("FAMODELS weapon poll: " + ex.Message); }
        if (Time.realtimeSinceStartup - syncT > 0.2f) { syncT = Time.realtimeSinceStartup; try { SyncVisibility(); } catch (Exception ex) { MelonLogger.Error("FAMODELS sync: " + ex.Message); } }
        // 0.3.31: the turret-yaw diagnostic walked every China unit's whole transform tree every 2 s; only with verbose.txt now.
        if (Verbose && Time.realtimeSinceStartup - yawT > 2f) { yawT = Time.realtimeSinceStartup; try { YawLog(); } catch (Exception ex) { MelonLogger.Error("FAMODELS yaw: " + ex.Message); } }
        try { CamTick(); } catch (Exception ex) { MelonLogger.Error("FAMODELS cam: " + ex.Message); camWant = "off"; }
        if (fallbackMats.Count > 0 && Time.realtimeSinceStartup - upgradeT > 10f) { upgradeT = Time.realtimeSinceStartup; try { UpgradeFallbacks(false); } catch (Exception ex) { MelonLogger.Error("FAMODELS cockpit upgrade: " + ex.Message); } }
        for (int i = queue.Count - 1; i >= 0; i--)
        {
            var q = queue[i];
            if (q.root == null) { queue.RemoveAt(i); continue; }
            // 0.3.25 (Osama 14 Nov): no fixed 0.5 s wait before the swap. Build on the next frame; Apply waits (up to 0.5 s)
            // only while a turret bone the model needs is not there yet. The 1 s re-hide pass for late renderers stays.
            float wait = q.pass == 0 ? 0f : 1.0f;
            if (Time.realtimeSinceStartup - q.t < wait) continue;
            try { if (!Apply(q.root, q.e, q.unit, q.pass == 0, Time.realtimeSinceStartup - q.t)) continue; }
            catch (Exception ex) { MelonLogger.Error($"FAMODELS {q.unit}: replacement rejected; original retained: {ex}"); queue.RemoveAt(i); continue; }
            queue[i] = (q.root, q.e, q.unit, Time.realtimeSinceStartup, q.pass + 1);
        }
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
    // Without a stand-in LODGroup: 0.25 / 0.10 / 0.02 of the screen height. Past the last level the model is culled, as vanilla's is.
    static void AddLods(GameObject root, GameObject holder, List<List<Renderer>> levelRenderers, string unit)
    {
        float[] h = { 0.25f, 0.10f, 0.02f };
        var native = root.GetComponentsInChildren<LODGroup>(true).FirstOrDefault(g => g.gameObject != holder);
        if (native != null) { var nl = native.GetLODs(); for (int i = 0; i < Math.Min(nl.Length, h.Length); i++) h[i] = nl[i].screenRelativeTransitionHeight; }
        int n = levelRenderers.Count; var lods = new Il2CppReferenceArray<LOD>(n);
        for (int i = 0; i < n; i++) lods[i] = new LOD(i < h.Length ? h[i] : h[h.Length - 1] * 0.5f, new Il2CppReferenceArray<Renderer>(levelRenderers[i].ToArray()));
        var g = holder.AddComponent<LODGroup>(); g.SetLODs(lods); g.RecalculateBounds();
        if (Verbose) MelonLogger.Msg($"FAMODELS {unit}: {n} detail levels at {string.Join("/", h.Take(n).Select(x => x.ToString("F3")))} of the screen ({(native != null ? "stand-in's" : "default")})");
    }
    static float[] Floats(BinaryReader f, int n) { var b = f.ReadBytes(n * 4); var r = new float[n]; Buffer.BlockCopy(b, 0, r, 0, b.Length); return r; }

    // Returns false to try again next frame (pass 0 only, while a needed turret bone is not spawned yet, at most 0.5 s).
    static bool Apply(GameObject root, Entry e, string unit, bool build, float age)
    {
        // Hide-only entries: turrets, gunners and LOD children can be spawned after InitView, so re-check every pass.
        if (e.file == "") { if (e.hide != "") HideMatching(root, e.hide, unit); return true; }
        if (!build) { int late = Hide(root); if (late > 0) MelonLogger.Msg($"FAMODELS {unit}: re-hid {late} late renderer(s) on {root.name}"); return true; }
        var sw = System.Diagnostics.Stopwatch.StartNew();
        var fam = LoadFam(e.file, out bool kept);
        float loadMs = (float)sw.Elapsed.TotalMilliseconds;
        if (age < 0.5f && fam.Any(p => p.bone != "root" && Find(root.transform, p.bone) == null)) return false;
        var holder = new GameObject("FAM_holder");
        holder.SetActive(false);
        var pending = new List<(GameObject, string)>();
        try
        {
        holder.transform.SetParent(root.transform, false);
        holder.transform.localPosition = new Vector3(e.offset[0], e.offset[1], e.offset[2]);
        holder.transform.localRotation = Quaternion.Euler(0, e.yaw, 0);
        holder.transform.localScale = Vector3.one * e.scale;
        int verts = 0, parts = 0;
        // 0.3.31: distance detail levels like vanilla's LOD groups. A battle entry may name lighter copies ("lods": [l1, l2]); each level
        // gets its own parts, and a LODGroup switches between them at the stand-in's own distances (below). Level 0 is the model above.
        var levels = new List<List<FamPart>> { fam };
        foreach (var lf in e.lods) if (lf != "" && File.Exists(Path.Combine(dir, lf))) levels.Add(LoadFam(lf, out _));
        var levelRenderers = levels.Select(_ => new List<Renderer>()).ToList();
        for (int L = 0; L < levels.Count; L++)
        foreach (var fp in levels[L])
        {
            string bone = fp.bone;
            var part = new GameObject(L == 0 ? "FAM_" + bone : $"FAM_{bone}_L{L}");
            part.transform.SetParent(holder.transform, false);
            for (int s = 0; s < fp.subs.Count; s++)
            {
                var go = new GameObject(L == 0 ? $"FAM_{bone}_{s}" : $"FAM_{bone}_{s}_L{L}");
                go.transform.SetParent(part.transform, false);
                go.AddComponent<MeshFilter>().sharedMesh = fp.subs[s].mesh;
                var mr = go.AddComponent<MeshRenderer>(); mr.sharedMaterial = fp.subs[s].mat; levelRenderers[L].Add(mr);
                if (L == 0) verts += fp.subs[s].mesh.vertexCount;
            }
            if (bone != "root") pending.Add((part, bone));
            if (L == 0) parts++;
        }
        // Line the turret up with the stand-in's turret bone (x/z), so it turns about its own ring; then reparent.
        bool aligned = false;
        foreach (var (part, bone) in pending)
        {
            var b = Find(root.transform, bone);
            if (b == null) { MelonLogger.Warning($"FAMODELS {unit}: bone {bone} not found; part stays on the hull"); continue; }
            if (!aligned && e.align)
            {
                var mfs = part.GetComponentsInChildren<MeshFilter>();
                if (mfs.Length > 0)
                {
                    // Turret ring centre: mean x/z of the turret's lowest 0.35 m, in root space (a long barrel would skew a box centre).
                    float minY = float.MaxValue; var pts = new List<Vector3>();
                    foreach (var mf in mfs) { var vs = mf.sharedMesh.vertices; for (int k = 0; k < vs.Length; k += 7) { var w = root.transform.InverseTransformPoint(mf.transform.TransformPoint(vs[k])); pts.Add(w); if (w.y < minY) minY = w.y; } }
                    double sx = 0, sz = 0; int n = 0; foreach (var w in pts) if (w.y < minY + 0.35f) { sx += w.x; sz += w.z; n++; }
                    var c = new Vector3((float)(sx / n), 0, (float)(sz / n)); var bp = root.transform.InverseTransformPoint(b.position);
                    var d = new Vector3(bp.x - c.x, 0, bp.z - c.z);
                    holder.transform.localPosition += d;
                    MelonLogger.Msg($"FAMODELS {unit}: moved model ({d.x:F2}, {d.z:F2}) m to put the turret on {bone}");
                }
                aligned = true;
            }
            part.transform.SetParent(b, true);
            { string path = b.name; for (var q = b.parent; q != null && q != root.transform; q = q.parent) path = q.name + "/" + path;
              var rp = root.transform.InverseTransformPoint(part.transform.position); var mr = part.GetComponentInChildren<MeshRenderer>(true);
              MelonLogger.Msg($"FAMODELS {unit}: {bone} -> {path} active={b.gameObject.activeInHierarchy} scale={b.lossyScale} partPos=({rp.x:F2},{rp.y:F2},{rp.z:F2}) bounds={(mr != null ? mr.bounds.center - root.transform.position : Vector3.zero)}"); }
        }
        if (levels.Count > 1) AddLods(root, holder, levelRenderers, unit);
        int hidden = Hide(root);
        holder.SetActive(true);
        live.Add((root, unit));
        modelSwapsThisFrame++;
        // 0.3.29: infantry weapon swaps log only with UserData/FAModels/verbose.txt (they were ~1,600 lines a session).
        if (Verbose || !kept || !unit.StartsWith("infantry ")) MelonLogger.Msg($"FAMODELS {unit}: hid {hidden} renderer(s), added {parts} part(s), {verts} vertices from {e.file} in {sw.Elapsed.TotalMilliseconds:F0} ms ({(kept ? "kept model" : $"loaded from file in {loadMs:F0} ms")}, after {age:F2} s)");
        return true;
        }
        catch
        {
            // Parts may already have been reparented to native bones. Remove those too.
            foreach (var (part, _) in pending) if (part != null) { part.SetActive(false); UnityEngine.Object.Destroy(part); }
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
                return t;
            }
            catch (Exception ex) { MelonLogger.Warning($"FAMODELS texture {png}: {ex.Message}; using the PNG"); }
        }
        var p = new Texture2D(2, 2, TextureFormat.RGBA32, true, linear) { name = "FAM_" + png };
        ImageConversion.LoadImage(p, File.ReadAllBytes(Path.Combine(dir, png)), true);
        return p;
    }
    static string Str(BinaryReader f) { int n = f.ReadInt32(); return System.Text.Encoding.UTF8.GetString(f.ReadBytes(n)); }

    public class MatP { public bool sourceCanopy { get; set; } public string cockpitDonor { get; set; } = ""; public float[] colorScale { get; set; } = new float[] { 1f, 1f, 1f }; public float metallic { get; set; } = 0.1f; public float smoothness { get; set; } = 0.3f; public string alpha { get; set; } = "OPAQUE"; public float cutoff { get; set; } = 0.5f; public float[] emissive { get; set; } = new float[3]; public bool unlit { get; set; } public bool clearGlass { get; set; } public float opacity { get; set; } = 0.025f; }
    static string MatKey(string tex, Color c) => tex + "|" + string.Join(",", new[] { c.r, c.g, c.b, c.a }.Select(x => x.ToString("F4", System.Globalization.CultureInfo.InvariantCulture)));
    static Material Mat(string tex, Color col, MatP p)
    {
        if (!string.IsNullOrEmpty(p?.cockpitDonor))
        {
            // 0.3.22: the donor (F-16 glass) is only loaded in some scenes (not the editor, not every match). Before this the
            // whole model swap was refused and the stand-in showed (FK-2000, DF-15/17/21, J-jets). Use clear glass until it loads.
            try { return CockpitMaterial(p.cockpitDonor); }
            catch (InvalidDataException e)
            {
                if (donorFallbacks.Add(p.cockpitDonor)) MelonLogger.Warning($"FAMODELS_COCKPIT_FALLBACK {p.cockpitDonor}: {e.Message}; clear glass used until the donor loads");
                // 0.3.23 (Osama 13 Nov): the 0.3 fallback read as frosted white on every jet that uses the F-16 glass. Use the clear
                // value the good-looking canopies use, and upgrade these materials to the donor in place once it loads (UpgradeFallbacks).
                fallbackDonor = p.cockpitDonor;
                p = new MatP { clearGlass = true, opacity = 0.025f, alpha = "BLEND", metallic = 0f, smoothness = 0.95f };
            }
        }
        // Canopy policy is opt-in. Its effective texture/colour also belong in the cache key.
        bool clearGlass = p?.clearGlass == true;
        if (clearGlass) { tex = ""; col = new Color(1f, 1f, 1f, Mathf.Clamp01(p.opacity)); }
        // Optional material-only livery adjustment; source textures and UVs stay intact.
        if (!clearGlass && p?.colorScale is { Length: 3 } scale && scale.All(x => float.IsFinite(x) && x >= 0f && x <= 4f))
            col = new Color(col.r * scale[0], col.g * scale[1], col.b * scale[2], col.a);
        string key = tex + col + (p == null ? "" : $"{p.metallic}/{p.smoothness}/{p.alpha}/{p.cutoff}/{string.Join(",", p.emissive)}/{p.clearGlass}/{p.opacity}/{p.sourceCanopy}");
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
            m.SetFloat("_EnableBlendModePreserveSpecularLighting", 0f); m.DisableKeyword("_BLENDMODE_PRESERVE_SPECULAR_LIGHTING");
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
            m.SetFloat("_MetallicRemapMin", 0f); m.SetFloat("_MetallicRemapMax", 1f); m.SetFloat("_SmoothnessRemapMin", 0f); m.SetFloat("_SmoothnessRemapMax", 1f);
            m.SetFloat("_AORemapMin", 0f); m.SetFloat("_AORemapMax", 1f);
        }
        ApplyCanopyFinish(m, p.sourceCanopy);
        // Runtime-made materials skip the editor's HDRP setup (render queue, depth/motion-vector passes, keywords).
        // Without it, TAA smears the model with the background and it looks see-through. Run HDRP's own validation.
        bool ok = false; try { ok = UnityEngine.Rendering.HighDefinition.HDMaterial.ValidateMaterial(m); } catch (Exception ex) { MelonLogger.Warning("FAMODELS validate: " + ex.Message); }
        mats[key] = m;
        if (fallbackDonor != null) { if (!fallbackMats.TryGetValue(fallbackDonor, out var fl)) fallbackMats[fallbackDonor] = fl = new List<Material>(); fl.Add(m); fallbackDonor = null; }
        MelonLogger.Msg($"FAMODELS material {key}: shader {(sh == null ? "MISSING" : sh.name)} surface={p.alpha} sourceCanopy={p.sourceCanopy} preserveSpecular={m.GetFloat("_EnableBlendModePreserveSpecularLighting"):F0} effectiveMetallic={m.GetFloat("_Metallic"):F2} smoothRange={m.GetFloat("_SmoothnessRemapMin"):F2}..{m.GetFloat("_SmoothnessRemapMax"):F2} clearGlass={clearGlass} opacity={col.a:F3} met={p.metallic:F2} smooth={p.smoothness:F2} normal={m.IsKeywordEnabled("_NORMALMAP")} mask={m.IsKeywordEnabled("_MASKMAP")} validated={ok} queue={m.renderQueue} mv={m.GetShaderPassEnabled("MotionVectors")} depth={m.GetShaderPassEnabled("DepthOnly")}");
        return m;
    }
}

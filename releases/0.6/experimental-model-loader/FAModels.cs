using System.Linq;
using HarmonyLib;
using MelonLoader;
using UnityEngine;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using Il2CppBrokenArrow.Client.Ecs.Spawn;
using Il2CppBrokenArrow.DataBase.Models;
using System.Text.Json;
using Il2CppBrokenArrow.Shared.Ecs.MemoryController;

[assembly: MelonInfo(typeof(FAModels.Mod), "FAModels", "0.3.1", "Freedom Arrow")]
[assembly: MelonGame(null, "BrokenArrow")]
namespace FAModels;

// Replaces the look of chosen units with meshes loaded from UserData/FAModels/*.fam (made by famconv.py from glTF).
// The stand-in unit keeps its own prefab, rig and scripts; only its renderers are hidden and new meshes are added.
// Parts named for a bone (for example turret_0) are reparented to that bone, so they turn with it.
public partial class Mod : MelonMod
{
    class Entry { public string file { get; set; } = ""; public float scale { get; set; } = 1; public float[] offset { get; set; } = new float[3]; public float yaw { get; set; } public bool align { get; set; } = true; public string battle { get; set; } = ""; }
    static Dictionary<string, Entry> map = new();
    static string dir = "";
    static readonly List<(GameObject root, Entry e, string unit, float t, int pass)> queue = new();
    static readonly Dictionary<string, Material> mats = new();

    public override void OnInitializeMelon()
    {
        dir = Path.Combine(MelonLoader.Utils.MelonEnvironment.UserDataDirectory, "FAModels");
        var cfg = Path.Combine(dir, "models.json");
        if (File.Exists(cfg)) map = JsonSerializer.Deserialize<Dictionary<string, Entry>>(File.ReadAllText(cfg)) ?? new();
        LoadWeaponRules();
        LoadBodyRules();
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
            QueueBodies(unitModel, unitData.Id);
            QueueWeapons(unitModel, unitData.Id, scope?.TryCast<Il2CppBrokenArrow.Client.Ecs.Controllers.BattleLifetime>() != null);
            if (!map.TryGetValue(unitData.Name, out var e)) return;
            // In a battle, use the entry's low-res copy (smaller textures and mesh; aircraft with the gear up) when it has one.
            // The armory keeps the full-fidelity file.
            if (e.battle != "" && scope?.TryCast<Il2CppBrokenArrow.Client.Ecs.Controllers.BattleLifetime>() != null)
                e = new Entry { file = e.battle, scale = e.scale, offset = e.offset, yaw = e.yaw, align = e.align };
            Hide(unitModel.PrefabRootScript.gameObject);
            queue.Add((unitModel.PrefabRootScript.gameObject, e, unitData.Name, Time.realtimeSinceStartup, 0));
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
    static void SyncVisibility()
    {
        for (int i = live.Count - 1; i >= 0; i--)
        {
            var (root, unit) = live[i];
            if (root == null) { live.RemoveAt(i); continue; }
            if (!origs.TryGetValue(root.GetInstanceID(), out var os) || os.Count == 0) continue;
            bool vis = false;
            foreach (var o in os) if (o != null && o.enabled && o.gameObject.activeInHierarchy) { vis = true; break; }
            var h = root.transform.Find("FAM_holder");
            if (h != null) foreach (var fr in h.GetComponentsInChildren<MeshRenderer>(true)) fr.enabled = vis;
            foreach (var t in root.GetComponentsInChildren<Transform>(true)) if (t.name.StartsWith("FAM_") && t.name != "FAM_holder" && t.parent != h) foreach (var fr in t.GetComponentsInChildren<MeshRenderer>(true)) fr.enabled = vis;
        }
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

    public override void OnUpdate()
    {
        try { TickInfantryBodies(); } catch (Exception ex) { MelonLogger.Error("FAMODELS body poll: " + ex.Message); }
        try { TickInfantryWeapons(); } catch (Exception ex) { MelonLogger.Error("FAMODELS weapon poll: " + ex.Message); }
        if (Time.realtimeSinceStartup - syncT > 0.2f) { syncT = Time.realtimeSinceStartup; try { SyncVisibility(); } catch (Exception ex) { MelonLogger.Error("FAMODELS sync: " + ex.Message); } }
        if (Time.realtimeSinceStartup - yawT > 2f) { yawT = Time.realtimeSinceStartup; try { YawLog(); } catch (Exception ex) { MelonLogger.Error("FAMODELS yaw: " + ex.Message); } }
        try { CamTick(); } catch (Exception ex) { MelonLogger.Error("FAMODELS cam: " + ex.Message); camWant = "off"; }
        for (int i = queue.Count - 1; i >= 0; i--)
        {
            var q = queue[i];
            if (q.root == null) { queue.RemoveAt(i); continue; }
            float wait = q.pass == 0 ? 0.5f : 1.0f;
            if (Time.realtimeSinceStartup - q.t < wait) continue;
            try { Apply(q.root, q.e, q.unit, q.pass == 0); }
            catch (Exception ex) { MelonLogger.Error($"FAMODELS {q.unit}: {ex}"); }
            queue[i] = (q.root, q.e, q.unit, Time.realtimeSinceStartup, q.pass + 1);
        }
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

    // Hide the stand-in's own meshes. Called in the InitView postfix too, so the stand-in never shows before our model is built.
    static int Hide(GameObject root)
    {
        int hidden = 0;
        foreach (var r in root.GetComponentsInChildren<Renderer>(true))
        {
            if (r.gameObject.name.StartsWith("FAM_")) continue;
            if (r.TryCast<MeshRenderer>() != null || r.TryCast<SkinnedMeshRenderer>() != null) { if (!r.forceRenderingOff) { hidden++; r.forceRenderingOff = true; origs.TryAdd(root.GetInstanceID(), new()); origs[root.GetInstanceID()].Add(r); } }
        }
        return hidden;
    }

    static void Apply(GameObject root, Entry e, string unit, bool build)
    {
        int hidden = Hide(root);
        if (build) live.Add((root, unit));
        if (!build) { if (hidden > 0) MelonLogger.Msg($"FAMODELS {unit}: re-hid {hidden} late renderer(s) on {root.name}"); return; }
        var holder = new GameObject("FAM_holder");
        holder.transform.SetParent(root.transform, false);
        holder.transform.localPosition = new Vector3(e.offset[0], e.offset[1], e.offset[2]);
        holder.transform.localRotation = Quaternion.Euler(0, e.yaw, 0);
        holder.transform.localScale = Vector3.one * e.scale;
        int verts = 0, parts = 0;
        var pending = new List<(GameObject, string)>();
        var mj = Path.Combine(dir, Path.ChangeExtension(e.file, null) + ".mat.json");
        var mp = File.Exists(mj) ? JsonSerializer.Deserialize<Dictionary<string, MatP>>(File.ReadAllText(mj)) ?? new() : new Dictionary<string, MatP>();
        using var f = new BinaryReader(File.OpenRead(Path.Combine(dir, e.file)));
        if (new string(f.ReadChars(4)) != "FAM1") throw new Exception("not a FAM1 file");
        int np = f.ReadInt32();
        for (int p = 0; p < np; p++)
        {
            string bone = Str(f); int ns = f.ReadInt32();
            var part = new GameObject("FAM_" + bone);
            part.transform.SetParent(holder.transform, false);
            for (int s = 0; s < ns; s++)
            {
                string tex = Str(f); var col = new Color(f.ReadSingle(), f.ReadSingle(), f.ReadSingle(), f.ReadSingle());
                int nv = f.ReadInt32();
                var pos = new Il2CppStructArray<Vector3>(nv); for (int k = 0; k < nv; k++) pos[k] = new Vector3(f.ReadSingle(), f.ReadSingle(), f.ReadSingle());
                var nrm = new Il2CppStructArray<Vector3>(nv); bool anyN = false;
                for (int k = 0; k < nv; k++) { var v = new Vector3(f.ReadSingle(), f.ReadSingle(), f.ReadSingle()); nrm[k] = v; anyN |= v.sqrMagnitude > 0; }
                var uv = new Il2CppStructArray<Vector2>(nv); for (int k = 0; k < nv; k++) uv[k] = new Vector2(f.ReadSingle(), f.ReadSingle());
                int ni = f.ReadInt32(); var idx = new Il2CppStructArray<int>(ni); for (int k = 0; k < ni; k++) idx[k] = f.ReadInt32();
                var mesh = new Mesh { name = $"FAM_{unit}_{bone}_{s}" };
                mesh.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;
                mesh.vertices = pos; mesh.uv = uv; mesh.triangles = idx;
                if (anyN) mesh.normals = nrm; else mesh.RecalculateNormals();
                mesh.RecalculateBounds();
                var go = new GameObject($"FAM_{bone}_{s}");
                go.transform.SetParent(part.transform, false);
                go.AddComponent<MeshFilter>().sharedMesh = mesh;
                mp.TryGetValue(MatKey(tex, col), out var matp);
                var mat = Mat(tex, col, matp);
                if (mat.IsKeywordEnabled("_NORMALMAP")) mesh.RecalculateTangents();  // HDRP normal maps need tangents; the .fam carries none
                go.AddComponent<MeshRenderer>().sharedMaterial = mat;
                verts += nv;
            }
            if (bone != "root") pending.Add((part, bone));
            parts++;
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
        MelonLogger.Msg($"FAMODELS {unit}: hid {hidden} renderer(s), added {parts} part(s), {verts} vertices from {e.file}");
    }

    static string Str(BinaryReader f) { int n = f.ReadInt32(); return System.Text.Encoding.UTF8.GetString(f.ReadBytes(n)); }

    public class MatP { public float metallic { get; set; } = 0.1f; public float smoothness { get; set; } = 0.3f; public string alpha { get; set; } = "OPAQUE"; public float cutoff { get; set; } = 0.5f; public float[] emissive { get; set; } = new float[3]; public bool unlit { get; set; } }
    static string MatKey(string tex, Color c) => tex + "|" + string.Join(",", new[] { c.r, c.g, c.b, c.a }.Select(x => x.ToString("F4", System.Globalization.CultureInfo.InvariantCulture)));
    static Material Mat(string tex, Color col, MatP p)
    {
        string key = tex + col + (p == null ? "" : $"{p.metallic}/{p.smoothness}/{p.alpha}/{p.cutoff}/{string.Join(",", p.emissive)}");
        if (mats.TryGetValue(key, out var m) && m != null) return m;
        // Debug: UserData/FAModels/flat.txt present -> every part plain light grey, no textures, to judge geometry alone.
        if (File.Exists(Path.Combine(dir, "flat.txt"))) { tex = ""; col = new Color(0.6f, 0.6f, 0.6f, 1f); key = "FLAT"; if (mats.TryGetValue(key, out var fm) && fm != null) return fm; }
        var sh = Shader.Find("HDRP/Lit");
        m = new Material(sh) { name = "FAM_" + tex };
        m.SetColor("_BaseColor", col.gamma);  // glTF colour factors are linear; SetColor expects sRGB
        if (tex != "")
        {
            var t = new Texture2D(2, 2, TextureFormat.RGBA32, true);
            ImageConversion.LoadImage(t, File.ReadAllBytes(Path.Combine(dir, tex)));
            m.SetTexture("_BaseColorMap", t);
        }
        // The model's own surface settings (metallic, smoothness, alpha mode, emission) from famconv's X.mat.json.
        p ??= new MatP();
        m.SetFloat("_Metallic", p.metallic); m.SetFloat("_Smoothness", p.smoothness);
        if (p.alpha == "MASK") { m.SetFloat("_AlphaCutoffEnable", 1f); m.SetFloat("_AlphaCutoff", p.cutoff); m.EnableKeyword("_ALPHATEST_ON"); }
        if (p.alpha == "BLEND" || col.a < 0.99f) { m.SetFloat("_SurfaceType", 1f); m.SetFloat("_BlendMode", 0f); }
        if (p.emissive != null && p.emissive.Length == 3 && p.emissive.Max() > 0) m.SetColor("_EmissiveColor", new Color(p.emissive[0], p.emissive[1], p.emissive[2]) * 1000f);
        // The source materials are double-sided (thin panels, mirrored halves); single-sided rendering left see-through gaps.
        m.SetFloat("_DoubleSidedEnable", 1f); m.SetFloat("_DoubleSidedNormalMode", 0f); m.SetFloat("_CullMode", 0f); m.SetFloat("_CullModeForward", 0f);
        m.EnableKeyword("_DOUBLESIDED_ON"); m.doubleSidedGI = true;
        // PBR maps from the source model, written by famconv.py beside the base texture: X_n.png (normal) and X_mask.png
        // (HDRP mask map: R metallic, G occlusion, B detail mask, A smoothness). Both are linear data, not colour.
        string stem = tex.EndsWith(".png") ? tex[..^4] : tex;
        if (tex != "" && File.Exists(Path.Combine(dir, stem + "_n.png")))
        {
            var n = new Texture2D(2, 2, TextureFormat.RGBA32, true, true);
            ImageConversion.LoadImage(n, File.ReadAllBytes(Path.Combine(dir, stem + "_n.png")));
            m.SetTexture("_NormalMap", n); m.SetFloat("_NormalScale", 1f); m.EnableKeyword("_NORMALMAP"); m.EnableKeyword("_NORMALMAP_TANGENT_SPACE");
        }
        if (tex != "" && File.Exists(Path.Combine(dir, stem + "_mask.png")))
        {
            var k = new Texture2D(2, 2, TextureFormat.RGBA32, true, true);
            ImageConversion.LoadImage(k, File.ReadAllBytes(Path.Combine(dir, stem + "_mask.png")));
            m.SetTexture("_MaskMap", k); m.EnableKeyword("_MASKMAP");
            m.SetFloat("_MetallicRemapMin", 0f); m.SetFloat("_MetallicRemapMax", 1f); m.SetFloat("_SmoothnessRemapMin", 0f); m.SetFloat("_SmoothnessRemapMax", 1f);
            m.SetFloat("_AORemapMin", 0f); m.SetFloat("_AORemapMax", 1f);
        }
        // Runtime-made materials skip the editor's HDRP setup (render queue, depth/motion-vector passes, keywords).
        // Without it, TAA smears the model with the background and it looks see-through. Run HDRP's own validation.
        bool ok = false; try { ok = UnityEngine.Rendering.HighDefinition.HDMaterial.ValidateMaterial(m); } catch (Exception ex) { MelonLogger.Warning("FAMODELS validate: " + ex.Message); }
        mats[key] = m;
        MelonLogger.Msg($"FAMODELS material {key}: shader {(sh == null ? "MISSING" : sh.name)} surface={p.alpha} met={p.metallic:F2} smooth={p.smoothness:F2} normal={m.IsKeywordEnabled("_NORMALMAP")} mask={m.IsKeywordEnabled("_MASKMAP")} validated={ok} queue={m.renderQueue} mv={m.GetShaderPassEnabled("MotionVectors")} depth={m.GetShaderPassEnabled("DepthOnly")}");
        return m;
    }
}

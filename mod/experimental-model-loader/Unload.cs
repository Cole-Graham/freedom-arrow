using MelonLoader;
using UnityEngine;
namespace FAModels;

// 0.3.35 (Osama 18 Nov 2026: "ishtar is the one that crashed, we should free models"). Since 0.3.25 every model ever loaded stayed in
// famCache for the whole session (meshes, materials and their GPU textures). ishtar's dev.41 game went down while browsing the Arsenal
// after a match with 132 models held (about 2.5 GB of textures); the whole Arsenal is about 6.6 GB. Now a model that no live unit uses is
// freed (mesh, material and its FAM_ textures destroyed): every unused model when a scene loads (so Arsenal models go before a battle and
// battle models go back in the menu), and in the menu all but the 12 most recently used. Infantry weapon files are left alone (small, and
// InfantryWeapons.cs shares their meshes). FAMODELS memory logs process RAM and what the cache holds every 60 s.
public partial class Mod
{
    const int MenuKeep = 12;
    static readonly Dictionary<string, List<GameObject>> famUsers = new();
    static readonly Dictionary<string, float> famUsed = new();
    static readonly Dictionary<string, long> texBytes = new();
    static int freedModels; static float memT;
    static bool inMenu;

    static void NoteUse(string file, GameObject root)
    {
        famUsed[file] = Time.realtimeSinceStartup;
        if (!famUsers.TryGetValue(file, out var l)) famUsers[file] = l = new List<GameObject>();
        l.RemoveAll(g => g == null); if (!l.Contains(root)) l.Add(root);
    }
    static bool InUse(string file) => famUsers.TryGetValue(file, out var l) && l.Any(g => g != null);
    static bool IsWeaponFile(string file) => weaponRules.Any(r => r.file == file || r.battle == file);

    public override void OnSceneWasLoaded(int buildIndex, string sceneName)
    {
        inMenu = sceneName == "Hangar_Scene";
        FreeUnused(0, "scene " + sceneName);
    }

    // Frees cached models no live unit uses, keeping the `keep` most recently used of them.
    static void FreeUnused(int keep, string why)
    {
        var unused = famCache.Keys.Where(f => !InUse(f) && !IsWeaponFile(f)).OrderByDescending(f => famUsed.TryGetValue(f, out var t) ? t : 0f).Skip(keep).ToList();
        if (unused.Count == 0) return;
        var keptMats = new HashSet<IntPtr>();
        foreach (var kv in famCache) if (!unused.Contains(kv.Key)) foreach (var part in kv.Value) foreach (var s in part.subs) if (s.mat != null) keptMats.Add(s.mat.Pointer);
        long bytes = 0;
        foreach (var f in unused)
        {
            foreach (var part in famCache[f]) foreach (var sub in part.subs)
            {
                if (sub.mesh != null) { bytes += MeshBytes(sub.mesh); UnityEngine.Object.Destroy(sub.mesh); }
                if (sub.mat == null || keptMats.Contains(sub.mat.Pointer) || !sub.mat.name.StartsWith("FAM_") || sub.mat.name.StartsWith("FAM_COCKPIT_")) continue;
                foreach (var prop in new[] { "_BaseColorMap", "_NormalMap", "_MaskMap" })
                    if (sub.mat.HasProperty(prop) && sub.mat.GetTexture(prop) is Texture t && t != null && t.name.StartsWith("FAM_"))
                    { bytes += texBytes.TryGetValue(t.name, out var b) ? b : 0; texBytes.Remove(t.name); texMade.TryRemove(Path.Combine(dir, Path.ChangeExtension(t.name.Substring(4), ".fat")), out _); UnityEngine.Object.Destroy(t); }
                foreach (var k in mats.Where(kv => kv.Value == sub.mat).Select(kv => kv.Key).ToList()) mats.Remove(k);
                foreach (var l in fallbackMats.Values) l.Remove(sub.mat);
                UnityEngine.Object.Destroy(sub.mat);
            }
            famCache.Remove(f); famUsers.Remove(f); famUsed.Remove(f); freedModels++;
        }
        MelonLogger.Msg($"FAMODELS freed {unused.Count} unused model(s), about {bytes >> 20} MB ({why}); {famCache.Count} kept");
    }

    // Vertices are held twice (readable CPU copy and GPU copy; turret alignment reads them), at about 32 bytes each.
    static long MeshBytes(Mesh m) { if (m == null) return 0; long b = (long)m.vertexCount * 2 * 32; for (int i = 0; i < m.subMeshCount; i++) b += 4L * (long)m.GetIndexCount(i); return b; }

    static void MemoryLog()
    {
        if (Time.realtimeSinceStartup - memT < 60f) return;
        memT = Time.realtimeSinceStartup;
        long tex = texBytes.Values.Sum(), mesh = 0; int verts = 0;
        foreach (var parts in famCache.Values) foreach (var part in parts) foreach (var s in part.subs) if (s.mesh != null) { verts += s.mesh.vertexCount; mesh += MeshBytes(s.mesh); }
        var proc = System.Diagnostics.Process.GetCurrentProcess();
        MelonLogger.Msg($"FAMODELS memory: process {proc.WorkingSet64 >> 20} MB working set, {proc.PrivateMemorySize64 >> 20} MB private; cache {famCache.Count} model(s), {verts} vertices, ~{mesh >> 20} MB meshes, ~{tex >> 20} MB textures; {freedModels} freed so far; detail levels on demand: {lodBuilt} built, {lodUnloaded} removed, {lodFilesFreed} files freed (~{lodBytesFreed >> 20} MB); {(inMenu ? "menu" : "battle")}");
    }
}

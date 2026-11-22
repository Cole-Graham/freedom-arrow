using System.Collections;
using System.Reflection;
using Il2CppInterop.Runtime;
using MelonLoader;
using UnityEngine;

namespace FreedomArrow;

/// <summary>
/// Osama 22 Nov 2026 12:5x PST (thread 1567745029781454889): "Please log those and continue optimizing", after the dev.29 RAM test:
/// menu 5.99 GB, back in the menu 7.33 / 7.30 / 7.56 GB after three short matches; Unity alloc +0.9 GB after the first match then flat;
/// IL2CPP GC heap 469 -> 652 -> 889 -> 1031 MB (+~0.2 GB a match). Right after each MemoryCleanup pass this logs what is still alive:
/// Unity object counts by type, the mods' own .NET heap, and every static collection in the Freedom Arrow assemblies (FreedomArrow*,
/// FAModels, FA* add-ons) found by reflection, the largest first, with the change since the previous probe. A collection that grows
/// every match is a leak of ours; flat counts with a growing IL2CPP heap point at the base game.
/// </summary>
static class MemoryProbe
{
    static readonly (string Name, System.Func<Il2CppSystem.Type> Type)[] UnityTypes =
    {
        ("objects", () => Il2CppType.Of<UnityEngine.Object>()), ("GameObject", () => Il2CppType.Of<GameObject>()),
        ("Mesh", () => Il2CppType.Of<Mesh>()), ("Material", () => Il2CppType.Of<Material>()), ("Texture2D", () => Il2CppType.Of<Texture2D>()),
        ("RenderTexture", () => Il2CppType.Of<RenderTexture>()),
        ("ScriptableObject", () => Il2CppType.Of<ScriptableObject>()),
    };
    static readonly Dictionary<string, long> last = new();
    static List<(Type Owner, FieldInfo Field)> fields;

    public static void Log(string reason)
    {
        try
        {
            var unity = new List<string>();
            foreach (var (name, type) in UnityTypes)
            {
                try { unity.Add($"{name} {Delta("unity." + name, Resources.FindObjectsOfTypeAll(type()).Length)}"); }
                catch { unity.Add($"{name} n/a"); }
            }
            long managed = System.GC.GetTotalMemory(false) >> 20;
            var statics = new List<(string Key, long Count)>();
            foreach (var (owner, f) in Fields())
            {
                long n = Count(f);
                if (n > 0) statics.Add(($"{owner.Assembly.GetName().Name}:{owner.Name}.{f.Name}", n));
            }
            long total = statics.Sum(s => s.Count);
            var top = statics.OrderByDescending(s => s.Count).Take(15).Select(s => $"{s.Key}={Delta("s." + s.Key, s.Count)}");
            MelonLogger.Msg($"FREEDOM_ARROW_MEMORY_PROBE {reason}: unity [{string.Join(", ", unity)}], dotnet heap {Delta("dotnet", managed)} MB; " +
                $"mod statics {statics.Count} non-empty, {Delta("statics.total", total)} entries; largest: {string.Join(", ", top)}");
        }
        catch (Exception e) { MelonLogger.Warning("FREEDOM_ARROW_MEMORY_PROBE failed: " + e.Message); }
    }

    // value and the change since the previous probe, e.g. "1234 (+56)"
    static string Delta(string key, long value)
    {
        string d = last.TryGetValue(key, out var old) ? $" ({(value - old >= 0 ? "+" : "")}{value - old})" : "";
        last[key] = value;
        return value + d;
    }

    static List<(Type, FieldInfo)> Fields()
    {
        if (fields != null) return fields;
        fields = new();
        foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
        {
            string n = asm.GetName().Name ?? "";
            if (!(n.StartsWith("FreedomArrow") || n.StartsWith("FA"))) continue;
            Type[] types;
            try { types = asm.GetTypes(); } catch (ReflectionTypeLoadException e) { types = e.Types.Where(t => t != null).ToArray(); }
            foreach (var t in types)
            {
                if (t.ContainsGenericParameters) continue;
                foreach (var f in t.GetFields(BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic))
                    if (!f.IsLiteral && (typeof(IEnumerable).IsAssignableFrom(f.FieldType) || f.FieldType.GetProperty("Count") != null) && f.FieldType != typeof(string))
                        fields.Add((t, f));
            }
        }
        return fields;
    }

    static long Count(FieldInfo f)
    {
        try
        {
            object v = f.GetValue(null);
            if (v == null) return 0;
            if (v is ICollection c) return c.Count;
            if (v is Array a) return a.Length;
            var p = v.GetType().GetProperty("Count");
            if (p != null && p.GetValue(v) is int i) return i;
        }
        catch { }
        return 0;
    }
}

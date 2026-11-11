using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using MelonLoader;

namespace FAModels;
public partial class Mod
{
    // Clone the game's actual material, including shader, texture references and all HDRP settings.
    // A donor prefab may be loaded as an asset for this lookup; it is never instantiated.
    static readonly Dictionary<string, Material> cockpitMaterials = new();
    static readonly Dictionary<string, string> cockpitTokens = new()
    {
        ["US_F22_Glass"] = "f22",
        ["US_F16_Glass"] = "f16",
        ["!RU_SU-57glass"] = "su57"
    };
    static string Compact(string s) => new string(s.ToLowerInvariant().Where(char.IsLetterOrDigit).ToArray());
    static Material FindCockpitMaterial(string name) => Resources.FindObjectsOfTypeAll<Material>()
        .FirstOrDefault(m => m != null && (m.name == name || m.name == name + " (Instance)"));
    static Material CockpitMaterial(string name)
    {
        if (!cockpitTokens.TryGetValue(name, out var token)) throw new InvalidDataException("Unknown cockpit donor: " + name);
        if (cockpitMaterials.TryGetValue(name, out var ready) && ready != null) return ready;
        var source = FindCockpitMaterial(name);
        if (source == null)
        {
            var bundles = AssetBundle.GetAllLoadedAssetBundles().GetEnumerator();
            var iterator = bundles.Cast<Il2CppSystem.Collections.IEnumerator>();
            while (iterator.MoveNext())
            {
                var bundle = bundles.Current;
                foreach (var path in bundle.GetAllAssetNames())
                {
                    if (!path.EndsWith(".prefab", StringComparison.OrdinalIgnoreCase) || !Compact(Path.GetFileNameWithoutExtension(path)).Contains(token)) continue;
                    var prefab = bundle.LoadAsset<GameObject>(path);
                    if (prefab == null) continue;
                    foreach (var renderer in prefab.GetComponentsInChildren<Renderer>(true))
                        foreach (var material in renderer.sharedMaterials)
                            if (material != null && material.name == name) { source = material; break; }
                    source ??= FindCockpitMaterial(name);
                    if (source != null) break;
                }
                if (source != null) break;
            }
        }
        if (source == null) throw new InvalidDataException("Cockpit donor unavailable: " + name + "; no substituted material was applied");
        var clone = new Material(source) { name = "FAM_COCKPIT_" + name };
        cockpitMaterials[name] = clone;
        MelonLogger.Msg($"FAMODELS_COCKPIT donor={name}; shader={clone.shader.name}; source={source.GetInstanceID()}; clone={clone.GetInstanceID()}; textures={string.Join(",", clone.GetTexturePropertyNames())}");
        return clone;
    }
}

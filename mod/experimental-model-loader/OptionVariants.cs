using MelonLoader;
using UnityEngine;
using Il2CppBrokenArrow.DataBase.Models;

namespace FAModels;
// 0.3.39 (Osama 22 Nov 2026, thread 1572407822849810463: "Shawn uploaded the ZTZ-99B, this is an upgrade variant of the ZTZ-99A, when someone gets
// the APS option, they get this model"). A models.json entry may list "variants": [{"options": [option names or ids], "file", "battle", "lods",
// "scale"}]. When the unit's current loadout has one of a variant's options, that variant's files are used instead of the entry's. The loadout is
// read again every 0.25 s (it may not be set yet at InitView, and the Arsenal changes it without rebuilding the unit), and the model is rebuilt
// when the chosen variant changes.
public partial class Mod
{
    class Variant { public string[] options { get; set; } = Array.Empty<string>(); public string file { get; set; } = ""; public string battle { get; set; } = ""; public string[] lods { get; set; } = Array.Empty<string>(); public float scale { get; set; } }
    static readonly List<(GameObject root, Units data, Entry baseE, string unit, bool battle, int idx)> variantViews = new();
    static float variantT; static int variantLogs;
    static int VariantIndex(Entry e, Units u)
    {
        var o = u?.CurrentOptions; if (o == null || e.variants.Length == 0) return -1;
        for (int v = 0; v < e.variants.Length; v++)
            for (int i = 0; i < o.Count; i++) { var x = o[i]; if (x != null && (e.variants[v].options.Contains(x.Name) || e.variants[v].options.Contains(x.Id.ToString()))) return v; }
        return -1;
    }
    static Entry Resolve(Entry e, int vi, bool battle)
    {
        var r = e;
        if (vi >= 0)
        {
            var v = e.variants[vi];
            r = new Entry { file = v.file != "" ? v.file : e.file, battle = v.battle != "" ? v.battle : e.battle, lods = v.lods.Length > 0 ? v.lods : e.lods,
                            scale = v.scale > 0 ? v.scale : e.scale, offset = e.offset, yaw = e.yaw, align = e.align, hide = e.hide, dustPoint = e.dustPoint, keep = e.keep };
        }
        if (battle && r.battle != "") r = new Entry { file = r.battle, scale = r.scale, offset = r.offset, yaw = r.yaw, align = r.align, lods = r.lods, dustPoint = r.dustPoint, keep = r.keep };
        else if (!battle && r.lods.Length > 0) r = new Entry { file = r.file, scale = r.scale, offset = r.offset, yaw = r.yaw, align = r.align, hide = r.hide, dustPoint = r.dustPoint, keep = r.keep };   // 0.3.49: armory = full model only
        return r;
    }
    static void TickVariants()
    {
        if (variantViews.Count == 0 || Time.realtimeSinceStartup - variantT < 0.25f) return;
        variantT = Time.realtimeSinceStartup;
        for (int i = variantViews.Count - 1; i >= 0; i--)
        {
            var v = variantViews[i];
            if (v.root == null || !v.root) { variantViews.RemoveAt(i); continue; }
            int w;
            try { w = VariantIndex(v.baseE, v.data); } catch { variantViews.RemoveAt(i); continue; }
            if (w == v.idx) continue;
            var old = v.root.transform.Find("FAM_holder");
            if (old != null) { old.name = "FAM_holder_old"; old.gameObject.SetActive(false); UnityEngine.Object.Destroy(old.gameObject); }
            queue.Add((v.root, Resolve(v.baseE, w, v.battle), v.unit, Time.realtimeSinceStartup, 0));
            Hide(v.root);
            if (variantLogs++ < 50) MelonLogger.Msg($"FAMODELS {v.unit}: loadout variant {(w < 0 ? "default" : string.Join("/", v.baseE.variants[w].options))} -> {Resolve(v.baseE, w, v.battle).file}");
            variantViews[i] = (v.root, v.data, v.baseE, v.unit, v.battle, w);
        }
    }
}

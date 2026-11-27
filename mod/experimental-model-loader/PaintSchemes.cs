using System.Text.Json;
using HarmonyLib;
using MelonLoader;
using UnityEngine;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.InfoCard;
using Il2CppBrokenArrow.Client.Ecs.Configs.UserItems;

namespace FAModels;
// 0.3.36 paint schemes (Osama 21 Nov 2026, thread 1572407822849810463: "add variants of all the units we have multiple textures for as a paint
// option ... Mainly for Arsenal", "for our Chinese and new models, remove the default skins", "make sure they're Armory quality").
// 0.3.37 (21 Nov 19:3x, "every model from that one chinese creator should have paint schemes"): 73 units, and every FAModels unit without
// schemes hides the donor's vanilla skins.
// The extra colour sets that came with the model packs are shipped as <texture>@<Scheme>.fat next to the default texture, at the same size.
// paint-schemes.json lists the schemes of each unit. On those units the Arsenal paint menu shows "Default" and the pack schemes instead of
// the donor's vanilla skins (which never showed on our models). The choice is local (paint-choices.json, per unit): it never goes into the
// deck or to the game's server, so a player cannot be refused for an unowned skin. It shows in the Arsenal and in the player's own battles.
public partial class Mod
{
    static Dictionary<string, string[]> paintSchemes = new();
    static Dictionary<string, string> paintChoices = new();
    // 0.3.42 (Osama 23 Nov 2026 18:1x "Z-19G should have its naval skin as default"): paint-defaults.json (unit Name -> scheme) sets the scheme
    // a unit shows until the player picks one; picking "Default" still shows the pack's base colours.
    static Dictionary<string, string> paintDefaults = new();
    static string CurrentPaint(string unit) => paintChoices.TryGetValue(unit, out var c) && c != null ? c : paintDefaults.TryGetValue(unit, out var d) && d != null ? d : "";
    static readonly Dictionary<int, Material> paintOrig = new();        // renderer -> its default (shared) material
    static readonly Dictionary<string, Material> paintMats = new();     // default material + scheme -> scheme copy
    const int PaintIdBase = 970000;                                     // button ids: base + index (0 = Default); never sent anywhere
    static readonly Dictionary<string, string> PaintNames = new(StringComparer.OrdinalIgnoreCase)
    {
        ["Plain"] = "Plain", ["Dust"] = "Desert", ["DustCamo"] = "Desert camo", ["DustMix"] = "Desert mix", ["Camo"] = "Woodland camo",
        ["Mix"] = "Mixed camo", ["dig"] = "Digital", ["Yellow"] = "Yellow", ["YellowMix"] = "Yellow mix", ["Yellowmix"] = "Yellow mix",
        ["Green"] = "Green", ["Navy"] = "Navy grey", ["Black"] = "Black", ["Army"] = "Army green", ["Grey"] = "Grey", ["GreenMix"] = "Green mix",
        ["Camo1"] = "Camo 1", ["Camo2"] = "Camo 2", ["Mix1"] = "Mix 1", ["Mix2"] = "Mix 2",
        ["GreyCamo"] = "Grey camo",
        ["Mosaic"] = "Mosaic camo",   // ROC CM-34 MAISAIKE set (Shawn 27 Nov 2026)   // ROC Mirage 2000-5 second skin (Shawn 26 Nov 2026)
    };
    static string PaintLabel(string s) => s == "" ? "Default" : PaintNames.TryGetValue(s, out var n) ? n : s;
    static string ChoicesFile => Path.Combine(MelonLoader.Utils.MelonEnvironment.UserDataDirectory, "FAModels-paint-choices.json");

    static void InstallPaintSchemes(HarmonyLib.Harmony h)
    {
        var f = Path.Combine(dir, "paint-schemes.json");
        var extras = Directory.Exists(dir) ? Directory.GetFiles(dir, "paint-schemes-*.json").OrderBy(x => x, StringComparer.Ordinal).ToArray() : new string[0];
        if (!File.Exists(f) && extras.Length == 0) { MelonLogger.Msg("FAMODELS_PAINT off: no paint-schemes.json"); return; }
        if (File.Exists(f)) paintSchemes = JsonSerializer.Deserialize<Dictionary<string, string[]>>(File.ReadAllText(f)) ?? new();
        // Add-on packs (ROC, 26 Nov 2026) bring their own paint-schemes-<pack>.json. A bad add-on file is skipped alone.
        foreach (var extra in extras)
        {
            try { var add = JsonSerializer.Deserialize<Dictionary<string, string[]>>(File.ReadAllText(extra)) ?? new(); foreach (var kv in add) paintSchemes[kv.Key] = kv.Value; MelonLogger.Msg($"FAMODELS_PAINT add-on {Path.GetFileName(extra)}: {add.Count} unit(s)"); }
            catch (Exception ex) { MelonLogger.Warning($"FAMODELS_PAINT add-on {Path.GetFileName(extra)} skipped: " + ex.Message); }
        }
        var df = Path.Combine(dir, "paint-defaults.json");
        try { if (File.Exists(df)) paintDefaults = JsonSerializer.Deserialize<Dictionary<string, string>>(File.ReadAllText(df)) ?? new(); }
        catch (Exception ex) { MelonLogger.Warning("FAMODELS_PAINT defaults unreadable, base colours: " + ex.Message); }
        try { if (File.Exists(ChoicesFile)) paintChoices = JsonSerializer.Deserialize<Dictionary<string, string>>(File.ReadAllText(ChoicesFile)) ?? new(); }
        catch (Exception ex) { MelonLogger.Warning("FAMODELS_PAINT choices unreadable, all default: " + ex.Message); }
        h.Patch(AccessTools.Method(typeof(UnitInfoCard), "SetUnitSkins"), postfix: new HarmonyMethod(typeof(Mod), nameof(AfterSetUnitSkins)));
        MelonLogger.Msg($"FAMODELS_PAINT ready: {paintSchemes.Count} unit(s) with pack paint schemes, {paintDefaults.Count} default(s), {paintChoices.Count} saved choice(s)");
    }

    // Called after a model is built for a unit (Apply) and when the player picks a scheme.
    static void ApplyPaint(GameObject root, string unit)
    {
        if (root == null || !paintSchemes.ContainsKey(unit)) return;
        var scheme = CurrentPaint(unit);
        foreach (var r in root.GetComponentsInChildren<MeshRenderer>(true))
        {
            int id = r.GetInstanceID();
            if (!paintOrig.TryGetValue(id, out var orig))
            {
                var m0 = r.sharedMaterial;
                if (m0 == null || !m0.name.StartsWith("FAM_")) continue;
                paintOrig[id] = orig = m0;
            }
            r.sharedMaterial = scheme == "" ? orig : PaintMaterial(orig, scheme);
        }
    }
    static Material PaintMaterial(Material orig, string scheme)
    {
        var t = orig.GetTexture("_BaseColorMap");
        if (t == null || !t.name.StartsWith("FAM_")) return orig;
        var png = t.name.Substring(4); var alt = Path.ChangeExtension(png, null) + "@" + scheme + ".png";
        if (!TexExists(alt)) return orig;                 // this part keeps its colours in that scheme
        string key = orig.GetInstanceID() + "@" + scheme;
        if (paintMats.TryGetValue(key, out var m) && m != null) return m;
        m = new Material(orig) { name = orig.name + "@" + scheme };
        m.hideFlags |= HideFlags.DontUnloadUnusedAsset;
        m.SetTexture("_BaseColorMap", Tex(alt, false));
        // 0.3.38 (Abrams X): a scheme may bring its own surface map, <texture>@<Scheme>_mask, when the default's is a custom finish (silver).
        var mask = Path.ChangeExtension(png, null) + "@" + scheme + "_mask.png";
        if (TexExists(mask)) { m.SetTexture("_MaskMap", Tex(mask, true)); m.EnableKeyword("_MASKMAP"); }
        paintMats[key] = m;
        return m;
    }

    // Arsenal unit card: replace the donor's skin buttons with Default + the pack schemes.
    static void AfterSetUnitSkins(UnitInfoCard __instance)
    {
        try
        {
            var unit = __instance._unit; if (unit == null) return;
            paintSchemes.TryGetValue(unit.Name, out var list);
            bool ours = map.ContainsKey(unit.Name);
            if (!ours && (list == null || list.Length == 0)) return;          // vanilla model: vanilla skins
            var buttons = __instance._activeSkinButtons;
            foreach (var b in buttons) if (b != null) b.gameObject.SetActive(false);
            buttons.Clear();
            if (list == null || list.Length == 0)
            {
                // 0.3.37 (Osama 21 Nov: the Z-10 card showed the donor's vanilla skins). Our model with one colour set: the donor's skins never
                // showed on it, so the paint menu is hidden.
                if (__instance._skinMenuButton != null) __instance._skinMenuButton.gameObject.SetActive(false);
                if (__instance._selectedSkinName != null) __instance._selectedSkinName.text = PaintLabel("");
                if (__instance._selectedSkinDescription != null) __instance._selectedSkinDescription.text = "This model came with one paint scheme.";
                return;
            }
            var schemes = new[] { "" }.Concat(list).ToArray();
            var cur = CurrentPaint(unit.Name);
            string name = unit.Name;
            for (int i = 0; i < schemes.Length; i++)
            {
                var b = UnityEngine.Object.Instantiate(__instance._skinItemPrefab, __instance._skinsContainer);
                b.gameObject.SetActive(true);
                int idx = i;
                b.Initialize(PaintIdBase + i, true, schemes[i] == cur,
                    (Il2CppSystem.Action<int>)(System.Action<int>)(_ => PickPaint(__instance, name, schemes[idx])),
                    (Il2CppSystem.Action<int, SkinPackData>)(System.Action<int, SkinPackData>)((_, _) => { if (__instance._selectedSkinName != null) __instance._selectedSkinName.text = PaintLabel(schemes[idx]); }),
                    null, false);
                var thumb = PaintThumb(name, schemes[i]); if (thumb != null && b._preview != null) b._preview.sprite = thumb;
                buttons.Add(b);
            }
            if (__instance._skinMenuButton != null) __instance._skinMenuButton.gameObject.SetActive(true);
            if (__instance._selectedSkinName != null) __instance._selectedSkinName.text = PaintLabel(cur);
            if (__instance._selectedSkinDescription != null) __instance._selectedSkinDescription.text = "Paint scheme from the model pack. Shown in the Arsenal and in your battles.";
            MelonLogger.Msg($"FAMODELS_PAINT card {name}: {schemes.Length} scheme button(s), current '{PaintLabel(cur)}'");
        }
        catch (Exception ex) { MelonLogger.Error("FAMODELS_PAINT card: " + ex); }
    }
    static void PickPaint(UnitInfoCard card, string unit, string scheme)
    {
        paintChoices[unit] = scheme;
        try { File.WriteAllText(ChoicesFile, JsonSerializer.Serialize(paintChoices)); } catch (Exception ex) { MelonLogger.Warning("FAMODELS_PAINT save: " + ex.Message); }
        foreach (var (root, u) in live) if (u == unit && root != null) ApplyPaint(root, u);
        if (card != null && card._selectedSkinName != null) card._selectedSkinName.text = PaintLabel(scheme);
        MelonLogger.Msg($"FAMODELS_PAINT {unit} -> {PaintLabel(scheme)}");
    }
    static readonly Dictionary<string, Sprite> paintThumbs = new();
    static Sprite PaintThumb(string unit, string scheme)
    {
        var key = unit + "@" + scheme; if (paintThumbs.TryGetValue(key, out var s) && s != null) return s;
        var f = Path.Combine(dir, "paint", PaintFile(unit) + "@" + (scheme == "" ? "Default" : scheme) + ".png");
        if (!File.Exists(f)) return null;
        var t = new Texture2D(2, 2, TextureFormat.RGBA32, false) { name = "FAM_paint_" + key }; ImageConversion.LoadImage(t, File.ReadAllBytes(f), true);
        t.hideFlags |= HideFlags.DontUnloadUnusedAsset;
        s = Sprite.Create(t, new Rect(0, 0, t.width, t.height), new Vector2(0.5f, 0.5f)); s.hideFlags |= HideFlags.DontUnloadUnusedAsset;
        return paintThumbs[key] = s;
    }
    internal static string PaintFile(string unit) => new string(unit.Select(c => char.IsLetterOrDigit(c) ? c : '_').ToArray());
}

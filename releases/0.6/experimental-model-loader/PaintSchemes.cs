using System.Text.Json;
using HarmonyLib;
using MelonLoader;
using UnityEngine;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.InfoCard;
using Il2CppBrokenArrow.Client.Ecs.Configs.UserItems;

namespace FAModels;
// 0.3.36 paint schemes (Osama 21 Nov 2026, thread 1572407822849810463: "add variants of all the units we have multiple textures for as a paint
// option ... Mainly for Arsenal", "for our Chinese and new models, remove the default skins", "make sure they're Armory quality").
// The extra colour sets that came with the model packs are shipped as <texture>@<Scheme>.fat next to the default texture, at the same size.
// paint-schemes.json lists the schemes of each unit. On those units the Arsenal paint menu shows "Default" and the pack schemes instead of
// the donor's vanilla skins (which never showed on our models). The choice is local (paint-choices.json, per unit): it never goes into the
// deck or to the game's server, so a player cannot be refused for an unowned skin. It shows in the Arsenal and in the player's own battles.
public partial class Mod
{
    static Dictionary<string, string[]> paintSchemes = new();
    static Dictionary<string, string> paintChoices = new();
    static readonly Dictionary<int, Material> paintOrig = new();        // renderer -> its default (shared) material
    static readonly Dictionary<string, Material> paintMats = new();     // default material + scheme -> scheme copy
    const int PaintIdBase = 970000;                                     // button ids: base + index (0 = Default); never sent anywhere
    static readonly Dictionary<string, string> PaintNames = new(StringComparer.OrdinalIgnoreCase)
    {
        ["Plain"] = "Plain green", ["Dust"] = "Desert", ["DustCamo"] = "Desert camo", ["DustMix"] = "Desert mix", ["Camo"] = "Woodland camo",
        ["Mix"] = "Mixed camo", ["dig"] = "Digital", ["Yellow"] = "Yellow", ["YellowMix"] = "Yellow mix", ["Yellowmix"] = "Yellow mix",
        ["Green"] = "Green", ["Navy"] = "Navy grey", ["Black"] = "Black",
    };
    static string PaintLabel(string s) => s == "" ? "Default" : PaintNames.TryGetValue(s, out var n) ? n : s;
    static string ChoicesFile => Path.Combine(MelonLoader.Utils.MelonEnvironment.UserDataDirectory, "FAModels-paint-choices.json");

    static void InstallPaintSchemes(HarmonyLib.Harmony h)
    {
        var f = Path.Combine(dir, "paint-schemes.json");
        if (!File.Exists(f)) { MelonLogger.Msg("FAMODELS_PAINT off: no paint-schemes.json"); return; }
        paintSchemes = JsonSerializer.Deserialize<Dictionary<string, string[]>>(File.ReadAllText(f)) ?? new();
        try { if (File.Exists(ChoicesFile)) paintChoices = JsonSerializer.Deserialize<Dictionary<string, string>>(File.ReadAllText(ChoicesFile)) ?? new(); }
        catch (Exception ex) { MelonLogger.Warning("FAMODELS_PAINT choices unreadable, all default: " + ex.Message); }
        h.Patch(AccessTools.Method(typeof(UnitInfoCard), "SetUnitSkins"), postfix: new HarmonyMethod(typeof(Mod), nameof(AfterSetUnitSkins)));
        MelonLogger.Msg($"FAMODELS_PAINT ready: {paintSchemes.Count} unit(s) with pack paint schemes, {paintChoices.Count} saved choice(s)");
    }

    // Called after a model is built for a unit (Apply) and when the player picks a scheme.
    static void ApplyPaint(GameObject root, string unit)
    {
        if (root == null || !paintSchemes.ContainsKey(unit)) return;
        paintChoices.TryGetValue(unit, out var scheme); scheme ??= "";
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
        paintMats[key] = m;
        return m;
    }

    // Arsenal unit card: replace the donor's skin buttons with Default + the pack schemes.
    static void AfterSetUnitSkins(UnitInfoCard __instance)
    {
        try
        {
            var unit = __instance._unit; if (unit == null || !paintSchemes.TryGetValue(unit.Name, out var list) || list.Length == 0) return;
            var buttons = __instance._activeSkinButtons;
            foreach (var b in buttons) if (b != null) b.gameObject.SetActive(false);
            buttons.Clear();
            var schemes = new[] { "" }.Concat(list).ToArray();
            paintChoices.TryGetValue(unit.Name, out var cur); cur ??= "";
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

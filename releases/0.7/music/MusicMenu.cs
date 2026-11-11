using Il2CppBrokenArrow.Client.Ecs.UI.MainMenu;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using Il2CppTMPro;
using MelonLoader;
using HarmonyLib;
using UnityEngine;
using UnityEngine.UI;
using Object = UnityEngine.Object;

namespace FAMusic;

// Native UGUI control. No IMGUI overlay and no copied game callbacks.
internal static class MusicMenu
{
    static GameObject root;
    static MainMenuButton home;
    static TextMeshProUGUI label;
    static bool hasVersion;
    static Image flag;
    static Button button;
    static float nextScan;
    static string shown;
    static bool visible, failed;
    static readonly Dictionary<string, Sprite> sprites = new();
    static readonly Color Ink = new(.79f,.86f,.76f,1);

    internal static void Update()
    {
        if (failed || Time.unscaledTime < nextScan) return;
        nextScan = Time.unscaledTime + .2f;
        try
        {
            if (home == null)
            {
                foreach (var b in Resources.FindObjectsOfTypeAll<MainMenuButton>())
                {
                    if (!b.gameObject.scene.IsValid() || b._buttonText == null) continue;
                    if (!b._buttonText.text.Trim().Equals("Home", StringComparison.OrdinalIgnoreCase)) continue;
                    home = b; break;
                }
                if (home == null) return;
            }
            if (root == null) Create();
            bool show = home.isActiveAndEnabled && home.Selected;
            if (show != visible)
            {
                visible = show; root.SetActive(show);
                MelonLogger.Msg("FA_MUSIC_UI visible=" + show);
            }
            if (shown != Player.CurrentPack) Refresh();
        }
        catch (Exception e)
        {
            failed = true;
            if (root != null) root.SetActive(false);
            MelonLogger.Error("FA_MUSIC_UI_FAILED: " + e);
        }
    }

    static RectTransform Rect(string name, Transform parent, Vector2 position, Vector2 size)
    {
        var go = new GameObject(name);
        var rt = go.AddComponent<RectTransform>();
        rt.SetParent(parent, false);
        rt.anchorMin = rt.anchorMax = new Vector2(.5f,0);
        rt.pivot = new Vector2(.5f,0);
        rt.anchoredPosition = position; rt.sizeDelta = size;
        return rt;
    }
    static TextMeshProUGUI Text(string name, Transform parent, string text, Vector2 p, Vector2 size, float fontSize)
    {
        var rt = Rect(name,parent,p,size);
        var t = rt.gameObject.AddComponent<TextMeshProUGUI>();
        t.font = home._buttonText.font;
        t.fontSharedMaterial = home._buttonText.fontSharedMaterial;
        t.fontSize = fontSize; t.fontStyle = FontStyles.Bold;
        t.alignment = TextAlignmentOptions.Center;
        t.color = Ink; t.raycastTarget = false;
        t.text = text;
        return t;
    }
    internal static void Install(HarmonyLib.Harmony harmony)
    {
        var type = AccessTools.TypeByName("FreedomArrow.Conquest.Prototype");
        var draw = type == null ? null : AccessTools.Method(type,"DrawVersionLabel");
        if (draw != null) harmony.Patch(draw,prefix:new HarmonyMethod(typeof(MusicMenu),nameof(DrawVersion)));
    }
    static bool DrawVersion() => !visible || !hasVersion;
    static void Create()
    {
        var canvas = home.GetComponentInParent<Canvas>();
        var rt = Rect("FA Music pack selector",canvas.transform,new Vector2(0,14),new Vector2(260,112));
        root = rt.gameObject; root.SetActive(false);
        // Copy the menu's own font/material and border sprite; keep the selector's click independent.
        var panel = root.AddComponent<Image>();
        panel.color = new Color(.04f,.06f,.05f,.72f);
        button = root.AddComponent<Button>(); button.targetGraphic = panel;
        var colors = button.colors;
        colors.normalColor = Color.white;
        colors.highlightedColor = new Color(1.45f,1.6f,1.4f,1);
        colors.pressedColor = new Color(.65f,.9f,.65f,1);
        colors.selectedColor = Color.white; colors.fadeDuration = .12f;
        button.colors = colors;
        var nav = button.navigation; nav.mode = Navigation.Mode.None; button.navigation = nav;
        button.onClick.AddListener((UnityEngine.Events.UnityAction)(Action)(() => { Player.CyclePack(); Refresh(); }));
        Text("Heading",rt,"MUSIC PACK",new Vector2(0,86),new Vector2(240,22),18);
        var iconRect = Rect("Pack flag",rt,new Vector2(0,36),new Vector2(76,44));
        flag = iconRect.gameObject.AddComponent<Image>(); flag.preserveAspect = true; flag.raycastTarget = false;
        label = Text("Pack name",rt,"",new Vector2(0,8),new Vector2(226,24),18);
        Text("Cycle hint",rt,"›",new Vector2(108,44),new Vector2(24,26),26);
        var line = Rect("Native menu border",rt,new Vector2(0,0),new Vector2(260,2));
        var border = line.gameObject.AddComponent<Image>();
        border.sprite = home._bottomBorderImage?.sprite; border.color = Ink; border.raycastTarget = false;
        rt.SetAsLastSibling();
        var runtime = AccessTools.TypeByName("FreedomArrow.Runtime");
        var identity = runtime?.GetProperty("DisplayLabel")?.GetValue(null)?.ToString();
        var loaded = MelonBase.RegisteredMelons.FirstOrDefault(m => m.GetType().FullName == "FreedomArrow.Runtime");
        identity = MenuIdentity.Resolve(identity, loaded?.Info.Name, loaded?.Info.Version);
        hasVersion = !string.IsNullOrEmpty(identity);
        if (hasVersion) Text("Loaded mod version",rt,identity,new Vector2(0,120),new Vector2(450,22),16);
        Refresh();
        MelonLogger.Msg($"FA_MUSIC_UI created native UGUI; font={home._buttonText.font.name}; canvas={canvas.name}");
    }
    static void Refresh()
    {
        shown = Player.CurrentPack;
        label.text = shown == "Game music" ? "GAME SOUNDTRACK" : shown.ToUpperInvariant();
        string key = shown switch { "USA" => "usa", "Russia" => "russia", "China" => "china", "Black Hawk Down" => "rangers", _ => "game" };
        if (!sprites.TryGetValue(key,out var sprite))
        {
            using var stream = typeof(MusicMenu).Assembly.GetManifestResourceStream("FAMusic.icons."+key+".png") ?? throw new InvalidDataException(key);
            using var mem = new MemoryStream(); stream.CopyTo(mem);
            var tex = new Texture2D(2,2,TextureFormat.RGBA32,false) {name="Music pack "+key,filterMode=FilterMode.Bilinear,wrapMode=TextureWrapMode.Clamp};
            if (!ImageConversion.LoadImage(tex,(Il2CppStructArray<byte>)mem.ToArray(),true)) throw new InvalidDataException(key);
            sprite = Sprite.Create(tex,new UnityEngine.Rect(0,0,tex.width,tex.height),new Vector2(.5f,.5f),100);
            sprites[key] = sprite;
        }
        flag.sprite = sprite;
    }
}

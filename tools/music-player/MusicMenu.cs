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
    static Image flag;
    static Button button;
    static float nextScan, nextHomeScan;
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
            // 1.5.4 (Osama 18 Nov 2026 02:2x PST: "I'm seeing the music pack in deployment ... It should only appear in the main menu"). His log: visible=True
            // on the Home tab at 02:16:07, a match from 02:20, and no visible=False after it. Leaving the menu destroys the Home button, so the branch below
            // returned before the panel was hidden. Outside the menu scene the panel is now hidden first, whatever happened to the Home button.
            if (UnityEngine.SceneManagement.SceneManager.GetActiveScene().name != "Hangar_Scene")
            {
                if (visible) { visible = false; if (root != null) root.SetActive(false); MelonLogger.Msg("FA_MUSIC_UI visible=False (left the menu)"); }
                home = null;
                nextScan = Time.unscaledTime + 2f; return;
            }
            // 1.5.5 (Osama 22 Nov 2026 14:4x, dev.32 log: visible=True under the title at 14:27:52, visible=False at 14:28:02 one second after
            // "Press any key", then never again): the Home button found under the title is replaced when the menu opens, and the held copy stayed
            // hidden for the rest of the session. A held button that is gone or hidden is looked up again (every 2 s), and an active one is preferred.
            if (home != null && (home.WasCollected || !home.isActiveAndEnabled) && Time.unscaledTime >= nextHomeScan) home = null;
            if (home == null)
            {
                // 1.5.3 (Osama 17 Nov 2026, 5v5 FPS test): FindObjectsOfTypeAll walks every loaded object. In a battle the Home button does not
                // exist, so this ran 5 times a second for the whole match and cost about 0.5 ms per frame with 5-20 ms spikes. Search only in
                // the menu scene, and at most once every 2 s there.
                if (UnityEngine.SceneManagement.SceneManager.GetActiveScene().name != "Hangar_Scene") { nextScan = Time.unscaledTime + 2f; return; }
                nextScan = Time.unscaledTime + 2f; nextHomeScan = Time.unscaledTime + 2f;
                MainMenuButton first = null;
                foreach (var b in Resources.FindObjectsOfTypeAll<MainMenuButton>())
                {
                    if (!b.gameObject.scene.IsValid() || b._buttonText == null) continue;
                    if (!b._buttonText.text.Trim().Equals("Home", StringComparison.OrdinalIgnoreCase)) continue;
                    first ??= b;
                    if (b.isActiveAndEnabled) { home = b; break; }
                }
                home ??= first;
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
    static bool DrawVersion() => !visible;
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
        if (!string.IsNullOrEmpty(identity)) Text("Verified mod version",rt,identity,new Vector2(0,120),new Vector2(450,22),16);
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

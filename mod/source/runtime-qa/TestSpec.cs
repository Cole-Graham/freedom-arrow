using System.Text.Json.Nodes;
using MelonLoader;
namespace FreedomArrow;
// Hidden-units test specs (Osama 23 Nov 2026 18:5x PST, thread 1567745029781454889: "just leave it as a toggle"). Specs 26 China, 27 USA and
// 28 Russia ship with ShowInHangar false (tools/pla-specs/test_specs_1123.py). UserData/FreedomArrow/test-spec.json {"show": true} sets them true in the
// database copy this game loads, so the Armory and deck creation show it. Read once at load: restart to change. No file = off.
// The packaged files are not changed, so the payload check and other players are not affected.
// 0.9.7 (Osama 24 Nov 2026 21:0x PST, "or hidden if the test mode is off"): the Blue Dragon (23), France (24) and Germany (25) previews and the
// Eurocorp country (5, Hidden) are off in the data too and come on with the same file (test_mode_previews_1124.py).
static class TestSpec
{
    static readonly int[] Specs = { 23, 24, 25, 26, 27, 28 };
    static readonly int[] Countries = { 5 };
    static bool? show;
    static bool Show(string root)
    {
        if (show is bool known) return known;
        string path = Path.Combine(root, "test-spec.json");
        bool on = false;
        try { on = File.Exists(path) && JsonNode.Parse(File.ReadAllText(path))?["show"]?.GetValue<bool>() == true; }
        catch (Exception e) { MelonLogger.Warning("FREEDOM_ARROW_TEST_SPEC: test-spec.json not read (" + e.Message + "); test mode stays off"); }
        show = on;
        return on;
    }
    internal static void Apply(JsonArray specs, string root)
    {
        if (!Show(root)) return;
        int shown = 0;
        foreach (var row in specs)
            if (row?["Id"] is JsonNode id && System.Array.IndexOf(Specs, id.GetValue<int>()) >= 0) { row["ShowInHangar"] = true; shown++; }
        if (shown == Specs.Length) MelonLogger.Msg("FREEDOM_ARROW_TEST_SPEC: test specs " + string.Join(", ", Specs) + " shown by test-spec.json");
        else MelonLogger.Warning($"FREEDOM_ARROW_TEST_SPEC: {shown} of {Specs.Length} test specs in this build");
    }
    internal static void ApplyCountries(JsonArray countries, string root)
    {
        if (!Show(root)) return;
        int shown = 0;
        foreach (var row in countries)
            if (row?["Id"] is JsonNode id && System.Array.IndexOf(Countries, id.GetValue<int>()) >= 0) { row["Hidden"] = false; shown++; }
        if (shown == Countries.Length) MelonLogger.Msg("FREEDOM_ARROW_TEST_SPEC: Eurocorp (country 5) shown by test-spec.json");
        else MelonLogger.Warning($"FREEDOM_ARROW_TEST_SPEC: {shown} of {Countries.Length} test countries in this build");
    }
}

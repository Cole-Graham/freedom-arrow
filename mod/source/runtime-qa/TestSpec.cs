using System.Text.Json.Nodes;
using MelonLoader;
namespace FreedomArrow;
// Hidden-units test specs (Osama 23 Nov 2026 18:5x PST, thread 1567745029781454889: "just leave it as a toggle"). Specs 26 China, 27 USA and
// 28 Russia ship with ShowInHangar false (tools/pla-specs/test_specs_1123.py). UserData/FreedomArrow/test-spec.json {"show": true} sets them true in the
// database copy this game loads, so the Armory and deck creation show it. Read once at load: restart to change. No file = off.
// The packaged files are not changed, so the payload check and other players are not affected.
static class TestSpec
{
    static readonly int[] Specs = { 26, 27, 28 };
    internal static void Apply(JsonArray specs, string root)
    {
        string path = Path.Combine(root, "test-spec.json");
        bool show = false;
        try { show = File.Exists(path) && JsonNode.Parse(File.ReadAllText(path))?["show"]?.GetValue<bool>() == true; }
        catch (Exception e) { MelonLogger.Warning("FREEDOM_ARROW_TEST_SPEC: test-spec.json not read (" + e.Message + "); test spec stays off"); }
        if (!show) return;
        int shown = 0;
        foreach (var row in specs)
            if (row?["Id"] is JsonNode id && System.Array.IndexOf(Specs, id.GetValue<int>()) >= 0) { row["ShowInHangar"] = true; shown++; }
        if (shown == Specs.Length) MelonLogger.Msg("FREEDOM_ARROW_TEST_SPEC: hidden-units test specs 26, 27, 28 shown by test-spec.json");
        else MelonLogger.Warning($"FREEDOM_ARROW_TEST_SPEC: {shown} of {Specs.Length} test specs in this build");
    }
}

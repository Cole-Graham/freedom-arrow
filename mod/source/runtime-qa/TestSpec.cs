using System.Text.Json.Nodes;
using MelonLoader;
namespace FreedomArrow;
// China hidden-units test spec (Osama 23 Nov 2026 18:5x PST, thread 1567745029781454889: "just leave it as a toggle"). Spec 26 ships with
// ShowInHangar false (tools/pla-specs/china_test_spec_1123.py). UserData/FreedomArrow/test-spec.json {"show": true} sets it true in the
// database copy this game loads, so the Armory and deck creation show it. Read once at load: restart to change. No file = off.
// The packaged files are not changed, so the payload check and other players are not affected.
static class TestSpec
{
    const int Spec = 26;
    internal static void Apply(JsonArray specs, string root)
    {
        string path = Path.Combine(root, "test-spec.json");
        bool show = false;
        try { show = File.Exists(path) && JsonNode.Parse(File.ReadAllText(path))?["show"]?.GetValue<bool>() == true; }
        catch (Exception e) { MelonLogger.Warning("FREEDOM_ARROW_TEST_SPEC: test-spec.json not read (" + e.Message + "); test spec stays off"); }
        if (!show) return;
        foreach (var row in specs)
            if (row?["Id"]?.GetValue<int>() == Spec) { row["ShowInHangar"] = true; MelonLogger.Msg("FREEDOM_ARROW_TEST_SPEC: spec 26 (hidden China units) shown by test-spec.json"); return; }
        MelonLogger.Warning("FREEDOM_ARROW_TEST_SPEC: spec 26 not in this build");
    }
}

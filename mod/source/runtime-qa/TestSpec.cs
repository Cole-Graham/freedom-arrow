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
    static bool? show;
    // test-spec.json {"show": true}: also used by PreviewCards (Blue Dragon / Eurocorp stat cards).
    internal static bool Show(string root)
    {
        if (show is bool known) return known;
        string path = Path.Combine(root, "test-spec.json");
        bool on = false;
        try { on = File.Exists(path) && JsonNode.Parse(File.ReadAllText(path))?["show"]?.GetValue<bool>() == true; }
        catch (Exception e) { MelonLogger.Warning("FREEDOM_ARROW_TEST_SPEC: test-spec.json not read (" + e.Message + "); test mode stays off"); }
        show = on;
        return on;
    }
    // 24 Nov 2026 23:4x (Osama: "if I don't have developer option on I shouldn't see this"): the test-spec units ship with DisplayInArmory false,
    // otherwise the Armory shows a "Test: Hidden Units" heading with their cards. In test mode they are shown again. Units load before
    // SpecializationAvailabilities, so their test-spec rows are read from the packaged constants file.
    internal static void ApplyUnits(JsonArray units, string root)
    {
        if (!Show(root)) return;
        var ids = new HashSet<int>();
        try
        {
            var sa = JsonNode.Parse(File.ReadAllText(Path.Combine(root, "constants", "specialization_availabilities.json")))?.AsObject();
            if (sa != null)
                foreach (var kv in sa)
                    if (kv.Value?["SpecializationId"] is JsonNode s && System.Array.IndexOf(Specs, s.GetValue<int>()) >= 0 && kv.Value["UnitId"] is JsonNode u) ids.Add(u.GetValue<int>());
        }
        catch (Exception e) { MelonLogger.Warning("FREEDOM_ARROW_TEST_SPEC: test-spec units not read (" + e.Message + ")"); return; }
        int shown = 0;
        foreach (var row in units)
            if (row?["Id"] is JsonNode id && ids.Contains(id.GetValue<int>())) { row["DisplayInArmory"] = true; shown++; }
        MelonLogger.Msg($"FREEDOM_ARROW_TEST_SPEC: {shown} test-spec units shown in the Armory by test-spec.json");
    }
    internal static void Apply(JsonArray specs, string root)
    {
        if (!Show(root)) return;
        int shown = 0;
        foreach (var row in specs)
            if (row?["Id"] is JsonNode id && System.Array.IndexOf(Specs, id.GetValue<int>()) >= 0) { row["ShowInHangar"] = true; shown++; }
        if (shown == Specs.Length) MelonLogger.Msg("FREEDOM_ARROW_TEST_SPEC: hidden-units test specs 26, 27, 28 shown by test-spec.json");
        else MelonLogger.Warning($"FREEDOM_ARROW_TEST_SPEC: {shown} of {Specs.Length} test specs in this build");
    }
}

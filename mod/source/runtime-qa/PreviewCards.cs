using System.Text.Json.Nodes;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Arsenal.InfoCard;
using Il2CppBrokenArrow.DataBase.Models;
using MelonLoader;
using UnityEngine;
namespace FreedomArrow;
// Preview factions (Osama 24 Nov 2026 21:2x PST, thread 1567745029781454889: "for the BD and Eurocorp preview factions. I want people to go in and
// see the spec and look around. But I don't want people to click on it and see the stats"). Specs 23 Blue Dragon, 24 France and 25 Germany stay
// in the Armory; for their units the Armory info card (UnitInfoCard: stats, weapons, armour, abilities) is made invisible and click-through after
// Init/Refresh. Other units get the card back. test-spec.json {"show": true} (TestSpec) shows the cards. The unit set comes from the
// SpecializationAvailabilities rows this game loads (Runtime.cs), so new preview cards need no code change.
static class PreviewCards
{
    static readonly int[] Specs = { 23, 24, 25 };
    static readonly HashSet<int> units = new();
    static bool logged, broken;
    internal static void Collect(JsonArray rows)
    {
        units.Clear();
        foreach (var row in rows)
            if (row?["SpecializationId"] is JsonNode s && System.Array.IndexOf(Specs, s.GetValue<int>()) >= 0 && row["UnitId"] is JsonNode u) units.Add(u.GetValue<int>());
        MelonLogger.Msg($"FREEDOM_ARROW_PREVIEW_CARDS: {units.Count} preview units in specs 23, 24, 25");
    }
    public static void Install(HarmonyLib.Harmony h, string root)
    {
        if (TestSpec.Show(root)) { MelonLogger.Msg("FREEDOM_ARROW_PREVIEW_CARDS off: test-spec.json shows the preview stat cards"); return; }
        var after = new HarmonyMethod(typeof(PreviewCards), nameof(After));
        h.Patch(AccessTools.Method(typeof(UnitInfoCard), "Init"), postfix: after);
        h.Patch(AccessTools.Method(typeof(UnitInfoCard), "Refresh"), postfix: after);
        MelonLogger.Msg("FREEDOM_ARROW_PREVIEW_CARDS installed: Armory stat card hidden for units of specs 23, 24, 25 (unit list read at database load)");
    }
    static void After(UnitInfoCard __instance, Units __0)
    {
        if (broken || __instance == null) return;
        try
        {
            bool hide = __0 != null && units.Contains(__0.Id);
            var go = __instance.gameObject;
            var group = go.GetComponent<CanvasGroup>();
            if (group == null) { if (!hide) return; group = go.AddComponent<CanvasGroup>(); }
            group.alpha = hide ? 0f : 1f; group.interactable = !hide; group.blocksRaycasts = !hide;
            if (hide && !logged) { logged = true; MelonLogger.Msg($"FREEDOM_ARROW_PREVIEW_CARDS stat card hidden for preview unit {__0.Id}"); }
        }
        catch (Exception e) { broken = true; MelonLogger.Error("FREEDOM_ARROW_PREVIEW_CARDS_FAILED: native card kept. " + e.Message); }
    }
}

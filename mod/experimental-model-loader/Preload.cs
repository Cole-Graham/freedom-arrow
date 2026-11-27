using System.Text.Json;
using MelonLoader;
using UnityEngine;
using Il2CppBrokenArrow.Client.Ecs.Decks_v2;
using Il2CppBrokenArrow.Client.Ecs.Decks.Models;
namespace FAModels;
// 0.3.27 (Osama 14 Nov: "there's a stutter when I call a unit into the game"; "optimize for the potatoes"). The first copy of a unit
// type read its model file in the frame it spawned (J-35 323 ms, J-36 299 ms in his log). The game sets every player's deck at match
// start (SharedPlayerDeck.OnSetDeck); the battle models of the mapped units in those decks (and their transports) now load one per
// frame from then on, into the same kept-model cache the spawn uses. Only the match's decks; armory models are not loaded.
public partial class Mod
{
    static Dictionary<int, string> unitNames = new();
    static readonly Queue<string> preload = new();
    static readonly HashSet<string> preloadSeen = new();
    static readonly Queue<string> preloadHeavy = new();   // 0.3.46: heavier detail levels, built during deployment after the burst
    static void InstallPreload()
    {
        // Unit id -> Name for the mapped units, from the Freedom Arrow constants (models.json is keyed by Name).
        var cf = Path.Combine(MelonLoader.Utils.MelonEnvironment.UserDataDirectory, "FreedomArrow", "constants", "units.json");
        if (File.Exists(cf))
            foreach (var kv in JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(File.ReadAllText(cf)) ?? new())
                if (kv.Value.ValueKind == JsonValueKind.Object && kv.Value.TryGetProperty("Name", out var n) && n.ValueKind == JsonValueKind.String && map.ContainsKey(n.GetString()!))
                    unitNames[int.Parse(kv.Key)] = n.GetString()!;
        HookSetDeck();
        LoadSpecTables();
        MelonLogger.Msg($"FAMODELS preload installed: {unitNames.Count} mapped unit id(s), {specUnits.Count} spec(s) known, {swapsOf.Count} unit(s) with loadout swaps");
    }
    // native-preload branch (Osama 27 Nov 2026 02:1x: "make a version of the game that preloads models natively like we do in vanilla").
    // Player logs of 26/27 Nov show OnSetDeck queuing models only for the local player: every other player's deck arrives with no slots,
    // so their FA models were read and built the first time a unit of that type appeared in battle. A deck with no slots now queues every
    // mapped unit its two specializations can field (cards, their transports and their loadout swaps), from the Freedom Arrow constants.
    // Loadout swap units (ReplaceUnitId) are queued for the local deck too; before, a swap loadout loaded on its first spawn.
    static readonly Dictionary<int, HashSet<int>> specUnits = new();
    static readonly Dictionary<int, List<int>> swapsOf = new();
    static Dictionary<string, JsonElement> ReadConstants(string name)
    {
        var f = Path.Combine(MelonLoader.Utils.MelonEnvironment.UserDataDirectory, "FreedomArrow", "constants", name + ".json");
        return File.Exists(f) ? JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(File.ReadAllText(f)) ?? new() : new();
    }
    static int Int(JsonElement e, string k) => e.ValueKind == JsonValueKind.Object && e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.Number ? v.GetInt32() : 0;
    static void LoadSpecTables()
    {
        var cardSpec = new Dictionary<int, int>();
        foreach (var kv in ReadConstants("specialization_availabilities"))
        {
            int spec = Int(kv.Value, "SpecializationId"), unit = Int(kv.Value, "UnitId");
            if (spec == 0 || unit == 0) continue;
            cardSpec[int.Parse(kv.Key)] = spec;
            if (!specUnits.TryGetValue(spec, out var set)) specUnits[spec] = set = new();
            set.Add(unit);
        }
        foreach (var kv in ReadConstants("transport_availabilities"))
            if (cardSpec.TryGetValue(Int(kv.Value, "SpecializationAvailabilityId"), out var spec) && Int(kv.Value, "UnitId") is int u && u != 0) specUnits[spec].Add(u);
        var modUnit = new Dictionary<int, int>();
        foreach (var kv in ReadConstants("modifications")) if (Int(kv.Value, "UnitId") is int u && u != 0) modUnit[int.Parse(kv.Key)] = u;
        foreach (var kv in ReadConstants("options"))
            if (modUnit.TryGetValue(Int(kv.Value, "ModificationId"), out var u) && Int(kv.Value, "ReplaceUnitId") is int r && r != 0 && r != u)
            { if (!swapsOf.TryGetValue(u, out var l)) swapsOf[u] = l = new(); if (!l.Contains(r)) l.Add(r); }
    }
    // 0.3.51 (Osama 27 Nov 2026: "Why aren't we preloading all models and at the lowest lod at the Start of the game not after deployment"). The
    // 27 Nov Oil Rush logs (Ravity, CDRMatthew, FAModels 0.3.49) show OnSetDeck only in the first match after launch: the 2nd and 3rd matches,
    // including the 5v5, logged no deck at all, so all 771-871 battle models and bodies were built when each unit first appeared. Now the handler is
    // attached again on every scene load, and once a second outside the hangar the game's own deck table (SharedPlayerDeck._playerDecks) is read
    // directly; every deck found there that was not queued yet goes through the same preload. Each log line names the path that found the deck.
    static Il2CppSystem.Action<int, IDeckDataModel, IDeckHelper> setDeckCb;
    static void HookSetDeck()
    {
        try { if (setDeckCb != null) SharedPlayerDeck.remove_OnSetDeck(setDeckCb); } catch { }
        setDeckCb = new System.Action<int, IDeckDataModel, IDeckHelper>(OnSetDeck);
        SharedPlayerDeck.add_OnSetDeck(setDeckCb);
    }
    static readonly Dictionary<int, IntPtr> decksQueued = new();
    static float deckPollT; static bool battleScene;
    static void PreloadSceneLoaded(string sceneName)
    {
        battleScene = sceneName != "Hangar_Scene" && sceneName != "Void" && sceneName != "EntryPoint";
        decksQueued.Clear(); preloadSeen.Clear();   // FreeUnused has just freed every model no live unit uses
        try { HookSetDeck(); } catch (Exception ex) { MelonLogger.Warning("FAMODELS preload: deck event not attached: " + ex.Message); }
    }
    static void PollDecks()
    {
        if (!battleScene) return;
        float now = Time.realtimeSinceStartup;
        if (now - deckPollT < 1f) return;
        deckPollT = now;
        var table = SharedPlayerDeck._playerDecks;
        if (table == null) return;
        var ids = new List<int>();
        foreach (var k in table.Keys) ids.Add(k);
        foreach (var id in ids)
            if (SharedPlayerDeck.TryGetDeck(id, out var deck) && deck != null && (!decksQueued.TryGetValue(id, out var ptr) || ptr != deck.Pointer))
                QueueDeck(id, deck, "deck table");
    }
    // 0.3.34 (Osama 17 Nov 2026: "we should preload all the models before the game loads so there's no stuttering on model loading"). The
    // 5v5 detail log showed the one-per-frame preload as 10 s of 50-107 ms frames right after deployment began. Now the whole queue is built in
    // one go 0.3 s after the last deck of the match is set (the game is in its deployment pause then), so the match starts with every battle
    // model, LOD, body and infantry weapon already built: one pause at the start instead of a stutter for every model. preloadSeen is cleared
    // when a new match sets its decks (more than 30 s after the last deck), because the game unloads the kept meshes between scenes.
    static float lastSetDeck = -100f; static bool burst;
    static void OnSetDeck(int player, IDeckDataModel deck, IDeckHelper helper) => QueueDeck(player, deck, "deck event");
    static void QueueDeck(int player, IDeckDataModel deck, string source)
    {
        try
        {
            decksQueued[player] = deck.Pointer;
            float now = Time.realtimeSinceStartup;
            if (now - lastSetDeck > 30f) { preloadSeen.Clear(); preloadHeavy.Clear(); heavyBuilt = 0; ResetCurtainHold(); MelonLogger.Msg("FAMODELS preload: new match, cache list reset"); }
            lastSetDeck = now; burst = true;
            int added = 0, readOnly = 0, slotCount = 0;
            var ids = new List<int>();
            foreach (var slots in deck.GetSlots.Values)
                foreach (var s in slots) { slotCount++; ids.Add(s.UnitID); ids.Add(s.TransportID); }
            if (slotCount == 0)
            {
                source = $"specs {deck.Spec1ID}+{deck.Spec2ID} (deck has no slots)";
                foreach (var spec in new[] { deck.Spec1ID, deck.Spec2ID }) if (specUnits.TryGetValue(spec, out var set)) ids.AddRange(set);
            }
            foreach (var u in ids.ToList()) if (swapsOf.TryGetValue(u, out var l)) ids.AddRange(l);
            foreach (var id in ids.Distinct())
                    {
                        if (unitNames.TryGetValue(id, out var name) && map.TryGetValue(name, out var e) && e.file != "")
                        {
                            // 0.3.31: the file is read and prepared on a background thread right away (Background.cs Prefetch).
                            // 0.3.46 (Osama 24 Nov 2026: "load the lowest load and let the engine logic handle the rest"; "Shouldn't we
                            // preload during deployment?"): of a battle model with detail levels only the lightest is built in the burst. The
                            // heavier levels are read in the background and then built during the deployment pause, within the 6 ms frame
                            // budget (TickPreloadHeavy). A unit that spawns before its heavier levels are built shows the lightest and gets the
                            // rest over later frames (LodStreaming.cs). The levels are the ones Apply uses.
                            var levels = new List<string> { e.battle != "" ? e.battle : e.file };
                            if (e.battle != "") levels.AddRange(e.lods.Where(lf => lf != "" && File.Exists(Path.Combine(dir, lf))));
                            var light = levels[levels.Count - 1];
                            if (preloadSeen.Add(light)) { preload.Enqueue(light); Prefetch(light); added++; }
                            foreach (var lf in levels.Take(levels.Count - 1).Reverse()) if (preloadSeen.Add(lf)) { preloadHeavy.Enqueue(lf); Prefetch(lf); readOnly++; }
                        }
                        // 0.3.29 (Osama 15 Nov: "we should build it all before the match"): infantry bodies, their GPU textures and
                        // their battle weapon models are built here too, so the first squad of a type does no file work in battle.
                        foreach (var b in BodyFiles(id)) if (preloadSeen.Add("body:" + b)) { preload.Enqueue("body:" + b); added++; }
                        foreach (var r in weaponRules.Where(r => r.unitId == id))
                        { var f = r.battle != "" ? r.battle : r.file; if (f != "" && preloadSeen.Add(f)) { preload.Enqueue(f); Prefetch(f); added++; } }
                    }
            MelonLogger.Msg($"FAMODELS preload deck of player {player} from {source}, curtain {(curtainUp ? "up" : "down")}: {added} lightest battle level(s), bodies and infantry weapons queued; {readOnly} heavier level(s) to build during deployment");
        }
        catch (Exception ex) { MelonLogger.Error("FAMODELS preload deck: " + ex.Message); }
    }
    // One model per frame, so a weak PC never stalls for the whole deck at once.
    static void TickPreload()
    {
        try { PollDecks(); } catch (Exception ex) { MelonLogger.Warning("FAMODELS preload deck table: " + ex.Message); deckPollT = Time.realtimeSinceStartup + 30f; }
        if (preload.Count == 0) { burst = false; return; }
        if (burst && curtainUp && Time.realtimeSinceStartup - lastSetDeck > 0.3f)
        {
            // native-preload: under the loading screen, build within CurtainBudgetMs per frame so the screen keeps animating.
            long t0 = System.Diagnostics.Stopwatch.GetTimestamp(); int built = 0;
            while (preload.Count > 0 && SinceMs(t0) < CurtainBudgetMs)
            {
                var b = preload.Dequeue();
                try { if (b.StartsWith("body:")) PreloadBody(b.Substring(5)); else LoadFam(b, out _); built++; }
                catch (Exception ex) { MelonLogger.Warning($"FAMODELS preload {b}: {ex.Message}"); }
            }
            if (preload.Count == 0) { burst = false; MelonLogger.Msg($"FAMODELS preload: battle models built under the loading screen ({Time.realtimeSinceStartup - lastSetDeck:F1} s after the decks)"); }
            return;
        }
        if (burst && Time.realtimeSinceStartup - lastSetDeck > 0.3f)
        {
            burst = false;
            int n = preload.Count, fails = 0; var all = System.Diagnostics.Stopwatch.StartNew();
            while (preload.Count > 0)
            {
                var b = preload.Dequeue();
                inPreloadBuild = true;
                try { if (b.StartsWith("body:")) PreloadBody(b.Substring(5)); else LoadFam(b, out _); }   // LoadFam waits for the background job
                catch (Exception ex) { fails++; MelonLogger.Warning($"FAMODELS preload {b}: {ex.Message}"); }
                finally { inPreloadBuild = false; }
            }
            MelonLogger.Msg($"FAMODELS preload burst: {n} model(s)/bodies built in {all.Elapsed.TotalMilliseconds:F0} ms at match start ({fails} failed)");
            return;
        }
        var f = preload.Dequeue();
        // 0.3.31: a model whose background preparation is still running waits at the back of the queue; this frame does nothing.
        if (!f.StartsWith("body:") && !FamReady(f) && famJobs.ContainsKey(f)) { preload.Enqueue(f); return; }
        var sw = System.Diagnostics.Stopwatch.StartNew();
        try
        {
            bool kept = false;
            inPreloadBuild = true;
            if (f.StartsWith("body:")) PreloadBody(f.Substring(5)); else LoadFam(f, out kept);
            if (Verbose || preload.Count == 0 || sw.Elapsed.TotalMilliseconds > 50) MelonLogger.Msg($"FAMODELS preloaded {f} in {sw.Elapsed.TotalMilliseconds:F0} ms{(kept ? " (already kept)" : "")}, {preload.Count} left");
        }
        catch (Exception ex) { MelonLogger.Warning($"FAMODELS preload {f}: {ex.Message}"); }
        finally { inPreloadBuild = false; }
    }

    // 0.3.46: after the burst, the heavier detail levels are built one at a time while the frame has budget left, lightest first. Runs
    // after the spawn queue and the level upgrades (UpdateRest), so units being swapped come first. A file whose background read is
    // still running goes to the back of the queue. Levels a spawn already built are skipped.
    static int heavyBuilt; static float heavyT;
    static void TickPreloadHeavy(long budgetStart)
    {
        if (burst || preloadHeavy.Count == 0) return;
        if (heavyBuilt == 0) heavyT = Time.realtimeSinceStartup;
        for (int tries = preloadHeavy.Count; tries > 0 && preloadHeavy.Count > 0; tries--)
        {
            if (SinceMs(budgetStart) > (curtainUp ? CurtainBudgetMs : ModelBudgetMs)) return;
            var f = preloadHeavy.Dequeue();
            if (KeptFam(f)) continue;
            if (!StreamReady(f)) { preloadHeavy.Enqueue(f); continue; }
            inPreloadBuild = true;
            try { LoadFam(f, out _); heavyBuilt++; }
            catch (Exception ex) { MelonLogger.Warning($"FAMODELS preload level {f}: {ex.Message}"); }
            finally { inPreloadBuild = false; }
            if (preloadHeavy.Count == 0) MelonLogger.Msg($"FAMODELS preload: {heavyBuilt} heavier detail level(s) built in {Time.realtimeSinceStartup - heavyT:F1} s after the burst{(curtainUp ? " (under the loading screen)" : "")}");
            if (!curtainUp) return;   // at most one level per frame in the match; under the loading screen, as many as the budget allows
        }
    }
}

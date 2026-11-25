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
        SharedPlayerDeck.add_OnSetDeck(new System.Action<int, IDeckDataModel, IDeckHelper>(OnSetDeck));
        MelonLogger.Msg($"FAMODELS preload installed: {unitNames.Count} mapped unit id(s)");
    }
    // 0.3.34 (Osama 17 Nov 2026: "we should preload all the models before the game loads so there's no stuttering on model loading"). The
    // 5v5 detail log showed the one-per-frame preload as 10 s of 50-107 ms frames right after deployment began. Now the whole queue is built in
    // one go 0.3 s after the last deck of the match is set (the game is in its deployment pause then), so the match starts with every battle
    // model, LOD, body and infantry weapon already built: one pause at the start instead of a stutter for every model. preloadSeen is cleared
    // when a new match sets its decks (more than 30 s after the last deck), because the game unloads the kept meshes between scenes.
    static float lastSetDeck = -100f; static bool burst;
    static void OnSetDeck(int player, IDeckDataModel deck, IDeckHelper helper)
    {
        try
        {
            float now = Time.realtimeSinceStartup;
            if (now - lastSetDeck > 30f) { preloadSeen.Clear(); preloadHeavy.Clear(); heavyBuilt = 0; MelonLogger.Msg("FAMODELS preload: new match, cache list reset"); }
            lastSetDeck = now; burst = true;
            int added = 0, readOnly = 0;
            foreach (var slots in deck.GetSlots.Values)
                foreach (var s in slots)
                    foreach (var id in new[] { s.UnitID, s.TransportID })
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
            MelonLogger.Msg($"FAMODELS preload deck of player {player}: {added} lightest battle level(s), bodies and infantry weapons queued; {readOnly} heavier level(s) to build during deployment");
        }
        catch (Exception ex) { MelonLogger.Error("FAMODELS preload deck: " + ex.Message); }
    }
    // One model per frame, so a weak PC never stalls for the whole deck at once.
    static void TickPreload()
    {
        if (preload.Count == 0) { burst = false; return; }
        if (burst && Time.realtimeSinceStartup - lastSetDeck > 0.3f)
        {
            burst = false;
            int n = preload.Count, fails = 0; var all = System.Diagnostics.Stopwatch.StartNew();
            while (preload.Count > 0)
            {
                var b = preload.Dequeue();
                try { if (b.StartsWith("body:")) PreloadBody(b.Substring(5)); else LoadFam(b, out _); }   // LoadFam waits for the background job
                catch (Exception ex) { fails++; MelonLogger.Warning($"FAMODELS preload {b}: {ex.Message}"); }
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
            if (f.StartsWith("body:")) PreloadBody(f.Substring(5)); else LoadFam(f, out kept);
            if (Verbose || preload.Count == 0 || sw.Elapsed.TotalMilliseconds > 50) MelonLogger.Msg($"FAMODELS preloaded {f} in {sw.Elapsed.TotalMilliseconds:F0} ms{(kept ? " (already kept)" : "")}, {preload.Count} left");
        }
        catch (Exception ex) { MelonLogger.Warning($"FAMODELS preload {f}: {ex.Message}"); }
    }

    // 0.3.46: after the burst, the heavier detail levels are built one at a time while the frame has budget left, lightest first. Runs
    // after the spawn queue and the level upgrades (UpdateRest), so units being swapped come first. A file whose background read is
    // still running goes to the back of the queue. Levels a spawn already built are skipped.
    static int heavyBuilt; static float heavyT;
    // 0.3.47 (End 25 Nov: load a level only when it is needed, unload it when it is not): the heavier levels are only read in the
    // background during deployment (file work done before the battle); LodStreaming.cs builds each on the GPU when a unit needs it.
    // UserData/FAModels/lod-preload-build.txt brings back 0.3.46: build them all during deployment and never free them in battle.
    static bool? lodPreloadBuild;
    static bool LodPreloadBuild => lodPreloadBuild ??= File.Exists(Path.Combine(dir, "lod-preload-build.txt"));
    static void TickPreloadHeavy(long budgetStart)
    {
        if (burst || preloadHeavy.Count == 0) return;
        if (!LodPreloadBuild) { int n = preloadHeavy.Count; while (preloadHeavy.Count > 0) StreamReady(preloadHeavy.Dequeue()); MelonLogger.Msg($"FAMODELS preload: {n} heavier detail level(s) read in the background, built when a unit needs them"); return; }
        if (heavyBuilt == 0) heavyT = Time.realtimeSinceStartup;
        for (int tries = preloadHeavy.Count; tries > 0 && preloadHeavy.Count > 0; tries--)
        {
            if (SinceMs(budgetStart) > ModelBudgetMs) return;
            var f = preloadHeavy.Dequeue();
            if (KeptFam(f)) continue;
            if (!StreamReady(f)) { preloadHeavy.Enqueue(f); continue; }
            try { LoadFam(f, out _); heavyBuilt++; }
            catch (Exception ex) { MelonLogger.Warning($"FAMODELS preload level {f}: {ex.Message}"); }
            if (preloadHeavy.Count == 0) MelonLogger.Msg($"FAMODELS preload: {heavyBuilt} heavier detail level(s) built in {Time.realtimeSinceStartup - heavyT:F1} s after the burst");
            return;   // at most one level per frame
        }
    }
}

using System;
using System.IO;
using System.Collections.Generic;
using MelonLoader;
using HarmonyLib;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Events;
using Il2CppInterop.Runtime;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using Il2CppBrokenArrow.Client.Ecs.GNetwork.Services.Lobby;               // NetworkLobbyService
using Il2CppBrokenArrow.Client.Ecs.UI;                                    // ISceneTransition
using Il2CppBrokenArrow.Client.Ecs.Utils;                                // SceneLoadManager
using Il2CppBrokenArrow.MissionEditor.MissionResolver;                    // ScenarioSource, ScenariosService, ScenarioType
using Il2CppBrokenArrow.MissionEditor.Storage;                           // ScenarioMetaFile, ScenarioPublicOption
using Il2CppBrokenArrow.Shared.Ecs.Services;                             // Session
using Il2CppBrokenArrow.Client.Ecs.Decks;                                // DeckService
using Il2CppBrokenArrow.Client.Ecs.Decks.Models;                         // IDeckDataModel
using Il2CppBrokenArrow.Client.Ecs.Decks_v2;                             // PreloadSharedPlayerDeck
using Il2CppBrokenArrow.Client.Ecs.Campaign;                             // CampaignService
using Il2CppBrokenArrow.Shared.Ecs.Enums;                                // DifficultyLevel
using Il2CppNetworkCommon.Enums;                                          // LobbyType
using Il2CppBrokenArrow.MissionEditor;                                  // MissionLoader
using Il2CppBrokenArrow.Client.Ecs.Configs;                             // GameSessionContext
using Il2CppBrokenArrow.Client.Ecs.Controllers;                         // GameController
using Il2CppBrokenArrow.ScriptEngine.Nodes.Spawn;
using Il2CppBrokenArrow.ScriptEngine.Editor.Properties;
using Il2CppBrokenArrow.Shared.Ecs.MissionEditor;
using Il2CppBrokenArrow.MissionEditor.Inspector;
using Il2CppBrokenArrow.Shared.Ecs;
using Il2CppNetworkCommon.Enums.Common;
using Il2CppBrokenArrow.ScriptEngine.Network;                             // NetworkScenarioStorage
using Il2CppBrokenArrow.BrokenArrow.Client.Ecs.GNetwork.Services;         // EosAntiCheatService
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Network.Lobby;                 // LobbyList
using Il2CppBrokenArrow.Client.Ecs.UI.Menu.Network;                       // QuickSearchButton
using MelonLoader.Utils;                                                 // MelonEnvironment

[assembly: MelonInfo(typeof(BALocalSkirmish.Core), "BA Local Skirmish", "2.7.0", "BovineOverlord")]
[assembly: MelonGame(null, null)]
// Hooks are installed explicitly below so failures can block launching. Without this
// opt-out, MelonLoader installs them again and the second load prefix clears the plan.
[assembly: HarmonyDontPatchAll]

namespace BALocalSkirmish
{
    class AiSlot
    {
        public int PlayerUid;
        public string Name;
        public int DeckIndex = -1; // Same as player
    }

    // One configurable game option (map size, day/night, time limit, starting income, etc.),
    // read from the scenario's own public-option definitions.
    class OptDef
    {
        public int Uid;
        public string Label;
        public bool IsEnum;
        public List<int> EnumVals = new List<int>();
        public List<string> EnumLabels = new List<string>();
        public int Min, Max, Step, Default;
    }

    // v2.2: Skirmish setup panel with map + deck + the scenario's own game options (income, time
    // limit, day/night, map size, ...). Options are injected into SceneLoadManager.ScenarioPublicOptions
    // at load time so the local battle honours them.
    public class Core : MelonMod
    {
        public static Core Instance;
        // Scenario lobbies are the one mode the game's servers leave outside anti-cheat, and the game
        // runs a host/follower model for them. Everything else stays blocked by the patches below.
        public static bool IsOnlineScenarioBattle => Instance != null && Instance._onlineGuardReady
            && NetworkScenarioStorage.IsNetwork && NetworkScenarioStorage.ScenarioMode;
        public static bool IsGuardedLocalBattle => Instance != null && Instance._offlineLobbyGuardReady
            && (Instance._aiLoadPending || Instance._deckOverridesActive) && Instance.MatchesBattleScenario();
        static readonly System.Random _rng = new System.Random();

        // Options the user chose for the pending launch (uid -> value).
        public static readonly Dictionary<int, int> PendingOptions = new Dictionary<int, int>();
        int _applyFrames;
        bool _appliedLogged;

        // scenario/deck/option state
        readonly List<ScenarioSource> _maps = new List<ScenarioSource>();
        readonly List<string> _mapNames = new List<string>();
        int _mapIdx;
        readonly List<IDeckDataModel> _decks = new List<IDeckDataModel>();
        readonly List<string> _deckNames = new List<string>();
        int _deckIdx;
        readonly List<AiSlot> _aiSlots = new List<AiSlot>();
        int _aiSlotIdx;
        readonly Dictionary<int, IDeckDataModel> _battleAiDecks = new Dictionary<int, IDeckDataModel>();
        readonly Dictionary<int, int> _aiWaveCounts = new Dictionary<int, int>();
        ScenarioSource _battleScenario;
        IDeckDataModel _battlePlayerDeck;
        GameSessionContext _deckSession;
        bool _deckOverridesActive;
        bool _aiLoadPending, _aiRestartAllowed, _aiDeckPatchReady;
        readonly List<OptDef> _opts = new List<OptDef>();
        readonly Dictionary<int, int> _optVals = new Dictionary<int, int>();
        // FA difficulty (Osama 27 Nov 2026 19:3x PST, bugs thread: "the current mode is easy. Then it's medium then hard then challenge mode.
        // Challenge mode gives the AI 2.2x the income whereas medium is 1.2 and hard is 1.8"). The scripted Skirmish AI does not spend money:
        // it spawns waves, so its "income" is the size of each wave. Easy = today's AI (x1.0); Medium x1.2, Hard x1.8, Challenge x2.2 more
        // units per wave. The scenario's own (native) difficulty stays at the map's default, so the levels differ only by our multiplier.
        int _diff = 1;          // FA level 1..4 (index into _diffNames)
        int _nativeDiff = 2;    // the map's own DifficultyLevel (scenario scripts read it), unchanged
        bool _hasDiff = true;
        static readonly string[] _diffNames = { "None", "Easy", "Medium", "Hard", "Challenge" };
        static readonly double[] _diffScale = { 1.0, 1.0, 1.2, 1.8, 2.2 };
        internal static double AiWaveScale = 1.0;
        internal static string AiLevel = "Easy";

        // UI
        GameObject _root;
        Text _mapLabel, _deckLabel, _aiPlayerLabel, _aiDeckLabel, _statusLabel, _diffLabel, _previewCaption;
        Image _previewImg;
        readonly List<Text> _optLabels = new List<Text>();
        Font _font;

        // palette
        static readonly Color CDim = new Color(0f, 0f, 0f, 0.6f);
        static readonly Color CFrame = new Color(0.30f, 0.45f, 0.62f, 1f);
        static readonly Color CPanel = new Color(0.10f, 0.12f, 0.16f, 0.99f);
        static readonly Color CHeader = new Color(0.15f, 0.28f, 0.42f, 1f);
        static readonly Color CRow = new Color(1f, 1f, 1f, 0.04f);
        static readonly Color CLabel = new Color(0.62f, 0.78f, 0.98f);
        static readonly Color CVal = new Color(0.95f, 0.96f, 0.98f);
        static readonly Color CBtn = new Color(0.20f, 0.24f, 0.32f, 1f);
        static readonly Color CStart = new Color(0.20f, 0.50f, 0.30f, 1f);
        static readonly Color CCancel = new Color(0.48f, 0.24f, 0.26f, 1f);

        bool _offlineLobbyGuardReady, _onlineGuardReady;

        public override void OnInitializeMelon()
        {
            Instance = this;
            LoggerInstance.Msg("BA Local Skirmish v2.7.0 initializing (manual patch registration only)...");
            _offlineLobbyGuardReady = Patch(typeof(CreateLobbyPatch));
            _onlineGuardReady = _offlineLobbyGuardReady & Patch(typeof(JoinFromListPatch))
                & Patch(typeof(JoinByInvitePatch)) & Patch(typeof(QuickSearchPatch));
            LoggerInstance.Msg($"F8 and Skirmish open local AI setup. Online: private scenario lobbies only, guard ready={_onlineGuardReady}.");
            Patch(typeof(DeckGuardPatch));
            _aiDeckPatchReady = Patch(typeof(AiPlayerDeckPatch))
                & Patch(typeof(DeckAssignmentPatch)) & Patch(typeof(EndBattleDeckPatch))
                & Patch(typeof(AiSpawnPatch));
        }

        // Push the chosen game options into the live SceneLoadManager options dict.
        static bool ApplyOptionsOnce()
        {
            try
            {
                var slm = ISceneLoadManager.Instance;
                if (slm == null) return false;
                var dict = slm.ScenarioPublicOptions;
                if (dict == null) return false;
                foreach (var kv in PendingOptions) { try { dict[kv.Key] = kv.Value; } catch { } }
                return true;
            }
            catch { return false; }
        }

        public override void OnUpdate()
        {
            try { AutoRunTick(); } catch (Exception e) { MelonLogger.Error("[LocalSkirmish] AUTORUN: " + e.Message); _autoDone = true; }
            if (_offlineLobbyGuardReady && Input.GetKeyDown(KeyCode.F8))
            {
                try { OpenSetup(); }
                catch (Exception e) { LoggerInstance.Error("OFFLINE_ONLY: local setup hotkey failed: " + e); }
            }
            if (_applyFrames <= 0) return;
            _applyFrames--;
            if (PendingOptions.Count == 0) { _applyFrames = 0; return; }
            if (ApplyOptionsOnce() && !_appliedLogged)
            {
                _appliedLogged = true;
                MelonLogger.Msg($"[LocalSkirmish] Applied {PendingOptions.Count} game option(s) to the load.");
            }
        }
        bool Patch(Type t)
        {
            try { HarmonyInstance.CreateClassProcessor(t).Patch(); LoggerInstance.Msg("Patched " + t.Name); return true; }
            catch (Exception e) { LoggerInstance.Error("Patch failed for " + t.Name + ": " + e); return false; }
        }

        // ---------- data ----------
        static ScenarioType TypeOf(ScenarioSource s)
        { try { var m = s.MetaFile; if (m != null) return m.Type; } catch { } return ScenarioType.MultiplayerPVP; }
        static string NameOf(ScenarioSource s)
        { try { return s.MetaFile != null ? s.MetaFile.ScenarioName : "?"; } catch { return "?"; } }
        static ScenariosService ScenariosSvc()
        { try { ScenariosService s = null; Session.TryGetService<ScenariosService>(out s, false); return s; } catch { return null; } }
        static DeckService DecksSvc()
        { try { DeckService s = null; Session.TryGetService<DeckService>(out s, false); return s; } catch { return null; } }

        // Make a loc-key readable: "ui_lobby_Income_title" -> "Income"
        static string Clean(string s)
        {
            if (string.IsNullOrEmpty(s)) return s;
            string r = s;
            foreach (var p in new[] { "ui_lobby_", "ui_set_hangar_", "ui_lobby_random_", "ui_", })
                if (r.StartsWith(p, StringComparison.OrdinalIgnoreCase)) { r = r.Substring(p.Length); break; }
            foreach (var suf in new[] { "_title", "_Title", "_desc", "_Description", "_Desc" })
                if (r.EndsWith(suf, StringComparison.OrdinalIgnoreCase)) { r = r.Substring(0, r.Length - suf.Length); break; }
            r = r.Replace('_', ' ').Trim();
            if (r.Length > 0) r = char.ToUpper(r[0]) + r.Substring(1);
            return r.Length == 0 ? s : r;
        }

        void BuildMapList()
        {
            _maps.Clear(); _mapNames.Clear();
            var svc = ScenariosSvc();
            if (svc == null) return;
            var skirmish = new List<ScenarioSource>();
            var pve = new List<ScenarioSource>(); var solo = new List<ScenarioSource>();
            try
            {
                var list = svc._scenarios; int n = list != null ? list.Count : 0;
                for (int i = 0; i < n; i++)
                {
                    ScenarioSource s = null; try { s = list[i]; } catch { continue; }
                    if (s == null) continue;
                    var t = TypeOf(s);
                    // Dedicated skirmish scenarios have their own type and bot slots.
                    // Do not confuse them with MultiplayerPVP (*_network) scenarios.
                    if (t == ScenarioType.Skirmish) skirmish.Add(s);
                    else if (t == ScenarioType.MultiplayerPVE) pve.Add(s);
                    else if (t == ScenarioType.Singleplayer) solo.Add(s);
                }
            }
            catch (Exception e) { MelonLogger.Error("[LocalSkirmish] BuildMapList: " + e.Message); }
            foreach (var s in skirmish) { _maps.Add(s); _mapNames.Add(NameOf(s) + "  (skirmish)"); }
            foreach (var s in pve) { _maps.Add(s); _mapNames.Add(NameOf(s)); }
            foreach (var s in solo) { _maps.Add(s); _mapNames.Add(NameOf(s) + "  (mission)"); }
        }

        void RefreshDecks()
        {
            _decks.Clear(); _deckNames.Clear(); _deckIdx = 0;
            RefreshAiSlots();
            if (_mapIdx < 0 || _mapIdx >= _maps.Count) return;
            var ds = DecksSvc(); if (ds == null) return;
            try
            {
                var arr = ds.GetAvailableDecksForScenario(_maps[_mapIdx], 0);
                int n = arr != null ? arr.Count : 0;
                for (int i = 0; i < n; i++)
                {
                    IDeckDataModel d = null; try { d = arr[i]; } catch { continue; }
                    if (d == null) continue;
                    string nm = "?"; try { nm = d.Name; } catch { }
                    int cards = CountCards(d);
                    _decks.Add(d); _deckNames.Add(nm + $" [{cards} usable cards]");
                    MelonLogger.Msg($"[LocalSkirmish] DECK_DIAGNOSTIC index={i}, cards={cards}.");
                }
            }
            catch (Exception e) { MelonLogger.Error("[LocalSkirmish] RefreshDecks: " + e.Message); }
        }

        static int CountCards(IDeckDataModel deck)
        {
            int total = 0;
            if (deck?.GetSlots == null) return 0;
            foreach (var pair in deck.GetSlots)
                if (pair.Value != null)
                    foreach (var slot in pair.Value)
                        if (slot != null && slot.IsValid && slot.Count > 0) total++;
            return total;
        }

        bool IsSkirmishMap()
        {
            return _mapIdx >= 0 && _mapIdx < _maps.Count
                && TypeOf(_maps[_mapIdx]) == ScenarioType.Skirmish;
        }

        string AiDeckText()
        {
            int idx = _aiSlotIdx >= 0 && _aiSlotIdx < _aiSlots.Count ? _aiSlots[_aiSlotIdx].DeckIndex : -1;
            return idx >= 0 && idx < _deckNames.Count
                ? $"{idx + 1}/{_deckNames.Count}  {_deckNames[idx]}"
                : "Same as player";
        }

        void RefreshAiSlots()
        {
            _aiSlots.Clear(); _aiSlotIdx = 0;
            if (!IsSkirmishMap()) return;
            try
            {
                var teams = _maps[_mapIdx].MetaFile.Teams;
                if (teams == null) return;
                bool skippedHuman = false;
                var seen = new HashSet<int>();
                foreach (var team in teams)
                {
                    if (team == null || team.Slots == null) continue;
                    for (int i = 0; i < team.Slots.Count; i++)
                    {
                        var slot = team.Slots[i];
                        if (slot == null) continue;
                        // The offline loader chooses the first Alpha player as the human.
                        // Built-in skirmish metadata marks even that slot as a bot.
                        if ((int)team.TeamSide == 0 && !skippedHuman)
                        { skippedHuman = true; seen.Add(slot.BotId); continue; }
                        if (!slot.IsBot || slot.BotId < 0 || !seen.Add(slot.BotId)) continue;
                        string name = string.IsNullOrEmpty(slot.PlayerName)
                            ? $"{team.TeamName} player {i + 1}" : slot.PlayerName;
                        _aiSlots.Add(new AiSlot { PlayerUid = slot.BotId, Name = name });
                    }
                }
            }
            catch (Exception e)
            {
                _aiSlots.Clear();
                MelonLogger.Error("[LocalSkirmish] Read AI players: " + e.Message);
            }
        }

        void ClearBattleAiDecks()
        {
            _battleAiDecks.Clear(); _battleScenario = null;
            _battlePlayerDeck = null;
            StopDeckOverrides();
            _aiLoadPending = false; _aiRestartAllowed = false;
        }

        internal void StopDeckOverrides()
        {
            if (_deckOverridesActive)
                MelonLogger.Msg("[LocalSkirmish] Deck and AI spawn overrides detached from the local battle.");
            _deckOverridesActive = false; _deckSession = null;
            _aiWaveCounts.Clear();
        }

        bool MatchesBattleScenario()
        {
            var active = ScenariosService.ActiveScenario;
            return active != null && _battleScenario != null
                && TypeOf(active) == ScenarioType.Skirmish
                && string.Equals(active.Folder, _battleScenario.Folder, StringComparison.OrdinalIgnoreCase)
                && string.Equals(active.Name, _battleScenario.Name, StringComparison.Ordinal);
        }

        void PrepareDecks(ScenarioSource scenario, IDeckDataModel playerDeck)
        {
            ClearBattleAiDecks();
            // Keep the working human preload path. Scripted AI waves need their own
            // override because NodeSpawnMultiUnits deliberately bypasses player decks.
            PreloadSharedPlayerDeck.IsMissionRestart = false;
            PreloadSharedPlayerDeck.ScenarioStartDeck = playerDeck;
            PreloadSharedPlayerDeck.Alpha = playerDeck;
            PreloadSharedPlayerDeck.Bravo = playerDeck;
            if (TypeOf(scenario) != ScenarioType.Skirmish) return;
            foreach (var slot in _aiSlots)
            {
                if (slot.DeckIndex >= _decks.Count)
                    throw new InvalidOperationException("Choose an available deck for " + slot.Name + ".");
                _battleAiDecks.Add(slot.PlayerUid, slot.DeckIndex < 0 ? playerDeck : _decks[slot.DeckIndex]);
            }
            _battleScenario = scenario;
            _battlePlayerDeck = playerDeck;
            _aiLoadPending = true;
        }

        internal void BeginDeckLoad(MissionLoader loader)
        {
            StopDeckOverrides();
            if (_battlePlayerDeck == null) return;
            try
            {
                if (!MatchesBattleScenario() || (!_aiLoadPending && !(_aiRestartAllowed && PreloadSharedPlayerDeck.IsMissionRestart)))
                {
                    MelonLogger.Msg($"[LocalSkirmish] Deck plan discarded: matching scenario={MatchesBattleScenario()}, "
                        + $"pending={_aiLoadPending}, restart={PreloadSharedPlayerDeck.IsMissionRestart}.");
                    ClearBattleAiDecks(); return;
                }

                var session = loader._game.GameSession;
                var human = session.CurrentPlayer;
                if (human == null) throw new InvalidOperationException("Local player is unavailable; deck overrides skipped.");
                _deckSession = session;
                _deckOverridesActive = true;
                _aiLoadPending = false;
                _aiRestartAllowed = true;
                MelonLogger.Msg($"[LocalSkirmish] Individual deck choices bound to the local battle: human UID {human.UID}, {_battleAiDecks.Count} AI choices.");
            }
            catch (Exception e)
            {
                ClearBattleAiDecks();
                MelonLogger.Error("[LocalSkirmish] Bind deck choices: " + e);
            }
        }

        internal void OverrideDeckAssignment(int playerUid, ref IDeckDataModel inputDeck)
        {
            if (!_deckOverridesActive) return;
            try
            {
                if (!MatchesBattleScenario()) { ClearBattleAiDecks(); return; }
                var human = _deckSession.CurrentPlayer;
                if (human == null) { ClearBattleAiDecks(); return; }
                IDeckDataModel chosen;
                if (playerUid == human.UID) chosen = _battlePlayerDeck;
                else
                {
                    var player = _deckSession.GetPlayer(playerUid);
                    if (player == null || !player.IsBot || !_battleAiDecks.TryGetValue(playerUid, out chosen)) return;
                }
                if (chosen == null) return;
                string originalName = inputDeck == null ? "(none)" : inputDeck.Name;
                inputDeck = chosen;
                MelonLogger.Msg($"[LocalSkirmish] Player ID {playerUid}: deck request '{originalName}' -> selected '{chosen.Name}'.");
                // Let SetDeck run normally. Its returned clone is then used by the game's
                // economy/shop updates, including UnitGroupAndNameSystem.ChangePlayerDeck.
            }
            catch (Exception e)
            {
                ClearBattleAiDecks();
                MelonLogger.Error("[LocalSkirmish] Override deck assignment: " + e);
            }
        }

        // Replace the node input BEFORE native OnActivated calculates its completion count.
        // The request retains this new object during async spawning; the node's original
        // shared input is restored by the postfix, without changing any scenario pool.
        internal void OverrideAiSpawn(NodeSpawnMultiUnits node)
        {
            if (!_deckOverridesActive || node == null || node.PlayerOwner == null) return;
            int uid = node.PlayerOwner.DataUID;
            IDeckDataModel deck = null;
            try
            {
                if (!MatchesBattleScenario()) { ClearBattleAiDecks(); return; }
                var human = _deckSession.CurrentPlayer;
                if (human == null) { ClearBattleAiDecks(); return; }
                if (uid == human.UID) return;
                if (!_battleAiDecks.TryGetValue(uid, out deck)) return;
                var player = _deckSession.GetPlayer(uid);
                if (player == null || !player.IsBot) return;
                var original = node.UnitInfo;
                if (original == null || original.Units == null || original.Units.Length == 0) return;

                var slots = new List<DeckSlotModel>();
                if (deck?.GetSlots != null)
                    foreach (var pair in deck.GetSlots)
                        if (pair.Value != null)
                            foreach (var slot in pair.Value)
                                if (slot != null && slot.IsValid && slot.Count > 0) slots.Add(slot);

                DataBaseService database = null;
                Session.TryGetService<DataBaseService>(out database, false);
                var replacements = new List<UnitModData>();
                foreach (var requested in original.Units)
                {
                    // FA difficulty: whole copies plus one more with the fractional chance (x1.8 = 1 copy, 80% a second).
                    int copies = (int)Math.Floor(AiWaveScale) + (_rng.NextDouble() < AiWaveScale - Math.Floor(AiWaveScale) ? 1 : 0);
                    for (int c = 0; c < Math.Max(1, copies); c++) ReplaceSpawnUnit(requested, slots, database, replacements);
                }
                node.UnitInfo = new MultiUnits { Units = new Il2CppReferenceArray<UnitModData>(replacements.ToArray()) };
                // Native empty-input handling completes the node immediately. Clear the
                // previous activation's output so it cannot send old units down the graph.
                if (replacements.Count == 0) node.Units = new UnitObject(0);

                _aiWaveCounts.TryGetValue(uid, out int wave);
                _aiWaveCounts[uid] = ++wave;
                if (wave <= 3 || wave % 50 == 0)
                {
                    var ids = new List<string>();
                    foreach (var unit in replacements)
                    {
                        ids.Add(unit.UnitID.ToString());
                        foreach (var cargo in unit.Cargo.Slots) ids.Add("cargo:" + cargo.UnitID);
                    }
                    MelonLogger.Msg($"[LocalSkirmish] AI spawn UID {uid}, deck '{deck?.Name}', wave {wave}: "
                        + $"{original.TotalUnitsCount} -> {node.UnitInfo.TotalUnitsCount} units [{string.Join(",", ids)}].");
                }
            }
            catch (Exception e)
            {
                // Once this bot's deck is selected, a conversion error must not silently
                // spawn the stock roster. An empty wave follows the native completion path.
                if (deck != null)
                {
                    node.UnitInfo = new MultiUnits { Units = new Il2CppReferenceArray<UnitModData>(0) };
                    node.Units = new UnitObject(0);
                }
                MelonLogger.Error($"[LocalSkirmish] AI spawn UID {uid}: {e}");
            }
        }

        static void ReplaceSpawnUnit(UnitModData requested, List<DeckSlotModel> slots,
            DataBaseService database, List<UnitModData> output)
        {
            if (requested == null) return;
            // A scripted loaded transport represents its passengers' deck cards. Build
            // each passenger with the transport actually selected on that card, instead
            // of retaining a stock vehicle or putting unrelated cargo in it.
            var passengers = requested.Cargo?.Slots;
            if (passengers != null && passengers.Count > 0)
            {
                foreach (var passenger in passengers) ReplaceSpawnUnit(passenger, slots, database, output);
                return;
            }
            var selected = PickSpawnSlot(requested, slots, database);
            if (selected == null) return; // Missing categories never fall back to default units.
            var unit = MakeSpawnUnit(selected.UnitID, selected.Category, selected.UnitSkinId, selected.ModList);
            if (selected.IsValidTransport && selected.TransportCount > 0)
            {
                var transportData = selected.GetTransportUnitData();
                if (transportData != null)
                {
                    var transport = MakeSpawnUnit(selected.TransportID, transportData.CategoryType,
                        selected.TransportSkinId, selected.TransportModList);
                    transport.Cargo.Slots.Add(unit);
                    output.Add(transport);
                    return;
                }
            }
            // Osama 27 Nov 2026 19:3x: "the AI must ALWAYS buy a transport for the Infantry". A deck card without a transport used to spawn
            // its squad on foot (26-27 Nov logs: 55% of AI squads ever rode, against 95% of human squads). Borrow the transport of another
            // card in the same AI deck that has enough seats for this squad; ground transports first. Only when the deck has none at all
            // does the squad still walk.
            var unitData = selected.GetUnitData();
            if (unitData != null && unitData.Type == UnitType.Infantry && TryDeckTransport(unitData, slots, out var carrier))
            {
                var transportData = carrier.GetTransportUnitData();
                var transport = MakeSpawnUnit(carrier.TransportID, transportData.CategoryType, carrier.TransportSkinId, carrier.TransportModList);
                transport.Cargo.Slots.Add(unit);
                output.Add(transport);
                if (++_borrowedLogged <= 20) MelonLogger.Msg($"[LocalSkirmish] AI infantry {selected.UnitID} had no transport; given transport {carrier.TransportID} from the same deck.");
                return;
            }
            // Osama 27 Nov 19:5x: "no walking squads ever". No card in the AI deck can carry this squad: use the faction's standard truck.
            if (unitData != null && unitData.Type == UnitType.Infantry && database != null)
            {
                int need = Math.Max(1, unitData.SquadMembers?.Count ?? 1);
                foreach (var id in FallbackTrucks(unitData.CountryId))
                {
                    var truck = database.GetUnitById(id, false);
                    if (truck == null || truck.InfantrySlots < need) continue;
                    var transport = MakeSpawnUnit(id, truck.CategoryType, 0, null);
                    transport.Cargo.Slots.Add(unit);
                    output.Add(transport);
                    if (++_onFootLogged <= 20) MelonLogger.Msg($"[LocalSkirmish] AI infantry {selected.UnitID}: no transport in this AI deck; given the standard truck {id}.");
                    return;
                }
                if (++_onFootLogged <= 40) MelonLogger.Warning($"[LocalSkirmish] AI infantry {selected.UnitID} spawns on foot: no truck with {need} seats for country {unitData.CountryId}.");
            }
            output.Add(unit);
        }

        static int _borrowedLogged, _onFootLogged;
        // Standard trucks by CountryId (0.9.8 data): Russia KamAZ-6560 (32 seats), USA HEMTT (27), China Shaanxi SX2306 (27), Eurocorp TPz Fuchs (9);
        // the other factions' trucks follow as spares, so a squad never walks.
        static IEnumerable<int> FallbackTrucks(int country)
        {
            if (country == 1) yield return 95;
            else if (country == 2) yield return 242;
            else if (country == 4) yield return 1235;
            else if (country == 5) yield return 1424;
            foreach (var id in new[] { 242, 95, 1235 }) yield return id;
        }
        static bool TryDeckTransport(Il2CppBrokenArrow.DataBase.Models.Units squad, List<DeckSlotModel> slots, out DeckSlotModel carrier)
        {
            carrier = null;
            int need = Math.Max(1, squad.SquadMembers?.Count ?? 1);
            int bestScore = -1, weight = 0;
            foreach (var slot in slots)
            {
                if (!slot.IsValidTransport || slot.TransportCount <= 0) continue;
                var t = slot.GetTransportUnitData();
                if (t == null || t.InfantrySlots < need) continue;
                int score = t.Type == UnitType.Vehicle ? 1 : 0;   // ground first, helicopters only when no ground transport fits
                if (score < bestScore) continue;
                if (score > bestScore) { bestScore = score; weight = 0; }
                weight += slot.TransportCount;
                if (_rng.Next(weight) < slot.TransportCount) carrier = slot;
            }
            return carrier != null;
        }

        static DeckSlotModel PickSpawnSlot(UnitModData requested, List<DeckSlotModel> slots, DataBaseService database)
        {
            var original = database?.GetUnitById(requested.UnitID, false);
            DeckSlotModel selected = null;
            int bestScore = -1, weight = 0;
            foreach (var slot in slots)
            {
                if (slot.Category != requested.Category) continue;
                var data = slot.GetUnitData();
                if (data == null) continue;
                // Prefer the same physical type and role, such as AA versus artillery.
                // Card counts weight variety, but the scenario still controls wave timing.
                int score = original == null ? 0
                    : (data.Type == original.Type ? 4 : 0) + (data.Role == original.Role ? 2 : 0);
                if (score < bestScore) continue;
                if (score > bestScore) { bestScore = score; weight = 0; }
                weight += slot.Count;
                if (_rng.Next(weight) < slot.Count) selected = slot;
            }
            return selected;
        }

        static UnitModData MakeSpawnUnit(int id, UnitCategoryType category, int skin,
            Il2CppSystem.Collections.Generic.List<DeckModData> mods)
        {
            var unit = new UnitModData
            {
                UnitID = id, Category = category, SkinId = skin,
                Items = new Il2CppSystem.Collections.Generic.List<ModDataItem>(),
                Cargo = new CargoData { Slots = new Il2CppSystem.Collections.Generic.List<UnitModData>() }
            };
            if (mods != null)
                foreach (var mod in mods)
                    if (mod != null) unit.Items.Add(new ModDataItem(mod.ModID, mod.OptionID));
            return unit;
        }

        void RefreshOptions()
        {
            _opts.Clear(); _optVals.Clear();
            if (_mapIdx < 0 || _mapIdx >= _maps.Count) return;
            try
            {
                var meta0 = _maps[_mapIdx].MetaFile;
                _hasDiff = meta0 != null && meta0.HasDifficulty;
                int d = 2; try { d = (int)meta0.MEStartDifficulty; } catch { }
                _nativeDiff = (d >= 1 && d <= 3) ? d : 2;
            }
            catch { _hasDiff = true; _nativeDiff = 2; }
            try
            {
                var meta = _maps[_mapIdx].MetaFile;
                var pos = meta != null ? meta.PublicOptions : null;
                int n = pos != null ? pos.Count : 0;
                for (int i = 0; i < n; i++)
                {
                    ScenarioPublicOption po = null; try { po = pos[i]; } catch { continue; }
                    if (po == null) continue;
                    var od = new OptDef();
                    try { od.Uid = po.Uid; } catch { }
                    try { od.Label = Clean(po.Name); } catch { od.Label = "Opt " + od.Uid; }
                    try { od.Default = po.DefaultValue; } catch { }
                    try { od.Min = po.MinValue; od.Max = po.MaxValue; od.Step = po.StepValue > 0 ? po.StepValue : 1; } catch { }
                    try
                    {
                        var dd = po.DropdownValues;
                        if (dd != null && dd.Count > 0)
                        {
                            od.IsEnum = true;
                            foreach (var kv in dd) { od.EnumVals.Add(kv.Key); od.EnumLabels.Add(Clean(kv.Value)); }
                        }
                    }
                    catch { }
                    _opts.Add(od);
                    _optVals[od.Uid] = od.Default;
                }
            }
            catch (Exception e) { MelonLogger.Error("[LocalSkirmish] RefreshOptions: " + e.Message); }
        }

        string OptValueText(OptDef od)
        {
            int v = _optVals.TryGetValue(od.Uid, out var x) ? x : od.Default;
            if (od.IsEnum)
            {
                int idx = od.EnumVals.IndexOf(v);
                if (idx >= 0 && idx < od.EnumLabels.Count) return od.EnumLabels[idx];
                return v.ToString();
            }
            return v.ToString();
        }

        void CycleOpt(OptDef od, int dir)
        {
            int v = _optVals.TryGetValue(od.Uid, out var x) ? x : od.Default;
            if (od.IsEnum && od.EnumVals.Count > 0)
            {
                int idx = od.EnumVals.IndexOf(v); if (idx < 0) idx = 0;
                idx = (idx + dir + od.EnumVals.Count) % od.EnumVals.Count;
                v = od.EnumVals[idx];
            }
            else
            {
                v += dir * (od.Step > 0 ? od.Step : 1);
                if (od.Max > od.Min) { if (v < od.Min) v = od.Min; if (v > od.Max) v = od.Max; }
            }
            _optVals[od.Uid] = v;
            UpdateLabels();
        }

        // ---------- UI ----------
        RectTransform RT(GameObject go) => go.GetComponent<RectTransform>();
        void Place(GameObject go, Transform parent, float x, float y, float w, float h)
        {
            go.transform.SetParent(parent, false);
            var rt = RT(go);
            rt.anchorMin = rt.anchorMax = rt.pivot = new Vector2(0.5f, 0.5f);
            rt.sizeDelta = new Vector2(w, h);
            rt.anchoredPosition = new Vector2(x, y);
        }
        Text MakeLabel(Transform p, float x, float y, float w, float h, string s, int size, TextAnchor a, Color? c = null)
        {
            var go = new GameObject("L"); var t = go.AddComponent<Text>(); Place(go, p, x, y, w, h);
            t.font = _font; t.fontSize = size; t.alignment = a; t.color = c ?? Color.white; t.text = s;
            t.horizontalOverflow = HorizontalWrapMode.Overflow; t.verticalOverflow = VerticalWrapMode.Overflow;
            return t;
        }
        Image MakeImage(Transform p, float x, float y, float w, float h, Color col)
        {
            var go = new GameObject("I"); var img = go.AddComponent<Image>(); Place(go, p, x, y, w, h); img.color = col; return img;
        }
        void MakeButton(Transform p, float x, float y, float w, float h, string label, Action onClick, Color? col = null, int fontSize = 15)
        {
            var go = new GameObject("B"); var img = go.AddComponent<Image>(); Place(go, p, x, y, w, h);
            img.color = col ?? CBtn;
            var btn = go.AddComponent<Button>();
            btn.onClick.AddListener(DelegateSupport.ConvertDelegate<UnityAction>((Action)onClick));
            MakeLabel(go.transform, 0f, 0f, w, h, label, fontSize, TextAnchor.MiddleCenter);
        }

        // Load a scenario's preview.png into a Sprite (best-effort).
        Sprite LoadPreview(ScenarioSource s)
        {
            try
            {
                string path = null;
                try { path = s.PreviewPath; } catch { }
                if (string.IsNullOrEmpty(path) || !File.Exists(path))
                {
                    string folder = null; try { folder = s.Folder; } catch { }
                    if (!string.IsNullOrEmpty(folder)) path = Path.Combine(folder, "preview.png");
                }
                if (string.IsNullOrEmpty(path) || !File.Exists(path)) return null;
                byte[] bytes = File.ReadAllBytes(path);
                var tex = new Texture2D(2, 2);
                ImageConversion.LoadImage(tex, (Il2CppStructArray<byte>)bytes);
                return Sprite.Create(tex, new Rect(0f, 0f, tex.width, tex.height), new Vector2(0.5f, 0.5f));
            }
            catch (Exception e) { MelonLogger.Warning("[LocalSkirmish] preview load: " + e.Message); return null; }
        }

        void SetPreview()
        {
            if (_previewImg == null) return;
            Sprite sp = (_mapIdx >= 0 && _mapIdx < _maps.Count) ? LoadPreview(_maps[_mapIdx]) : null;
            _previewImg.sprite = sp;
            _previewImg.preserveAspect = true;
            _previewImg.color = sp != null ? Color.white : new Color(0.06f, 0.07f, 0.09f, 1f);
        }

        void BuildUI()
        {
            DestroyUI();
            if (_font == null)
            {
                try { _font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf"); } catch { }
                if (_font == null) { try { _font = Font.CreateDynamicFontFromOSFont("Liberation Sans", 16); } catch { } }
                if (_font == null) { try { _font = Font.CreateDynamicFontFromOSFont("Segoe UI", 16); } catch { } }
            }
            _optLabels.Clear();

            _root = new GameObject("BASkirmishSetup");
            UnityEngine.Object.DontDestroyOnLoad(_root);
            var canvas = _root.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay; canvas.sortingOrder = 30000;
            var scaler = _root.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080);
            scaler.matchWidthOrHeight = 0.5f;
            _root.AddComponent<GraphicRaycaster>();
            MakeImage(_root.transform, 0f, 0f, 5000f, 3000f, CDim); // dim backdrop

            const float W = 860f;
            const float rowH = 34f;
            const float headH = 52f;
            int optRows = Math.Min(_opts.Count, 6);
            int rows = 2 + (_aiSlots.Count > 0 ? 2 : 0) + (_hasDiff ? 1 : 0) + optRows;
            float bodyH = rows * rowH;
            float h = headH + 24f + bodyH + 64f + 30f;   // header + pad + rows + buttons + status
            if (h < 380f) h = 380f;                       // room for preview

            // frame + panel
            MakeImage(_root.transform, 0f, 0f, W + 4f, h + 4f, CFrame);
            var panel = MakeImage(_root.transform, 0f, 0f, W, h, CPanel);
            var pt = panel.transform;
            float top = h / 2f;

            // header bar
            MakeImage(pt, 0f, top - headH / 2f, W, headH, CHeader);
            MakeLabel(pt, 0f, top - headH / 2f, W - 40f, 34f, "Local AI Skirmish", 24, TextAnchor.MiddleCenter);

            // layout: controls on the left column, preview on the right
            float colX = -W / 2f + 30f;      // left edge of controls
            float labX = colX + 90f;         // label center
            float ltX = colX + 175f;         // "<" center
            float valX = colX + 210f;        // value left
            float rtX = colX + 470f;         // ">" center
            float y = top - headH - 22f;

            void Row(string name, Color nameCol, string val, Action dec, Action inc, Action<Text> keep)
            {
                MakeImage(pt, colX + 250f, y, 500f, rowH - 4f, CRow);
                MakeLabel(pt, labX, y, 170f, 26f, name, 15, TextAnchor.MiddleLeft, nameCol);
                MakeButton(pt, ltX, y, 30f, 26f, "<", dec);
                var vl = MakeLabel(pt, valX + 117.5f, y, 235f, 26f, val, 15, TextAnchor.MiddleLeft, CVal);
                vl.horizontalOverflow = HorizontalWrapMode.Wrap;
                vl.resizeTextForBestFit = true; vl.resizeTextMinSize = 10; vl.resizeTextMaxSize = 15;
                MakeButton(pt, rtX, y, 30f, 26f, ">", inc);
                keep?.Invoke(vl);
                y -= rowH;
            }

            Row("Map", CLabel, "-", () => CycleMap(-1), () => CycleMap(1), t => _mapLabel = t);
            Row("Player deck", CLabel, "-", () => CycleDeck(-1), () => CycleDeck(1), t => _deckLabel = t);
            if (_aiSlots.Count > 0)
            {
                Row("AI player", CLabel, "-", () => CycleAiPlayer(-1), () => CycleAiPlayer(1), t => _aiPlayerLabel = t);
                Row("AI deck", CLabel, AiDeckText(), () => CycleAiDeck(-1), () => CycleAiDeck(1), t => _aiDeckLabel = t);
            }
            if (_hasDiff)
                Row("Difficulty", new Color(1f, 0.82f, 0.55f), _diffNames[_diff], () => CycleDiff(-1), () => CycleDiff(1), t => _diffLabel = t);
            for (int i = 0; i < optRows; i++)
            {
                var od = _opts[i];
                Row(od.Label, new Color(0.85f, 0.85f, 0.7f), OptValueText(od), () => CycleOpt(od, -1), () => CycleOpt(od, 1), t => _optLabels.Add(t));
            }

            // preview (right side)
            float pvW = 300f, pvH = 170f;
            float pvX = W / 2f - pvW / 2f - 28f;
            float pvY = top - headH - 22f - pvH / 2f + 13f;
            MakeImage(pt, pvX, pvY, pvW + 4f, pvH + 4f, CFrame);
            _previewImg = MakeImage(pt, pvX, pvY, pvW, pvH, new Color(0.06f, 0.07f, 0.09f, 1f));
            _previewCaption = MakeLabel(pt, pvX, pvY - pvH / 2f - 16f, pvW + 20f, 22f, "", 13, TextAnchor.MiddleCenter, new Color(0.8f, 0.85f, 0.95f));

            // buttons
            float by = -top + 74f;
            MakeButton(pt, colX + 110f, by, 200f, 40f, "Start Battle", StartBattle, CStart, 17);
            MakeButton(pt, colX + 330f, by, 150f, 40f, "Random", RandomMap, CBtn, 15);
            MakeButton(pt, W / 2f - 90f, by, 120f, 40f, "Cancel", CloseSetup, CCancel, 15);

            _statusLabel = MakeLabel(pt, 0f, -top + 26f, W - 40f, 24f, "", 12, TextAnchor.MiddleCenter, new Color(0.72f, 0.75f, 0.8f));

            SetPreview();
            UpdateLabels();
        }

        void DestroyUI()
        {
            if (_root != null) { try { UnityEngine.Object.Destroy(_root); } catch { } _root = null; }
            _mapLabel = _deckLabel = _aiPlayerLabel = _aiDeckLabel = _statusLabel = _diffLabel = _previewCaption = null; _previewImg = null; _optLabels.Clear();
        }

        void UpdateLabels()
        {
            if (_mapLabel != null) _mapLabel.text = _maps.Count > 0 ? $"{_mapIdx + 1}/{_maps.Count}  {_mapNames[_mapIdx]}" : "(none)";
            if (_previewCaption != null) _previewCaption.text = _maps.Count > 0 ? _mapNames[_mapIdx] : "";
            if (_deckLabel != null) _deckLabel.text = _decks.Count > 0 ? $"{_deckIdx + 1}/{_decks.Count}  {_deckNames[_deckIdx]}" : "(no valid decks)";
            if (_aiPlayerLabel != null) _aiPlayerLabel.text = _aiSlots.Count > 0
                ? $"{_aiSlotIdx + 1}/{_aiSlots.Count}  {_aiSlots[_aiSlotIdx].Name}" : "(no AI players)";
            if (_aiDeckLabel != null) _aiDeckLabel.text = AiDeckText();
            if (_diffLabel != null) _diffLabel.text = _diffNames[Math.Max(0, Math.Min(4, _diff))];
            for (int i = 0; i < _optLabels.Count && i < _opts.Count; i++)
                if (_optLabels[i] != null) _optLabels[i].text = OptValueText(_opts[i]);
            if (_statusLabel != null)
            {
                string extra = _opts.Count > 0 ? $"{_opts.Count} map option(s)." : "This map has no extra options.";
                int customCount = _aiSlots.FindAll(s => s.DeckIndex >= 0).Count;
                string hint = IsSkirmishMap() ? $"AI decks saved per player ({customCount}/{_aiSlots.Count} custom)." : "Set difficulty & deck, then Start.";
                _statusLabel.text = $"Map {_mapIdx + 1}/{_maps.Count}.  {extra}  {hint}";
            }
        }

        // ---------- unattended test runs ----------
        // UserData/LocalSkirmish-autorun.json (perf / AI test runs on Vengeance, Osama 28 Nov 2026 01:5x "boot the game and run the tests ... build,
        // test, improve, test repeat"): {"map":"Airbase","deck":"name part","diff":3,"minutes":34,"opts":{"Size":"Large"}}. 20 s after the local
        // setup is ready it opens the setup, picks the first map and deck whose names match the given regular expressions (all names are logged), sets the FA difficulty and the named
        // options (label part -> value label part or number), starts the battle and, with "minutes", quits the game that long after the launch.
        // The file is renamed to .used first, so a crash never loops. No file: nothing happens.
        bool _autoDone; float _autoAt = -1f, _autoQuit = -1f;
        void AutoRunTick()
        {
            if (_autoQuit > 0f && Time.realtimeSinceStartup > _autoQuit) { _autoQuit = -1f; MelonLogger.Msg("[LocalSkirmish] AUTORUN time up: quitting the game."); Application.Quit(); return; }
            if (_autoDone || !_offlineLobbyGuardReady) return;
            string f = Path.Combine(MelonLoader.Utils.MelonEnvironment.UserDataDirectory, "LocalSkirmish-autorun.json");
            if (!File.Exists(f)) { _autoDone = true; return; }
            if (_autoAt < 0f) { _autoAt = Time.realtimeSinceStartup + 20f; return; }
            if (Time.realtimeSinceStartup < _autoAt) return;
            _autoDone = true;
            var j = System.Text.Json.Nodes.JsonNode.Parse(File.ReadAllText(f));
            File.Copy(f, f + ".used", true); File.Delete(f);
            string map = (string)j["map"] ?? "", deck = (string)j["deck"] ?? "";
            float min0 = j["minutes"] != null ? (float)j["minutes"] : 0f;
            // {"lobby":"[FA] PvE AI Hard RU Jelgava 0.1","minutes":20}: open that vs AI map as a private online lobby (as the Skirmish button does);
            // the tester starts the match from the lobby.
            if (j["lobby"] is System.Text.Json.Nodes.JsonNode ln)
            {
                var sc = CreateLobbyPatch.FindScenario((string)ln);
                if (sc == null) { MelonLogger.Error($"[LocalSkirmish] AUTORUN: lobby map '{(string)ln}' not installed"); return; }
                if (min0 > 0f) _autoQuit = Time.realtimeSinceStartup + min0 * 60f;
                MelonLogger.Msg($"[LocalSkirmish] AUTORUN lobby '{(string)ln}' (private online, vs AI), quit after {min0} min");
                NetworkLobbyService.CreateLobby(LobbyType.Scenario, sc, true);
                return;
            }
            OpenSetup();
            MelonLogger.Msg("[LocalSkirmish] AUTORUN maps: " + string.Join(" | ", _mapNames));
            var rx = new System.Text.RegularExpressions.Regex(map, System.Text.RegularExpressions.RegexOptions.IgnoreCase);
            int mi = _mapNames.FindIndex(n => rx.IsMatch(n));
            if (mi < 0) { MelonLogger.Error($"[LocalSkirmish] AUTORUN: no map contains '{map}'"); return; }
            _mapIdx = mi; RefreshDecks(); RefreshOptions();
            MelonLogger.Msg("[LocalSkirmish] AUTORUN decks: " + string.Join(" | ", _deckNames));
            var dx = new System.Text.RegularExpressions.Regex(deck, System.Text.RegularExpressions.RegexOptions.IgnoreCase);
            int di = _deckNames.FindIndex(n => dx.IsMatch(n)); if (di >= 0) _deckIdx = di;
            if (j["diff"] != null) _diff = Math.Max(1, Math.Min(4, (int)j["diff"]));
            if (j["opts"] is System.Text.Json.Nodes.JsonObject oj)
                foreach (var kv in oj)
                {
                    var od = _opts.Find(o => o.Label != null && o.Label.IndexOf(kv.Key, StringComparison.OrdinalIgnoreCase) >= 0);
                    if (od == null) { MelonLogger.Warning($"[LocalSkirmish] AUTORUN: no option '{kv.Key}' ({string.Join(", ", _opts.ConvertAll(o => o.Label))})"); continue; }
                    string want = kv.Value?.ToString() ?? "";
                    int li = od.EnumLabels.FindIndex(l => l != null && l.IndexOf(want, StringComparison.OrdinalIgnoreCase) >= 0);
                    if (od.IsEnum && li >= 0) _optVals[od.Uid] = od.EnumVals[li]; else if (int.TryParse(want, out int v)) _optVals[od.Uid] = v;
                    MelonLogger.Msg($"[LocalSkirmish] AUTORUN option {od.Label} = {OptValueText(od)}");
                }
            float min = j["minutes"] != null ? (float)j["minutes"] : 0f;
            if (min > 0f) _autoQuit = Time.realtimeSinceStartup + min * 60f;
            MelonLogger.Msg($"[LocalSkirmish] AUTORUN map '{_mapNames[_mapIdx]}', deck '{(_deckNames.Count > 0 ? _deckNames[_deckIdx] : "none")}', FA level {_diffNames[_diff]}, {_aiSlots.Count} AI, quit after {min} min");
            StartBattle();
        }

        // ---------- actions ----------
        public void OpenSetup()
        {
            if (_root != null) return;
            ClearBattleAiDecks();
            BuildMapList(); _mapIdx = 0; RefreshDecks(); RefreshOptions(); BuildUI();
            MelonLogger.Msg($"[LocalSkirmish] Setup opened ({_maps.Count} maps). Font ready={_font != null}, selected={(_mapNames.Count>0?_mapNames[_mapIdx]:"none")}, decks={_decks.Count}.");
        }
        void CloseSetup() { DestroyUI(); }
        void CycleMap(int dir)
        {
            if (_maps.Count == 0) return;
            _mapIdx = (_mapIdx + dir + _maps.Count) % _maps.Count;
            RefreshDecks(); RefreshOptions(); BuildUI();
        }
        void CycleDeck(int dir)
        { if (_decks.Count == 0) return; _deckIdx = (_deckIdx + dir + _decks.Count) % _decks.Count; UpdateLabels(); }
        void CycleAiDeck(int dir)
        {
            if (!IsSkirmishMap() || _aiSlotIdx < 0 || _aiSlotIdx >= _aiSlots.Count) return;
            // Include the default entry when wrapping in either direction.
            int count = _decks.Count + 1;
            var slot = _aiSlots[_aiSlotIdx];
            slot.DeckIndex = ((slot.DeckIndex + 1 + dir) % count + count) % count - 1;
            UpdateLabels();
        }
        void CycleAiPlayer(int dir)
        {
            if (_aiSlots.Count == 0) return;
            int count = _aiSlots.Count;
            _aiSlotIdx = ((_aiSlotIdx + dir) % count + count) % count;
            UpdateLabels();
        }
        void CycleDiff(int dir)
        { _diff += dir; if (_diff < 1) _diff = 4; if (_diff > 4) _diff = 1; UpdateLabels(); }
        void RandomMap()
        {
            if (_maps.Count == 0) return; _mapIdx = _rng.Next(_maps.Count);
            RefreshDecks(); RefreshOptions(); BuildUI();
        }

        void StartBattle()
        {
            try
            {
                if (!_offlineLobbyGuardReady || !IsSkirmishMap())
                { if (_statusLabel != null) _statusLabel.text = "Local setup is not ready. Check the mod log."; return; }
                if (_mapIdx < 0 || _mapIdx >= _maps.Count) { if (_statusLabel != null) _statusLabel.text = "Pick a map."; return; }
                if (_deckIdx < 0 || _deckIdx >= _decks.Count) { if (_statusLabel != null) _statusLabel.text = "This map has no valid deck for you."; return; }
                var scenario = _maps[_mapIdx];
                var deck = _decks[_deckIdx];
                if (CountCards(deck) == 0)
                { if (_statusLabel != null) _statusLabel.text = "Selected deck has no usable cards. Choose another or create a test deck in Army builder."; return; }
                if (IsSkirmishMap() && !_aiDeckPatchReady)
                {
                    if (_statusLabel != null) _statusLabel.text = "Skirmish deck support could not load. Check the MelonLoader log.";
                    return;
                }
                var st = ISceneTransition.Instance;
                if (st == null) { if (_statusLabel != null) _statusLabel.text = "Scene transition unavailable."; return; }
                PrepareDecks(scenario, deck);

                // FA difficulty: AI wave size multiplier, applied in OverrideAiSpawn
                AiWaveScale = _diffScale[Math.Max(1, Math.Min(4, _diff))]; AiLevel = _diffNames[Math.Max(1, Math.Min(4, _diff))];
                MelonLogger.Msg($"[LocalSkirmish] FA difficulty = {AiLevel}: AI waves x{AiWaveScale:0.0}.");
                // native difficulty (scenario scripts read CampaignService.Difficulty): the map's own default
                if (_hasDiff)
                {
                    try
                    {
                        CampaignService cs = null; Session.TryGetService<CampaignService>(out cs, false);
                        if (cs != null) { cs.Difficulty = (DifficultyLevel)_nativeDiff; MelonLogger.Msg($"[LocalSkirmish] Native difficulty = {(DifficultyLevel)_nativeDiff}."); }
                        else MelonLogger.Warning("[LocalSkirmish] CampaignService not available; difficulty not set.");
                    }
                    catch (Exception e) { MelonLogger.Error("[LocalSkirmish] set difficulty: " + e.Message); }
                }

                // hand our option choices to the applier (runs after ChangeScene sets up the load)
                PendingOptions.Clear();
                foreach (var kv in _optVals) PendingOptions[kv.Key] = kv.Value;

                MelonLogger.Msg($"[LocalSkirmish] Launching '{_mapNames[_mapIdx]}' player deck '{_deckNames[_deckIdx]}', {_battleAiDecks.Count} individual AI deck(s) with {PendingOptions.Count} option(s).");
                DestroyUI();
                st.ChangeScene(scenario);
                _appliedLogged = false;
                _applyFrames = 300;      // keep pushing options in until the battle load consumes them
                ApplyOptionsOnce();      // and try immediately
            }
            catch (Exception e)
            {
                ClearBattleAiDecks();
                if (_statusLabel != null) _statusLabel.text = e.Message;
                MelonLogger.Error("[LocalSkirmish] StartBattle: " + e);
            }
        }
    }

    [HarmonyPatch(typeof(MissionLoader), nameof(MissionLoader.LoadPlayersDeck))]
    static class AiPlayerDeckPatch
    {
        static void Prefix(MissionLoader __instance) { Core.Instance?.BeginDeckLoad(__instance); }
    }

    [HarmonyPatch(typeof(SharedPlayerDeck), nameof(SharedPlayerDeck.SetDeck))]
    static class DeckAssignmentPatch
    {
        static void Prefix(int playerUID, ref IDeckDataModel inputDeck)
        { Core.Instance?.OverrideDeckAssignment(playerUID, ref inputDeck); }
    }

    [HarmonyPatch(typeof(GameController), nameof(GameController.Dispose))]
    static class EndBattleDeckPatch
    {
        static void Prefix() { Core.Instance?.StopDeckOverrides(); }
    }

    [HarmonyPatch(typeof(NodeSpawnMultiUnits), nameof(NodeSpawnMultiUnits.OnActivated))]
    static class AiSpawnPatch
    {
        static void Prefix(NodeSpawnMultiUnits __instance, out MultiUnits __state)
        {
            __state = __instance.UnitInfo;
            Core.Instance?.OverrideAiSpawn(__instance);
        }

        static void Postfix(NodeSpawnMultiUnits __instance, MultiUnits __state)
        { __instance.UnitInfo = __state; }
    }

    static class OnlineRules
    {
        // Same rule as the game's servers report: a lobby type on this list needs anti-cheat.
        public static bool ScenarioAllowed()
        {
            try
            {
                var types = EosAntiCheatService.ProtectedLobbyTypes;
                if (types == null) return false;
                int count = types.Cast<Il2CppSystem.Collections.Generic.IReadOnlyCollection<LobbyType>>().Count;
                for (int i = 0; i < count; i++)
                    if (types[i] == LobbyType.Scenario) return false;
                return true;
            }
            catch (Exception e) { MelonLogger.Error("[LocalSkirmish] protected lobby types unreadable: " + e.Message); return false; }
        }
        public static bool Refuse(string what)
        {
            MelonLogger.Warning("[LocalSkirmish] ONLINE_RULE: blocked " + what + ". Modded play uses private scenario lobbies.");
            return false;
        }
        public static bool ScenarioOnly(LobbyType type, string what)
        {
            if (type != LobbyType.Scenario) return Refuse(what + " of type " + type);
            return ScenarioAllowed() || Refuse(what + ": the game's servers require anti-cheat for scenario lobbies");
        }
    }

    [HarmonyPatch(typeof(NetworkLobbyService), nameof(NetworkLobbyService.CreateLobby))]
    static class CreateLobbyPatch
    {
        const string VsAiDefault = "[FA] PvE AI Easy CN Dead Center 0.1";
        internal static ScenarioSource FindScenario(string name)
        {
            ScenariosService svc = null;
            try { Session.TryGetService<ScenariosService>(out svc, false); } catch { }
            var list = svc?._scenarios; int n = list != null ? list.Count : 0;
            for (int i = 0; i < n; i++)
            {
                ScenarioSource s = null; try { s = list[i]; } catch { continue; }
                string nm = null; try { nm = s?.MetaFile?.ScenarioName; } catch { }
                if (nm != null && nm.Trim() == name) return s;
            }
            return null;
        }
        [HarmonyPriority(Priority.First)]
        static bool Prefix(LobbyType lobbyType, ScenarioSource initScenario, bool isPrivateLobby)
        {
            try
            {
                if (lobbyType == LobbyType.Skirmish)
                {
                    // Osama 27 Nov 2026 20:0x: "the skirmish button should put you in an online lobby but all player slots locked except
                    // for 1". Skirmish now opens a private online Scenario lobby on a vs AI map (one human slot, one AI bot; pve.py VSAI),
                    // where the host can pick another vs AI map or difficulty. Shift-click, no scenario lobbies (anti-cheat rule) or a
                    // missing map open the local setup as before.
                    bool local = Input.GetKey(KeyCode.LeftShift) || Input.GetKey(KeyCode.RightShift);
                    if (!local && OnlineRules.ScenarioAllowed())
                    {
                        var s = FindScenario(VsAiDefault);
                        if (s != null)
                        {
                            MelonLogger.Msg($"[LocalSkirmish] Skirmish clicked -> private online lobby on '{VsAiDefault}' (vs AI). Shift-click for the local setup.");
                            NetworkLobbyService.CreateLobby(LobbyType.Scenario, s, true);
                            return false;
                        }
                        MelonLogger.Warning($"[LocalSkirmish] vs AI map '{VsAiDefault}' not installed; local setup instead.");
                    }
                    MelonLogger.Msg("[LocalSkirmish] Skirmish clicked -> local setup; native Skirmish lobby blocked.");
                    Core.Instance?.OpenSetup();
                    return false;
                }
                if (!OnlineRules.ScenarioOnly(lobbyType, "lobby")) return false;
                MelonLogger.Msg($"[LocalSkirmish] ONLINE_RULE: scenario lobby allowed, private={isPrivateLobby}.");
                return true;
            }
            catch (Exception e) { MelonLogger.Error("[LocalSkirmish] lobby rule failed; lobby blocked. " + e); return false; }
        }
    }

    [HarmonyPatch(typeof(LobbyList), "JoinLobby")]
    static class JoinFromListPatch
    {
        [HarmonyPriority(Priority.First)]
        static bool Prefix(LobbyList __instance, int lobbyId)
        {
            try
            {
                var selected = __instance._selectedItemModel?.ModelLobbyInfo;
                if (selected != null && selected.LobbyId == lobbyId)
                    return OnlineRules.ScenarioOnly((LobbyType)selected.LobbyType, "listed lobby");
                var items = __instance._itemModels;
                for (int i = 0; items != null && i < items.Count; i++)
                {
                    var info = items[i]?.ModelLobbyInfo;
                    if (info != null && info.LobbyId == lobbyId)
                        return OnlineRules.ScenarioOnly((LobbyType)info.LobbyType, "listed lobby");
                }
                return OnlineRules.Refuse("listed lobby of unknown type");
            }
            catch (Exception e) { MelonLogger.Error("[LocalSkirmish] join rule failed; join blocked. " + e); return false; }
        }
    }

    [HarmonyPatch(typeof(NetworkLobbyService), "JoinLobbyByInviteInternal")]
    static class JoinByInvitePatch
    {
        [HarmonyPriority(Priority.First)]
        static bool Prefix(LobbyInviteMessage lobbyInviteMessage)
        {
            try
            {
                return lobbyInviteMessage != null
                    ? OnlineRules.ScenarioOnly(lobbyInviteMessage.LobbyType, "invite")
                    : OnlineRules.Refuse("empty invite");
            }
            catch (Exception e) { MelonLogger.Error("[LocalSkirmish] invite rule failed; join blocked. " + e); return false; }
        }
    }

    [HarmonyPatch(typeof(QuickSearchButton), "OnClick")]
    static class QuickSearchPatch
    {
        [HarmonyPriority(Priority.First)]
        static bool Prefix(QuickSearchButton __instance)
        {
            try
            {
                // The same button cancels a search that is already running.
                var search = __instance._networkQuickSearchService;
                if (search != null && search.IsQuickSearchActive) return true;
            }
            catch (Exception e) { MelonLogger.Error("[LocalSkirmish] quick search check failed. " + e); }
            return OnlineRules.Refuse("quick search");
        }
    }

    // Saved decks can hold options this mod deleted or moved to a new card. Drop those options
    // before the game builds the slot. Selections that remain on the unit keep working.
    [HarmonyPatch(typeof(DeckService), "PostLoad")]
    static class DeckGuardPatch
    {
        static Dictionary<int, int> _moved;
        static Dictionary<int, int> Moved()
        {
            if (_moved != null) return _moved;
            _moved = new Dictionary<int, int>();
            string path = Path.Combine(MelonEnvironment.UserDataDirectory, "FreedomArrow", "deck-migration.json");
            foreach (var pair in System.Text.Json.JsonSerializer.Deserialize<Dictionary<string, int>>(File.ReadAllText(path)))
                _moved[int.Parse(pair.Key)] = pair.Value;
            return _moved;
        }
        static Dictionary<string, int> _renumbered;
        static Dictionary<string, int> Renumbered()
        {
            if (_renumbered != null) return _renumbered;
            string path = Path.Combine(MelonEnvironment.UserDataDirectory, "FreedomArrow", "option-id-migration.json");
            _renumbered = System.Text.Json.JsonSerializer.Deserialize<Dictionary<string, int>>(File.ReadAllText(path));
            return _renumbered;
        }
        static void Clean(DataBaseService db, Il2CppSystem.Collections.Generic.List<DeckModData> mods, int unit, string deck)
        {
            var f21Slots = new HashSet<int>();
            for (int i = (mods?.Count ?? 0) - 1; i >= 0; i--)
            {
                int option = mods[i]?.OptionID ?? 0;
                if (option == 0) continue;
                if (Renumbered().TryGetValue(option.ToString(), out int replacement))
                {
                    var migrated = db.GetOptionById(replacement);
                    if (migrated == null) throw new InvalidOperationException("Missing migrated option " + replacement);
                    mods[i].OptionID = replacement;
                    MelonLogger.Msg($"[DeckGuard] deck '{deck}': option {option} migrated to {replacement} on unit {unit}.");
                    option = replacement;
                }
                bool moved = Moved().TryGetValue(option, out int parent) && parent == unit;
                var resolved = db.GetOptionById(option);
                if (!moved && resolved != null && (unit != 981 || f21Slots.Add(resolved.ModificationId))) continue;
                MelonLogger.Msg($"[DeckGuard] deck '{deck}': option {option} removed from unit {unit}.");
                mods.RemoveAt(i);
            }
        }
        static void Prefix(DeckService __instance, DeckDataModel deckModel)
        {
            try
            {
                var db = __instance?._dbService;
                var slots = deckModel?._slots;
                if (db == null || slots == null || !db.IsLoaded) return;
                foreach (UnitCategoryType category in Enum.GetValues(typeof(UnitCategoryType)))
                {
                    if (!slots.TryGetValue(category, out var row) || row == null) continue;
                    for (int i = 0; i < row.Length; i++)
                    {
                        var slot = row[i];
                        if (slot == null || slot.UnitID == 0) continue;
                        Clean(db, slot.ModList, slot.UnitID, deckModel.Name);
                        if (slot.TransportID != 0) Clean(db, slot.TransportModList, slot.TransportID, deckModel.Name);
                    }
                }
            }
            catch (Exception e) { MelonLogger.Error("[DeckGuard] deck check failed: " + e); }
        }
    }
}

using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using HarmonyLib;
using Il2CppBrokenArrow.Shared.Ecs;
using MelonLoader;
using MelonLoader.Utils;
using UnityEngine;

[assembly: MelonInfo(typeof(FreedomArrow.Runtime), "Freedom Arrow", "0.9.6-dev.20", "Freedom Arrow development")]
[assembly: MelonGame(null, null)]
[assembly: HarmonyDontPatchAll]
namespace FreedomArrow;

public class Runtime : MelonMod
{
    static readonly byte[] Key = Encoding.ASCII.GetBytes("09234237536700238099172758697347");
    static readonly byte[] Marker = Encoding.ASCII.GetBytes("fhk3s0g3");
    static string Root => Path.Combine(MelonEnvironment.GameRootDirectory, "UserData", "FreedomArrow");
    static bool applied, failed;
    public static bool IsApplied => applied && !failed;
    static int count;
    static string PackageVersion="unknown";
    public static string DisplayLabel { get; private set; } = "Freedom Arrow (not verified)";
    internal static string DiagnosticPackageVersion=>PackageVersion;
    static readonly DateTime DiagnosticSessionStart=DateTime.UtcNow;
    static readonly Dictionary<string, string> Files = new()
    {
        ["Units"]="units.json", ["AbilitiesJson"]="abilities.json", ["UnitAbilitiesJson"]="unit_abilities.json",
        ["AmmunitionsJson"]="ammunitions.json", ["ArmorsJson"]="armors.json", ["MobilityJson"]="mobility.json",
        ["FlyPresetsJson"]="fly_presets.json", ["UnitPropulsionsJson"]="unit_propulsions.json", ["CountriesJson"]="countries.json",
        ["TurretsJson"]="turrets.json", ["TurretUnitsJson"]="turret_units.json", ["WeaponsJson"]="weapons.json",
        ["TurretWeaponsJson"]="turret_weapons.json", ["WeaponAmmunitionsJson"]="weapon_ammunitions.json",
        ["SensorUnitsJson"]="sensor_units.json", ["SensorsJson"]="sensors.json", ["SquadMembersJson"]="squad_members.json",
        ["SquadWeaponsJson"]="squad_weapons.json", ["ModificationsJson"]="modifications.json", ["OptionsJson"]="options.json",
        ["UnitArmorsJson"]="unit_armors.json", ["SpecializationAvailabilitiesJson"]="specialization_availabilities.json",
        ["SpecializationsJson"]="specializations.json", ["TransportAvailabilitiesJson"]="transport_availabilities.json"
    };
    static string Sha(byte[] bytes) => Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
    // Batch (Lateralus, 8 November 2026): the conquest mode (formerly FreedomArrow.ConquestBatch.dll) is compiled into this
    // DLL. It starts first, as it did when MelonLoader loaded its DLL before this one, and fails on its own.
    static Conquest.Prototype conquest;
    const string RetiredConquestDll="FreedomArrow.ConquestBatch";
    void StartConquest()
    {
        if(AppDomain.CurrentDomain.GetAssemblies().Any(a=>a.GetName().Name==RetiredConquestDll))
        {
            LoggerInstance.Error($"FREEDOM_ARROW_CONQUEST_FAILED: old Mods/{RetiredConquestDll}.dll is loaded; the built-in conquest stays off. Delete that file and restart.");
            return;
        }
        try { File.Delete(Path.Combine(MelonEnvironment.GameRootDirectory,"Mods",RetiredConquestDll+".dll")); } catch { }
        conquest=new Conquest.Prototype(Info);
        try { conquest.OnInitializeMelon(); }
        catch (Exception e) { LoggerInstance.Error("FREEDOM_ARROW_CONQUEST_FAILED: "+e); }
    }
    public override void OnUpdate() { conquest?.OnUpdate(); MirrorSkin.Tick(); ChinaVoice.Tick(); LogUpload.Tick(); MenuArt.Tick(); DeckReorder.Tick(); MultiplayerToModLobbies.Tick(); MemoryCleanup.Tick(); RankedMenu.Tick(); WebsiteButton.Tick(); PartySizeWarning.Tick(); NationLayout.Tick(); }
    public override void OnLateUpdate()
    {
        DiagnosticLog.Heartbeat();
        HookHealth.LateUpdate();
        InterceptLead.LateUpdate();
        SeadOverkill.LateUpdate();
        LobbySlotDefaults.LateUpdate();
        AaCooldown.LateUpdate();
        SpaagWeapons.LateUpdate();
        SameUnitClaim.LateUpdate();
        Dazzler.LateUpdate();
        PlaneSale.LateUpdate();
        ServerMoney.LateUpdate();
        GroundAaLog.LateUpdate();
        GroundAaLog.Flush();
        SupplyStealth.LateUpdate();
        PlayableBorders.Update();
        HideTextureTest.LateUpdate();
    }
    public override void OnGUI() { conquest?.OnGUI(); RankedMenu.OnGUI(); PartySizeWarning.OnGUI(); }
    public override void OnSceneWasLoaded(int buildIndex,string sceneName)
    {
        DiagnosticLog.Write("scene_loaded",new{buildIndex,sceneName});
        try { LogUpload.SceneLoaded(sceneName); } catch (Exception e) { MelonLogger.Warning("FREEDOM_ARROW_LOG_UPLOAD scene: "+e.Message); }
        GroundAaLog.SceneChanged();
        InterceptLead.SceneChanged();
        SeadOverkill.SceneChanged();
        SeadRetarget.SceneChanged();
        AltitudeIntent.SceneChanged();
        AaCooldown.SceneChanged();
        SpaagWeapons.SceneChanged();
        SameUnitClaim.SceneChanged();
        Dazzler.SceneChanged();
        PlaneSale.SceneChanged();
        ServerMoney.SceneChanged();
        PlayableBorders.SceneChanged();
        MenuArt.SceneChanged();
        MemoryCleanup.SceneChanged(sceneName);
        PartySizeWarning.SceneChanged(sceneName);
        conquest?.OnSceneWasLoaded(buildIndex,sceneName);
    }
    public override void OnDeinitializeMelon()
    {
        NuclearLaunchWarning.Shutdown();
        try { conquest?.OnDeinitializeMelon(); }
        finally
        {
            try { InterceptLead.Close(); } catch(Exception e) { MelonLogger.Warning("FREEDOM_ARROW_INTERCEPT_LEAD_CLOSE_FAILED: "+e.Message); }
            AaCooldown.SceneChanged();
            GroundAaLog.Close();DiagnosticLog.Close("deinitialize");
            PlayableBorders.Clear();
            try
            {
                var bundle=TestLogBundle.Create(MelonEnvironment.GameRootDirectory,DiagnosticSessionStart,PackageVersion);
                MelonLogger.Msg("FREEDOM_ARROW_TEST_LOG_BUNDLE "+bundle);
            }
            catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_TEST_LOG_BUNDLE_FAILED: "+e.Message);}
            // Osama 21 Nov 2026: the game hung for minutes after quit on Linux; end the process if it is still alive 10 s after this.
            try { ExitWatchdog.Start(); } catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_EXIT_WATCHDOG_FAILED: "+e.Message);}
        }
    }
    public override void OnInitializeMelon()
    {
        ThirdPartyCfg.Redirect();   // ActualArrow mods' settings in UserData/FreedomArrow/ThirdParty (Lateralus 22 Nov 2026)
        StartConquest();
        Directory.CreateDirectory(Root);
        try { PackageVersion=JsonNode.Parse(File.ReadAllText(Path.Combine(Root,"channel.json")))["package_version"].GetValue<string>(); } catch { }
        DiagnosticLog.Start(Root,PackageVersion);
        try { LogUpload.Start(PackageVersion); } catch (Exception e) { MelonLogger.Warning("FREEDOM_ARROW_LOG_UPLOAD off: "+e.Message); }
        try { UpdateNotice.Start(PackageVersion); } catch (Exception e) { MelonLogger.Warning("FREEDOM_ARROW_UPDATE_NOTICE off: "+e.Message); }
        // 0.9.0-dev.3: before the payload check, so even a refused package never loads or rewrites vanilla decks.
        try { DeckFolder.Install(HarmonyInstance); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_DECK_FOLDER_FAILED: decks use the vanilla folder. "+e.Message); }
        File.Delete(Path.Combine(Root,"runtime-receipt.json"));
        File.Delete(Path.Combine(Root,"runtime-failure.txt"));
        try
        {
            var manifest=JsonNode.Parse(File.ReadAllText(Path.Combine(Root,"payload-manifest.json"))).AsObject();
            int files=PayloadVerifier.Verify(MelonEnvironment.GameRootDirectory,manifest["sha256"].AsObject());
            var identity=JsonNode.Parse(File.ReadAllText(Path.Combine(Root,"pla-package-manifest.json"))).AsObject();
            string label=BuildIdentity.ResolveLabel(Info.Version,PackageVersion,identity["build"].GetValue<int>(),identity["label"].GetValue<string>());
            // Check the actual infantry files before claiming that this build is loaded.
            var infantryHashes=new JsonObject();
            foreach(var entry in identity["sha256"].AsObject())
                if(entry.Key=="Mods/FAModels.dll" || entry.Key=="UserData/FAModels/infantry-bodies.json" || entry.Key.StartsWith("UserData/FAModels/pla2_",StringComparison.Ordinal))
                    infantryHashes[entry.Key]=JsonValue.Create(entry.Value.GetValue<string>());
            // 0.8.0-dev.101: 25 body types + 2 Type 21 backpack bodies (x3 meshes, diffuse + normal) + 2 backpack gear atlases (x3 LODs, diffuse + normal), loader and rules.
            // 0.9.0-dev.13: FAModels 0.3.30 adds battle copies (X_b.fat, X_b_n.fat) of the 29 infantry texture pairs. They are verified
            // with the rest but not counted, so the count still checks the armory set.
            int battleCopies=infantryHashes.Count(e=>e.Key.EndsWith("_b.fat",StringComparison.Ordinal)||e.Key.EndsWith("_b_n.fat",StringComparison.Ordinal));
            // 0.9.5-dev.30 (Osama 22 Nov 2026: "Pla recon snipers use this model"): the recon frog-shirt body adds 9 files (3 LODs, diffuse +
            // normal) and 2 battle copies. Packages with the older Assets keep 257 + 0 or 58.
            int armorySet=infantryHashes.Count-battleCopies;
            if(!(armorySet==257&&(battleCopies==0||battleCopies==58)) && !(armorySet==266&&(battleCopies==0||battleCopies==60)))
                throw new InvalidDataException($"Expected 257 infantry files with 0 or 58 battle copies, or 266 with 0 or 60 (with the recon frog-shirt body); found {armorySet} with {battleCopies}");
            int infantryFiles=PayloadVerifier.Verify(MelonEnvironment.GameRootDirectory,infantryHashes);
            DisplayLabel=label;
            File.WriteAllText(Path.Combine(Root,"loaded-build.json"),JsonSerializer.Serialize(new { label,version=PackageVersion,process_id=Environment.ProcessId,loaded_at_utc=DateTime.UtcNow,core_files=files,infantry_files=infantryFiles },new JsonSerializerOptions { WriteIndented=true }));
            LoggerInstance.Msg($"PLA_BUILD_LOADED: {label}; core={files}; infantry={infantryFiles}; process={Environment.ProcessId}");
            InstallScenarios();
            LoggerInstance.Msg($"FREEDOM_ARROW_PAYLOAD_VERIFIED: {files} files");
            DiagnosticLog.Write("payload_verified",new{files,version=PackageVersion});
        }
        catch(Exception e)
        {
            DiagnosticLog.Write("payload_failed",new{error=e.ToString()});
            DisplayLabel="Freedom Arrow (verification failed)";failed=true;File.WriteAllText(Path.Combine(Root,"runtime-failure.txt"),e.ToString());
            LoggerInstance.Error("FREEDOM_ARROW_FAILED: payload refused before database hook: "+e.Message);return;
        }
        // Scenarios can route to another database. This line shows which one a battle uses.
        try { HarmonyInstance.Patch(AccessTools.Method(typeof(DataBaseService), "LoadCompiled"),prefix: new HarmonyMethod(typeof(Runtime), nameof(LogDatabase))); }
        catch(Exception e) { LoggerInstance.Error("FREEDOM_ARROW_DB_SOURCE_FAILED: "+e.Message); }
        HarmonyInstance.Patch(AccessTools.Method(typeof(DataBaseCompiled), "LoadSource"),
            prefix: new HarmonyMethod(typeof(Runtime), nameof(Apply)) { priority=HarmonyLib.Priority.First });
        LoggerInstance.Msg($"Freedom Arrow {PackageVersion} package initialized. Main database constants hook installed.");
        try {PlayableBorders.Install(HarmonyInstance);}
        catch(Exception e){LoggerInstance.Error("FREEDOM_ARROW_PLAYABLE_BORDERS_INSTALL_FAILED: "+e.Message);}
        try { DetectionConfig.Install(HarmonyInstance,Root); }
        catch(Exception e) { LoggerInstance.Error("FREEDOM_ARROW_DETECTION_FAILED: config hook not installed. "+e.Message); }
        try { CoverDamage.Install(HarmonyInstance,Root); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_COVER_DAMAGE_FAILED: not installed. "+e.Message); }
        try { SpottingCap.Install(HarmonyInstance,Root); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_SPOTTING_CAP_FAILED: not installed. "+e.Message); }
        try { HeliRange.Install(HarmonyInstance,Root); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_HELI_RANGE_FAILED: not installed. "+e.Message); }
        try { HeliRangeCard.Install(HarmonyInstance); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_HELI_CARD_FAILED: not installed. "+e.Message); }
        try { CardStatFit.Install(HarmonyInstance); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_CARD_STAT_FIT_FAILED: not installed; vanilla wrapping. "+e.Message); }
        try { PlaneReturnCurve.Install(HarmonyInstance,Root); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_PLANE_RETURN_FAILED: not installed; vanilla plane return times. "+e.Message); }
        try { PlaneResupplyCostRow.Install(HarmonyInstance); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_PLANE_RESUPPLY_COST_FAILED: not installed; the line stays visible. "+e.Message); }
        try { ModLobbyNoGroup.Install(HarmonyInstance); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_MOD_LOBBY_NO_GROUP_FAILED: not installed; the Mod Lobbies page keeps group and search. "+e.Message); }
        try { SmokeGroundFire.Install(HarmonyInstance); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_SMOKE_GROUND_FAILED: not installed; Fire at position still shoots through smoke. "+e.Message); }
        try { MissileHitChance.Install(HarmonyInstance); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_MISSILE_CHANCE_FAILED: not installed; vanilla missile hit chance. "+e.Message); }
        try { NlosTrait.Install(HarmonyInstance,Root); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_NLOS_FAILED: not installed; NLOS missiles use vanilla seekers. "+e.Message); }
        try { ProjectileHealth.Install(HarmonyInstance,Root); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_PROJECTILE_HEALTH_FAILED: not installed; projectiles keep 1 HP. "+e.Message); }
        try { SameUnitClaim.Install(HarmonyInstance,Root); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_SAME_UNIT_CLAIM_FAILED: not installed; native targeting. "+e.Message); }
        try { TurretDiag.Install(HarmonyInstance,Root); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_TURRET_DIAG_FAILED: "+e.Message); }
        try { LoadingScreens.Install(HarmonyInstance,Root); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_LOADING_SCREENS_FAILED: not installed; vanilla loading screens. "+e.Message); }
        try { MusicVolumeOnLaunch.Install(HarmonyInstance); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_MUSIC_ON_LAUNCH_FAILED: not installed; the Music slider keeps the player's value. "+e.Message); }
        try { DeckReorder.Install(HarmonyInstance); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_DECK_REORDER_FAILED: not installed; deck units keep their order. "+e.Message); }
        try { MenuArt.Install(Root); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_MENU_ART_FAILED: not installed; vanilla start screen. "+e.Message); }
        try { MirrorSkin.Install(HarmonyInstance,Root); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_MIRROR_SKIN_FAILED: not installed; mirror finishes show the normal skin. "+e.Message); }
        try { Dazzler.Install(HarmonyInstance,Root); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_DAZZLER_FAILED: not installed; ZTZ-99A APS is a vanilla point-blank APS. "+e.Message); }
        try { PlaneSale.Install(HarmonyInstance,Root); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_PLANE_SALE_FAILED: not installed; native refunds. "+e.Message); }
        try { ServerMoney.Install(HarmonyInstance); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_SERVER_MONEY_FAILED: not installed; no server points log. "+e.Message); }
        try { SeadOverkill.Install(HarmonyInstance,Root); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_SEAD_OVERKILL_FAILED: not installed; vanilla SEAD overkill (0.99). "+e.Message); }
        try { SeadRetarget.Install(HarmonyInstance); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_SEAD_RETARGET_FAILED: not installed; SEAD missiles keep flying to a dead radar. "+e.Message); }
        try { AltitudeIntent.Install(HarmonyInstance); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_ALTITUDE_INTENT_FAILED: not installed; the game's own altitude icon. "+e.Message); }
        try { LobbySlotDefaults.Install(HarmonyInstance); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_LOBBY_SLOTS_FAILED: not installed; new lobbies open every slot. "+e.Message); }
        try { SpaagWeapons.Install(HarmonyInstance,Root); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_SPAAG_WEAPONS_FAILED: not installed; vanilla card DPS and bursts. "+e.Message); }
        try { ChinaVoice.Install(HarmonyInstance,Root); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_CHINA_VOICE_FAILED: not installed; China units use their preset voices. "+e.Message); }
        try { GroundAaLog.Install(Root); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_AA_LOG_FAILED: not installed; gameplay unchanged. "+e.Message); }
        try { InterceptLead.Install(); }
        catch (Exception e)
        {
            DiagnosticLog.Write("intercept_lead_install_failed",new{error=e.ToString(),fallback="native leading"});
            MelonLogger.Error("FREEDOM_ARROW_INTERCEPT_LEAD_FAILED: not installed; native leading. "+e);
        }
        try { AaCooldown.Install(HarmonyInstance,Root); }
        catch(Exception e)
        {
            DiagnosticLog.Write("aa_cooldown_install_failed",new{error=e.ToString(),fallback="native overkill"});
            MelonLogger.Error("FREEDOM_ARROW_AA_COOLDOWN_FAILED: not installed; native overkill. "+e);
        }
        try { SupplyStealth.Install(); }
        catch (Exception e)
        {
            DiagnosticLog.Write("supply_bind_failed",new{error=e.ToString()});
            MelonLogger.Error("FREEDOM_ARROW_SUPPLY_STEALTH_FAILED: not installed; caches keep stealth 1.0. "+e);
        }
        try { CardIcons.Install(HarmonyInstance); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_CARD_ICONS_FAILED: not installed; vanilla card icons. "+e.Message); }
        try { ChinaUi.Install(HarmonyInstance); }
        catch (Exception e) { MelonLogger.Error("PLA_CHINA_UI_FAILED: "+e.Message); }
        try { NationLayout.Install(HarmonyInstance); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_NATION_LAYOUT_FAILED: native layout kept. "+e.Message); }
        try { SupportSlots.Install(HarmonyInstance); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_SUPPORT_SLOTS_FAILED: SUP tab keeps 7 slots. "+e.Message); }
        try { ThirdPartyGuard.Ensure(); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_THIRD_PARTY_FAILED: "+e.Message); }
        try { NuclearLaunchWarning.Install(HarmonyInstance); }
        catch (Exception e) { MelonLogger.Error("PLA_NUCLEAR_WARNING_FAILED: "+e.Message); }
        try { AlertSounds.Install(HarmonyInstance,Root); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_ALERT_SOUNDS_FAILED: old alarms stay. "+e.Message); }
        HideTextureTest.Install(Root);
    }
    public override void OnLateInitializeMelon()
    {
        ThirdPartyCfg.Redirect();   // the rest of the ActualArrow categories, before FA changes any of their values
        try { NuclearLaunchWarning.Install(HarmonyInstance); }
        catch (Exception e) { MelonLogger.Error("PLA_NUCLEAR_WARNING_FAILED: "+e.Message); }
        try { AlertSounds.Install(HarmonyInstance,Root); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_ALERT_SOUNDS_FAILED: old alarms stay. "+e.Message); }
        try { conquest?.OnLateInitializeMelon(); }
        catch (Exception e) { LoggerInstance.Error("FREEDOM_ARROW_CONQUEST_FAILED: late "+e.Message); }
        try { MatchLog.Install(HarmonyInstance,Root,LogUpload.Session); }
        catch (Exception e) { MelonLogger.Warning("FREEDOM_ARROW_MATCH_LOG failed: "+e.Message); }
        try { OverkillHooks.Install(HarmonyInstance); }   // after AaCooldown, SameUnitClaim and SeadOverkill registered (0.9.0-dev.37)
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_OVERKILL_HOOK_FAILED: native overkill for all three. "+e); }
        try { PerfProbe.Install(HarmonyInstance,Root); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_PERF_FAILED: "+e.Message); }
        try { ThirdPartyGuard.Ensure(); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_THIRD_PARTY_FAILED: "+e.Message); }
        try { ThirdPartyGuard.PointArrowQueue(); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_MATCHMAKING_FAILED: "+e.Message); }
        try { ThirdPartyGuard.NameArrowQueue(HarmonyInstance,PackageVersion); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_MATCHMAKING_FAILED: names "+e.Message); }
        try { MultiplayerToModLobbies.Install(HarmonyInstance); }   // 0.9.4 (Osama 21 Nov 2026): Multiplayer opens Mod Lobbies
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_PLAY_MENU_FAILED: "+e.Message); }
        try { ArsenalOnlySpecs.Install(HarmonyInstance); }   // 0.9.4 (Osama 21 Nov 2026): Blue Dragon in the Arsenal only, not in deck creation
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_ARSENAL_ONLY_SPECS_FAILED: not installed; Blue Dragon can be picked in deck creation. "+e.Message); }
        try { WebsiteButton.Install(HarmonyInstance); }   // Osama 22 Nov 2026: Home tab banner that opens freedomarrow.app
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_WEBSITE_BUTTON_FAILED: no website button. "+e.Message); }
        try { RankedMenu.Install(HarmonyInstance); }   // Lateralus 22 Nov 2026: Ranked card, ranked menu and leaderboard
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_RANKED_FAILED: no ranked menu. "+e.Message); }
        try { PartySizeWarning.Install(HarmonyInstance); }   // Osama 22 Nov 2026: warning over Ready when a team is larger than the [NvN] map (0.9.5)
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_PARTY_SIZE_FAILED: not installed; no oversized-party warning. "+e.Message); }
        try { LangNames.Install(HarmonyInstance,Root); }   // Osama 23 Nov 2026: bilingual names show English OR Chinese, by game language
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_LANG_NAMES_FAILED: not installed; bilingual names show both languages. "+e.Message); }
    }
    public override void OnApplicationQuit()
    {
        DiagnosticLog.Write("application_quit",new{});
        LogUpload.Quit();
        try { ThirdPartyGuard.RestoreArrowQueue(); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_MATCHMAKING_FAILED: restore "+e.Message); }
    }
    // Previous packaged names. Remove leftover copies so the lobby does not list both.
    internal static readonly string[] RetiredScenarioFolders={"[FA] Central Village","[FA] Central Village Skirmish","[FA] Dead Center 0.1"};
    // Maps we no longer ship, by folder and the exact GUID we published. Lateralus (12 November 2026) still saw the old
    // vanilla-built Airport, Baltiisk and Dam in the mod lobby list after the [5v5]/[3v3] redesigns replaced them; their
    // GUIDs match no packaged map, so the rename cleanup above never removed them. A different GUID (someone else's map) stays.
    internal static readonly (string Folder,string Guid)[] RetiredScenarios={
        ("[FA] Airport 0.1","6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c01a"),("[FA] Airport Skirmish 0.1","6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c01b"),
        ("[FA] Baltiisk 0.1","6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c02a"),("[FA] Baltiisk Skirmish 0.1","6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c02b"),
        ("[FA] Dam 0.1","6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c03a"),("[FA] Dam Skirmish 0.1","6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c03b"),
        // Lateralus 14 Nov 2026: the 0.2 versions replace these (GUID = uuid5(URL namespace, name), as common.py makes them).
        ("[FA] [5v5] Oil Rush 0.1","45ab8340-2c7f-54ca-9ec4-aa8f625472c0"),("[FA] [5v5] Oil Rush Skirmish 0.1","2bace80d-9e50-557a-a2c1-a864e8aacaf1"),
        ("[FA] [5v5] Airport 0.1","7d8ec986-71aa-5f4c-832c-9997babdbf2f"),("[FA] [5v5] Airport Skirmish 0.1","986a0190-74a4-5182-81ec-26dae52deb73"),
        ("[FA] [5v5] Cold Harbor 0.1","931bc088-091f-59a7-9764-08b11e6f3bfa"),("[FA] [5v5] Cold Harbor Skirmish 0.1","56545179-c383-5ea9-b6e6-36ca3a16cb02"),
        // Lateralus 16 Nov 2026: "Remove Central Village 1v1 and Chernyakhovsky from our mod, they are not suitable designs" (shipped 0.9.0-dev.11 to dev.25).
        // Chernyakhovsky came back the same day as Lateralus's new design under the same name and GUID, so it is not retired.
        ("[FA] [1v1] Central Village 0.1","8007113c-143e-5b93-a5c5-d1515ce0e8e6"),("[FA] [1v1] Central Village Skirmish 0.1","fd87c5c8-5b82-5567-88da-613af880c648"),
        // Lateralus 16 Nov 2026: the 0.2 versions (his zone and spawn edits) replace these.
        ("[FA] [2v2] Highway of Death 0.1","35645673-5d88-500b-8ddf-6ad4900f79d6"),("[FA] [2v2] Highway of Death Skirmish 0.1","fa8367be-1748-5e68-8b34-eb3caea31251"),
        ("[FA] [3v3] Baltiisk 0.1","4822100d-5d11-57f9-8d2f-63dfc816e735"),("[FA] [3v3] Baltiisk Skirmish 0.1","f203ec91-e074-5557-a946-ab4eb6fc7bb6"),
        ("[FA] [3v3] Dam 0.1","0286f6b4-b70d-5a15-9bf0-39c4df27fd0e"),("[FA] [3v3] Dam Skirmish 0.1","eff1170e-8014-5993-b0e3-66adee16e306"),
        ("[FA] [2v2] Chkalovsk Airbase 0.1","6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c007"),("[FA] [2v2] Chkalovsk Airbase Skirmish 0.1","6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c008"),
        ("[FA] [2v2] Dead Center 0.1","6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c003"),("[FA] [2v2] Dead Center Skirmish 0.1","6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c004"),
        ("[FA] [1v1] Dead Center 0.1","6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c005"),("[FA] [1v1] Dead Center Skirmish 0.1","6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c006"),
        // Osama 19 Nov 2026: PvE maps renamed (player count first) and given AI bot slots; the 0.2 names replace these.
        ("[FA] [PvE] Dead Center vs China (1P) 0.1","b001c57c-c600-5d77-981e-8e6543a08721"),("[FA] [PvE] Dead Center vs China (1P) Skirmish 0.1","d06dc805-8e31-5d46-908b-5bee0258b1db"),("[FA] [PvE] Highway of Death vs China (2P) 0.1","da056b8c-dffc-5c53-9500-0e9de20ee17f"),("[FA] [PvE] Highway of Death vs China (2P) Skirmish 0.1","6b2691fa-d73c-5b8f-8393-5736cd401b54"),("[FA] [PvE] Dam vs China (3P) 0.1","22f35646-50ca-5140-8e33-3954ab147582"),("[FA] [PvE] Dam vs China (3P) Skirmish 0.1","c40aedda-5a93-54cc-9223-827508f2d853"),
        // Lateralus 23 Nov 2026 (0.9.6): the three [5v5] maps are now [4v4] (same layout and zone values, new name and GUID).
        ("[FA] [5v5] Airport 0.2","b28f9451-d7cc-56a4-b536-7cbc89a2fd38"),("[FA] [5v5] Airport Skirmish 0.2","99dd9bc5-dff6-5356-b7e3-8f83a979133d"),
        ("[FA] [5v5] Oil Rush 0.2","7c9c5eb7-37b7-56ce-b33f-c5390ea6e9e0"),("[FA] [5v5] Oil Rush Skirmish 0.2","c9e53f60-a3da-5359-ad6a-058247cac84b"),
        ("[FA] [5v5] Cold Harbor 0.2","1fef0897-64e8-5238-bc01-66687b1598c1"),("[FA] [5v5] Cold Harbor Skirmish 0.2","8ae843b6-d6e9-5271-a308-c4cd1098089c"),
        // Lateralus 23 Nov 2026 (0.9.6): new zone values; the 0.3 versions replace these.
        ("[FA] [2v2] Highway of Death 0.2","32e238bc-e2df-5aed-93ca-a74b406e292d"),("[FA] [2v2] Highway of Death Skirmish 0.2","f22e8f35-e2bc-5b70-b6f3-893705babf14"),
        ("[FA] [1v1] Dead Center 0.2","a8726371-f049-5a03-8bfa-5ad4867936ad"),("[FA] [1v1] Dead Center Skirmish 0.2","fc9a8f06-f10e-5f7c-a829-c0a962eff198"),
    };
    static void RemoveRetiredScenarios()
    {
        foreach(var (folder,guid) in RetiredScenarios)
            foreach(string root in new[]{Path.Combine(MelonEnvironment.GameRootDirectory,"Scenarios"),Path.Combine(MelonEnvironment.GameRootDirectory,"Mods","Scenarios")})
            {
                string leftover=Path.Combine(root,folder),meta=Path.Combine(leftover,"meta.json");
                if(!File.Exists(meta)||JsonNode.Parse(File.ReadAllText(meta))?["guid"]?.GetValue<string>()!=guid)continue;
                Directory.Delete(leftover,true);
                MelonLogger.Msg("FREEDOM_ARROW_SCENARIO: removed retired "+folder);
            }
    }
    // The mod manager only installs Mods and UserData. Copy packaged scenarios to the game's scenario folder.
    static void InstallScenarios()
    {
        string source=Path.Combine(Root,"scenarios");
        if(!Directory.Exists(source))return;
        try
        {
            foreach(string folder in Directory.GetDirectories(source))
            {
                // Online lobbies leave out the game's local Scenarios folder. They list Mods/Scenarios as manually downloaded.
                string target=Path.Combine(MelonEnvironment.GameRootDirectory,"Mods","Scenarios",Path.GetFileName(folder));
                string old=Path.Combine(MelonEnvironment.GameRootDirectory,"Scenarios",Path.GetFileName(folder));
                // Remove only our own old copy. A map author's copy under the same name has another GUID and stays.
                if(Directory.Exists(old)&&SameGuid(old,folder))Directory.Delete(old,true);
                Directory.CreateDirectory(target);
                foreach(string file in Directory.GetFiles(folder))
                {
                    string copy=Path.Combine(target,Path.GetFileName(file));
                    if(!File.Exists(copy)||Sha(File.ReadAllBytes(copy))!=Sha(File.ReadAllBytes(file)))File.Copy(file,copy,true);
                }
                foreach(string retired in RetiredScenarioFolders)
                {
                    if(retired==Path.GetFileName(folder))continue;
                    foreach(string root in new[]{Path.Combine(MelonEnvironment.GameRootDirectory,"Scenarios"),Path.Combine(MelonEnvironment.GameRootDirectory,"Mods","Scenarios")})
                    {
                        string leftover=Path.Combine(root,retired);
                        if(Directory.Exists(leftover)&&SameGuid(leftover,folder))Directory.Delete(leftover,true);
                    }
                }
                MelonLogger.Msg("FREEDOM_ARROW_SCENARIO: installed "+Path.GetFileName(folder));
            }
        }
        catch(Exception e){MelonLogger.Error("FREEDOM_ARROW_SCENARIO_FAILED: "+e.Message);}
        try{RemoveRetiredScenarios();}
        catch(Exception e){MelonLogger.Error("FREEDOM_ARROW_SCENARIO_RETIRE_FAILED: "+e.Message);}
    }
    static bool SameGuid(string a,string b)
    {
        string Read(string folder)
        {
            string meta=Path.Combine(folder,"meta.json");
            return File.Exists(meta)?JsonNode.Parse(File.ReadAllText(meta))?["guid"]?.GetValue<string>():null;
        }
        string guid=Read(a);
        return guid!=null&&guid==Read(b);
    }
    static byte[] Decrypt(string input)
    {
        var bytes=Convert.FromBase64String(input);
        if (bytes.Length < 40 || !bytes.Take(8).SequenceEqual(Marker)) throw new InvalidDataException("Unexpected table marker");
        using var aes=Aes.Create(); aes.Key=Key; aes.IV=bytes.Skip(8).Take(16).ToArray();
        return aes.CreateDecryptor().TransformFinalBlock(bytes,24,bytes.Length-24);
    }
    static string Encrypt(byte[] input)
    {
        using var aes=Aes.Create(); aes.Key=Key; aes.GenerateIV();
        var bytes=aes.CreateEncryptor().TransformFinalBlock(input,0,input.Length);
        return Convert.ToBase64String(Marker.Concat(aes.IV).Concat(bytes).ToArray());
    }
    static JsonNode Clone(JsonNode node) => node==null ? null : JsonNode.Parse(node.ToJsonString());
    static JsonValueKind Kind(JsonNode node) => JsonTypes.Kind(node);
    static void LogDatabase(DataBaseCompiled dataBase,string sourceId)
    {
        try { MelonLogger.Msg($"FREEDOM_ARROW_DB_SOURCE {dataBase?.name} main={dataBase?.MainBuildDatabase} source={sourceId} patched={applied}"); }
        catch(Exception e) { MelonLogger.Error("FREEDOM_ARROW_DB_SOURCE_FAILED: "+e.Message); }
    }
    static void Apply(DataBaseCompiled __instance)
    {
        if (applied || failed) return;
        var original=new Dictionary<PropertyInfo,string>();
        try
        {
            var main=typeof(DataBaseCompiled).GetProperty("MainBuildDatabase") ?? throw new InvalidDataException("Missing main database flag");
            if (!(main.GetValue(__instance) is bool yes) || !yes) return;
            var compatibility=JsonNode.Parse(File.ReadAllText(Path.Combine(Root,"compatibility.json"))).AsObject();
            string assembly=Path.Combine(MelonEnvironment.GameRootDirectory,"GameAssembly.dll");
            if (!File.Exists(assembly)) assembly=Path.Combine(MelonEnvironment.GameRootDirectory,"BrokenArrow_Data","GameAssembly.dll");
            if (Sha(File.ReadAllBytes(assembly)) != compatibility["game_assembly_sha256"].GetValue<string>())
                throw new InvalidDataException("GameAssembly build mismatch");
            var schema=JsonNode.Parse(File.ReadAllText(Path.Combine(Root,"reference-schema.json"))).AsObject();
            var prospective=new Dictionary<string,JsonArray>();
            var patchedTables=new Dictionary<string,JsonObject>();
            var ready=new Dictionary<PropertyInfo,string>();
            var receipt=new List<object>();
            foreach (var table in Files)
            {
                string path=Path.Combine(Root,"constants",table.Value);
                if (!File.Exists(path)) continue;
                var overrides=JsonNode.Parse(File.ReadAllText(path)).AsObject();
                if (overrides.Count==0) continue;
                var property=typeof(DataBaseCompiled).GetProperty(table.Key) ?? throw new InvalidDataException("Missing table "+table.Key);
                string cipher=(string)property.GetValue(__instance);
                byte[] plain=Decrypt(cipher);
                if (Sha(plain) != compatibility["source_plaintext_sha256"][table.Key].GetValue<string>())
                    throw new InvalidDataException("Source table mismatch: "+table.Key);
                var rows=RowPlanner.Apply(JsonNode.Parse(Encoding.UTF8.GetString(plain)).AsArray(),overrides,
                    compatibility["allow_new_rows"]?.GetValue<bool>()==true,
                    (id,field,before,after,added)=>receipt.Add(new {table=table.Key,id,field,before,after,action=added?"add_row":"edit"}));
                if(table.Key=="SpecializationsJson")TestSpec.Apply(rows,Root);   // Osama 23 Nov 2026: hidden test spec toggle
                prospective[table.Key]=rows;
                patchedTables[table.Key]=overrides;
                original[property]=cipher;
                ready[property]=Encrypt(Encoding.UTF8.GetBytes(rows.ToJsonString(new JsonSerializerOptions { WriteIndented=false })));
            }
            foreach (var table in patchedTables)
            {
                if (!schema.TryGetPropertyValue(table.Key,out var linksNode)) continue;
                foreach (var patch in table.Value)
                foreach (var link in linksNode.AsObject())
                {
                    var fields=patch.Value?.AsObject();
                    if (fields==null || !fields.ContainsKey(link.Key)) continue;
                    if (!int.TryParse(fields[link.Key]?.ToJsonString(),out int value) || value<0)
                        throw new InvalidDataException("Invalid Int32 reference "+table.Key+"."+link.Key);
                    var rule=link.Value.AsArray();string target=rule[0].GetValue<string>();
                    if (value==0 && rule[1].GetValue<bool>()) continue;
                    if (!prospective.TryGetValue(target,out var targetRows))
                    {
                        string targetCipher=(string)typeof(DataBaseCompiled).GetProperty(target).GetValue(__instance);
                        byte[] bytes=Decrypt(targetCipher);
                        if (Sha(bytes)!=compatibility["source_plaintext_sha256"][target].GetValue<string>())
                            throw new InvalidDataException("Reference target table mismatch: "+target);
                        prospective[target]=targetRows=JsonNode.Parse(Encoding.UTF8.GetString(bytes)).AsArray();
                    }
                    if (value==0 || !targetRows.Any(r=>r["Id"].GetValue<int>()==value))
                        throw new InvalidDataException("Dangling reference "+table.Key+"."+link.Key+" -> "+target+" "+value);
                }
            }
            if (ready.Count==0) throw new InvalidDataException("No nonempty gameplay constants were packaged");
            if(patchedTables.ContainsKey("TurretWeaponsJson")||patchedTables.ContainsKey("SquadWeaponsJson"))
            {
                foreach(string table in WeaponCoverage.Tables)
                {
                    if(prospective.ContainsKey(table))continue;
                    byte[] bytes=Decrypt((string)typeof(DataBaseCompiled).GetProperty(table).GetValue(__instance));
                    if(Sha(bytes)!=compatibility["source_plaintext_sha256"][table].GetValue<string>())throw new InvalidDataException("Weapon dependency table mismatch: "+table);
                    prospective[table]=JsonNode.Parse(Encoding.UTF8.GetString(bytes)).AsArray();
                }
                WeaponCoverage.Validate(prospective,patchedTables);
            }
            // Commit only after every table, field, type and build precondition validates.
            foreach (var pair in ready) pair.Key.SetValue(__instance,pair.Value);
            count=receipt.Count;applied=true;
            File.WriteAllText(Path.Combine(Root,"runtime-receipt.json"),JsonSerializer.Serialize(new { package="freedomarrow.gameplay",version=PackageVersion,tables=ready.Count,fields=count,changes=receipt },new JsonSerializerOptions { WriteIndented=true }));
            MelonLogger.Msg($"FREEDOM_ARROW_APPLIED: {ready.Count} tables, {count} fields; receipt saved. This is a data-load result, not a behavior test.");
        }
        catch (Exception e)
        {
            foreach (var pair in original) try { pair.Key.SetValue(__instance,pair.Value); } catch { }
            failed=true;
            File.WriteAllText(Path.Combine(Root,"runtime-failure.txt"),e.ToString());
            MelonLogger.Error("FREEDOM_ARROW_FAILED: constants not applied; original fields restored. "+e.Message);
        }
    }
    // Player UI is owned by the native match HUD; diagnostics stay in logs.

}

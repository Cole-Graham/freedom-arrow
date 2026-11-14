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

[assembly: MelonInfo(typeof(FreedomArrow.Runtime), "Freedom Arrow", "0.8.0-dev.73", "Freedom Arrow development")]
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
    public override void OnUpdate() => conquest?.OnUpdate();
    public override void OnLateUpdate()
    {
        DiagnosticLog.Heartbeat();
        CramPrediction.LateUpdate();
        AaCooldown.LateUpdate();
        GroundAaLog.LateUpdate();
        GroundAaLog.Flush();
        SupplyStealth.LateUpdate();
        PlayableBorders.Update();
    }
    public override void OnGUI() => conquest?.OnGUI();
    public override void OnSceneWasLoaded(int buildIndex,string sceneName)
    {
        DiagnosticLog.Write("scene_loaded",new{buildIndex,sceneName});
        GroundAaLog.SceneChanged();
        CramPrediction.SceneChanged();
        AaCooldown.SceneChanged();
        PlayableBorders.SceneChanged();
        conquest?.OnSceneWasLoaded(buildIndex,sceneName);
    }
    public override void OnDeinitializeMelon()
    {
        NuclearLaunchWarning.Shutdown();
        try { conquest?.OnDeinitializeMelon(); }
        finally
        {
            try { CramPrediction.Close(); } catch(Exception e) { MelonLogger.Warning("FREEDOM_ARROW_CRAM_PREDICTION_CLOSE_FAILED: "+e.Message); }
            AaCooldown.SceneChanged();
            GroundAaLog.Close();DiagnosticLog.Close("deinitialize");
            PlayableBorders.Clear();
            try
            {
                var bundle=TestLogBundle.Create(MelonEnvironment.GameRootDirectory,DiagnosticSessionStart,PackageVersion);
                MelonLogger.Msg("FREEDOM_ARROW_TEST_LOG_BUNDLE "+bundle);
            }
            catch(Exception e){MelonLogger.Warning("FREEDOM_ARROW_TEST_LOG_BUNDLE_FAILED: "+e.Message);}
        }
    }
    public override void OnInitializeMelon()
    {
        StartConquest();
        Directory.CreateDirectory(Root);
        try { PackageVersion=JsonNode.Parse(File.ReadAllText(Path.Combine(Root,"channel.json")))["package_version"].GetValue<string>(); } catch { }
        DiagnosticLog.Start(Root,PackageVersion);
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
            if(infantryHashes.Count!=227)throw new InvalidDataException("Expected 25 infantry configurations with 3 meshes with diffuse and normal textures each, plus loader and rules");
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
        try { MissileHitChance.Install(HarmonyInstance); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_MISSILE_CHANCE_FAILED: not installed; vanilla missile hit chance. "+e.Message); }
        try { NlosTrait.Install(HarmonyInstance,Root); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_NLOS_FAILED: not installed; NLOS missiles use vanilla seekers. "+e.Message); }
        try { GroundAaLog.Install(Root); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_AA_LOG_FAILED: not installed; gameplay unchanged. "+e.Message); }
        try { CramPrediction.Install(); }
        catch (Exception e)
        {
            DiagnosticLog.Write("cram_prediction_install_failed",new{error=e.ToString(),fallback="native leading"});
            MelonLogger.Error("FREEDOM_ARROW_CRAM_PREDICTION_FAILED: not installed; native leading. "+e);
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
        try { SupportSlots.Install(HarmonyInstance); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_SUPPORT_SLOTS_FAILED: SUP tab keeps 7 slots. "+e.Message); }
        try { ThirdPartyGuard.Ensure(); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_THIRD_PARTY_FAILED: "+e.Message); }
        try { NuclearLaunchWarning.Install(HarmonyInstance); }
        catch (Exception e) { MelonLogger.Error("PLA_NUCLEAR_WARNING_FAILED: "+e.Message); }
    }
    public override void OnLateInitializeMelon()
    {
        try { NuclearLaunchWarning.Install(HarmonyInstance); }
        catch (Exception e) { MelonLogger.Error("PLA_NUCLEAR_WARNING_FAILED: "+e.Message); }
        try { conquest?.OnLateInitializeMelon(); }
        catch (Exception e) { LoggerInstance.Error("FREEDOM_ARROW_CONQUEST_FAILED: late "+e.Message); }
        try { ThirdPartyGuard.Ensure(); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_THIRD_PARTY_FAILED: "+e.Message); }
        try { ThirdPartyGuard.PointArrowQueue(); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_MATCHMAKING_FAILED: "+e.Message); }
        try { ThirdPartyGuard.NameArrowQueue(HarmonyInstance,PackageVersion); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_MATCHMAKING_FAILED: names "+e.Message); }
    }
    public override void OnApplicationQuit()
    {
        DiagnosticLog.Write("application_quit",new{});
        try { ThirdPartyGuard.RestoreArrowQueue(); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_MATCHMAKING_FAILED: restore "+e.Message); }
    }
    // Previous packaged names. Remove leftover copies so the lobby does not list both.
    static readonly string[] RetiredScenarioFolders={"[FA] Central Village","[FA] Central Village Skirmish","[FA] Dead Center 0.1"};
    // Maps we no longer ship, by folder and the exact GUID we published. Lateralus (12 November 2026) still saw the old
    // vanilla-built Airport, Baltiisk and Dam in the mod lobby list after the [5v5]/[3v3] redesigns replaced them; their
    // GUIDs match no packaged map, so the rename cleanup above never removed them. A different GUID (someone else's map) stays.
    static readonly (string Folder,string Guid)[] RetiredScenarios={
        ("[FA] Airport 0.1","6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c01a"),("[FA] Airport Skirmish 0.1","6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c01b"),
        ("[FA] Baltiisk 0.1","6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c02a"),("[FA] Baltiisk Skirmish 0.1","6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c02b"),
        ("[FA] Dam 0.1","6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c03a"),("[FA] Dam Skirmish 0.1","6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c03b")};
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

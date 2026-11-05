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

[assembly: MelonInfo(typeof(FreedomArrow.Runtime), "Freedom Arrow", "0.3.0-dev.17", "Freedom Arrow development")]
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
    public override void OnInitializeMelon()
    {
        Directory.CreateDirectory(Root);
        try { PackageVersion=JsonNode.Parse(File.ReadAllText(Path.Combine(Root,"channel.json")))["package_version"].GetValue<string>(); } catch { }
        File.Delete(Path.Combine(Root,"runtime-receipt.json"));
        File.Delete(Path.Combine(Root,"runtime-failure.txt"));
        try
        {
            var manifest=JsonNode.Parse(File.ReadAllText(Path.Combine(Root,"payload-manifest.json"))).AsObject();
            int files=PayloadVerifier.Verify(MelonEnvironment.GameRootDirectory,manifest["sha256"].AsObject());
            InstallScenarios();
            LoggerInstance.Msg($"FREEDOM_ARROW_PAYLOAD_VERIFIED: {files} files");
        }
        catch(Exception e)
        {
            failed=true;File.WriteAllText(Path.Combine(Root,"runtime-failure.txt"),e.ToString());
            LoggerInstance.Error("FREEDOM_ARROW_FAILED: payload refused before database hook: "+e.Message);return;
        }
        HarmonyInstance.Patch(AccessTools.Method(typeof(DataBaseCompiled), "LoadSource"),
            prefix: new HarmonyMethod(typeof(Runtime), nameof(Apply)) { priority=HarmonyLib.Priority.First });
        LoggerInstance.Msg($"Freedom Arrow {PackageVersion} package initialized. Main database constants hook installed.");
        try { DetectionConfig.Install(HarmonyInstance,Root); }
        catch(Exception e) { LoggerInstance.Error("FREEDOM_ARROW_DETECTION_FAILED: config hook not installed. "+e.Message); }
        try { CoverDamage.Install(HarmonyInstance,Root); }
        catch (Exception e) { MelonLogger.Error("FREEDOM_ARROW_COVER_DAMAGE_FAILED: not installed. "+e.Message); }
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
                string target=Path.Combine(MelonEnvironment.GameRootDirectory,"Scenarios",Path.GetFileName(folder));
                Directory.CreateDirectory(target);
                foreach(string file in Directory.GetFiles(folder))
                {
                    string copy=Path.Combine(target,Path.GetFileName(file));
                    if(!File.Exists(copy)||Sha(File.ReadAllBytes(copy))!=Sha(File.ReadAllBytes(file)))File.Copy(file,copy,true);
                }
                MelonLogger.Msg("FREEDOM_ARROW_SCENARIO: installed "+Path.GetFileName(folder));
            }
        }
        catch(Exception e){MelonLogger.Error("FREEDOM_ARROW_SCENARIO_FAILED: "+e.Message);}
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

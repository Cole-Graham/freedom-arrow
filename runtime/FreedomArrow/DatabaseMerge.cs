using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Nodes;
using HarmonyLib;
using MelonLoader;

namespace FreedomArrow;

public static class DatabaseMerge
{
    static readonly JsonSerializerOptions WriteOpts = new()
    {
        Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
    };

    static MelonLogger.Instance _log = null!;
    static string _root = "";
    static bool _loggedBuild;
    static readonly HashSet<IntPtr> _done = new();

    public static void Install(string root, MelonLogger.Instance log)
    {
        _root = root;
        _log = log;
        var harmony = new HarmonyLib.Harmony("freedomarrow.gameplay");
        var compiled = FindType("Il2CppBrokenArrow.Shared.Ecs.DataBaseCompiled", "BrokenArrow.Shared.Ecs.DataBaseCompiled");
        var service = FindType("Il2CppBrokenArrow.Shared.Ecs.DataBaseService", "BrokenArrow.Shared.Ecs.DataBaseService");
        if (compiled == null || service == null)
        {
            log.Error("DataBaseCompiled or DataBaseService was not found. Constants will not be applied.");
            return;
        }
        Patch(harmony, AccessTools.Method(compiled, "LoadSource"), instanceIsDatabase: true);
        Patch(harmony, AccessTools.Method(service, "LoadCompiled"), instanceIsDatabase: false);
    }

    static void Patch(HarmonyLib.Harmony harmony, MethodInfo? method, bool instanceIsDatabase)
    {
        if (method == null)
        {
            _log.Error("a database load method is missing. Constants will not be applied.");
            return;
        }
        var prefix = instanceIsDatabase
            ? AccessTools.Method(typeof(DatabaseMerge), nameof(PrefixInstance))
            : BindCompiled(method);
        harmony.Patch(method, prefix: new HarmonyMethod(prefix));
        _log.Msg("HOOK OK " + method.DeclaringType?.Name + "." + method.Name);
    }

    static MethodInfo BindCompiled(MethodInfo target)
    {
        var parameter = target.GetParameters().FirstOrDefault();
        var name = string.IsNullOrEmpty(parameter?.Name) ? "__0" : parameter!.Name;
        if (name == "dataBase")
            return AccessTools.Method(typeof(DatabaseMerge), nameof(PrefixCompiled));
        return HookBinder.Prefix(name, parameter!.ParameterType, nameof(PrefixCompiledBody));
    }

    public static void PrefixInstance(object __instance) => Apply(__instance);

    public static void PrefixCompiled(object dataBase) => Apply(dataBase);

    public static void PrefixCompiledBody(object database) => Apply(database);

    static void Apply(object? database)
    {
        if (database == null)
            return;
        try
        {
            if (!IsMainLevel(database))
                return;
            var pointer = PointerOf(database);
            if (pointer != IntPtr.Zero && _done.Contains(pointer))
                return;
            var pending = Prepare(database);
            foreach (var (property, json) in pending)
                SetString(database, property, json);
            if (pointer != IntPtr.Zero)
                _done.Add(pointer);
        }
        catch (Exception ex)
        {
            _log.Error("constant merge failed: " + ex.Message);
        }
    }

    static List<(string Property, string Json)> Prepare(object database)
    {
        var directory = Path.Combine(_root, "constants");
        var files = Directory.Exists(directory)
            ? Directory.GetFiles(directory, "*.json").OrderBy(path => path, StringComparer.Ordinal).ToArray()
            : Array.Empty<string>();
        LogBuild(files);
        var overrides = ReadOverrides(files);
        var source = Tables.All.ToDictionary(item => item.Property, item => GetString(database, item.Property));
        var pending = PrepareTables(source, overrides, out var counts);
        _log.Msg(counts.Count == 0
            ? "constants changed no rows"
            : "patched rows: " + string.Join(", ", counts));
        return pending;
    }

    // Keep the wire-format preparation independent of Unity and logging so the
    // same path can be checked without starting the game. No properties are set here.
    internal static List<(string Property, string Json)> PrepareTables(
        IReadOnlyDictionary<string, string> source,
        Dictionary<string, Dictionary<string, JsonObject>> overrides,
        out List<string> counts)
    {
        var decrypted = new Dictionary<string, JsonArray>();
        foreach (var (property, file) in Tables.All)
        {
            var wire = source[property];
            JsonNode? node;
            try
            {
                node = JsonNode.Parse(Crypto.Decrypt(wire));
            }
            catch (Exception ex)
            {
                throw new InvalidDataException($"{file} did not decrypt: {ex.Message}");
            }
            if (node is not JsonArray rows)
                throw new InvalidDataException($"{file} is not a list of rows");
            decrypted[file] = rows;
        }
        var merged = new Dictionary<string, JsonArray>();
        counts = new List<string>();
        var changedFiles = new HashSet<string>();
        foreach (var (property, file) in Tables.All)
        {
            overrides.TryGetValue(file, out var patch);
            var (rows, changed) = MergeTable(file, decrypted[file], patch);
            merged[file] = rows;
            if (changed > 0)
            {
                counts.Add($"{file} {changed}");
                changedFiles.Add(file);
            }
        }
        CheckLinks(merged);
        var pending = new List<(string, string)>();
        foreach (var (property, file) in Tables.All)
        {
            if (!changedFiles.Contains(file))
                continue;
            pending.Add((property, Crypto.Encrypt(merged[file].ToJsonString(WriteOpts))));
        }
        return pending;
    }

    static Dictionary<string, Dictionary<string, JsonObject>> ReadOverrides(string[] files)
    {
        var known = Tables.All.Select(item => item.File).ToHashSet(StringComparer.Ordinal);
        var result = new Dictionary<string, Dictionary<string, JsonObject>>();
        foreach (var path in files)
        {
            var name = Path.GetFileName(path);
            if (!known.Contains(name))
                throw new InvalidDataException($"unknown constants file {name}");
            var text = File.ReadAllText(path);
            var node = JsonNode.Parse(text);
            result[name] = Normalize(name, node);
        }
        return result;
    }

    static Dictionary<string, JsonObject> Normalize(string file, JsonNode? node)
    {
        var rows = new Dictionary<string, JsonObject>();
        if (node is null || node is JsonObject empty && empty.Count == 0)
            return rows;
        if (node is JsonObject map)
        {
            foreach (var (key, value) in map)
            {
                if (value is not JsonObject fields)
                    throw new InvalidDataException($"{file} entry {key} must be an object of fields");
                if (fields.ContainsKey("Id"))
                    throw new InvalidDataException($"{file} entry {key} must not repeat Id inside the fields");
                rows[key] = fields;
            }
            return rows;
        }
        if (node is JsonArray list)
        {
            foreach (var item in list)
            {
                if (item is not JsonObject fields || !TryId(fields, out var id))
                    throw new InvalidDataException($"{file} rows need an Id");
                fields.Remove("Id");
                rows[id.ToString()] = fields;
            }
            return rows;
        }
        throw new InvalidDataException($"{file} must be an object keyed by Id");
    }

    static (JsonArray Rows, int Changed) MergeTable(string file, JsonArray vanilla, Dictionary<string, JsonObject>? patch)
    {
        var copy = JsonNode.Parse(vanilla.ToJsonString())!.AsArray();
        if (patch == null || patch.Count == 0)
            return (copy, 0);
        var index = new Dictionary<string, int>();
        for (var i = 0; i < copy.Count; i++)
        {
            if (copy[i] is JsonObject row && TryId(row, out var id))
                index[id.ToString()] = i;
        }
        var changed = 0;
        foreach (var (rowId, fields) in patch)
        {
            if (!index.TryGetValue(rowId, out var at) || copy[at] is not JsonObject row)
                throw new InvalidDataException($"{file} has no Id {rowId}");
            var rowChanged = false;
            foreach (var (key, value) in fields)
            {
                if (key.StartsWith("_", StringComparison.Ordinal))
                    continue;
                if (key == "Id")
                    throw new InvalidDataException($"{file} Id {rowId} cannot change Id");
                if (!row.ContainsKey(key))
                    throw new InvalidDataException($"{file} Id {rowId} has no field {key}");
                if (Kind(row[key]) != Kind(value))
                    throw new InvalidDataException($"{file} Id {rowId} field {key} type change: {Kind(row[key])} -> {Kind(value)}");
                if (row[key]?.ToJsonString() != value?.ToJsonString())
                {
                    row[key] = value == null ? null : JsonNode.Parse(value.ToJsonString());
                    rowChanged = true;
                }
            }
            if (rowChanged)
                changed++;
        }
        return (copy, changed);
    }

    static void CheckLinks(Dictionary<string, JsonArray> merged)
    {
        var ids = merged.ToDictionary(pair => pair.Key, pair => Ids(pair.Value));
        foreach (var (source, field, target) in Tables.Links)
        {
            if (!merged.TryGetValue(source, out var rows) || !ids.TryGetValue(target, out var targetIds))
                continue;
            foreach (var node in rows)
            {
                if (node is not JsonObject row || !TryId(row, out var id) || !row.ContainsKey(field))
                    continue;
                if (Unset(row[field]))
                    continue;
                var key = IdKey(row[field]);
                if (key == null || targetIds.Contains(key))
                    continue;
                throw new InvalidDataException($"{source} Id {id} field {field} missing {target} {row[field]}");
            }
        }
    }

    static bool IsMainLevel(object database)
    {
        var main = ReadBool(database, "MainBuildDatabase");
        var level = ReadInt(database, "Level");
        if (main == false)
            return false;
        if (level is int value && value != 2)
            return false;
        if (main == null && level == null)
        {
            _log.Warning("DataBaseCompiled has no MainBuildDatabase flag and no Level. This database was left alone.");
            return false;
        }
        return main == true || level == 2;
    }

    static void LogBuild(string[] files)
    {
        if (_loggedBuild)
            return;
        _loggedBuild = true;
        _log.Msg("game build " + GameBuild());
        var builder = new StringBuilder();
        foreach (var path in files)
        {
            var hash = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant();
            builder.Append(Path.GetFileName(path)).Append(hash);
            _log.Msg($"constant {Path.GetFileName(path)} sha256 {hash}");
        }
        if (files.Length > 0)
            _log.Msg("constants sha256 " + Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(builder.ToString()))).ToLowerInvariant());
    }

    static string GameBuild()
    {
        var application = FindType("UnityEngine.Application");
        var version = application?.GetProperty("unityVersion")?.GetValue(null)?.ToString();
        return string.IsNullOrEmpty(version) ? "unknown" : version;
    }

    static Type? FindType(params string[] names)
    {
        foreach (var name in names)
        {
            var found = AccessTools.TypeByName(name);
            if (found != null)
                return found;
        }
        return null;
    }

    static string GetString(object database, string property)
    {
        var value = database.GetType().GetProperty(property)?.GetValue(database);
        return value?.ToString() ?? "";
    }

    static void SetString(object database, string property, string value)
    {
        var prop = database.GetType().GetProperty(property);
        if (prop == null)
            throw new MissingMemberException(database.GetType().Name + "." + property);
        if (prop.PropertyType == typeof(string))
            prop.SetValue(database, value);
        else
            prop.SetValue(database, Activator.CreateInstance(prop.PropertyType, value));
    }

    static bool? ReadBool(object database, string property)
    {
        var prop = database.GetType().GetProperty(property);
        if (prop == null || prop.PropertyType != typeof(bool))
            return null;
        return prop.GetValue(database) is bool value ? value : null;
    }

    static int? ReadInt(object database, string property)
    {
        var prop = database.GetType().GetProperty(property);
        if (prop == null)
            return null;
        var value = prop.GetValue(database);
        if (value is int number)
            return number;
        if (value != null && int.TryParse(value.ToString(), out var parsed))
            return parsed;
        return null;
    }

    static IntPtr PointerOf(object database)
    {
        var prop = database.GetType().GetProperty("Pointer");
        return prop?.GetValue(database) is IntPtr pointer ? pointer : IntPtr.Zero;
    }

    static bool TryId(JsonObject row, out int id)
    {
        id = 0;
        return row.TryGetPropertyValue("Id", out var node) && node is JsonValue value && value.TryGetValue<int>(out id);
    }

    static string? IdKey(JsonNode? node)
    {
        if (node is not JsonValue value)
            return null;
        if (value.TryGetValue<int>(out var number))
            return number.ToString();
        if (value.TryGetValue<string>(out var text) && !string.IsNullOrWhiteSpace(text))
            return text.Trim();
        return null;
    }

    static bool Unset(JsonNode? node)
    {
        if (node is null)
            return true;
        if (node is not JsonValue value)
            return false;
        if (value.TryGetValue<int>(out var number))
            return number == 0;
        if (value.TryGetValue<string>(out var text))
            return string.IsNullOrWhiteSpace(text);
        return false;
    }

    static HashSet<string> Ids(JsonArray rows)
    {
        var found = new HashSet<string>();
        foreach (var node in rows)
        {
            if (node is JsonObject row && TryId(row, out var id))
                found.Add(id.ToString());
        }
        return found;
    }

    static string Kind(JsonNode? node)
    {
        if (node is null)
            return "null";
        if (node is JsonArray)
            return "list";
        if (node is JsonObject)
            return "object";
        if (node is JsonValue value)
        {
            if (value.TryGetValue<bool>(out _))
                return "bool";
            if (value.TryGetValue<string>(out _))
                return "string";
            if (value.TryGetValue<double>(out _) || value.TryGetValue<int>(out _))
                return "number";
        }
        return "null";
    }
}

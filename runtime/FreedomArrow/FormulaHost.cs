using System.Text.Json;
using MelonLoader;

namespace FreedomArrow;

static class FormulaHost
{
    static readonly string[] Envelope = { "method", "change", "parameters" };

    static readonly Dictionary<string, Action<JsonElement, MelonLogger.Instance>> Hooks = new(StringComparer.Ordinal)
    {
    };

    public static void Install(string root, MelonLogger.Instance log)
    {
        var directory = Path.Combine(root, "formulas");
        var loaded = new List<FormulaFile>();
        try
        {
            if (Directory.Exists(directory))
            {
                foreach (var path in Directory.EnumerateFiles(directory, "*.json", SearchOption.AllDirectories).OrderBy(path => path, StringComparer.Ordinal))
                {
                    JsonDocument? document = null;
                    try
                    {
                        document = JsonDocument.Parse(File.ReadAllText(path));
                        var method = ReadMethod(document.RootElement, path, directory);
                        loaded.Add(new FormulaFile(method, document));
                        document = null;
                    }
                    catch (Exception ex)
                    {
                        log.Error($"formula {path} left unread: {ex.Message}");
                    }
                    finally
                    {
                        document?.Dispose();
                    }
                }
            }

            var claimed = new HashSet<string>(StringComparer.Ordinal);
            foreach (var group in loaded.GroupBy(file => file.Method, StringComparer.Ordinal))
            {
                claimed.Add(group.Key);
                var files = group.ToList();
                if (files.Count != 1)
                {
                    log.Error($"formula {group.Key} is declared by more than one file; left unpatched");
                    continue;
                }
                if (!Hooks.TryGetValue(group.Key, out var hook))
                {
                    log.Error($"no hook for {group.Key}; left unpatched");
                    continue;
                }
                try
                {
                    hook(files[0].Document.RootElement.GetProperty("parameters"), log);
                }
                catch (Exception ex)
                {
                    log.Error($"formula startup aborted; {group.Key} left unpatched: {ex.Message}");
                }
            }

            foreach (var method in Hooks.Keys)
            {
                if (!claimed.Contains(method))
                    log.Msg($"no formula for {method}; hook not installed");
            }
        }
        finally
        {
            foreach (var file in loaded)
                file.Document.Dispose();
        }
    }

    public static float ReadNumber(JsonElement parameters, string name, double min, double max)
    {
        if (parameters.ValueKind != JsonValueKind.Object
            || !parameters.TryGetProperty(name, out var property)
            || property.ValueKind != JsonValueKind.Number)
            throw new InvalidDataException(name + " must be a number");
        var value = property.GetDouble();
        if (value < min || value > max)
            throw new InvalidDataException(name + " must be a number from " + min + " to " + max);
        return (float)value;
    }

    static string ReadMethod(JsonElement root, string path, string directory)
    {
        if (root.ValueKind != JsonValueKind.Object)
            throw new InvalidDataException("formula must be a JSON object");
        var keys = root.EnumerateObject().Select(property => property.Name).ToHashSet(StringComparer.Ordinal);
        if (!keys.SetEquals(Envelope))
            throw new InvalidDataException("formula keys must be method, change, and parameters");
        if (root.GetProperty("method").ValueKind != JsonValueKind.String)
            throw new InvalidDataException("formula method must be a non-empty string");
        var method = root.GetProperty("method").GetString();
        if (string.IsNullOrWhiteSpace(method))
            throw new InvalidDataException("formula method must be a non-empty string");
        if (root.GetProperty("change").ValueKind != JsonValueKind.String)
            throw new InvalidDataException("formula change must be after, before, inside, or instead");
        var change = root.GetProperty("change").GetString();
        if (change is not ("after" or "before" or "inside" or "instead"))
            throw new InvalidDataException("formula change must be after, before, inside, or instead");
        if (change != "after")
            throw new InvalidDataException($"formula change '{change}' is not implemented");
        CheckParameters(root.GetProperty("parameters"));
        var suffix = Suffix(directory, path);
        if (string.IsNullOrEmpty(suffix) || (method != suffix && !method.EndsWith("." + suffix, StringComparison.Ordinal)))
            throw new InvalidDataException("formula path does not match method");
        return method;
    }

    static void CheckParameters(JsonElement parameters)
    {
        if (parameters.ValueKind != JsonValueKind.Object)
            throw new InvalidDataException("formula parameters must be an object");
        foreach (var property in parameters.EnumerateObject())
        {
            if (!IsParameter(property.Value))
                throw new InvalidDataException(
                    $"parameter {property.Name} must be a number, string, boolean, or array of those");
        }
    }

    static bool IsParameter(JsonElement value)
    {
        if (IsScalar(value))
            return true;
        if (value.ValueKind != JsonValueKind.Array)
            return false;
        foreach (var item in value.EnumerateArray())
        {
            if (!IsScalar(item))
                return false;
        }
        return true;
    }

    static bool IsScalar(JsonElement value)
    {
        return value.ValueKind is JsonValueKind.Number or JsonValueKind.String or JsonValueKind.True or JsonValueKind.False;
    }

    static string Suffix(string directory, string path)
    {
        var relative = Path.GetRelativePath(directory, path);
        var without = Path.ChangeExtension(relative, null);
        if (without == null)
            return "";
        return without.Replace(Path.DirectorySeparatorChar, '.').Replace(Path.AltDirectorySeparatorChar, '.');
    }

    sealed class FormulaFile
    {
        public FormulaFile(string method, JsonDocument document)
        {
            Method = method;
            Document = document;
        }

        public string Method { get; }
        public JsonDocument Document { get; }
    }
}

using System.Reflection;
using System.Text.Json.Nodes;
using FreedomArrow;
using MelonLoader;

// Runs the real plugin assembly in a console host; no game files, Unity calls,
// native hooks, MelonLoader initialization or test framework packages required.
public static class Program
{
    static int _checks;

    public static void Main()
    {
        Registration();
        GeneratedHooks();
        EncryptedMerge();
        ConfigGuard();
        Console.WriteLine($"PASS: {_checks} runtime assertions (host checks; native gameplay unverified)");
    }

    static void Check(bool condition, string message)
    {
        _checks++;
        if (!condition)
            throw new Exception(message);
    }

    static void Throws<T>(Action action, string message) where T : Exception
    {
        _checks++;
        try { action(); }
        catch (T) { return; }
        throw new Exception(message);
    }

    static void Registration()
    {
        var info = typeof(FreedomArrowMod).Assembly.GetCustomAttribute<MelonInfoAttribute>();
        Check(info != null, "MelonInfo registration missing");
        Check(info!.SystemType == typeof(FreedomArrowMod), "wrong mod entry point");
        Check(info.SystemType.IsSubclassOf(typeof(MelonMod)), "entry point must be a MelonMod");
        Check(typeof(DatabaseMerge).IsVisible && typeof(ForestCover).IsVisible, "emitted hooks need visible bridge types");
    }

    static void GeneratedHooks()
    {
        var prefix = HookBinder.Prefix("__0", typeof(object), nameof(DatabaseMerge.PrefixCompiledBody));
        prefix.Invoke(null, new object?[] { null });
        Check(prefix.GetParameters()[0].Name == "__0", "prefix binding changed");

        var target = typeof(Program).GetMethod(nameof(Hit))!;
        var postfix = HookBinder.Postfix(target, typeof(ForestCover).GetMethod(nameof(ForestCover.Apply))!);
        object?[] args = { null, 10f, null, 23f };
        postfix.Invoke(null, args);
        Check((float)args[3]! == 23f, "null-target forest hook must preserve damage");

        var typed = HookBinder.Postfix(typeof(Program).GetMethod(nameof(TypedHit))!, typeof(Program).GetMethod(nameof(RecordHit))!);
        var ammo = new Ammo { Value = 3f };
        object?[] typedArgs = { ammo, new Entity { Value = 4 }, 100f, 2f };
        typed.Invoke(null, typedArgs);
        Check((float)typedArgs[3]! == 9f, "postfix must bind by name, box the entity and pass result by reference");
        Check(typed.GetParameters()[3].Name == "__result", "Harmony result binding missing");
    }

    public struct Entity { public int Value; }
    public sealed class Ammo { public float Value; }
    public static float Hit(object? target, float baseDamage, object? ammoInfo) => baseDamage;
    public static float TypedHit(Ammo ammoInfo, Entity target, float baseDamage) => baseDamage;
    public static void RecordHit(object? target, object? ammo, ref float result)
        => result += ((Entity)target!).Value + ((Ammo)ammo!).Value;

    static Dictionary<string, string> Source()
        => Tables.All.ToDictionary(item => item.Property,
            item => Crypto.Encrypt("[{\"Id\":1,\"Cost\":10,\"Name\":\"café\"}]"));

    static Dictionary<string, Dictionary<string, JsonObject>> Patch(string file, string fields)
        => new() { [file] = new() { ["1"] = JsonNode.Parse(fields)!.AsObject() } };

    static void EncryptedMerge()
    {
        var source = Source();
        var original = new Dictionary<string, string>(source);
        var none = DatabaseMerge.PrepareTables(source, new(), out var noCounts);
        Check(none.Count == 0 && noCounts.Count == 0, "empty constants must write nothing");

        var pending = DatabaseMerge.PrepareTables(source, Patch("units.json", "{\"Cost\":40}"), out var counts);
        Check(pending.Count == 1 && pending[0].Property == "Units", "only the changed table must be written");
        Check(counts.SequenceEqual(new[] { "units.json 1" }), "changed-row log count");
        var wire = pending[0].Json;
        Check(!wire.StartsWith("["), "changed property must contain ciphertext, not JSON");
        var rows = JsonNode.Parse(Crypto.Decrypt(wire))!.AsArray();
        Check(rows[0]!["Cost"]!.GetValue<int>() == 40, "edited value must survive encrypted round trip");
        Check(rows[0]!["Name"]!.GetValue<string>() == "café", "unmodified Unicode value lost");
        Check(source.All(pair => original[pair.Key] == pair.Value), "preparation must never mutate original ciphertext");

        var noop = DatabaseMerge.PrepareTables(source, Patch("units.json", "{\"Cost\":10}"), out _);
        Check(noop.Count == 0, "same-value edits must preserve ciphertext");
        var patch = Patch("units.json", "{\"Cost\":40}");
        patch["weapons.json"] = new() { ["1"] = JsonNode.Parse("{\"Cost\":70}")!.AsObject() };
        var both = DatabaseMerge.PrepareTables(source, patch, out _);
        Check(both.Count == 2, "two table edits must produce two writes");
        foreach (var item in both)
            Check(JsonNode.Parse(Crypto.Decrypt(item.Json))!.AsArray().Count == 1, "each write must be valid encrypted JSON");

        Throws<InvalidDataException>(() => DatabaseMerge.PrepareTables(source, Patch("units.json", "{\"Cost\":\"bad\"}"), out _), "type changes must fail");
        Throws<InvalidDataException>(() => DatabaseMerge.PrepareTables(source, Patch("units.json", "{\"Missing\":3}"), out _), "unknown fields must fail");
        var missing = Patch("units.json", "{\"Cost\":40}");
        missing["units.json"]["99"] = new JsonObject { ["Cost"] = 40 };
        Throws<InvalidDataException>(() => DatabaseMerge.PrepareTables(source, missing, out _), "unknown rows must fail");

        source["WeaponAmmunitionsJson"] = Crypto.Encrypt("[{\"Id\":1,\"AmmunitionId\":1}]");
        Throws<InvalidDataException>(() => DatabaseMerge.PrepareTables(source, Patch("weapon_ammunitions.json", "{\"AmmunitionId\":999}"), out _), "new broken links must fail");
        var beforeFailure = new Dictionary<string, string>(source);
        source["WeaponsJson"] = "invalid ciphertext";
        Throws<InvalidDataException>(() => DatabaseMerge.PrepareTables(source, Patch("units.json", "{\"Cost\":40}"), out _), "invalid ciphertext must fail preparation");
        Check(source["Units"] == beforeFailure["Units"], "failed preparation must leave Units untouched");
        Throws<FormatException>(() => Crypto.Decrypt("[{\"Id\":1}]"), "decryptor must reject plaintext");
    }

    static void ConfigGuard()
    {
        var root = Path.Combine(Path.GetTempPath(), "FreedomArrowTests-" + Guid.NewGuid());
        try
        {
            FreedomArrowMod.CheckSupportedInputs(root);
            Directory.CreateDirectory(Path.Combine(root, "configs", "nested"));
            FreedomArrowMod.CheckSupportedInputs(root);
            File.WriteAllText(Path.Combine(root, "configs", "nested", "FOWToolConfig.JSON"), "{}");
            Throws<InvalidDataException>(() => FreedomArrowMod.CheckSupportedInputs(root), "unsupported config files must fail startup clearly");
        }
        finally { if (Directory.Exists(root)) Directory.Delete(root, recursive: true); }
    }
}

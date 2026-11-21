namespace BAModManager.Core;

/// <summary>
/// Launcher 1.1.6 (Osama 18 Nov 2026: "will our new launcher remove foreign DLLs?" / "please build that" / "we have a lot of players that
/// play actual arrow and it conflicts with our mod"). Before a Freedom Arrow PLAY, every DLL in the game's Mods folder that is not a file of
/// the active Freedom Arrow pack is moved to FA-parked-mods next to the game exe. MelonLoader loads only Mods\*.dll, so parked mods (for
/// example ActualArrow's MLDatabaseMod.dll, which replaces the unit database and removes China) no longer load and no longer change the
/// ArrowQueue build code. Nothing is deleted. "Turn off mods" moves them back, so ActualArrow and other mods still work outside Freedom Arrow.
/// </summary>
public static class ForeignMods
{
    public const string FolderName = "FA-parked-mods";

    /// <summary>1.1.14 (Osama 21 Nov 2026, "make sure dll and deck files are properly moved and maintained separately"): Freedom Arrow's own
    /// DLLs. Every one of them is named FreedomArrow*.dll or FA + capital letter (FAArrowQueue, FAFlatIncomeMod, FAModels...), so they never
    /// share a name with ActualArrow's DLLs.</summary>
    public static bool IsFreedomArrowDll(string fileName) =>
        fileName.StartsWith("FreedomArrow", StringComparison.OrdinalIgnoreCase) ||
        fileName.Length > 2 && fileName.StartsWith("FA", StringComparison.Ordinal) && char.IsUpper(fileName[2]);

    private static readonly string[] LoaderFolders = { "Mods", "Plugins" };   // the folders MelonLoader loads *.dll from

    public static string ParkFolder(string gameDir) => Path.Combine(gameDir, FolderName);

    /// <summary>Moves every Mods\*.dll not in <paramref name="keepGamePaths"/> (game-relative, e.g. "Mods/ArrowQueue.dll") to the park folder.</summary>
    public static List<string> Park(string gameDir, IEnumerable<string> keepGamePaths, Action<string> log)
    {
        var keep = new HashSet<string>(keepGamePaths.Select(p => Path.GetFileName(p.Replace('\\', '/'))), StringComparer.OrdinalIgnoreCase);
        var mods = Path.Combine(gameDir, "Mods");
        var moved = new List<string>();
        if (!Directory.Exists(mods)) return moved;
        foreach (var file in Directory.GetFiles(mods, "*.dll", SearchOption.TopDirectoryOnly).OrderBy(f => f, StringComparer.OrdinalIgnoreCase))
        {
            var name = Path.GetFileName(file);
            if (keep.Contains(name)) continue;
            if (IsFreedomArrowDll(name))
            {
                // A Freedom Arrow DLL the current version no longer ships: switched off where it is, never handed to other mods.
                File.Move(file, file + PathUtil.DisabledSuffix, overwrite: true);
                log("Old Freedom Arrow file switched off: Mods/" + name);
                continue;
            }
            var park = ParkFolder(gameDir);
            Directory.CreateDirectory(park);
            var target = Path.Combine(park, name);
            if (File.Exists(target) && !SameBytes(file, target))
                File.Move(target, Path.Combine(park, name + "." + DateTime.UtcNow.ToString("yyyyMMdd-HHmmss") + ".old"));   // older copy kept, never restored
            File.Move(file, target, overwrite: true);
            moved.Add(name);
        }
        if (moved.Count > 0)
            log("Not part of Freedom Arrow, moved to " + FolderName + " (put back when mods are turned off): " + string.Join(", ", moved));
        return moved;
    }

    /// <summary>Moves parked DLLs back into Mods (a file already in Mods wins), for playing other mods or vanilla.</summary>
    public static List<string> Restore(string gameDir, Action<string> log)
    {
        var park = ParkFolder(gameDir);
        var back = new List<string>();
        if (!Directory.Exists(park)) return back;
        var mods = Path.Combine(gameDir, "Mods");
        Directory.CreateDirectory(mods);
        foreach (var file in Directory.GetFiles(park, "*.dll").OrderBy(f => f, StringComparer.OrdinalIgnoreCase))
        {
            var name = Path.GetFileName(file);
            if (IsFreedomArrowDll(name)) continue;   // parked by an older launcher: stays parked
            var target = Path.Combine(mods, name);
            if (File.Exists(target)) continue;
            File.Move(file, target);
            back.Add(name);
        }
        if (back.Count > 0) log("Other mods put back into Mods: " + string.Join(", ", back));
        return back;
    }

    /// <summary>
    /// "Play vanilla" / other mods: Freedom Arrow's own DLLs in Mods and Plugins get the .disabled ending, so MelonLoader started by
    /// another launcher (ActualArrow) loads only that mod. PLAY switches them back (<see cref="EnableOwn"/>) before checking the install.
    /// </summary>
    public static List<string> DisableOwn(string gameDir, Action<string> log)
    {
        var off = new List<string>();
        foreach (var folder in LoaderFolders)
        {
            var dir = Path.Combine(gameDir, folder);
            if (!Directory.Exists(dir)) continue;
            foreach (var file in Directory.GetFiles(dir, "*.dll", SearchOption.TopDirectoryOnly))
            {
                var name = Path.GetFileName(file);
                if (!IsFreedomArrowDll(name)) continue;
                File.Move(file, file + PathUtil.DisabledSuffix, overwrite: true);
                off.Add(folder + "/" + name);
            }
        }
        if (off.Count > 0) log("Freedom Arrow switched off for other mods and vanilla: " + string.Join(", ", off));
        return off;
    }

    /// <summary>PLAY: Freedom Arrow DLLs that <see cref="DisableOwn"/> switched off are switched back on (a working copy wins).</summary>
    public static List<string> EnableOwn(string gameDir, IEnumerable<string> ownGamePaths, Action<string> log)
    {
        var on = new List<string>();
        foreach (var rel in ownGamePaths.Select(p => p.Replace('\\', '/')).Distinct(StringComparer.OrdinalIgnoreCase))
        {
            if (!rel.EndsWith(".dll", StringComparison.OrdinalIgnoreCase) || !LoaderFolders.Any(f => rel.StartsWith(f + "/", StringComparison.OrdinalIgnoreCase))) continue;
            var path = PathUtil.ToFull(gameDir, rel);
            if (File.Exists(path) || !File.Exists(path + PathUtil.DisabledSuffix)) continue;
            File.Move(path + PathUtil.DisabledSuffix, path);
            on.Add(rel);
        }
        if (on.Count > 0) log("Freedom Arrow switched back on: " + string.Join(", ", on));
        return on;
    }

    private static bool SameBytes(string a, string b)
    {
        var fa = new FileInfo(a); var fb = new FileInfo(b);
        if (fa.Length != fb.Length) return false;
        return File.ReadAllBytes(a).AsSpan().SequenceEqual(File.ReadAllBytes(b));
    }
}

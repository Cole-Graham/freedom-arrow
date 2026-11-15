using System.Text.RegularExpressions;
using Microsoft.Win32;

namespace BAModManager.Core;

/// <summary>
/// Linux support (Lateralus, 14 November 2026): the launcher runs under Steam + Proton (or Wine) as a non-Steam game.
/// Inside Wine the game runs in another Proton prefix, so the Windows process list, registry and user folders are the
/// wrong ones. Wine maps the Linux root to Z:, so Linux Steam folders, /proc and the game's own prefix are read there.
/// </summary>
public static class LinuxSteam
{
    /// <summary>The exact Steam launch option Broken Arrow needs on Linux to load MelonLoader's version.dll.</summary>
    public const string LaunchOption = "WINEDLLOVERRIDES=\"version=n,b\" %command%";

    public static bool IsWine { get; } = Detect();

    private static bool Detect()
    {
        try
        {
            using var key = Registry.CurrentUser.OpenSubKey(@"Software\Wine");
            if (key != null) return true;
        }
        catch { /* not Wine */ }
        return Environment.GetEnvironmentVariable("WINEHOMEDIR") != null || Environment.GetEnvironmentVariable("STEAM_COMPAT_DATA_PATH") != null;
    }

    /// <summary>Linux path to a Windows path through Wine's Z: drive.</summary>
    public static string ToWindows(string unix) => "Z:" + unix.Replace('/', '\\');

    /// <summary>The Linux home folder as a Z: path. Wine sets WINEHOMEDIR (\??\Z:\home\name); HOME is the fallback.</summary>
    public static string? Home
    {
        get
        {
            var w = Environment.GetEnvironmentVariable("WINEHOMEDIR");
            if (!string.IsNullOrEmpty(w)) return w.StartsWith(@"\??\", StringComparison.Ordinal) ? w[4..] : w;
            var h = Environment.GetEnvironmentVariable("HOME");
            return h != null && h.StartsWith('/') ? ToWindows(h) : null;
        }
    }

    /// <summary>Native, Flatpak and Snap Steam folders.</summary>
    public static IEnumerable<string> SteamRoots()
    {
        if (Home is not string home) yield break;
        foreach (var rel in new[] { @".local\share\Steam", @".steam\steam", @".steam\root",
                     @".var\app\com.valvesoftware.Steam\.local\share\Steam", @"snap\steam\common\.local\share\Steam" })
        {
            var p = Path.Combine(home, rel);
            if (Directory.Exists(p)) yield return p;
        }
    }

    /// <summary>libraryfolders.vdf on Linux lists Linux paths ("/mnt/games/SteamLibrary").</summary>
    public static string LibraryPath(string vdfPath) => IsWine && vdfPath.StartsWith('/') ? ToWindows(vdfPath) : vdfPath;

    /// <summary>
    /// Running processes with this name, from /proc (Z:\proc) when under Wine, because the game runs in its own prefix
    /// and the Windows process list doesn't show it. comm holds up to 15 characters ("BrokenArrow.exe" fits exactly).
    /// </summary>
    public static bool ProcessRunning(string name, string proc = @"Z:\proc")
    {
        var want = name.Length > 15 ? name[..15] : name;
        try
        {
            foreach (var dir in Directory.EnumerateDirectories(proc))
            {
                var pid = Path.GetFileName(dir);
                if (pid.Length == 0 || !pid.All(char.IsDigit)) continue;
                try { if (File.ReadAllText(Path.Combine(dir, "comm")).Trim() == want) return true; }
                catch { /* process ended */ }
            }
        }
        catch { /* no /proc */ }
        return false;
    }

    /// <summary>
    /// The game's own Proton prefix decks: steamapps\common\GAME -> steamapps\compatdata\APPID\pfx\...\Decks.
    /// Null when the game isn't in a Steam library or Proton hasn't created the folder (Windows, or never started).
    /// </summary>
    public static string? ProtonDecks(string? gameDir, string appId)
    {
        try
        {
            if (gameDir == null) return null;
            var dir = new DirectoryInfo(Path.TrimEndingDirectorySeparator(Path.GetFullPath(gameDir)));
            if (dir.Parent?.Name.Equals("common", StringComparison.OrdinalIgnoreCase) != true || dir.Parent.Parent == null) return null;
            var decks = Path.Combine(dir.Parent.Parent.FullName, "compatdata", appId, "pfx", "drive_c", "users", "steamuser",
                "AppData", "LocalLow", "SteelBalalaikaStudio", "BrokenArrow", "Decks");
            return Directory.Exists(decks) ? decks : null;
        }
        catch { return null; }
    }

    /// <summary>
    /// Broken Arrow's launch options from every Steam account's localconfig.vdf. Null when no localconfig was found
    /// (unknown); otherwise true when any account has the version.dll override.
    /// </summary>
    public static bool? HasLaunchOption(IEnumerable<string> steamRoots, string appId)
    {
        bool found = false;
        foreach (var root in steamRoots)
        {
            var users = Path.Combine(root, "userdata");
            if (!Directory.Exists(users)) continue;
            foreach (var cfg in Directory.EnumerateFiles(users, "localconfig.vdf", SearchOption.AllDirectories))
            {
                found = true;
                string? options;
                try { options = LaunchOptions(File.ReadAllText(cfg), appId); }
                catch { continue; }
                if (options != null && Regex.IsMatch(options, @"WINEDLLOVERRIDES=\\?""?[^""\s]*version=n,b")) return true;
            }
        }
        return found ? false : null;
    }

    /// <summary>The LaunchOptions value inside the "APPID" { ... } block of a localconfig.vdf.</summary>
    public static string? LaunchOptions(string vdf, string appId)
    {
        foreach (Match m in Regex.Matches(vdf, "\"" + appId + "\"\\s*\\{"))
        {
            int depth = 1, i = m.Index + m.Length, start = i;
            for (; i < vdf.Length && depth > 0; i++)
            {
                if (vdf[i] == '"') { i = vdf.IndexOf('"', i + 1); if (i < 0) return null; continue; }
                if (vdf[i] == '{') depth++;
                else if (vdf[i] == '}') depth--;
            }
            var block = vdf[start..Math.Max(start, i - 1)];
            // Only the block's own keys, not nested blocks
            var own = block;
            for (string prev = ""; prev != own;) { prev = own; own = Regex.Replace(own, "\\{[^{}]*\\}", ""); }
            var lo = Regex.Match(own, "\"LaunchOptions\"\\s+\"((?:[^\"\\\\]|\\\\.)*)\"", RegexOptions.IgnoreCase);
            if (lo.Success) return Regex.Unescape(lo.Groups[1].Value);
        }
        return null;
    }
}

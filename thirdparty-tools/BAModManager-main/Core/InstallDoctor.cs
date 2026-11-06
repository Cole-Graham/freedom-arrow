using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using static BAModManager.Core.Loc;

namespace BAModManager.Core;

/// <summary>
/// "Help me install": a read-only check of the game folder. It only reads files under the game folder
/// (and asks Windows whether it runs under Wine/Proton). It changes nothing and sends nothing.
/// </summary>
public static class InstallDoctor
{
    public sealed record Finding(bool Ok, string Title, string Fix);

    public static (List<Finding> Findings, string Report) Run(string? gameDir)
    {
        var found = new List<Finding>();
        bool wine = UnderWine();
        if (gameDir == null || !GameLocator.IsGameFolder(gameDir))
        {
            found.Add(new(false, T("Broken Arrow wasn't found."),
                T("Open Settings and choose the Broken Arrow folder: the one that has BrokenArrow.exe in it.")));
            return (found, Report(found, wine, null, null));
        }

        // MelonLoader
        bool loader = File.Exists(Path.Combine(gameDir, "version.dll")) && Directory.Exists(Path.Combine(gameDir, "MelonLoader"));
        var logPath = Path.Combine(gameDir, "MelonLoader", "Latest.log");
        string log = "";
        try { if (File.Exists(logPath)) log = File.ReadAllText(logPath); } catch (IOException) { /* the game has it open */ }
        var loaderLine = log.Split('\n').FirstOrDefault(l => l.Contains("MelonLoader v", StringComparison.Ordinal))?.Trim();
        found.Add(loader
            ? new(true, T("MelonLoader is installed."), loaderLine ?? "")
            : new(false, T("MelonLoader isn't installed."), T("Press PLAY once in this launcher. It installs MelonLoader for you.")));

        // The modpack: every file listed in its payload manifest, by SHA-256
        string? version = null;
        var allowed = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var manifests = Directory.Exists(Path.Combine(gameDir, "UserData"))
            ? Directory.GetFiles(Path.Combine(gameDir, "UserData"), "payload-manifest.json", SearchOption.AllDirectories)
            : Array.Empty<string>();
        if (manifests.Length == 0)
            found.Add(new(false, T("The mod pack isn't installed."), T("Press PLAY in this launcher. It downloads and installs the mod pack.")));
        foreach (var path in manifests)
        {
            try
            {
                using var doc = JsonDocument.Parse(File.ReadAllText(path));
                version = doc.RootElement.TryGetProperty("version", out var v) ? v.GetString() : null;
                int missing = 0, changed = 0, total = 0;
                foreach (var file in doc.RootElement.GetProperty("sha256").EnumerateObject())
                {
                    total++;
                    allowed.Add(Path.GetFileName(file.Name));
                    var full = Path.Combine(gameDir, file.Name.Replace('/', Path.DirectorySeparatorChar));
                    if (!File.Exists(full)) { missing++; continue; }
                    using var s = File.OpenRead(full);
                    if (!Convert.ToHexString(SHA256.HashData(s)).Equals(file.Value.GetString(), StringComparison.OrdinalIgnoreCase)) changed++;
                }
                found.Add(missing + changed == 0
                    ? new(true, T("The mod pack {0} is installed and every file is correct ({1} files).", version ?? "?", total), "")
                    : new(false, T("The mod pack {0} is damaged: {1} files missing, {2} files changed.", version ?? "?", missing, changed),
                        T("Close the game, then drop the .bamod file on this launcher to install it again.")));
            }
            catch (Exception ex) when (ex is IOException or JsonException or InvalidOperationException or KeyNotFoundException)
            {
                found.Add(new(false, T("The mod pack's file list can't be read."), T("Drop the .bamod file on this launcher to install it again.")));
            }
        }

        // Other gameplay mods that are turned on
        var modsDir = Path.Combine(gameDir, "Mods");
        var others = Directory.Exists(modsDir)
            ? Directory.GetFiles(modsDir, "*.dll").Select(Path.GetFileName).Where(n => n != null && !allowed.Contains(n!)).Cast<string>().ToList()
            : new List<string>();
        if (others.Count > 0 && manifests.Length > 0)
            found.Add(new(false, T("Other mods are turned on: {0}", string.Join(", ", others)),
                T("Turn them off in the Mod Manager (for example ActualArrow). Two mod packs at once break each other.")));

        // What the game said the last time it started
        if (loader)
        {
            if (log.Length == 0)
                found.Add(new(false, T("The game hasn't started with mods yet."), wine ? LinuxFix() : T("Press PLAY in this launcher, not in Steam.")));
            else if (log.Contains("_FAILED", StringComparison.Ordinal) || log.Contains("mismatch", StringComparison.OrdinalIgnoreCase))
                found.Add(new(false, T("The mod pack failed to load the last time the game started."),
                    T("Drop the .bamod file on this launcher to install it again. If it still fails, send the report below.")));
            else if (log.Contains("_APPLIED", StringComparison.Ordinal))
                found.Add(new(true, T("The mod pack loaded the last time the game started."), ""));
            else if (manifests.Length > 0)
                found.Add(new(false, T("The last game start didn't load the mod pack."), wine ? LinuxFix() : T("Start the game with PLAY in this launcher.")));
        }
        if (wine) found.Add(new(true, T("This PC runs Linux (Proton)."), LinuxFix()));

        return (found, Report(found, wine, version, log));
    }

    private static string LinuxFix() =>
        T("On Linux, start the game from Steam, not from this launcher: in Steam, right-click Broken Arrow, Properties, Launch Options, enter  WINEDLLOVERRIDES=\"version=n,b\" %command%  then choose \"Play Anti-Cheat Disabled\".");

    private static string Report(List<Finding> found, bool wine, string? version, string? log)
    {
        var sb = new StringBuilder();
        sb.AppendLine($"Install check, {DateTime.Now:yyyy-MM-dd HH:mm}, {AppInfo.ShortName}");
        sb.AppendLine($"System: {(wine ? "Linux (Proton/Wine)" : "Windows")}; mod pack: {version ?? "none"}");
        foreach (var f in found) sb.AppendLine((f.Ok ? "OK   " : "FIX  ") + f.Title);
        if (!string.IsNullOrEmpty(log))
        {
            sb.AppendLine("Log lines:");
            var lines = log.Split('\n');
            foreach (var line in lines.Where(l => l.Contains("MelonLoader v", StringComparison.Ordinal)).Take(1)
                .Concat(lines.Where(l => l.Contains("_VERIFIED", StringComparison.Ordinal) || l.Contains("_APPLIED", StringComparison.Ordinal)
                    || l.Contains("_FAILED", StringComparison.Ordinal) || l.Contains("mismatch", StringComparison.OrdinalIgnoreCase)
                    || l.Contains("[ERROR]", StringComparison.OrdinalIgnoreCase)).TakeLast(12)))
                sb.AppendLine("  " + line.Trim());
        }
        // Keep the player's name out of the report
        var home = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
        var text = sb.ToString();
        if (home.Length > 3) text = text.Replace(home, "~", StringComparison.OrdinalIgnoreCase);
        return Environment.UserName.Length >= 3 ? text.Replace(Environment.UserName, "<user>", StringComparison.OrdinalIgnoreCase) : text;
    }

    [DllImport("kernel32", CharSet = CharSet.Ansi)] private static extern IntPtr GetModuleHandleA(string name);
    [DllImport("kernel32", CharSet = CharSet.Ansi)] private static extern IntPtr GetProcAddress(IntPtr module, string name);

    /// <summary>Wine and Proton add wine_get_version to ntdll; Windows doesn't have it.</summary>
    private static bool UnderWine()
    {
        try
        {
            var ntdll = GetModuleHandleA("ntdll.dll");
            return ntdll != IntPtr.Zero && GetProcAddress(ntdll, "wine_get_version") != IntPtr.Zero;
        }
        catch (Exception) { return false; }
    }
}

using System.Reflection;
using System.Security.Cryptography;
using System.Text.RegularExpressions;

namespace BAModManager.Core;

/// <summary>
/// Linux crash fix (Osama 20 Nov 2026: "can we add it to the launcher so it applies all of this"). Under Proton the game's garbage
/// collector pauses every thread; when a thread does not stop the normal way, wineserver traces it with ptrace. With the kernel's
/// default kernel.yama.ptrace_scope=1 that is refused, the collector retries for about 30 s and the game stops with
/// "Fatal error in GC / SuspendThread loop failed" (5 crashes on Osama's PC on 20 Nov, each one with the kernel's
/// "ptrace attach ... was attempted by wineserver" messages). fa_ptracer.so (Assets/Linux, source next to it) is loaded with
/// LD_PRELOAD and calls prctl(PR_SET_PTRACER, ANY): only the processes started by Broken Arrow's launch line may be traced, only
/// while they run. No system setting changes. The launcher puts the file in place and copies the launch line; Steam's launch
/// options are read, never written (Steam overwrites localconfig.vdf while it runs).
/// </summary>
public static class LinuxGcFix
{
    public const string FileName = "fa_ptracer.so";
    public const string Sha256 = "fe5ef52f3763dc2db0007984b88cfa3ff8d40b74ef9244af211cba028b1726a1";
    private const string FlatpakRel = @".var\app\com.valvesoftware.Steam";

    /// <summary>kernel.yama.ptrace_scope: 0 = no restriction, 1/2 = the crash can happen, 3 = no tracing at all; null = unknown (no Yama).</summary>
    public static int? PtraceScope(string proc = @"Z:\proc")
    {
        try { return int.TryParse(File.ReadAllText(Path.Combine(proc, "sys", "kernel", "yama", "ptrace_scope")).Trim(), out var v) ? v : null; }
        catch { return null; }
    }

    /// <summary>Folder for the helper, as a Z: path: inside Flatpak Steam's own folder when Broken Arrow is set up there (the sandbox
    /// cannot see ~/.local/share), otherwise ~/.local/share/FreedomArrow.</summary>
    public static string? Folder(IEnumerable<string> steamRoots, string appId)
    {
        if (LinuxSteam.Home is not string home) return null;
        bool flatpak = steamRoots.Any(r => r.Contains(FlatpakRel, StringComparison.OrdinalIgnoreCase) && LaunchOptionsIn(r, appId).Any());
        return flatpak ? Path.Combine(home, FlatpakRel, @".local\share\FreedomArrow") : Path.Combine(home, @".local\share\FreedomArrow");
    }

    /// <summary>Z:\home\me\x → /home/me/x</summary>
    public static string ToUnix(string zPath) => zPath.StartsWith("Z:", StringComparison.OrdinalIgnoreCase) ? zPath[2..].Replace('\\', '/') : zPath.Replace('\\', '/');

    /// <summary>Writes the helper from the launcher's own (signed, hash-checked) exe when it is missing or different. Returns its Linux path.</summary>
    public static string Install(string folder)
    {
        using var res = Assembly.GetExecutingAssembly().GetManifestResourceStream("Linux." + FileName)
            ?? throw new InvalidDataException("The Linux crash fix is missing from the launcher.");
        using var ms = new MemoryStream(); res.CopyTo(ms); var bytes = ms.ToArray();
        if (!Convert.ToHexString(SHA256.HashData(bytes)).Equals(Sha256, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("The Linux crash fix inside the launcher has the wrong checksum.");
        var path = Path.Combine(folder, FileName);
        bool same = File.Exists(path) && Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).Equals(Sha256, StringComparison.OrdinalIgnoreCase);
        if (!same)
        {
            Directory.CreateDirectory(folder);
            File.WriteAllBytes(path + ".part", bytes);
            File.Move(path + ".part", path, true);
        }
        return ToUnix(path);
    }

    /// <summary>true when any Steam account's launch options for the game preload fa_ptracer.so; null when none could be read.</summary>
    public static bool? Active(IEnumerable<string> steamRoots, string appId)
    {
        var all = steamRoots.SelectMany(r => LaunchOptionsIn(r, appId)).ToList();
        if (all.Count == 0) return null;
        return all.Any(o => Regex.IsMatch(o, @"LD_PRELOAD=\S*" + Regex.Escape(FileName)));
    }

    /// <summary>The launch line to paste: the helper in front of the mod loader's line.</summary>
    public static string LaunchLine(string unixPath) => "LD_PRELOAD=\"" + unixPath + "\" " + LinuxSteam.LaunchOption;

    private static IEnumerable<string> LaunchOptionsIn(string root, string appId)
    {
        var users = Path.Combine(root, "userdata");
        if (!Directory.Exists(users)) yield break;
        foreach (var cfg in Directory.EnumerateFiles(users, "localconfig.vdf", SearchOption.AllDirectories))
        {
            string? o = null;
            try { o = LinuxSteam.LaunchOptions(File.ReadAllText(cfg), appId); } catch { /* unreadable */ }
            if (o != null) yield return o;
        }
    }
}

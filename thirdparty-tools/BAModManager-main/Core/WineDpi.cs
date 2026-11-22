using System.Globalization;
using Microsoft.Win32;

namespace BAModManager.Core;

/// <summary>
/// 1.1.16 (Osama 22 Nov 2026, thread 1567745029781454889: "the installer is really small on my 4k resolution, we might need to zoom it in or follow
/// the user's zoom level?"). On Windows the launcher already follows the display zoom (PerMonitorV2, AutoScaleMode.Dpi). Under Proton/Wine the
/// prefix always reports 100 % (LogPixels 96), whatever the Linux desktop scale is: on his 4K screen KDE has [Xwayland] Scale=2 (X programs scale
/// themselves), so the 1440x960 window came out half size. At start-up the launcher reads the desktop scale and sets the same DPI in its own Wine
/// prefix (HKCU\Control Panel\Desktop LogPixels), then restarts once, because Wine reads it when a program starts.
/// Scale, first found: FA_LAUNCHER_SCALE (override, e.g. 1.5), GDK_SCALE, QT_SCALE_FACTOR, KDE kwinrc [Xwayland] Scale, else a 4K-sized screen = 2
/// (1500+ px high = 1.5). A LogPixels the player set themselves is left alone, and so is the game's own prefix (Steam app 1604270).
/// </summary>
public static class WineDpi
{
    private const string DesktopKey = @"Control Panel\Desktop", MarkKey = @"Software\FreedomArrowLauncher", MarkValue = "AutoLogPixels";

    /// <summary>True when the prefix DPI was changed and the launcher should restart to use it.</summary>
    public static bool Apply()
    {
        if (!LinuxSteam.IsWine) return false;
        try
        {
            var compat = Environment.GetEnvironmentVariable("STEAM_COMPAT_DATA_PATH")?.TrimEnd('/', '\\');
            if (compat != null && (compat.EndsWith("/1604270") || compat.EndsWith("\\1604270"))) return false;
            using var desktop = Registry.CurrentUser.CreateSubKey(DesktopKey);
            using var mark = Registry.CurrentUser.CreateSubKey(MarkKey);
            int current = desktop.GetValue("LogPixels") is int c ? c : 96;
            int? ours = mark.GetValue(MarkValue) is int o ? o : null;
            if (current != 96 && ours != current) { NetDiagnostics.Append($"Display scale: LogPixels {current} was set by the player, left as it is"); return false; }
            var (scale, source) = HostScale();
            int want = Math.Clamp((int)Math.Round(96 * scale), 96, 288);
            if (want == current) return false;
            desktop.SetValue("LogPixels", want, RegistryValueKind.DWord);
            mark.SetValue(MarkValue, want, RegistryValueKind.DWord);
            NetDiagnostics.Append($"Display scale {scale.ToString("0.##", CultureInfo.InvariantCulture)} ({source}): Wine LogPixels {current} -> {want}, restarting");
            return true;
        }
        catch (Exception ex)
        {
            NetDiagnostics.Append("Display scale not set: " + ex.GetType().Name + ": " + ex.Message);
            return false;
        }
    }

    public static (double Scale, string Source) HostScale()
    {
        foreach (var name in new[] { "FA_LAUNCHER_SCALE", "GDK_SCALE", "QT_SCALE_FACTOR" })
            if (Number(Environment.GetEnvironmentVariable(name)) is double s && s >= 1) return (s, name);
        if (LinuxSteam.Home is string home && KwinXwaylandScale(Path.Combine(home, ".config", "kwinrc")) is double k && k >= 1) return (k, "KDE Xwayland scale");
        var h = Screen.PrimaryScreen?.Bounds.Height ?? 0;
        return h >= 2000 ? (2, $"screen {h} px high") : h >= 1500 ? (1.5, $"screen {h} px high") : (1, $"screen {h} px high");
    }

    /// <summary>Scale= in the [Xwayland] group of kwinrc (KDE Plasma 6 sets it when legacy X programs scale themselves).</summary>
    public static double? KwinXwaylandScale(string path)
    {
        try
        {
            if (!File.Exists(path)) return null;
            bool inGroup = false;
            foreach (var raw in File.ReadLines(path))
            {
                var line = raw.Trim();
                if (line.StartsWith('[')) { inGroup = line == "[Xwayland]"; continue; }
                if (inGroup && line.StartsWith("Scale=", StringComparison.Ordinal)) return Number(line[6..]);
            }
        }
        catch { /* unreadable: no answer */ }
        return null;
    }

    private static double? Number(string? s) =>
        double.TryParse(s?.Trim(), NumberStyles.Float, CultureInfo.InvariantCulture, out var v) && v > 0 && v <= 4 ? v : null;
}

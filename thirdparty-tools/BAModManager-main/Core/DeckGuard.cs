using System.IO.Compression;
using System.Security.Cryptography;
using System.Text.Json;
using static BAModManager.Core.Loc;

namespace BAModManager.Core;

/// <summary>
/// Keeps vanilla decks safe (Osama, 14 November 2026). Broken Arrow keeps decks as .dek files in
/// LocalLow\SteelBalalaikaStudio\BrokenArrow\Decks and re-saves every deck it "fixes" at start. Freedom Arrow 0.9.0-dev.3+
/// moves mod decks to Decks\FreedomArrow; this is the second layer. Before each launch both folders are zipped to
/// %AppData%\(launcher)\deck-backups (newest 20 per folder, skipped when nothing changed). After a modded session any vanilla
/// deck that changed or vanished is put back from that zip, because vanilla is not running then.
/// </summary>
public static class DeckGuard
{
    public const string Vanilla = "vanilla", Mod = "mod";
    private const string ModSub = "FreedomArrow";
    private const int Keep = 20;

    public static string? DecksDir
    {
        get
        {
            var local = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            var parent = string.IsNullOrEmpty(local) ? null : Path.GetDirectoryName(local);
            if (parent == null) return null;
            var dir = Path.Combine(parent, "LocalLow", "SteelBalalaikaStudio", "BrokenArrow", "Decks");
            return Directory.Exists(dir) ? dir : null;
        }
    }

    public static string BackupDir => Path.Combine(AppSettings.FolderPath, "deck-backups");
    private static string PendingFile => Path.Combine(BackupDir, "modded-session.json");

    private static string? Folder(string side) => DecksDir is string d ? side == Mod ? Path.Combine(d, ModSub) : d : null;

    private static Dictionary<string, string> Hashes(string? dir)
    {
        var map = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        if (dir == null || !Directory.Exists(dir)) return map;
        foreach (var f in Directory.GetFiles(dir, "*.dek", SearchOption.TopDirectoryOnly))
            map[Path.GetFileName(f)] = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(f)));
        return map;
    }

    private static string Fingerprint(Dictionary<string, string> h) =>
        Convert.ToHexString(SHA256.HashData(System.Text.Encoding.UTF8.GetBytes(string.Join("\n", h.OrderBy(x => x.Key, StringComparer.OrdinalIgnoreCase).Select(x => x.Key + "=" + x.Value)))));

    /// <summary>Zips one folder's decks. Returns the newest zip that holds the current decks, or null when there are none.</summary>
    public static string? Backup(string side, Action<string> log)
    {
        var dir = Folder(side);
        var hashes = Hashes(dir);
        if (hashes.Count == 0) return null;
        Directory.CreateDirectory(BackupDir);
        var print = Fingerprint(hashes);
        var zips = Directory.GetFiles(BackupDir, side + "-*.zip").OrderByDescending(f => f, StringComparer.Ordinal).ToList();
        if (zips.Count > 0 && Path.GetFileNameWithoutExtension(zips[0]).EndsWith(print[..12], StringComparison.Ordinal)) return zips[0];
        var zip = Path.Combine(BackupDir, $"{side}-{DateTime.Now:yyyyMMdd-HHmmss}-{print[..12]}.zip");
        using (var z = ZipFile.Open(zip + ".tmp", ZipArchiveMode.Create))
            foreach (var name in hashes.Keys) z.CreateEntryFromFile(Path.Combine(dir!, name), name, CompressionLevel.Optimal);
        File.Move(zip + ".tmp", zip, true);
        foreach (var old in zips.Skip(Keep - 1)) { try { File.Delete(old); } catch { /* next time */ } }
        log(T("Deck backup ({0}): {1} decks saved to {2}", side, hashes.Count, zip));
        return zip;
    }

    private sealed record Session(string? Zip, Dictionary<string, string> Vanilla);

    /// <summary>Before PLAY or Play vanilla: finish any open check, back up both folders, and for PLAY remember the vanilla decks.</summary>
    public static string? BeforeLaunch(bool modded, Action<string> log)
    {
        string? message = null;
        try
        {
            message = AfterModdedSession(log);
            var zip = Backup(Vanilla, log);
            Backup(Mod, log);
            if (modded && DecksDir != null)
                File.WriteAllText(PendingFile, JsonSerializer.Serialize(new Session(zip, Hashes(Folder(Vanilla)))));
        }
        catch (Exception ex) { log(T("Deck backup failed: ") + ex.Message); }
        return message;
    }

    /// <summary>
    /// After a modded session (call only while the game is closed): vanilla decks that changed or vanished are restored from
    /// the backup taken at PLAY. New files are left alone. Returns a message for the player when something was restored.
    /// </summary>
    public static string? AfterModdedSession(Action<string> log)
    {
        if (!File.Exists(PendingFile)) return null;
        try
        {
            var s = JsonSerializer.Deserialize<Session>(File.ReadAllText(PendingFile));
            var dir = Folder(Vanilla);
            if (s == null || dir == null) return null;
            var now = Hashes(dir);
            var changed = s.Vanilla.Where(x => !now.TryGetValue(x.Key, out var h) || h != x.Value).Select(x => x.Key).ToList();
            if (changed.Count == 0)
            {
                log(T("Vanilla decks checked after the modded session: {0} unchanged.", s.Vanilla.Count));
                return null;
            }
            if (s.Zip == null || !File.Exists(s.Zip)) throw new FileNotFoundException(T("The deck backup from PLAY is missing."), s.Zip);
            using var z = ZipFile.OpenRead(s.Zip);
            foreach (var name in changed) z.GetEntry(name)!.ExtractToFile(Path.Combine(dir, name), true);
            var left = Hashes(dir);
            var bad = changed.Where(n => !left.TryGetValue(n, out var h) || h != s.Vanilla[n]).ToList();
            if (bad.Count > 0) throw new IOException(T("Couldn't restore: ") + string.Join(", ", bad));
            var msg = T("The modded game changed {0} vanilla decks; they were put back from the backup: {1}", changed.Count, string.Join(", ", changed));
            log(msg);
            return msg;
        }
        catch (Exception ex)
        {
            var msg = T("Couldn't check the vanilla decks: {0}\nBackups are in {1}", ex.Message, BackupDir);
            log(msg);
            return msg;
        }
        finally { try { File.Delete(PendingFile); } catch { /* checked again next time */ } }
    }

    /// <summary>Puts one backup zip back (game closed). The current decks of that folder are backed up first. Returns decks restored.</summary>
    public static int Restore(string zip, Action<string> log)
    {
        var side = Path.GetFileName(zip).StartsWith(Mod + "-", StringComparison.Ordinal) ? Mod : Vanilla;
        var dir = Folder(side) ?? throw new DirectoryNotFoundException(T("Broken Arrow's Decks folder wasn't found."));
        Directory.CreateDirectory(dir);
        Backup(side, log);
        int n = 0;
        using (var z = ZipFile.OpenRead(zip))
            foreach (var e in z.Entries.Where(e => e.Name.EndsWith(".dek", StringComparison.OrdinalIgnoreCase) && e.Name == e.FullName))
            { e.ExtractToFile(Path.Combine(dir, e.Name), true); n++; }
        log(T("Restored {0} {1} decks from {2}", n, side, zip));
        return n;
    }
}

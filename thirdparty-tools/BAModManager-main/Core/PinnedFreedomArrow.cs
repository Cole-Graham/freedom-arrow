using System.IO.Compression;
using System.Security.Cryptography;
using System.Text.Json;

namespace BAModManager.Core;

/// <summary>The dedicated playtest launcher uses the exact bundled pack, never GitHub latest.</summary>
public static class PinnedFreedomArrow
{
#if FA_DEV45
    public static bool Enabled => true;
#else
    public static bool Enabled => false;
#endif
    public const string Repo = "Cole-Graham/freedom-arrow";
    public const string Id = "freedomarrow.gameplay";
    public const string Version = "0.7.0-dev.45";
    public const string FileName = "FreedomArrow-0.7.0-dev.45.bamod";
    public const string Sha256 = "33323fc1c760acabcc87cc1e237e99251d2d2495a14c858977791b0cf7d2ab5d";
    public static string ArchivePath => Path.Combine(AppContext.BaseDirectory, FileName);

    public static void VerifyArchive(string path)
    {
        if (!File.Exists(path))
            throw new FileNotFoundException("Extract the entire Freedom Arrow dev.45 ZIP before pressing PLAY. Missing " + FileName);
        using var file = File.OpenRead(path);
        if (!Convert.ToHexString(SHA256.HashData(file)).Equals(Sha256, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("The included dev.45 package failed its checksum. Download and extract the ZIP again.");
        file.Position = 0;
        using var zip = new ZipArchive(file, ZipArchiveMode.Read);
        using var metadata = JsonDocument.Parse(zip.GetEntry("mod.json")!.Open());
        if (metadata.RootElement.GetProperty("id").GetString() != Id ||
            metadata.RootElement.GetProperty("version").GetString() != Version)
            throw new InvalidDataException("This launcher accepts only Freedom Arrow dev.45.");
    }

    // Called on the worker thread. Read-only checks cover all bundled payload files, including disabled copies.
    public static bool PayloadMatches(string gameDir, string archive, CancellationToken ct)
    {
        using var zip = ZipFile.OpenRead(archive);
        foreach (var entry in zip.Entries)
        {
            ct.ThrowIfCancellationRequested();
            var rel = entry.FullName.Replace('\\', '/');
            if (!new[] { "Mods/", "Plugins/", "UserData/", "UserLibs/" }.Any(rel.StartsWith) || rel.EndsWith('/')) continue;
            var path = PathUtil.ToFull(gameDir, rel);
            if (!File.Exists(path)) path += PathUtil.DisabledSuffix;
            if (!File.Exists(path) || new FileInfo(path).Length != entry.Length) return false;
            using var expected = entry.Open();
            using var actual = File.OpenRead(path);
            if (!SHA256.HashData(expected).SequenceEqual(SHA256.HashData(actual))) return false;
        }
        return true;
    }

    public static void Ensure(LauncherService launcher, string gameDir, Action<string> log, CancellationToken ct)
    {
        VerifyArchive(ArchivePath);
        var pack = launcher.FindPack(Manifest.Load(gameDir));
        if (pack?.Info?.Version != Version || !PayloadMatches(gameDir, ArchivePath, ct))
        {
            ct.ThrowIfCancellationRequested();
            log("Installing the included Freedom Arrow dev.45 package.");
            if (!launcher.InstallPackFile(gameDir, ArchivePath, log))
                throw new InvalidDataException("The included dev.45 package was not accepted.");
        }
        var manifest = Manifest.Load(gameDir);
        pack = launcher.FindPack(manifest) ?? throw new InvalidDataException("dev.45 installation record is missing.");
        launcher.Activate(gameDir, manifest, pack, log);
        manifest.Save(gameDir);
        if (pack.Info?.Version != Version || !PayloadMatches(gameDir, ArchivePath, ct))
            throw new InvalidDataException("dev.45 payload verification failed. The game will not start.");
        log("Verified Freedom Arrow 0.7.0-dev.45. Gameplay updates are locked in this launcher.");
    }
}

using System.IO.Compression;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Nodes;

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
    public const string AssetsId = "freedomarrow.assets.live";
    public const string AssetsVersion = "0.1.14";
    public const string AssetsFileName = "FreedomArrow-Assets-0.1.14.bamod";
    public const string AssetsSha256 = "1683bae9270a1d19e43cba662c93f92a5002635c1d61841191762701d25ac153";
    public static string AssetsArchivePath => Path.Combine(AppContext.BaseDirectory, AssetsFileName);

    public static void VerifyAssetsArchive()
    {
        using var file = File.OpenRead(AssetsArchivePath);
        if (!Convert.ToHexString(SHA256.HashData(file)).Equals(AssetsSha256, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("The included Models + Music/Voices package failed its checksum. Extract the full ZIP again.");
        file.Position = 0;
        using var zip = new ZipArchive(file, ZipArchiveMode.Read);
        using var metadata = JsonDocument.Parse(zip.GetEntry("mod.json")!.Open());
        if (metadata.RootElement.GetProperty("id").GetString() != AssetsId ||
            metadata.RootElement.GetProperty("version").GetString() != AssetsVersion)
            throw new InvalidDataException("The included Models + Music/Voices package has the wrong identity.");
    }

    private static bool SameContent(PlannedFile file, string path)
    {
        using var expected = file.Open();
        using var actual = File.OpenRead(path);
        return SHA256.HashData(expected).SequenceEqual(SHA256.HashData(actual));
    }

    // Install through the upstream package planner. UserData files already on disk are retained so
    // approved skins, music replacements and preferences survive. Missing content is installed atomically.
    private static void EnsureAssets(string gameDir, Action<string> log, CancellationToken ct)
    {
        var mods = new ModService(new ManagerConfig());
        using var plan = mods.BuildPlan(AssetsArchivePath, _ => null)
            ?? throw new InvalidDataException("The included asset package is empty.");
        var manifest = Manifest.Load(gameDir);
        var pack = manifest.Packages.FirstOrDefault(p => p.Info?.Id == AssetsId);
        bool newer = pack?.Info?.Version != null && ModVersion.Compare(pack.Info.Version, AssetsVersion) > 0;
        int installed = 0, retained = 0;
        foreach (var file in plan.Files)
        {
            ct.ThrowIfCancellationRequested();
            var path = PathUtil.ToFull(gameDir, file.TargetRel);
            if (!File.Exists(path) && File.Exists(path + PathUtil.DisabledSuffix))
                File.Move(path + PathUtil.DisabledSuffix, path);
            bool exists = File.Exists(path);
            if (exists && file.TargetRel.Replace('\\', '/') == "UserData/FAModels/models.json")
            {
                // An older asset install can lack newly required model bindings. Add missing units,
                // retaining each existing model entry in full, including approved offsets and skins.
                var current = JsonNode.Parse(File.ReadAllText(path)) as JsonObject
                    ?? throw new InvalidDataException("Existing models.json is not a model registry.");
                using var src = file.Open();
                var baseline = JsonNode.Parse(src)!.AsObject();
                bool changed = false;
                foreach (var pair in baseline)
                    if (!current.ContainsKey(pair.Key)) { current[pair.Key] = pair.Value?.DeepClone(); changed = true; }
                if (changed)
                {
                    var tempRegistry = path + ".fa-install-" + Guid.NewGuid().ToString("N");
                    try
                    {
                        File.WriteAllText(tempRegistry, current.ToJsonString(new JsonSerializerOptions { WriteIndented = true }));
                        File.Move(tempRegistry, path, overwrite: true);
                    }
                    finally { if (File.Exists(tempRegistry)) File.Delete(tempRegistry); }
                }
            }
            bool userData = file.TargetRel.Replace('\\', '/').StartsWith("UserData/", StringComparison.OrdinalIgnoreCase);
            if (exists && (userData || newer || SameContent(file, path))) { retained++; continue; }
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            var temp = path + ".fa-install-" + Guid.NewGuid().ToString("N");
            try
            {
                using (var src = file.Open())
                using (var dst = new FileStream(temp, FileMode.CreateNew, FileAccess.Write, FileShare.None))
                    src.CopyTo(dst);
                if (!SameContent(file, temp)) throw new InvalidDataException("Asset write verification failed: " + file.TargetRel);
                ct.ThrowIfCancellationRequested();
                File.Move(temp, path, overwrite: exists);
                installed++;
            }
            finally { if (File.Exists(temp)) File.Delete(temp); }
        }
        if (pack == null)
        {
            pack = new InstalledPackage { Name = plan.PackageName, Source = AssetsArchivePath, Info = plan.Info, InstalledAt = DateTime.Now };
            manifest.Packages.Add(pack);
        }
        else if (!newer) pack.Info = plan.Info;
        pack.Files = pack.Files.Concat(plan.Files.Select(f => f.TargetRel)).Distinct(StringComparer.OrdinalIgnoreCase).ToList();
        // Also enable extra files belonging to an already installed newer asset pack.
        var entry = mods.Scan(gameDir, manifest).FirstOrDefault(e => e.Package == pack);
        if (entry != null && !entry.Enabled) mods.SetEnabled(gameDir, entry, true, log);
        pack.Enabled = true;
        manifest.Save(gameDir);
        foreach (var file in plan.Files)
            if (!File.Exists(PathUtil.ToFull(gameDir, file.TargetRel)))
                throw new InvalidDataException("An asset file is missing: " + file.TargetRel);
        log($"Models + Music/Voices ready: {installed} installed/repaired; {retained} existing files retained.");
    }


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
        VerifyAssetsArchive();
        EnsureAssets(gameDir, log, ct);
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
        log("Verified Freedom Arrow 0.7.0-dev.45 with Models + Music/Voices. Gameplay updates are locked.");
    }
}

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
    public static string Version => HostedDistribution.Active.Gameplay.Version;
    public static string FileName => HostedDistribution.Active.Gameplay.Filename;
    public static string Sha256 => HostedDistribution.Active.Gameplay.Sha256;
    public static string ArchivePath => HostedDistribution.ArchivePath(HostedDistribution.Active.Gameplay);
    public const string AssetsId = "freedomarrow.assets.live";
    public static string AssetsVersion => HostedDistribution.Active.Assets.Version;
    public static string AssetsFileName => HostedDistribution.Active.Assets.Filename;
    public static string AssetsSha256 => HostedDistribution.Active.Assets.Sha256;
    public static string AssetsArchivePath => HostedDistribution.ArchivePath(HostedDistribution.Active.Assets);

    // A manifest with an Assets file list (launcher 1.1.5+) installs file by file; otherwise the full package is used, as before.
    public static string? AssetsIndexPath => HostedDistribution.IndexPath(HostedDistribution.Active.Assets);
    public static void VerifyAssets()
    {
        if (HostedDistribution.Active.Assets.Index == null) { VerifyAssetsArchive(); return; }
        AssetsIndexInstall.Load(AssetsIndexPath ?? throw new FileNotFoundException("The Models + Music/Voices file list was not downloaded."), HostedDistribution.Active.Assets);
    }

    // Game-relative files of the Models + Music/Voices package (Mods/FAModels.dll, Mods/FAMusic.dll ...): kept in Mods by ForeignMods.Park.
    private static IEnumerable<string> AssetsGamePaths()
    {
        if (HostedDistribution.Active.Assets.Index != null)
            return AssetsIndexInstall.Load(AssetsIndexPath!, HostedDistribution.Active.Assets).Files.Select(f => f.Path);
        using var zip = ZipFile.OpenRead(AssetsArchivePath);
        return zip.Entries.Select(e => e.FullName.Replace('\\', '/')).ToList();
    }

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
    private static readonly HashSet<string> Preferences = new(StringComparer.OrdinalIgnoreCase)
        { "UserData/FAMusic/voice-presets.txt", "UserData/FAMusic/music-history.txt" };

    private static void EnsureAssets(string gameDir, Action<string> log, CancellationToken ct, IProgress<LaunchProgress>? progress = null)
    {
        if (HostedDistribution.Active.Assets.Index != null)
        {
            AssetsIndexInstall.Ensure(gameDir, AssetsIndexPath!, HostedDistribution.Active.Assets, Preferences, log, ct, progress);
            return;
        }
        var mods = new ModService(new ManagerConfig());
        using var plan = mods.BuildPlan(AssetsArchivePath, _ => null)
            ?? throw new InvalidDataException("The included asset package is empty.");
        var manifest = Manifest.Load(gameDir);
        var pack = manifest.Packages.FirstOrDefault(p => p.Info?.Id == AssetsId);
        int installed = 0, retained = 0;
        foreach (var file in plan.Files)
        {
            ct.ThrowIfCancellationRequested();
            var path = PathUtil.ToFull(gameDir, file.TargetRel);
            if (!File.Exists(path) && File.Exists(path + PathUtil.DisabledSuffix))
                File.Move(path + PathUtil.DisabledSuffix, path);
            bool exists = File.Exists(path);
            // Lateralus 14 Nov 2026: keeping every existing UserData file meant model, texture and infantry updates never
            // arrived (0.9.0-dev.2 refused to load: old UserData/FAModels/infantry-bodies.json). Same rule as the PC
            // installer (switch.py): the package's files win; only the player's voice and music preferences are kept.
            bool preference = Preferences.Contains(file.TargetRel.Replace('\\', '/'));
            if (exists && (preference || SameContent(file, path))) { retained++; continue; }
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
        else pack.Info = plan.Info;
        pack.Files = pack.Files.Concat(plan.Files.Select(f => f.TargetRel)).Distinct(StringComparer.OrdinalIgnoreCase).ToList();
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
            throw new InvalidDataException("The gameplay package does not match the active manifest.");
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

    public static void Ensure(LauncherService launcher, string gameDir, Action<string> log, CancellationToken ct, IProgress<LaunchProgress>? progress = null)
    {
        progress?.Report(new LaunchProgress(Loc.T("Checking mod files…"), Stage: LaunchStage.Mod));
        VerifyArchive(ArchivePath);
        VerifyAssets();
        // 1.1.14: switch Freedom Arrow's DLLs back on if "Play vanilla" switched them off (the payload check accepts .disabled files).
        ForeignMods.EnableOwn(gameDir, (launcher.FindPack(Manifest.Load(gameDir))?.Files ?? new List<string>()).Concat(AssetsGamePaths()), log);
        var pack = launcher.FindPack(Manifest.Load(gameDir));
        if (pack?.Info?.Version != Version || !PayloadMatches(gameDir, ArchivePath, ct))
        {
            ct.ThrowIfCancellationRequested();
            progress?.Report(new LaunchProgress(Loc.T("Installing Freedom Arrow {0}…", Version), Stage: LaunchStage.Mod));
            log("Installing Freedom Arrow " + Version + ".");
            if (!launcher.InstallPackFile(gameDir, ArchivePath, log))
                throw new InvalidDataException("The included dev.45 package was not accepted.");
        }
        var manifest = Manifest.Load(gameDir);
        pack = launcher.FindPack(manifest) ?? throw new InvalidDataException("dev.45 installation record is missing.");
        launcher.Activate(gameDir, manifest, pack, log);
        manifest.Save(gameDir);
        // 1.1.12: Models + Music/Voices after the gameplay package. Replacing a gameplay package that was installed from a complete package
        // (PC installer, older launchers) removes that package's model and music files; checked first, they were gone when the game started
        // (measured on Vengeance 20 Nov 2026: 0.9.2-dev.7 complete -> 0.9.2 left no UserData/FAModels, FAMusic or FAAssets).
        EnsureAssets(gameDir, log, ct, progress);
        manifest = Manifest.Load(gameDir);
        pack = launcher.FindPack(manifest) ?? throw new InvalidDataException("dev.45 installation record is missing.");
        progress?.Report(new LaunchProgress(Loc.T("Checking mod files…"), Stage: LaunchStage.Verify));
        if (pack.Info?.Version != Version || !PayloadMatches(gameDir, ArchivePath, ct))
            throw new InvalidDataException("dev.45 payload verification failed. The game will not start.");
        log("Verified Freedom Arrow " + Version + " with Models + Music/Voices.");
        ForeignMods.Park(gameDir, pack.Files.Concat(AssetsGamePaths()), log);   // 1.1.6: other mods' DLLs (ActualArrow etc.) wait outside Mods during a Freedom Arrow game
    }
}

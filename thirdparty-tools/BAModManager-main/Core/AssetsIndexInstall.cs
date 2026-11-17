using System.IO.Compression;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace BAModManager.Core;

public sealed record AssetsIndexFile(string Path, long Size, string Sha256);
public sealed record AssetsIndex(int Schema, string Id, string Version, string Package,
    [property: JsonPropertyName("files_base")] string FilesBase, [property: JsonPropertyName("mod_json")] string ModJson, List<AssetsIndexFile> Files);

/// <summary>
/// Models + Music/Voices from a per-file list (Lateralus 17 Nov 2026, thread 1571554273639006392: "only changed and new models have to be
/// downloaded, instead of the entire assets pack"). The list (tools/distribution/publish_assets_index.py) names every installed file with its
/// size and SHA-256; each file is on R2 once, gzipped, as files_base + sha256 + ".gz". Files already on disk with the right content are kept;
/// only missing or changed files are downloaded (8 at a time), checked and moved into place. A file that the previous list installed and the
/// new list no longer has is removed only if it is unchanged. Same keep rules as the full-package install: the player's voice and music
/// preferences, and everything when a newer Assets version is already installed.
/// </summary>
public static class AssetsIndexInstall
{
    private static readonly string[] Roots = { "Mods/", "Plugins/", "UserData/", "UserLibs/" };
    private static readonly JsonSerializerOptions Json = new() { PropertyNameCaseInsensitive = true };
    /// <summary>The launcher's download client; tests replace it.</summary>
    public static HttpClient Client { get; set; } = HostedDistribution.Client;
    private sealed record Seen(long Size, long Ticks, string Sha256);
    private sealed class State
    {
        public string GameDir { get; set; } = "";
        public string Version { get; set; } = "";
        public Dictionary<string, AssetsIndexFile> Installed { get; set; } = new(StringComparer.OrdinalIgnoreCase);
        public Dictionary<string, Seen> Hashes { get; set; } = new(StringComparer.OrdinalIgnoreCase);
    }
    private static string StateFile => Path.Combine(HostedDistribution.CacheRoot, "assets-state.json");

    public static AssetsIndex Load(string file, DistributionPackage p)
    {
        var index = JsonSerializer.Deserialize<AssetsIndex>(File.ReadAllText(file), Json) ?? throw new InvalidDataException("Empty Assets file list.");
        if (index.Schema != 1 || index.Id != p.Id || index.Version != p.Version || index.Files == null || index.Files.Count == 0 ||
            !Uri.TryCreate(index.FilesBase, UriKind.Absolute, out var b) || b.Scheme != "https" || !index.FilesBase.EndsWith('/'))
            throw new InvalidDataException("The Assets file list does not match the version manifest.");
        var info = ModInfo.Parse(index.ModJson);
        if (info.Id != p.Id || info.Version != p.Version) throw new InvalidDataException("The Assets file list has the wrong identity.");
        foreach (var f in index.Files)
            if (f.Size < 0 || f.Sha256 == null || f.Sha256.Length != 64 || !f.Sha256.All(Uri.IsHexDigit) ||
                PathUtil.NormalizeRel(f.Path) != f.Path || !Roots.Any(r => f.Path.StartsWith(r, StringComparison.Ordinal)))
                throw new InvalidDataException("Invalid entry in the Assets file list: " + f.Path);
        if (index.Files.Select(f => f.Path).Distinct(StringComparer.OrdinalIgnoreCase).Count() != index.Files.Count)
            throw new InvalidDataException("The Assets file list names a file twice.");
        return index;
    }

    private static string Hash(string path)
    {
        using var s = File.OpenRead(path);
        return Convert.ToHexString(SHA256.HashData(s)).ToLowerInvariant();
    }
    // Hash once per file version: a file with the size and write time seen before keeps its recorded hash.
    private static string HashCached(State state, string rel, string path)
    {
        var fi = new FileInfo(path);
        if (state.Hashes.TryGetValue(rel, out var s) && s.Size == fi.Length && s.Ticks == fi.LastWriteTimeUtc.Ticks) return s.Sha256;
        var sha = Hash(path);
        fi.Refresh();
        lock (state) state.Hashes[rel] = new Seen(fi.Length, fi.LastWriteTimeUtc.Ticks, sha);
        return sha;
    }

    private static State LoadState(string gameDir)
    {
        try
        {
            var s = JsonSerializer.Deserialize<State>(File.ReadAllText(StateFile), Json);
            if (s != null && string.Equals(s.GameDir, Path.GetFullPath(gameDir), StringComparison.OrdinalIgnoreCase))
                return new State { GameDir = s.GameDir, Version = s.Version,
                    Installed = new(s.Installed, StringComparer.OrdinalIgnoreCase), Hashes = new(s.Hashes, StringComparer.OrdinalIgnoreCase) };
        }
        catch (Exception ex) when (ex is IOException or JsonException or UnauthorizedAccessException) { }
        return new State { GameDir = Path.GetFullPath(gameDir) };
    }
    private static void SaveState(State s)
    {
        Directory.CreateDirectory(HostedDistribution.CacheRoot);
        File.WriteAllText(StateFile + ".tmp", JsonSerializer.Serialize(s));
        File.Move(StateFile + ".tmp", StateFile, true);
    }

    private static async Task DownloadAsync(AssetsIndex index, AssetsIndexFile f, string path, CancellationToken ct)
    {
        var url = index.FilesBase + f.Sha256.ToLowerInvariant() + ".gz";
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        var temp = path + ".fa-install-" + Guid.NewGuid().ToString("N");
        for (int attempt = 0; ; attempt++)
        {
            try
            {
                using var req = new HttpRequestMessage(HttpMethod.Get, url);
                req.Headers.UserAgent.ParseAdd("FreedomArrowLauncher/3");
                using var r = await Client.SendAsync(req, HttpCompletionOption.ResponseHeadersRead, ct);
                r.EnsureSuccessStatusCode();
                using var sha = SHA256.Create();
                await using (var src = new GZipStream(await r.Content.ReadAsStreamAsync(ct), CompressionMode.Decompress))
                await using (var dst = new FileStream(temp, FileMode.CreateNew, FileAccess.Write, FileShare.None, 131072, true))
                {
                    var buffer = new byte[131072]; long done = 0; int read;
                    while ((read = await src.ReadAsync(buffer, ct)) > 0)
                    {
                        done += read;
                        if (done > f.Size) throw new InvalidDataException("Asset file is larger than its list entry: " + f.Path);
                        sha.TransformBlock(buffer, 0, read, null, 0);
                        await dst.WriteAsync(buffer.AsMemory(0, read), ct);
                    }
                    sha.TransformFinalBlock(Array.Empty<byte>(), 0, 0);
                    if (done != f.Size || !Convert.ToHexString(sha.Hash!).Equals(f.Sha256, StringComparison.OrdinalIgnoreCase))
                        throw new InvalidDataException("Asset file checksum failed: " + f.Path);
                }
                File.Move(temp, path, overwrite: true);
                return;
            }
            catch (Exception ex) when ((ex is HttpRequestException || ex is IOException && ex is not InvalidDataException) && !ct.IsCancellationRequested && attempt < 2)
            { await Task.Delay(TimeSpan.FromSeconds(attempt + 1), ct); }
            finally { if (File.Exists(temp)) File.Delete(temp); }
        }
    }

    public static void Ensure(string gameDir, string indexFile, DistributionPackage p, IReadOnlySet<string> preferences, Action<string> log, CancellationToken ct)
    {
        var index = Load(indexFile, p);
        var info = ModInfo.Parse(index.ModJson);
        var mods = new ModService(new ManagerConfig());
        var manifest = Manifest.Load(gameDir);
        var pack = manifest.Packages.FirstOrDefault(x => x.Info?.Id == p.Id);
        bool newer = pack?.Info?.Version != null && ModVersion.Compare(pack.Info.Version, p.Version) > 0;
        var state = LoadState(gameDir);
        var need = new List<(AssetsIndexFile File, string Path)>();
        int retained = 0;
        foreach (var f in index.Files)
        {
            ct.ThrowIfCancellationRequested();
            var path = PathUtil.ToFull(gameDir, f.Path);
            if (!File.Exists(path) && File.Exists(path + PathUtil.DisabledSuffix))
                File.Move(path + PathUtil.DisabledSuffix, path);
            bool exists = File.Exists(path);
            if (exists && (preferences.Contains(f.Path) || newer ||
                new FileInfo(path).Length == f.Size && HashCached(state, f.Path, path).Equals(f.Sha256, StringComparison.OrdinalIgnoreCase)))
            { retained++; continue; }
            need.Add((f, path));
        }
        if (need.Count > 0)
        {
            // Identical content at several paths (many music tracks) is downloaded once and copied.
            var groups = need.GroupBy(n => n.File.Sha256, StringComparer.OrdinalIgnoreCase).ToList();
            long total = groups.Sum(g => g.First().File.Size), done = 0; int files = 0; var last = DateTime.MinValue;
            log($"Models + Music/Voices {p.Version}: downloading {need.Count} changed or missing files ({groups.Count} different, {total / 1048576.0:0} MB); {retained} files already up to date.");
            Parallel.ForEachAsync(groups, new ParallelOptions { MaxDegreeOfParallelism = 8, CancellationToken = ct }, async (g, token) =>
            {
                var first = g.First();
                await DownloadAsync(index, first.File, first.Path, token);
                HashCached(state, first.File.Path, first.Path);
                foreach (var other in g.Skip(1))
                {
                    Directory.CreateDirectory(Path.GetDirectoryName(other.Path)!);
                    var temp = other.Path + ".fa-install-" + Guid.NewGuid().ToString("N");
                    try { File.Copy(first.Path, temp); File.Move(temp, other.Path, overwrite: true); }
                    finally { if (File.Exists(temp)) File.Delete(temp); }
                    HashCached(state, other.File.Path, other.Path);
                }
                var d = Interlocked.Add(ref done, first.File.Size); var c = Interlocked.Increment(ref files);
                lock (need)
                    if ((DateTime.UtcNow - last).TotalSeconds >= 2 || c == groups.Count)
                    { last = DateTime.UtcNow; log($"Downloaded {c}/{groups.Count} files ({d / 1048576.0:0}/{total / 1048576.0:0} MB)."); }
            }).GetAwaiter().GetResult();
        }
        // Files the previous list installed and this list dropped: removed only if still exactly as installed.
        var keep = new HashSet<string>(index.Files.Select(f => f.Path), StringComparer.OrdinalIgnoreCase);
        var removed = new List<string>();
        if (!newer)
            foreach (var old in state.Installed.Values.Where(o => !keep.Contains(o.Path)))
            {
                var path = PathUtil.ToFull(gameDir, old.Path);
                if (File.Exists(path) && HashCached(state, old.Path, path).Equals(old.Sha256, StringComparison.OrdinalIgnoreCase))
                { File.Delete(path); removed.Add(old.Path); state.Hashes.Remove(old.Path); }
            }
        if (pack == null)
        {
            pack = new InstalledPackage { Name = info.Name ?? Path.GetFileNameWithoutExtension(index.Package), Source = p.Index!.Url, Info = info, InstalledAt = DateTime.Now };
            manifest.Packages.Add(pack);
        }
        else if (!newer) pack.Info = info;
        pack.Files = pack.Files.Concat(index.Files.Select(f => f.Path)).Except(removed, StringComparer.OrdinalIgnoreCase)
            .Distinct(StringComparer.OrdinalIgnoreCase).ToList();
        var entry = mods.Scan(gameDir, manifest).FirstOrDefault(e => e.Package == pack);
        if (entry != null && !entry.Enabled) mods.SetEnabled(gameDir, entry, true, log);
        pack.Enabled = true;
        manifest.Save(gameDir);
        foreach (var f in index.Files)
            if (!File.Exists(PathUtil.ToFull(gameDir, f.Path)))
                throw new InvalidDataException("An asset file is missing: " + f.Path);
        if (!newer) { state.Version = p.Version; state.Installed = index.Files.ToDictionary(f => f.Path, StringComparer.OrdinalIgnoreCase); }
        SaveState(state);
        log($"Models + Music/Voices {p.Version} ready: {need.Count} downloaded; {retained} existing files kept; {removed.Count} old files removed.");
    }
}

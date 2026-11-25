using System.IO.Compression;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Serialization;
using static BAModManager.Core.Loc;

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

    /// <summary>The cached file list failed its checksum and was deleted; the next PrepareAsync downloads it again.</summary>
    public sealed class DamagedListException(string message) : IOException(message);

    public static AssetsIndex Load(string file, DistributionPackage p)
    {
        // 1.1.13 (Beep 20 Nov 2026, Linux: "I have to delete the relevant file every time I launch the game"; 0x00 bytes in the list at
        // byte 1,156,664): parse exactly the bytes that pass the signed-list checksum. A damaged copy is deleted so it is downloaded again.
        var bytes = File.ReadAllBytes(file);
        if (p.Index != null && (bytes.LongLength != p.Index.Size ||
            !Convert.ToHexString(SHA256.HashData(bytes)).Equals(p.Index.Sha256, StringComparison.OrdinalIgnoreCase)))
        {
            try { File.Delete(file); } catch (IOException) { /* in use */ }
            throw new DamagedListException("The Models + Music/Voices file list on disk was damaged; it was removed and is downloaded again.");
        }
        var index = JsonSerializer.Deserialize<AssetsIndex>(bytes, Json) ?? throw new InvalidDataException("Empty Assets file list.");
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

    // 1.1.11 (Osama 20 Nov 2026, Chinese players "stuck" on PLAY): a body read that gets no data for StallTimeout is retried.
    // HttpClient.Timeout does not cover body reads after ResponseHeadersRead, so a stalled connection could wait forever.
    internal static TimeSpan StallTimeout = TimeSpan.FromSeconds(60);
    private const int Attempts = 6;

    private static async Task DownloadAsync(AssetsIndex index, AssetsIndexFile f, string path, CancellationToken ct, Action<long>? onBytes = null,
        Action<int, Exception>? onRetry = null)
    {
        var url = index.FilesBase + f.Sha256.ToLowerInvariant() + ".gz";
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        var temp = path + ".fa-install-" + Guid.NewGuid().ToString("N");
        long done = 0;
        for (int attempt = 0; ; attempt++)
        {
            if (done > 0) { onBytes?.Invoke(-done); done = 0; }   // a retry starts the file again
            try
            {
                using var req = new HttpRequestMessage(HttpMethod.Get, url);
                req.Headers.UserAgent.ParseAdd("FreedomArrowLauncher/3");
                using var stall = CancellationTokenSource.CreateLinkedTokenSource(ct);
                stall.CancelAfter(StallTimeout);
                using var r = await Client.SendAsync(req, HttpCompletionOption.ResponseHeadersRead, stall.Token);
                r.EnsureSuccessStatusCode();
                using var sha = SHA256.Create();
                await using (var src = new GZipStream(await r.Content.ReadAsStreamAsync(stall.Token), CompressionMode.Decompress))
                await using (var dst = new FileStream(temp, FileMode.CreateNew, FileAccess.Write, FileShare.None, 131072, true))
                {
                    var buffer = new byte[131072]; int read;
                    while (true)
                    {
                        stall.CancelAfter(StallTimeout);   // restart the stall clock for every read
                        try { read = await src.ReadAsync(buffer, stall.Token); }
                        catch (OperationCanceledException) when (!ct.IsCancellationRequested)
                        { throw new IOException("No data for " + StallTimeout.TotalSeconds + " s: " + f.Path); }
                        if (read <= 0) break;
                        done += read; onBytes?.Invoke(read);
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
            catch (Exception ex) when ((ex is HttpRequestException || ex is IOException && ex is not InvalidDataException ||
                                        ex is OperationCanceledException) && !ct.IsCancellationRequested && attempt < Attempts - 1)
            { onRetry?.Invoke(attempt, ex); await Task.Delay(TimeSpan.FromSeconds(Math.Min(2 * (attempt + 1), 10)), ct); }
            finally { if (File.Exists(temp)) File.Delete(temp); }
        }
    }

    public static void Ensure(string gameDir, string indexFile, DistributionPackage p, IReadOnlySet<string> preferences, Action<string> log, CancellationToken ct,
        IProgress<LaunchProgress>? progress = null)
    {
        var index = Load(indexFile, p);
        var info = ModInfo.Parse(index.ModJson);
        var mods = new ModService(new ManagerConfig());
        var manifest = Manifest.Load(gameDir);
        var pack = manifest.Packages.FirstOrDefault(x => x.Info?.Id == p.Id);
        // Dev launcher: the picked build's exact files, also when an older version than the installed one was picked.
        bool newer = !HostedDistribution.DevChannel && pack?.Info?.Version != null && ModVersion.Compare(pack.Info.Version, p.Version) > 0;
        var state = LoadState(gameDir);
        var need = new List<(AssetsIndexFile File, string Path)>();
        int retained = 0, checkedFiles = 0; var shown = DateTime.MinValue;
        foreach (var f in index.Files)
        {
            ct.ThrowIfCancellationRequested();
            if (progress != null && (DateTime.UtcNow - shown).TotalMilliseconds >= 250)
            {
                shown = DateTime.UtcNow;
                progress.Report(new LaunchProgress(T("Checking models and music… {0} / {1} files", checkedFiles, index.Files.Count),
                    (double)checkedFiles / Math.Max(1, index.Files.Count), LaunchStage.Assets));
            }
            checkedFiles++;
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
            long bytes = 0; var reported = DateTime.MinValue;
            void Show()
            {
                var b = Math.Max(0, Interlocked.Read(ref bytes));
                progress?.Report(new LaunchProgress(T("Downloading models and music… {0} / {1} files", Interlocked.CompareExchange(ref files, 0, 0), groups.Count),
                    Math.Min(1.0, (double)b / Math.Max(1, total)), LaunchStage.Assets, b, total));
            }
            void OnBytes(long n)
            {
                Interlocked.Add(ref bytes, n);
                if (progress == null) return;
                lock (need) { if ((DateTime.UtcNow - reported).TotalMilliseconds < 250) return; reported = DateTime.UtcNow; }
                Show();
            }
            Show();
            Parallel.ForEachAsync(groups, new ParallelOptions { MaxDegreeOfParallelism = 8, CancellationToken = ct }, async (g, token) =>
            {
                var first = g.First();
                await DownloadAsync(index, first.File, first.Path, token, OnBytes, (attempt, ex) => progress?.Report(new LaunchProgress(
                    T("Downloading models and music… {0} / {1} files", Interlocked.CompareExchange(ref files, 0, 0), groups.Count),
                    Math.Min(1.0, (double)Math.Max(0, Interlocked.Read(ref bytes)) / Math.Max(1, total)), LaunchStage.Assets, Math.Max(0, Interlocked.Read(ref bytes)), total,
                    T("A file download was interrupted ({0}). Trying again ({1} of {2})…", ex.Message, attempt + 2, Attempts))));
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
            Show();   // the throttled reports can skip the last one
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

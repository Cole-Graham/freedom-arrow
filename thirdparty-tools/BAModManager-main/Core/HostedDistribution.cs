using System.Net;
using System.Net.Http.Headers;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;

namespace BAModManager.Core;

public sealed record DistributionPackage(string Id, string Version, string Filename, string Url, long Size, string Sha256, DistributionIndex? Index = null);
/// <summary>Per-file Assets list (Lateralus 17 Nov 2026): launchers from 1.1.5 download only missing or changed files. Older launchers ignore it.</summary>
public sealed record DistributionIndex(string Url, long Size, string Sha256);
public sealed record DistributionRelease(string Version, DistributionPackage Gameplay, DistributionPackage Assets);
/// <summary>1.1.9 (Lateralus 19 Nov 2026): the launcher replaces itself with this exe when its version is newer than the running one.</summary>
public sealed record LauncherRelease(string Version, string Url, long Size, string Sha256);
/// <summary>1.1.9: the MelonLoader zip the Freedom Arrow builds are made for, checked by SHA-256 before it is installed.</summary>
public sealed record MelonLoaderRelease(string Tag, string Asset, string Url, long Size, string Sha256);
/// <summary>Serial: signing time; a launcher never accepts a list older than the one it has already accepted.</summary>
public sealed record DistributionManifest(int Schema, string Channel, string Current, [property: JsonPropertyName("locked_version")] string? LockedVersion, List<DistributionRelease> Releases,
    long Serial = 0, LauncherRelease? Launcher = null, MelonLoaderRelease? MelonLoader = null);

/// <summary>Public HTTPS manifest, verified atomic package cache and Drive confirmation handling.</summary>
public static class HostedDistribution
{
    // 1.1.7 (Osama 19 Nov 2026, Chinese playtesters: "The mod launcher is easy to use but totally broke in China, due to GFW"): Google Drive is
    // blocked in mainland China, and the manifest was the one file still read from Drive (packages already come from freedomarrow.app, R2).
    // ba-publish-manifest writes the same manifest to both places; the R2 copy is read first, Drive only if R2 does not answer.
    // 1.1.9 (Lateralus 19 Nov 2026): only the signed list is read (SignedManifest). The unsigned live.json and its Drive copy stay for
    // launchers up to 1.1.8; this launcher no longer reads them.
    private static readonly HttpClient Http = new() { Timeout = TimeSpan.FromMinutes(20) };
    private static readonly JsonSerializerOptions Json = new() { PropertyNameCaseInsensitive = true, PropertyNamingPolicy = JsonNamingPolicy.CamelCase, WriteIndented = true };
    public static DistributionRelease Active { get; private set; } = new("0.7.0-dev.45",
        new("freedomarrow.gameplay", "0.7.0-dev.45", "FreedomArrow-0.7.0-dev.45.bamod", "https://drive.google.com/uc?export=download&id=1Ks7wj3aT5WPL0vA8RH9tg0PtApi8wuQK",121358977,"33323fc1c760acabcc87cc1e237e99251d2d2495a14c858977791b0cf7d2ab5d"),
        new("freedomarrow.assets.live", "0.1.14", "FreedomArrow-Assets-0.1.14.bamod", "https://drive.google.com/uc?export=download&id=1wTorxKwQLwPmAUFYVRw8sh4NFqLJunC_",1219887422,"1683bae9270a1d19e43cba662c93f92a5002635c1d61841191762701d25ac153"));
    public static string CacheRoot => Path.Combine(AppSettings.FolderPath,"downloads");
    private static string CacheFile(DistributionPackage p) => Path.Combine(CacheRoot,p.Sha256.ToLowerInvariant()+"-"+p.Filename);
    public static string ArchivePath(DistributionPackage p)
    {
        var cached=CacheFile(p);
        return File.Exists(cached)?cached:Path.Combine(AppContext.BaseDirectory,p.Filename);
    }

    public static DistributionManifest Parse(string text)
    {
        var m=JsonSerializer.Deserialize<DistributionManifest>(text,Json) ?? throw new InvalidDataException("Empty version manifest.");
        if(m.Schema!=1 || m.Channel!="live" || m.Releases==null || m.Releases.Count==0 || m.Releases.Count>20 || m.Releases.Select(r=>r.Version).Distinct().Count()!=m.Releases.Count)
            throw new InvalidDataException("Unsupported or ambiguous version manifest.");
        foreach(var r in m.Releases)
        {
            Validate(r.Gameplay,"freedomarrow.gameplay");Validate(r.Assets,"freedomarrow.assets.live");
            if(r.Version!=r.Gameplay.Version)throw new InvalidDataException("Gameplay version does not match its release.");
        }
        if(!m.Releases.Any(r=>r.Version==m.Current) || !m.Releases.Any(r=>r.Version==(m.LockedVersion??m.Current)))
            throw new InvalidDataException("The current or locked release is missing.");
        if(m.Launcher is {} l && (!System.Version.TryParse(l.Version,out _) || !Hosted(l.Url) || l.Size<=0 || l.Size>MaxLauncherSize || !Sha(l.Sha256)))
            throw new InvalidDataException("Invalid launcher in version manifest.");
        if(m.MelonLoader is {} ml && (string.IsNullOrWhiteSpace(ml.Tag) || string.IsNullOrWhiteSpace(ml.Asset) || !Hosted(ml.Url) || ml.Size<=0 || ml.Size>MaxLauncherSize || !Sha(ml.Sha256)))
            throw new InvalidDataException("Invalid MelonLoader in version manifest.");
        return m;
    }
    private static void Validate(DistributionPackage p,string id)
    {
        if(p==null || p.Id!=id || string.IsNullOrWhiteSpace(p.Version) || p.Size<=0 || !Regex.IsMatch(p.Sha256??"","^[a-fA-F0-9]{64}$") ||
            string.IsNullOrWhiteSpace(p.Filename) || p.Filename!=Path.GetFileName(p.Filename) || p.Filename.Contains('\\') || p.Filename.Contains(':') || !p.Filename.EndsWith(".bamod",StringComparison.OrdinalIgnoreCase) ||
            !Uri.TryCreate(p.Url,UriKind.Absolute,out var url) || url.Scheme!="https")throw new InvalidDataException("Invalid package in version manifest.");
        if(p.Index!=null && (p.Index.Size<=0 || p.Index.Size>MaxIndexSize || !Regex.IsMatch(p.Index.Sha256??"","^[a-fA-F0-9]{64}$") ||
            !Uri.TryCreate(p.Index.Url,UriKind.Absolute,out var index) || index.Scheme!="https"))throw new InvalidDataException("Invalid file list in version manifest.");
    }
    public const long MaxIndexSize=16<<20;
    public const long MaxLauncherSize=512L<<20;
    static bool Sha(string? s)=>Regex.IsMatch(s??"","^[a-fA-F0-9]{64}$");
    // Launcher and MelonLoader downloads come only from our own host.
    static bool Hosted(string? link)=>Uri.TryCreate(link,UriKind.Absolute,out var u) && u.Scheme=="https" && u.Host=="freedomarrow.app";
    /// <summary>True when the file has exactly this size and SHA-256.</summary>
    public static bool Matches(string file,long size,string sha256)
    {
        if(!File.Exists(file) || new FileInfo(file).Length!=size)return false;
        using var src=File.OpenRead(file);
        return Convert.ToHexString(SHA256.HashData(src)).Equals(sha256,StringComparison.OrdinalIgnoreCase);
    }
    /// <summary>The signed manifest the launcher accepted in this session (null before PLAY or the start-up update check).</summary>
    public static DistributionManifest? Verified { get; private set; }
    internal static HttpClient Client => Http;
    /// <summary>The verified cached file list of a package, or null when the manifest has none (full-package mode).</summary>
    public static string? IndexPath(DistributionPackage p)
    {
        if(p.Index==null)return null;
        var file=Path.Combine(CacheRoot,p.Index.Sha256.ToLowerInvariant()+"-"+Path.GetFileNameWithoutExtension(p.Filename)+".files.json");
        return File.Exists(file)?file:null;
    }
    private static async Task EnsureIndexAsync(DistributionPackage p,HttpClient client,string cache,IProgress<LaunchProgress>? progress,CancellationToken ct)
    {
        var dest=Path.Combine(cache,p.Index!.Sha256.ToLowerInvariant()+"-"+Path.GetFileNameWithoutExtension(p.Filename)+".files.json");
        bool Valid(byte[] b)=>b.LongLength==p.Index.Size && Convert.ToHexString(SHA256.HashData(b)).Equals(p.Index.Sha256,StringComparison.OrdinalIgnoreCase);
        if(File.Exists(dest) && Valid(await File.ReadAllBytesAsync(dest,ct))){progress?.Report(new("Using cached file list for "+p.Filename));return;}
        progress?.Report(new("Downloading the file list for "+p.Filename));
        for(int attempt=0;;attempt++)
        {
            try
            {
                using var r=await OpenAsync(client,p.Index.Url,0,ct);
                if(r.Content.Headers.ContentLength>MaxIndexSize)throw new InvalidDataException("File list is too large.");
                var bytes=await r.Content.ReadAsByteArrayAsync(ct);
                if(!Valid(bytes))throw new InvalidDataException("File list checksum failed; the game will not start.");
                // 1.1.13: written with write-through, flushed and read back before it replaces the cached copy (Beep 20 Nov 2026, Linux:
                // the cached list had 0x00 bytes on every later launch).
                using(var fs=new FileStream(dest+".part",FileMode.Create,FileAccess.Write,FileShare.None,1<<16,FileOptions.WriteThrough)){fs.Write(bytes);fs.Flush(true);}
                if(!Valid(await File.ReadAllBytesAsync(dest+".part",ct)))throw new IOException("The file list did not read back correctly.");
                File.Move(dest+".part",dest,true);return;
            }
            catch(Exception ex) when((ex is HttpRequestException || ex is IOException && ex is not InvalidDataException) && !ct.IsCancellationRequested && attempt<2)
            { await Task.Delay(TimeSpan.FromSeconds(attempt+1),ct); }
        }
    }
    public static DistributionRelease Select(DistributionManifest m)=>m.Releases.Single(r=>r.Version==(m.LockedVersion??m.Current));
    public static bool ValidFile(string file,DistributionPackage p)=>Matches(file,p.Size,p.Sha256);

    internal static async Task<HttpResponseMessage> OpenAsync(HttpClient client,string url,long offset,CancellationToken ct)
    {
        async Task<HttpResponseMessage> Get(string link)
        {
            if(!Uri.TryCreate(link,UriKind.Absolute,out var uri)||uri.Scheme!="https")throw new InvalidDataException("Package download requires HTTPS.");
            using var req=new HttpRequestMessage(HttpMethod.Get,uri);
            req.Headers.UserAgent.ParseAdd("FreedomArrowLauncher/3");
            req.Headers.CacheControl=new CacheControlHeaderValue { NoCache=true };
            if(offset>0)req.Headers.Range=new RangeHeaderValue(offset,null);
            var response=await client.SendAsync(req,HttpCompletionOption.ResponseHeadersRead,ct);
            if(response.RequestMessage?.RequestUri?.Scheme!="https"){response.Dispose();throw new InvalidDataException("Insecure download redirect.");}
            response.EnsureSuccessStatusCode();return response;
        }
        var r=await Get(url);
        if(r.Content.Headers.ContentType?.MediaType!="text/html")return r;
        // Drive returns a public virus-scan confirmation page for large archives.
        var html=await r.Content.ReadAsStringAsync(ct);r.Dispose();
        if(html.Length>131072)throw new InvalidDataException("Unexpected download page.");
        var action=Regex.Match(html,"<form[^>]+action=\"([^\"]+)\"",RegexOptions.IgnoreCase);
        if(!action.Success)throw new InvalidDataException(html.Contains("Quota exceeded",StringComparison.OrdinalIgnoreCase)
            ? "Google Drive's download limit for this file has been reached (too many downloads today). Try PLAY again later; Drive says it can take up to 24 hours."
            : "Drive did not return the package. It may be unavailable or over quota.");
        var target=WebUtility.HtmlDecode(action.Groups[1].Value);
        if(!Uri.TryCreate(target,UriKind.Absolute,out var formUri) || formUri.Scheme!="https" || formUri.Host!="drive.usercontent.google.com")
            throw new InvalidDataException("Unexpected Drive download confirmation.");
        var values=new List<string>();
        foreach(Match input in Regex.Matches(html,"<input\\b[^>]*>",RegexOptions.IgnoreCase))
        {
            var name=Regex.Match(input.Value,"name=\"([^\"]+)\"");var value=Regex.Match(input.Value,"value=\"([^\"]*)\"");
            if(name.Success)values.Add(Uri.EscapeDataString(WebUtility.HtmlDecode(name.Groups[1].Value))+"="+Uri.EscapeDataString(WebUtility.HtmlDecode(value.Groups[1].Value)));
        }
        r=await Get(target+"?"+string.Join("&",values));
        if(r.Content.Headers.ContentType?.MediaType=="text/html")
        {
            // 14 Nov 2026: a busy 8.7 GB file hit Drive's per-file download limit ("Quota exceeded").
            var page=await r.Content.ReadAsStringAsync(ct);r.Dispose();
            if(page.Contains("Quota exceeded",StringComparison.OrdinalIgnoreCase)||page.Contains("Too many users",StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Google Drive's download limit for this file has been reached (too many downloads today). Try PLAY again later; Drive says it can take up to 24 hours.");
            throw new InvalidDataException("Drive returned another page instead of the package.");
        }
        return r;
    }

    public static async Task<string> EnsurePackageAsync(DistributionPackage p,HttpClient client,string cache,IProgress<LaunchProgress>? progress,CancellationToken ct)
    {
        Validate(p,p.Id);Directory.CreateDirectory(cache);
        var dest=Path.Combine(cache,p.Sha256.ToLowerInvariant()+"-"+p.Filename);
        if(ValidFile(dest,p)){progress?.Report(new("Using cached "+p.Filename));return dest;}
        var bundled=Path.Combine(AppContext.BaseDirectory,p.Filename);
        if(ValidFile(bundled,p))
        {
            File.Copy(bundled,dest+".part",true);File.Move(dest+".part",dest,true);return dest;
        }
        var part=dest+".part";
        for(int attempt=0;attempt<3;attempt++)
        {
            try
            {
                long offset=File.Exists(part)?new FileInfo(part).Length:0;
                if(offset>=p.Size){File.Delete(part);offset=0;}
                using var r=await OpenAsync(client,p.Url,offset,ct);
                bool resume=r.StatusCode==HttpStatusCode.PartialContent && r.Content.Headers.ContentRange?.From==offset;
                if(r.StatusCode==HttpStatusCode.PartialContent && !resume)throw new InvalidDataException("Invalid resumed package response.");
                if(!resume)offset=0;
                await using(var src=await r.Content.ReadAsStreamAsync(ct))
                await using(var dst=new FileStream(part,resume?FileMode.Append:FileMode.Create,FileAccess.Write,FileShare.None,131072,true))
                {
                    var buffer=new byte[131072];long done=offset;int read;var last=DateTime.MinValue;
                    while((read=await src.ReadAsync(buffer,ct))>0)
                    {
                        done+=read;if(done>p.Size)throw new InvalidDataException("Package is larger than its manifest size.");
                        await dst.WriteAsync(buffer.AsMemory(0,read),ct);
                        if((DateTime.UtcNow-last).TotalMilliseconds>250){progress?.Report(new("Downloading "+p.Filename,(double)done/p.Size));last=DateTime.UtcNow;}
                    }
                }
                if(new FileInfo(part).Length!=p.Size)throw new IOException("Incomplete package download.");
                if(!ValidFile(part,p)){File.Delete(part);throw new InvalidDataException("Package checksum failed; the game will not start.");}
                File.Move(part,dest,true);return dest;
            }
            catch(Exception ex) when((ex is HttpRequestException || ex is IOException && ex is not InvalidDataException) && !ct.IsCancellationRequested && attempt<2)
            { await Task.Delay(TimeSpan.FromSeconds(attempt+1),ct); }
        }
        throw new IOException("Package could not be downloaded.");
    }

    /// <summary>Reads and verifies the signed list; offline it uses the last verified cached one. Unsigned, damaged or older lists are refused.</summary>
    public static async Task<(DistributionManifest Manifest,byte[] Envelope)> ReadManifestAsync(HttpClient client,string url,string? manifestFile,IProgress<LaunchProgress>? progress,CancellationToken ct)
    {
        DistributionManifest? cached=null;byte[]? cachedBytes=null;
        if(manifestFile!=null && File.Exists(manifestFile))
        {
            try{cachedBytes=await File.ReadAllBytesAsync(manifestFile,ct);cached=Parse(SignedManifest.Open(cachedBytes));}
            catch(InvalidDataException){cached=null;cachedBytes=null;}
        }
        DistributionManifest manifest;byte[] bytes;
        try
        {
            using var request=new CancellationTokenSource(TimeSpan.FromSeconds(20));using var linked=CancellationTokenSource.CreateLinkedTokenSource(ct,request.Token);
            using var response=await OpenAsync(client,url,0,linked.Token);
            if(response.Content.Headers.ContentLength>SignedManifest.MaxSize)throw new InvalidDataException("The version list is too large.");
            bytes=await response.Content.ReadAsByteArrayAsync(linked.Token);
            manifest=Parse(SignedManifest.Open(bytes));
        }
        catch(Exception ex) when((ex is HttpRequestException || ex is IOException && ex is not InvalidDataException || ex is OperationCanceledException && !ct.IsCancellationRequested) && cached!=null)
        { manifest=cached;bytes=cachedBytes!;progress?.Report(new("Offline: using the last verified version manifest.")); }
        if(cached!=null && manifest.Serial<cached.Serial)
            throw new InvalidDataException("The version list is older than the one this launcher already accepted, so it is refused.");
        Verified=manifest;
        return (manifest,bytes);
    }

    /// <summary>The last verified signed list, kept byte for byte so its signature is checked again when it is read.</summary>
    public static string ManifestFile => Path.Combine(CacheRoot,"live-manifest.signed.json");
    public static async Task PrepareAsync(IProgress<LaunchProgress> progress,CancellationToken ct)
    {
        progress.Report(new("Checking Freedom Arrow version manifest…"));
        Directory.CreateDirectory(CacheRoot);
        var (manifest,envelope)=await ReadManifestAsync(Http,SignedManifest.Url,ManifestFile,progress,ct);
        var selected=Select(manifest);
        await EnsurePackageAsync(selected.Gameplay,Http,CacheRoot,progress,ct);
        // With a file list the Assets files are fetched one by one during install (AssetsIndexInstall); the full pack is not downloaded.
        if(selected.Assets.Index!=null)await EnsureIndexAsync(selected.Assets,Http,CacheRoot,progress,ct);
        else await EnsurePackageAsync(selected.Assets,Http,CacheRoot,progress,ct);
        // Commit the new manifest only once both referenced packages have verified successfully.
        await File.WriteAllBytesAsync(ManifestFile+".tmp",envelope,ct);File.Move(ManifestFile+".tmp",ManifestFile,true);
        Active=selected;
    }
}

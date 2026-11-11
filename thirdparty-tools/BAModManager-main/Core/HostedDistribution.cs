using System.Net;
using System.Net.Http.Headers;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;

namespace BAModManager.Core;

public sealed record DistributionPackage(string Id, string Version, string Filename, string Url, long Size, string Sha256);
public sealed record DistributionRelease(string Version, DistributionPackage Gameplay, DistributionPackage Assets);
public sealed record DistributionManifest(int Schema, string Channel, string Current, [property: JsonPropertyName("locked_version")] string? LockedVersion, List<DistributionRelease> Releases);

/// <summary>Public HTTPS manifest, verified atomic package cache and Drive confirmation handling.</summary>
public static class HostedDistribution
{
    public const string ManifestUrl = "https://drive.google.com/uc?export=download&id=1NvdXaFJrqkuOeZAceTo9s8iSyedAfRqE";
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
        return m;
    }
    private static void Validate(DistributionPackage p,string id)
    {
        if(p==null || p.Id!=id || string.IsNullOrWhiteSpace(p.Version) || p.Size<=0 || !Regex.IsMatch(p.Sha256??"","^[a-fA-F0-9]{64}$") ||
            string.IsNullOrWhiteSpace(p.Filename) || p.Filename!=Path.GetFileName(p.Filename) || p.Filename.Contains('\\') || p.Filename.Contains(':') || !p.Filename.EndsWith(".bamod",StringComparison.OrdinalIgnoreCase) ||
            !Uri.TryCreate(p.Url,UriKind.Absolute,out var url) || url.Scheme!="https")throw new InvalidDataException("Invalid package in version manifest.");
    }
    public static DistributionRelease Select(DistributionManifest m)=>m.Releases.Single(r=>r.Version==(m.LockedVersion??m.Current));
    public static bool ValidFile(string file,DistributionPackage p)
    {
        if(!File.Exists(file) || new FileInfo(file).Length!=p.Size)return false;
        using var src=File.OpenRead(file);
        return Convert.ToHexString(SHA256.HashData(src)).Equals(p.Sha256,StringComparison.OrdinalIgnoreCase);
    }

    private static async Task<HttpResponseMessage> OpenAsync(HttpClient client,string url,long offset,CancellationToken ct)
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
        if(!action.Success)throw new InvalidDataException("Drive did not return the package. It may be unavailable or over quota.");
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
        if(r.Content.Headers.ContentType?.MediaType=="text/html"){r.Dispose();throw new InvalidDataException("Drive returned another page instead of the package.");}
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

    public static async Task<DistributionManifest> ReadManifestAsync(HttpClient client,string url,string manifestFile,IProgress<LaunchProgress>? progress,CancellationToken ct)
    {
        DistributionManifest manifest;
        try
        {
            using var request=new CancellationTokenSource(TimeSpan.FromSeconds(20));using var linked=CancellationTokenSource.CreateLinkedTokenSource(ct,request.Token);
            using var response=await OpenAsync(client,url,0,linked.Token);
            var text=await response.Content.ReadAsStringAsync(linked.Token);
            if(text.Length>65536)throw new InvalidDataException("Version manifest is too large.");
            manifest=Parse(text);
        }
        catch(Exception ex) when((ex is HttpRequestException || ex is IOException && ex is not InvalidDataException || ex is OperationCanceledException && !ct.IsCancellationRequested) && File.Exists(manifestFile))
        { manifest=Parse(await File.ReadAllTextAsync(manifestFile,ct));progress?.Report(new("Offline: using the last verified version manifest.")); }
        return manifest;
    }

    public static async Task PrepareAsync(IProgress<LaunchProgress> progress,CancellationToken ct)
    {
        progress.Report(new("Checking Freedom Arrow version manifest…"));
        Directory.CreateDirectory(CacheRoot);var manifestFile=Path.Combine(CacheRoot,"live-manifest.json");
        var manifest=await ReadManifestAsync(Http,ManifestUrl,manifestFile,progress,ct);
        var selected=Select(manifest);
        await EnsurePackageAsync(selected.Gameplay,Http,CacheRoot,progress,ct);
        await EnsurePackageAsync(selected.Assets,Http,CacheRoot,progress,ct);
        // Commit the new manifest only once both referenced packages have verified successfully.
        await File.WriteAllTextAsync(manifestFile+".tmp",JsonSerializer.Serialize(manifest,Json),ct);File.Move(manifestFile+".tmp",manifestFile,true);
        Active=selected;
    }
}

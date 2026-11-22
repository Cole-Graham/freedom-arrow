using System.Diagnostics;
using System.Text.Json;

namespace BAModManager.Core;

/// <summary>
/// 1.1.15 (Osama 22 Nov 2026, "can we add a news section on the launcher? like the battle stats and patch notes?"):
/// the News panel's data. freedomarrow.app/site/data/news.json is written every 10 minutes by the site's stats job
/// (team-site/stats/build_news.py): the front page's Battlefield report numbers and the short release announcements.
/// Display only: it is shown as plain text, never runs anything, and links open only on freedomarrow.app.
/// A failed or slow read just leaves the panel saying the news is unavailable; it never holds up PLAY.
/// </summary>
public static class LauncherNews
{
    public const string Url = "https://freedomarrow.app/site/data/news.json";
    public const string Site = "https://freedomarrow.app/";
    private const int MaxBytes = 512 * 1024;

    private static readonly HttpClient Http = new() { Timeout = TimeSpan.FromSeconds(15) };

    public sealed record Stats(int? Online, int? Peak24, int? Players, int? Matches);
    public sealed record Note(string Version, string Date, string English, string Chinese, string Link);
    public sealed record Feature(string Title, string TitleZh, string Text, string TextZh, string Image);
    public sealed record News(Stats Stats, IReadOnlyList<Note> Notes, IReadOnlyList<Feature> Features);

    private const int MaxImageBytes = 12 * 1024 * 1024;

    /// <summary>A feature's picture (an animated GIF): downloaded once from freedomarrow.app, then read from the launcher's
    /// AppData folder (the address carries a ?v= number, so a new picture is a new file).</summary>
    public static async Task<byte[]?> LoadImageAsync(string url, CancellationToken ct = default)
    {
        if (!IsSiteLink(url)) return null;
        try
        {
            var dir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), AppInfo.Id, "news");
            var file = Path.Combine(dir, Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(System.Text.Encoding.UTF8.GetBytes(url)))[..16] + ".img");
            if (File.Exists(file)) return await File.ReadAllBytesAsync(file, ct).ConfigureAwait(false);
            using var resp = await Http.GetAsync(url, HttpCompletionOption.ResponseHeadersRead, ct).ConfigureAwait(false);
            if (!resp.IsSuccessStatusCode || resp.Content.Headers.ContentLength > MaxImageBytes) return null;
            var bytes = await ReadCapped(resp, MaxImageBytes, ct).ConfigureAwait(false);
            if (bytes == null) return null;
            Directory.CreateDirectory(dir);
            await File.WriteAllBytesAsync(file + ".part", bytes, ct).ConfigureAwait(false);
            File.Move(file + ".part", file, true);
            return bytes;
        }
        catch (Exception) { return null; }
    }

    private static async Task<byte[]?> ReadCapped(HttpResponseMessage resp, int max, CancellationToken ct)
    {
        await using var s = await resp.Content.ReadAsStreamAsync(ct).ConfigureAwait(false);
        using var buf = new MemoryStream();
        var chunk = new byte[65536];
        int n;
        while ((n = await s.ReadAsync(chunk, ct).ConfigureAwait(false)) > 0)
        {
            if (buf.Length + n > max) return null;
            buf.Write(chunk, 0, n);
        }
        return buf.ToArray();
    }

    public static async Task<News?> LoadAsync(CancellationToken ct = default)
    {
        try
        {
            using var resp = await Http.GetAsync(Url, HttpCompletionOption.ResponseHeadersRead, ct).ConfigureAwait(false);
            if (!resp.IsSuccessStatusCode) return null;
            if (resp.Content.Headers.ContentLength > MaxBytes) return null;
            var bytes = await ReadCapped(resp, MaxBytes, ct).ConfigureAwait(false);
            return bytes == null ? null : Parse(bytes);
        }
        catch (Exception) { return null; }
    }

    public static News? Parse(byte[] json)
    {
        try
        {
            using var doc = JsonDocument.Parse(json);
            var root = doc.RootElement;
            var st = root.TryGetProperty("stats", out var x) && x.ValueKind == JsonValueKind.Object ? x : default;
            var stats = new Stats(Int(st, "online"), Int(st, "peak24"), Int(st, "players"), Int(st, "matches"));
            var notes = new List<Note>();
            if (root.TryGetProperty("notes", out var arr) && arr.ValueKind == JsonValueKind.Array)
                foreach (var e in arr.EnumerateArray().Take(5))
                {
                    var link = Str(e, "url");
                    notes.Add(new Note(Str(e, "version"), Str(e, "date"), Str(e, "en"), Str(e, "zh"), IsSiteLink(link) ? link : Site));
                }
            var features = new List<Feature>();
            if (root.TryGetProperty("features", out var fa) && fa.ValueKind == JsonValueKind.Array)
                foreach (var e in fa.EnumerateArray().Take(5))
                    features.Add(new Feature(Str(e, "title"), Str(e, "title_zh"), Str(e, "text"), Str(e, "text_zh"), IsSiteLink(Str(e, "image")) ? Str(e, "image") : ""));
            return new News(stats, notes, features);
        }
        catch (Exception) { return null; }
    }

    /// <summary>Only https links on freedomarrow.app are opened.</summary>
    public static bool IsSiteLink(string? url) =>
        Uri.TryCreate(url, UriKind.Absolute, out var u) && u.Scheme == Uri.UriSchemeHttps && u.Host == "freedomarrow.app";

    public static void Open(string url)
    {
        if (!IsSiteLink(url)) return;
        try { Process.Start(new ProcessStartInfo(url) { UseShellExecute = true })?.Dispose(); }
        catch (Exception)
        {
            // Wine/Proton: winebrowser hands web links to the Linux browser.
            try { Process.Start(new ProcessStartInfo("winebrowser.exe", url) { UseShellExecute = false })?.Dispose(); }
            catch (Exception) { }
        }
    }

    private static int? Int(JsonElement e, string name) =>
        e.ValueKind == JsonValueKind.Object && e.TryGetProperty(name, out var v) && v.ValueKind == JsonValueKind.Number && v.TryGetInt32(out var i) ? i : null;

    private static string Str(JsonElement e, string name) =>
        e.ValueKind == JsonValueKind.Object && e.TryGetProperty(name, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() ?? "" : "";
}

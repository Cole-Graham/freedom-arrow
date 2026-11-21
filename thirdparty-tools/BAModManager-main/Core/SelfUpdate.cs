namespace BAModManager.Core;

/// <summary>
/// Launcher self-update (Lateralus 19 Nov 2026: "after that I would like the launcher to update itself", done "in a secure way").
/// The new exe is named only by the signed version list (SignedManifest), must come from freedomarrow.app, and must match the listed size
/// and SHA-256 before it replaces anything. Windows lets a running exe be renamed but not overwritten: the running exe becomes .old, the
/// checked download takes its name, and the launcher restarts. An older or equal version is never installed.
/// </summary>
public static class SelfUpdate
{
    public static Version Current => typeof(SelfUpdate).Assembly.GetName().Version ?? new Version(0, 0);

    /// <summary>Removes what an earlier update left next to the exe.</summary>
    public static void CleanUp(string exe)
    {
        foreach (var leftover in new[] { exe + ".old", exe + ".new" })
            try { if (File.Exists(leftover)) File.Delete(leftover); } catch { /* still running or locked; next start */ }
    }

    /// <summary>True when the newer listed launcher has replaced <paramref name="exe"/>; the caller starts it and exits.</summary>
    public static async Task<bool> ApplyAsync(LauncherRelease? release, string exe, HttpClient client, IProgress<LaunchProgress>? progress, CancellationToken ct)
    {
        if (release == null || !Version.TryParse(release.Version, out var listed) || listed <= Current) return false;
        var next = exe + ".new";
        var label = Loc.T("Downloading launcher {0}…", release.Version); var shown = DateTime.MinValue;
        progress?.Report(new LaunchProgress(label, 0, LaunchStage.Launcher, 0, release.Size));
        using (var response = await HostedDistribution.OpenAsync(client, release.Url, 0, ct))
        {
            if (response.Content.Headers.ContentLength is long length && length != release.Size)
                throw new InvalidDataException("The launcher download has the wrong size, so it was not installed.");
            await using var src = await response.Content.ReadAsStreamAsync(ct);
            await using var dst = new FileStream(next, FileMode.Create, FileAccess.Write, FileShare.None, 131072, true);
            var buffer = new byte[131072]; long done = 0; int read;
            while ((read = await src.ReadAsync(buffer, ct)) > 0)
            {
                done += read;
                if (done > release.Size) throw new InvalidDataException("The launcher download is larger than listed, so it was not installed.");
                await dst.WriteAsync(buffer.AsMemory(0, read), ct);
                if ((DateTime.UtcNow - shown).TotalMilliseconds >= 250 || done == release.Size)
                { shown = DateTime.UtcNow; progress?.Report(new LaunchProgress(label, (double)done / release.Size, LaunchStage.Launcher, done, release.Size)); }
            }
        }
        if (!HostedDistribution.Matches(next, release.Size, release.Sha256))
        {
            File.Delete(next);
            throw new InvalidDataException("The launcher download failed its checksum, so it was not installed.");
        }
        var old = exe + ".old";
        File.Move(exe, old, true);
        try { File.Move(next, exe); }
        catch { File.Move(old, exe, true); throw; }
        return true;
    }
}

using System.Net;
using System.Net.Security;
using System.Net.Sockets;
using System.Security.Authentication;
using System.Security.Cryptography.X509Certificates;
using System.Text;

namespace BAModManager.Core;

/// <summary>
/// 1.1.16 (Osama 22 Nov 2026, thread 1573561286803980289: a player on up-to-date Windows 10, no VPN, proxy or antivirus, got
/// "The SSL connection could not be established, see inner exception" and nothing else; the player asked us to "add it").
/// A failed PLAY now shows the whole exception chain (the inner reason, e.g. "UntrustedRoot"), and for a secure-connection
/// failure it also looks at what this PC actually receives from freedomarrow.app: the address DNS gives, the Windows proxy,
/// and who issued the certificate. Ours is issued by Google Trust Services through Cloudflare; any other issuer means
/// something on the PC or network (security software, router, ISP filter) is answering in our place. Cloudflare can also use a
/// backup authority (Let's Encrypt, SSL.com, Sectigo), so those are not reported as foreign.
/// Everything is also appended to %AppData%\FreedomArrowLauncherDev45\launcher.log (1 MB, one older file kept).
/// Read only: nothing is changed and the probe never sends anything but a TLS hello.
/// </summary>
public static class NetDiagnostics
{
    public const string Host = "freedomarrow.app";
    private const long MaxLogBytes = 1024 * 1024;
    private static readonly object LogLock = new();
    // The certificate authorities Cloudflare uses for its edge certificates (it can switch to a backup one at any time).
    private static readonly string[] CloudflareIssuers = { "Google Trust Services", "Let's Encrypt", "SSL.com", "Sectigo", "Cloudflare" };

    public static string LogPath => Path.Combine(AppSettings.FolderPath, "launcher.log");

    /// <summary>Every distinct message in the exception chain, outer first.</summary>
    public static string Describe(Exception ex)
    {
        var parts = new List<string>();
        for (var e = ex; e != null; e = e.InnerException)
        {
            var m = e.Message.Trim();
            if (m.Length > 0 && !parts.Contains(m)) parts.Add(m);
        }
        return string.Join(" → ", parts);
    }

    public static bool IsSecureConnectionFailure(Exception ex)
    {
        for (var e = ex; e != null; e = e.InnerException)
            if (e is AuthenticationException) return true;
        return false;
    }

    /// <summary>What this PC gets when it opens freedomarrow.app: DNS addresses, Windows proxy and the certificate.</summary>
    public static async Task<string> ProbeAsync(CancellationToken ct = default)
    {
        var sb = new StringBuilder();
        IPAddress[] addresses;
        try
        {
            addresses = await Dns.GetHostAddressesAsync(Host, ct);
            sb.AppendLine($"{Host} → {string.Join(", ", addresses.Select(a => a.ToString()))}");
        }
        catch (Exception ex)
        {
            sb.AppendLine($"{Host} → DNS failed: {ex.Message}");
            return sb.ToString().TrimEnd();
        }

        try
        {
            var uri = new Uri($"https://{Host}/");
            var proxy = HttpClient.DefaultProxy.GetProxy(uri);
            sb.AppendLine("Windows proxy: " + (proxy == null || proxy == uri ? "none" : proxy.ToString()));
        }
        catch (Exception ex) { sb.AppendLine("Windows proxy: unknown (" + ex.Message + ")"); }

        string? subject = null, issuer = null, chainProblems = null;
        SslPolicyErrors errors = SslPolicyErrors.None;
        try
        {
            using var cts = CancellationTokenSource.CreateLinkedTokenSource(ct);
            cts.CancelAfter(TimeSpan.FromSeconds(15));
            using var tcp = new TcpClient();
            await tcp.ConnectAsync(Host, 443, cts.Token);
            using var ssl = new SslStream(tcp.GetStream(), false, (_, cert, chain, policy) =>
            {
                if (cert != null)
                {
                    var c = new X509Certificate2(cert);
                    subject = c.Subject;
                    issuer = c.Issuer;
                }
                errors = policy;
                var flags = chain?.ChainStatus.Select(s => s.Status.ToString()).Distinct().ToArray();
                if (flags is { Length: > 0 }) chainProblems = string.Join(", ", flags);
                return true;   // look only: the probe never sends a request
            });
            await ssl.AuthenticateAsClientAsync(new SslClientAuthenticationOptions { TargetHost = Host }, cts.Token);
            sb.AppendLine($"Connection: {ssl.SslProtocol}");
        }
        catch (Exception ex)
        {
            sb.AppendLine("Connection failed: " + Describe(ex));
        }

        if (issuer != null)
        {
            sb.AppendLine("Certificate: " + subject);
            sb.AppendLine("Issued by: " + issuer);
            if (errors != SslPolicyErrors.None)
                sb.AppendLine($"Windows says: {errors}" + (chainProblems != null ? $" ({chainProblems})" : ""));
            if (!CloudflareIssuers.Any(i => issuer.Contains(i, StringComparison.OrdinalIgnoreCase)))
                sb.AppendLine("This is not our certificate (Cloudflare issues ours through Google Trust Services). Something on this PC or network is answering for freedomarrow.app.");
        }
        else
        {
            sb.AppendLine("No certificate was received.");
        }
        return sb.ToString().TrimEnd();
    }

    /// <summary>Appends one line (or block) to launcher.log; never throws.</summary>
    public static void Append(string text)
    {
        try
        {
            lock (LogLock)
            {
                Directory.CreateDirectory(AppSettings.FolderPath);
                var info = new FileInfo(LogPath);
                if (info.Exists && info.Length > MaxLogBytes)
                    File.Move(LogPath, Path.Combine(AppSettings.FolderPath, "launcher.old.log"), true);
                File.AppendAllText(LogPath, $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] {text}{Environment.NewLine}");
            }
        }
        catch { /* logging must never break the launcher */ }
    }
}

using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace BAModManager.Core;

/// <summary>
/// Signed version list (Lateralus 19 Nov 2026, after the Notepad++ updater hijack: "All mod and launcher self-updating needs to be done in a
/// secure way"). The version list names the SHA-256 of every file the launcher installs or runs, so it must not be trusted only because it
/// came from our host. bin/ba-sign-manifest on the BA deck signs the exact bytes with an ECDSA P-256 key that is never uploaded anywhere;
/// this launcher holds only the public key. A list that is not signed by a key below is refused, from the network and from the cache.
/// </summary>
public static class SignedManifest
{
    public const string Url = "https://freedomarrow.app/manifest/live.signed.json";
    public const int MaxSize = 262144;
    // Signed bytes = Context + manifest bytes, so a signature made for some other purpose can never pass as a version list.
    const string Context = "freedomarrow-manifest-v1\n";
    // SubjectPublicKeyInfo, base64. More than one key lets a backup key replace a lost or leaked main key.
    public static IReadOnlyList<string> TrustedKeys { get; internal set; } = new[]
    {
        "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEldksEagvrwoKFGwmy7XDip3JEB+AeHFQTn52LcUVl2BPxjwreE5BcR4DiIMlh0rfVicCMZXGfCBe+ZSKV5J5ew==",
    };

    /// <summary>The manifest text inside a signed envelope {"manifest": base64, "signature": base64 DER}, or InvalidDataException.</summary>
    public static string Open(byte[] envelope)
    {
        if (envelope.Length > MaxSize) throw new InvalidDataException("The version list is too large.");
        byte[] body, signature;
        try
        {
            using var doc = JsonDocument.Parse(envelope);
            body = Convert.FromBase64String(doc.RootElement.GetProperty("manifest").GetString() ?? "");
            signature = Convert.FromBase64String(doc.RootElement.GetProperty("signature").GetString() ?? "");
        }
        catch (Exception ex) when (ex is JsonException || ex is FormatException || ex is KeyNotFoundException || ex is InvalidOperationException)
        {
            throw new InvalidDataException("The version list is not a signed Freedom Arrow list.");
        }
        var signed = Encoding.UTF8.GetBytes(Context).Concat(body).ToArray();
        foreach (var key in TrustedKeys)
        {
            using var ec = ECDsa.Create();
            ec.ImportSubjectPublicKeyInfo(Convert.FromBase64String(key), out _);
            if (ec.VerifyData(signed, signature, HashAlgorithmName.SHA256, DSASignatureFormat.Rfc3279DerSequence))
                return Encoding.UTF8.GetString(body);
        }
        throw new InvalidDataException("The version list's signature is not valid, so the launcher will not use it. Ask in the Freedom Arrow Discord.");
    }
}

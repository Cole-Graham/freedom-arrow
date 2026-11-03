using System.Security.Cryptography;
using System.Text;

namespace FreedomArrow;

static class Crypto
{
    static readonly byte[] Key = Encoding.ASCII.GetBytes("09234237536700238099172758697347");
    static readonly byte[] Marker = Encoding.ASCII.GetBytes("fhk3s0g3");

    public static string Decrypt(string b64)
    {
        var raw = Convert.FromBase64String(b64);
        if (raw.Length < 24 || !raw.AsSpan(0, 8).SequenceEqual(Marker))
            throw new InvalidDataException("table is not in the expected encrypted format");
        using var aes = Aes.Create();
        aes.Key = Key;
        var plain = aes.DecryptCbc(raw.AsSpan(24), raw.AsSpan(8, 16));
        var text = Encoding.UTF8.GetString(plain);
        return text.Length > 0 && text[0] == '\ufeff' ? text[1..] : text;
    }

    public static string Encrypt(string json)
    {
        using var aes = Aes.Create();
        aes.Key = Key;
        var iv = RandomNumberGenerator.GetBytes(16);
        var cipher = aes.EncryptCbc(Encoding.UTF8.GetBytes(json), iv);
        var packed = new byte[24 + cipher.Length];
        Marker.CopyTo(packed, 0);
        iv.CopyTo(packed, 8);
        cipher.CopyTo(packed, 24);
        return Convert.ToBase64String(packed);
    }
}

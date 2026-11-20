using System.Globalization;
using System.Numerics;
using System.Security.Cryptography;

namespace BAModManager.Core;

/// <summary>
/// Launcher 1.1.12 (20 Nov 2026): ECDSA P-256 / SHA-256 signature check in plain C#. Proton/Wine has no working ECDSA in its crypto
/// libraries (.NET throws 0x80090029, measured on Vengeance with Proton Experimental), so 1.1.9-1.1.11 could not open the signed version
/// list on Linux or the Steam Deck. SignedManifest uses this only when the system ECDSA throws; it checks public data only, so it does not
/// need to run in constant time.
/// </summary>
public static class P256Verify
{
    static BigInteger H(string hex) => BigInteger.Parse("0" + hex, NumberStyles.HexNumber);
    static readonly BigInteger P = H("ffffffff00000001000000000000000000000000ffffffffffffffffffffffff");
    static readonly BigInteger N = H("ffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551");
    static readonly BigInteger A = P - 3;
    static readonly BigInteger B = H("5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b");
    static readonly (BigInteger X, BigInteger Y) G =
        (H("6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296"), H("4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5"));
    // DER SubjectPublicKeyInfo prefix for an uncompressed P-256 key (id-ecPublicKey, prime256v1), then 0x04 || X || Y.
    static readonly byte[] SpkiPrefix = Convert.FromHexString("3059301306072a8648ce3d020106082a8648ce3d030107034200");

    static BigInteger Mod(BigInteger x, BigInteger m) { var r = x % m; return r.Sign < 0 ? r + m : r; }
    static BigInteger Inv(BigInteger x, BigInteger m) => BigInteger.ModPow(Mod(x, m), m - 2, m);
    static BigInteger U(ReadOnlySpan<byte> b) => new(b, isUnsigned: true, isBigEndian: true);

    static (BigInteger X, BigInteger Y)? Add((BigInteger X, BigInteger Y)? p, (BigInteger X, BigInteger Y)? q)
    {
        if (p == null) return q;
        if (q == null) return p;
        var (x1, y1) = p.Value; var (x2, y2) = q.Value;
        BigInteger l;
        if (x1 == x2)
        {
            if (Mod(y1 + y2, P).IsZero) return null;
            l = Mod((3 * x1 * x1 + A) * Inv(2 * y1, P), P);
        }
        else l = Mod((y2 - y1) * Inv(x2 - x1, P), P);
        var x3 = Mod(l * l - x1 - x2, P);
        return (x3, Mod(l * (x1 - x3) - y1, P));
    }

    static (BigInteger X, BigInteger Y)? Mul(BigInteger k, (BigInteger X, BigInteger Y) pt)
    {
        (BigInteger X, BigInteger Y)? r = null, a = pt;
        for (; !k.IsZero; k >>= 1)
        {
            if (!k.IsEven) r = Add(r, a);
            a = Add(a, a);
        }
        return r;
    }

    /// <summary>Strict DER SEQUENCE { INTEGER r, INTEGER s }; null if malformed.</summary>
    static (BigInteger R, BigInteger S)? ParseDer(byte[] sig)
    {
        int i = 0;
        BigInteger? Int()
        {
            if (i + 2 > sig.Length || sig[i] != 0x02) return null;
            int len = sig[i + 1]; i += 2;
            if (len == 0 || len > 33 || i + len > sig.Length) return null;
            var v = sig.AsSpan(i, len);
            if ((v[0] & 0x80) != 0) return null;                                  // negative
            if (len > 1 && v[0] == 0 && (v[1] & 0x80) == 0) return null;          // not minimal
            i += len;
            return U(v);
        }
        if (sig.Length < 8 || sig[0] != 0x30 || sig[1] != sig.Length - 2) return null;
        i = 2;
        var r = Int(); var s = Int();
        if (r == null || s == null || i != sig.Length) return null;
        return (r.Value, s.Value);
    }

    public static bool Verify(byte[] spki, byte[] data, byte[] derSignature)
    {
        if (spki.Length != SpkiPrefix.Length + 65 || !spki.AsSpan(0, SpkiPrefix.Length).SequenceEqual(SpkiPrefix) || spki[SpkiPrefix.Length] != 0x04)
            return false;
        var qx = U(spki.AsSpan(SpkiPrefix.Length + 1, 32)); var qy = U(spki.AsSpan(SpkiPrefix.Length + 33, 32));
        if (qx >= P || qy >= P || Mod(qy * qy - (qx * qx * qx + A * qx + B), P) != 0) return false;   // key must be on the curve
        var rs = ParseDer(derSignature);
        if (rs == null) return false;
        var (r, s) = rs.Value;
        if (r.Sign <= 0 || r >= N || s.Sign <= 0 || s >= N) return false;
        var e = U(SHA256.HashData(data));
        var w = Inv(s, N);
        var x = Add(Mul(Mod(e * w, N), G), Mul(Mod(r * w, N), (qx, qy)));
        return x != null && Mod(x.Value.X, N) == r;
    }
}

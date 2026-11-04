using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Security.Cryptography;

namespace FreedomArrow.Conquest;

// Generated interop assemblies receive a fresh ModuleVersionId on each run.
// Ignore only that GUID; retain every instruction, signature and other byte.
public static class BuildFingerprint
{
    public const string Prefix = "sha256-mvid-v1:";

    public static string Compute(byte[] bytes, bool ignoreMvid)
    {
        if (!ignoreMvid) return Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
        using var stream = new MemoryStream(bytes, false);
        using var pe = new PEReader(stream);
        var metadata = pe.GetMetadataReader();
        var handle = metadata.GetModuleDefinition().Mvid;
        if (handle.IsNil) throw new InvalidDataException("Missing module MVID");
        byte[] guid = metadata.GetGuid(handle).ToByteArray();
        byte[] content = pe.GetMetadata().GetContent().ToArray();
        int found = -1;
        for (int i = 0; i <= content.Length - 16; i++)
        {
            if (!content.AsSpan(i, 16).SequenceEqual(guid)) continue;
            if (found >= 0) throw new InvalidDataException("Ambiguous module MVID location");
            found = i;
        }
        if (found < 0) throw new InvalidDataException("Module MVID not found in metadata");
        byte[] normalized = (byte[])bytes.Clone();
        Array.Clear(normalized, checked(pe.PEHeaders.MetadataStartOffset + found), 16);
        return Convert.ToHexString(SHA256.HashData(normalized)).ToLowerInvariant();
    }

    public static void Verify(string relativePath, byte[] bytes, string pin)
    {
        bool normalized = pin.StartsWith(Prefix, StringComparison.Ordinal);
        if (normalized && !(relativePath.StartsWith("MelonLoader/Il2CppAssemblies/", StringComparison.Ordinal)
                           && relativePath.EndsWith(".dll", StringComparison.Ordinal)))
            throw new InvalidDataException("MVID normalization is restricted to generated interop assemblies");
        string expected = normalized ? pin.Substring(Prefix.Length) : pin;
        if (Compute(bytes, normalized) != expected)
            throw new InvalidDataException("Build mismatch: " + relativePath);
    }
}

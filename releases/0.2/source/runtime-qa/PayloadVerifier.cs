using System.Security.Cryptography;
using System.Text.Json.Nodes;
namespace FreedomArrow;

public static class PayloadVerifier
{
    public static int Verify(string gameRoot,JsonObject hashes)
    {
        if(hashes.Count==0)throw new InvalidDataException("Empty payload manifest");
        string root=Path.GetFullPath(gameRoot)+Path.DirectorySeparatorChar;
        foreach(var entry in hashes)
        {
            if(entry.Key.Contains('\\')||!(entry.Key.StartsWith("Mods/",StringComparison.Ordinal)||entry.Key.StartsWith("UserData/",StringComparison.Ordinal)))
                throw new InvalidDataException("Unsupported payload path");
            string path=Path.GetFullPath(Path.Combine(root,entry.Key));
            if(!path.StartsWith(root,StringComparison.Ordinal)||entry.Key.Split('/').Any(p=>p==".."||p=="."))
                throw new InvalidDataException("Unsafe payload path");
            var info=new FileInfo(path);
            if(!info.Exists||info.LinkTarget!=null)throw new InvalidDataException("Missing/linked payload: "+entry.Key);
            string actual=Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant();
            if(actual!=entry.Value.GetValue<string>())throw new InvalidDataException("Payload checksum mismatch: "+entry.Key);
        }
        return hashes.Count;
    }
}

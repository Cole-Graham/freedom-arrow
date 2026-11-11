using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Security.Cryptography;
using System.Text.Json;
var root=Path.GetFullPath(args[0]);
using var input=File.OpenRead(Path.Combine(root,"bin/Release/net6.0/FreedomArrow.Runtime.dll"));
using var pe=new PEReader(input);var metadata=pe.GetMetadataReader();
var resources=metadata.ManifestResources.Select(x=>metadata.GetManifestResource(x)).ToDictionary(x=>metadata.GetString(x.Name));
var block=pe.GetSectionData(pe.PEHeaders.CorHeader!.ResourcesDirectory.RelativeVirtualAddress);
using var receipt=JsonDocument.Parse(File.ReadAllText(Path.Combine(root,"../UserData/FreedomArrow/pla-weapon-hud.json")));
var addresses=receipt.RootElement.GetProperty("entries").EnumerateArray().Select(x=>x.GetProperty("address").GetString()!).Distinct().ToArray();
foreach(var address in addresses)
{
    var resource=resources["FreedomArrow.icons."+address+".png"];
    var reader=block.GetReader((int)resource.Offset,block.Length-(int)resource.Offset);
    int size=reader.ReadInt32();var bytes=reader.ReadBytes(size);
    if(!SHA256.HashData(bytes).SequenceEqual(SHA256.HashData(File.ReadAllBytes(Path.Combine(root,"icons",address+".png")))))throw new Exception(address+" compiled PNG differs from approved source");
}
Console.WriteLine($"PASS: {addresses.Length} weapon-family PNGs embedded byte-identical in the compiled runtime; no game load claimed.");

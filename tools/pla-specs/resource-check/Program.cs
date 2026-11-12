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
using var identity=JsonDocument.Parse(File.ReadAllText(Path.Combine(root,"../UserData/FreedomArrow/pla-infantry-identity.json")));
var addresses=receipt.RootElement.GetProperty("resources").EnumerateArray().Select(x=>x.GetString()!).Concat(identity.RootElement.GetProperty("resources").EnumerateArray().Select(x=>x.GetString()!)).Concat(new[]{"FA_CHINA_FLAG","FA_CHINA_AIR_SF","FA_CHINA_ARMORED","FA_CHINA_ROCKET","FA_CHINA_NAVAL","FA_CHINA_MOTORIZED"}).Distinct().ToArray();
foreach(var address in addresses)
{
    var resource=resources["FreedomArrow.icons."+address+".png"];
    var reader=block.GetReader((int)resource.Offset,block.Length-(int)resource.Offset);
    int size=reader.ReadInt32();var bytes=reader.ReadBytes(size);
    if(!SHA256.HashData(bytes).SequenceEqual(SHA256.HashData(File.ReadAllBytes(Path.Combine(root,"icons",address+".png")))))throw new Exception(address+" compiled PNG differs from approved source");
}
Console.WriteLine($"PASS: {addresses.Length} weapon/unit icon PNGs embedded byte-identical in the compiled runtime; no game load claimed.");

// Read the actual compiled MelonInfo attribute without loading Unity/MelonLoader.
using var buildDoc=JsonDocument.Parse(File.ReadAllText(Path.Combine(root,"../UserData/FreedomArrow/pla-build.json")));
using var channel=JsonDocument.Parse(File.ReadAllText(Path.Combine(root,"../UserData/FreedomArrow/channel.json")));
string expected=buildDoc.RootElement.GetProperty("build").GetInt32().ToString();
string compiled="";
foreach(var handle in metadata.GetAssemblyDefinition().GetCustomAttributes())
{
    var attribute=metadata.GetCustomAttribute(handle);
    if(attribute.Constructor.Kind!=HandleKind.MemberReference)continue;
    var constructor=metadata.GetMemberReference((MemberReferenceHandle)attribute.Constructor);
    if(constructor.Parent.Kind!=HandleKind.TypeReference)continue;
    var type=metadata.GetTypeReference((TypeReferenceHandle)constructor.Parent);
    if(metadata.GetString(type.Name)!="MelonInfoAttribute")continue;
    var blob=metadata.GetBlobReader(attribute.Value);
    if(blob.ReadUInt16()!=1)throw new Exception("Invalid MelonInfo attribute");
    _=blob.ReadSerializedString(); // Type
    _=blob.ReadSerializedString(); // Display name
    compiled=blob.ReadSerializedString()??"";
}
if(compiled!=expected || channel.RootElement.GetProperty("package_version").GetString()!=expected
 || buildDoc.RootElement.GetProperty("label").GetString()!="PLA TEST Build "+expected
 || metadata.GetAssemblyDefinition().Version.ToString()!=expected+".0.0.0")
    throw new Exception($"Compiled runtime identity mismatch: MelonInfo={compiled}, expected={expected}, assembly={metadata.GetAssemblyDefinition().Version}");
Console.WriteLine($"PASS: compiled MelonInfo={compiled}, assembly={metadata.GetAssemblyDefinition().Version}, channel/build/label match.");

using FreedomArrow.Conquest;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;

int checks=0;
void Check(bool yes,string name) { if(!yes)throw new Exception(name); checks++;Console.WriteLine("PASS "+name); }
void Refused(Action action,string name)
{
    try { action(); }
    catch(Exception e) when(e is InvalidDataException or BadImageFormatException or InvalidOperationException) {Check(true,name);return;}
    throw new Exception("Unexpected acceptance: "+name);
}
byte[] original=File.ReadAllBytes(typeof(BuildFingerprint).Assembly.Location);
byte[] regenerated=(byte[])original.Clone();
using(var pe=new PEReader(new MemoryStream(original,false)))
{
    var md=pe.GetMetadataReader();byte[] guid=md.GetGuid(md.GetModuleDefinition().Mvid).ToByteArray();
    byte[] metadata=pe.GetMetadata().GetContent().ToArray();
    int at=Enumerable.Range(0,metadata.Length-15).Single(i=>metadata.AsSpan(i,16).SequenceEqual(guid));
    for(int i=0;i<16;i++)regenerated[pe.PEHeaders.MetadataStartOffset+at+i]^=0x5a;
}
string path="MelonLoader/Il2CppAssemblies/Generated.dll";
string pin=BuildFingerprint.Prefix+BuildFingerprint.Compute(original,true);
BuildFingerprint.Verify(path,original,pin);Check(true,"original wrapper accepted");
BuildFingerprint.Verify(path,regenerated,pin);Check(true,"fresh MVID accepted");
Check(BuildFingerprint.Compute(original,false)!=BuildFingerprint.Compute(regenerated,false),"raw hashes differ");
Refused(()=>BuildFingerprint.Verify(path,regenerated,BuildFingerprint.Compute(original,false)),"strict hash refuses regenerated wrapper");
byte[] changed=(byte[])regenerated.Clone();
using(var pe=new PEReader(new MemoryStream(changed,false)))changed[pe.PEHeaders.SectionHeaders.First(s=>s.Name==".text").PointerToRawData+128]^=1;
Refused(()=>BuildFingerprint.Verify(path,changed,pin),"non-MVID code-section byte rejected");
Refused(()=>BuildFingerprint.Verify("GameAssembly.dll",regenerated,pin),"native binary normalization forbidden");
Refused(()=>BuildFingerprint.Verify("Mods/Mod.dll",regenerated,pin),"mod normalization forbidden");
Refused(()=>BuildFingerprint.Verify(path,new byte[128],pin),"invalid PE refused");
BuildFingerprint.Verify("GameAssembly.dll",original,BuildFingerprint.Compute(original,false));Check(true,"exact native hash still accepted");
Check(original.SequenceEqual(File.ReadAllBytes(typeof(BuildFingerprint).Assembly.Location)),"input bytes preserved");
Console.WriteLine($"{checks} checks passed; no game data or launch required.");

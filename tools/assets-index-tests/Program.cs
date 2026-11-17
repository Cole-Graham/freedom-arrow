// Launcher 1.1.5 per-file Assets install (Lateralus 17 Nov 2026). Runs the real AssetsIndexInstall against a fake file server and a temp
// game folder; with --network it also fetches real files from https://freedomarrow.app/assets/ through a small slice of the live list.
using BAModManager.Core;
using System.IO.Compression;
using System.Net;
using System.Security.Cryptography;
using System.Text.Json;
if(args.Length==2&&args[0]=="--update")
{
 // Real-size check (Lateralus 17 Nov): run the launcher's file-list install on a COPY of a real game folder against the live 0.2.44 list.
 using var web=new HttpClient{Timeout=TimeSpan.FromMinutes(20)};var url="https://freedomarrow.app/assets/index/FreedomArrow-Assets-0.2.44.files.json";
 var bytes=await web.GetByteArrayAsync(url);var file=Path.Combine(Path.GetTempPath(),"fa-0.2.44.files.json");File.WriteAllBytes(file,bytes);
 var pk=new DistributionPackage("freedomarrow.assets.live","0.2.44","FreedomArrow-Assets-0.2.44.bamod","https://freedomarrow.app/assets/FreedomArrow-Assets-0.2.44.bamod",6479921431,"11015eb1ee2ecac84aa0ef7d27633acc6e1ae4a65b162fa3a7d62072a265a1f5",
  new DistributionIndex(url,bytes.Length,Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(bytes)).ToLowerInvariant()));
 AssetsIndexInstall.Client=web;var keepPrefs=new HashSet<string>(StringComparer.OrdinalIgnoreCase){"UserData/FAMusic/voice-presets.txt","UserData/FAMusic/music-history.txt"};
 for(int run=1;run<=2;run++)
 {
  var sw=System.Diagnostics.Stopwatch.StartNew();
  AssetsIndexInstall.Ensure(args[1],file,pk,keepPrefs,s=>Console.WriteLine($"[{sw.Elapsed:mm\\:ss}] {s}"),CancellationToken.None);
  Console.WriteLine($"RUN {run}: {sw.Elapsed.TotalSeconds:0.0} s");
 }
 return;
}
int count=0;
void Check(bool value,string label){if(!value)throw new Exception("FAIL "+label);count++;Console.WriteLine("PASS "+label);}
string Sha(byte[] b)=>Convert.ToHexString(SHA256.HashData(b)).ToLowerInvariant();
var root=Path.Combine(Path.GetTempPath(),"fa-assets-index-test-"+Guid.NewGuid().ToString("N"));var game=Path.Combine(root,"game");Directory.CreateDirectory(game);
var log=new List<string>();void Log(string s){lock(log)log.Add(s);}
var server=new Server();AssetsIndexInstall.Client=new HttpClient(server);
var prefs=new HashSet<string>(StringComparer.OrdinalIgnoreCase){"UserData/FAMusic/voice-presets.txt"};
(string index,DistributionPackage pkg) Publish(string version,Dictionary<string,byte[]> files)
{
 foreach(var b in files.Values){using var ms=new MemoryStream();using(var gz=new GZipStream(ms,CompressionLevel.Fastest,true))gz.Write(b);server.Files[Sha(b)]=ms.ToArray();}
 var mod=JsonSerializer.Serialize(new{id="freedomarrow.assets.live",name="Freedom Arrow Assets",version});
 var idx=JsonSerializer.Serialize(new{schema=1,id="freedomarrow.assets.live",version,package=$"FreedomArrow-Assets-{version}.bamod",files_base="https://fixture.test/assets/files/",mod_json=mod,
  files=files.Select(kv=>new{path=kv.Key,size=kv.Value.LongLength,sha256=Sha(kv.Value)})});
 var bytes=System.Text.Encoding.UTF8.GetBytes(idx);var file=Path.Combine(root,version+".files.json");File.WriteAllBytes(file,bytes);
 return (file,new DistributionPackage("freedomarrow.assets.live",version,$"FreedomArrow-Assets-{version}.bamod","https://fixture.test/assets/x.bamod",1,new string('0',64),new DistributionIndex("https://fixture.test/i.json",bytes.Length,Sha(bytes))));
}
byte[] B(string s)=>System.Text.Encoding.UTF8.GetBytes(s);
string G(string rel)=>Path.Combine(game,rel.Replace('/',Path.DirectorySeparatorChar));
try{
 Directory.Delete(HostedDistribution.CacheRoot,true);
}catch(DirectoryNotFoundException){}
try{
 var v1=new Dictionary<string,byte[]>{["UserData/FAModels/a.fam"]=B("model A v1"),["UserData/FAModels/b.fam"]=B("model B v1"),["UserData/FAMusic/x.mp3"]=B("music X"),
  ["UserData/FAMusic/dup.mp3"]=B("music X"),["Mods/FAModels.dll"]=B("dll v1"),["UserData/FAMusic/voice-presets.txt"]=B("default presets"),["UserData/FAModels/gone.fam"]=B("old model")};
 var (i1,p1)=Publish("0.2.1",v1);
 AssetsIndexInstall.Ensure(game,i1,p1,prefs,Log,CancellationToken.None);
 Check(v1.All(kv=>File.ReadAllBytes(G(kv.Key)).SequenceEqual(kv.Value)),"fresh install writes every file with the right content");
 Check(server.Requests==6,"fresh install downloads each distinct content once ("+server.Requests+" requests for 7 files, 6 contents)");
 var pack=Manifest.Load(game).Packages.Single(p=>p.Info?.Id=="freedomarrow.assets.live");
 Check(pack.Info!.Version=="0.2.1" && pack.Files.Count==7 && pack.Enabled,"package record written with version and files");
 server.Requests=0;AssetsIndexInstall.Ensure(game,i1,p1,prefs,Log,CancellationToken.None);
 Check(server.Requests==0,"second run with nothing changed downloads nothing");
 File.WriteAllBytes(G("UserData/FAModels/b.fam"),B("model B XX"));   // same size, other content
 File.Delete(G("UserData/FAMusic/x.mp3"));
 File.WriteAllBytes(G("UserData/FAMusic/voice-presets.txt"),B("my presets"));
 server.Requests=0;AssetsIndexInstall.Ensure(game,i1,p1,prefs,Log,CancellationToken.None);
 Check(server.Requests==2 && File.ReadAllBytes(G("UserData/FAModels/b.fam")).SequenceEqual(v1["UserData/FAModels/b.fam"]),"damaged and missing files repaired, only those downloaded");
 Check(File.ReadAllText(G("UserData/FAMusic/voice-presets.txt"))=="my presets","player's voice presets kept");
 var v2=new Dictionary<string,byte[]>(v1);v2["UserData/FAModels/a.fam"]=B("model A version 2");v2["UserData/FAModels/new.fam"]=B("new model");v2.Remove("UserData/FAModels/gone.fam");
 var keepEdited=new Dictionary<string,byte[]>(v2);
 var (i2,p2)=Publish("0.2.2",v2);
 server.Requests=0;log.Clear();AssetsIndexInstall.Ensure(game,i2,p2,prefs,Log,CancellationToken.None);
 Check(server.Requests==2,"update downloads only the changed and the new file ("+server.Requests+")");
 Check(!File.Exists(G("UserData/FAModels/gone.fam")),"file dropped from the list and unchanged is removed");
 Check(v2.Where(kv=>kv.Key!="UserData/FAMusic/voice-presets.txt").All(kv=>File.ReadAllBytes(G(kv.Key)).SequenceEqual(kv.Value)),"every file matches version 0.2.2");
 pack=Manifest.Load(game).Packages.Single(p=>p.Info?.Id=="freedomarrow.assets.live");
 Check(pack.Info!.Version=="0.2.2" && !pack.Files.Contains("UserData/FAModels/gone.fam") && pack.Files.Contains("UserData/FAModels/new.fam"),"package record updated to 0.2.2");
 Console.WriteLine("   log: "+string.Join(" | ",log));
 // A dropped file the player changed stays.
 var v3=new Dictionary<string,byte[]>(v2);v3.Remove("UserData/FAModels/new.fam");File.WriteAllBytes(G("UserData/FAModels/new.fam"),B("player edit"));
 var (i3,p3)=Publish("0.2.3",v3);AssetsIndexInstall.Ensure(game,i3,p3,prefs,Log,CancellationToken.None);
 Check(File.ReadAllText(G("UserData/FAModels/new.fam"))=="player edit","dropped file changed by the player is kept");
 // A corrupt download never replaces the file.
 var v4=new Dictionary<string,byte[]>(v3);v4["UserData/FAModels/b.fam"]=B("model B v4!");var (i4,p4)=Publish("0.2.4",v4);
 server.Corrupt=Sha(v4["UserData/FAModels/b.fam"]);bool bad=false;
 try{AssetsIndexInstall.Ensure(game,i4,p4,prefs,Log,CancellationToken.None);}catch(InvalidDataException){bad=true;}
 Check(bad && File.ReadAllBytes(G("UserData/FAModels/b.fam")).SequenceEqual(v1["UserData/FAModels/b.fam"]),"bad checksum rejected, old file left in place");
 Check(!Directory.EnumerateFiles(game,"*.fa-install-*",SearchOption.AllDirectories).Any(),"no temporary files left behind");
 server.Corrupt=null;server.FailOnce=true;AssetsIndexInstall.Ensure(game,i4,p4,prefs,Log,CancellationToken.None);
 Check(File.ReadAllBytes(G("UserData/FAModels/b.fam")).SequenceEqual(v4["UserData/FAModels/b.fam"]),"transient network failure retried");
 // Unsafe list entries are refused.
 foreach(var evil in new[]{"../escape.dll","UserData/../../x","C:/Windows/x","Other/x.dll"})
 {
  var (ie,pe)=Publish("0.2.9",new(){[evil]=B("x")});bool refused=false;
  try{AssetsIndexInstall.Ensure(game,ie,pe,prefs,Log,CancellationToken.None);}catch(InvalidDataException){refused=true;}
  Check(refused,"unsafe path refused: "+evil);
 }
 // Manifest: a file list is accepted next to the package; a bad one is refused; launchers without the field ignore it.
 var manifest=File.ReadAllText(args[0]);var m=HostedDistribution.Parse(manifest);
 var withIndex=m with{Releases=m.Releases.Select(r=>r with{Assets=r.Assets with{Index=new DistributionIndex("https://freedomarrow.app/assets/index/x.files.json",1000,new string('a',64))}}).ToList()};
 var text=JsonSerializer.Serialize(withIndex,new JsonSerializerOptions{PropertyNamingPolicy=JsonNamingPolicy.CamelCase});
 Check(HostedDistribution.Select(HostedDistribution.Parse(text)).Assets.Index?.Size==1000,"manifest with a file list parses");
 bool refusedIdx=false;try{HostedDistribution.Parse(text.Replace("https://freedomarrow.app/assets/index","http://freedomarrow.app/assets/index"));}catch(InvalidDataException){refusedIdx=true;}
 Check(refusedIdx,"non-HTTPS file list refused");
 Check(HostedDistribution.Select(m).Assets.Index==null,"manifest without a file list keeps full-package mode");
}
finally{Directory.Delete(root,true);try{Directory.Delete(HostedDistribution.CacheRoot,true);}catch(DirectoryNotFoundException){}}
if(args.Contains("--network"))
{
 // Real files from R2 through a 25-file slice of the live 0.2.44 list (smallest files, to keep it short).
 using var web=new HttpClient();var url="https://freedomarrow.app/assets/index/FreedomArrow-Assets-0.2.44.files.json";
 var full=await web.GetByteArrayAsync(url);var doc=JsonSerializer.Deserialize<AssetsIndex>(full,new JsonSerializerOptions{PropertyNameCaseInsensitive=true})!;
 var slice=doc with{Files=doc.Files.OrderBy(f=>f.Size).Take(20).Concat(doc.Files.Where(f=>f.Path.EndsWith(".fam")).OrderBy(f=>f.Size).Take(5)).DistinctBy(f=>f.Path).ToList()};
 var groot=Path.Combine(Path.GetTempPath(),"fa-assets-net-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(groot);
 try{
  var sliceBytes=JsonSerializer.SerializeToUtf8Bytes(slice);var sf=Path.Combine(groot,"slice.files.json");File.WriteAllBytes(sf,sliceBytes);
  var pk=new DistributionPackage("freedomarrow.assets.live","0.2.44","FreedomArrow-Assets-0.2.44.bamod","https://freedomarrow.app/assets/FreedomArrow-Assets-0.2.44.bamod",1,new string('0',64),new DistributionIndex(url,sliceBytes.Length,Sha(sliceBytes)));
  AssetsIndexInstall.Client=web;var g2=Path.Combine(groot,"game");Directory.CreateDirectory(g2);log.Clear();
  AssetsIndexInstall.Ensure(g2,sf,pk,prefs,Log,CancellationToken.None);
  Check(slice.Files.All(f=>{var p=Path.Combine(g2,f.Path);return File.Exists(p)&&new FileInfo(p).Length==f.Size&&Sha(File.ReadAllBytes(p))==f.Sha256;}),$"{slice.Files.Count} real files downloaded from R2 and verified");
  Console.WriteLine("   log: "+string.Join(" | ",log));
 }finally{Directory.Delete(groot,true);try{Directory.Delete(HostedDistribution.CacheRoot,true);}catch(DirectoryNotFoundException){}}
}
Console.WriteLine(JsonSerializer.Serialize(new{checks=count,network=args.Contains("--network")}));

sealed class Server:HttpMessageHandler
{
 public readonly Dictionary<string,byte[]> Files=new();public int Requests;public string? Corrupt;public bool FailOnce;
 protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage req,CancellationToken ct)
 {
  lock(this){Requests++;if(FailOnce){FailOnce=false;throw new HttpRequestException("temporary");}}
  var name=Path.GetFileName(req.RequestUri!.AbsolutePath).Replace(".gz","");
  if(!Files.TryGetValue(name,out var gz))return Task.FromResult(new HttpResponseMessage(HttpStatusCode.NotFound){RequestMessage=req});
  if(name==Corrupt){var raw=new MemoryStream();using(var g=new GZipStream(new MemoryStream(gz),CompressionMode.Decompress))g.CopyTo(raw);var b=raw.ToArray();b[0]^=0xff;
   var ms=new MemoryStream();using(var z=new GZipStream(ms,CompressionLevel.Fastest,true))z.Write(b);gz=ms.ToArray();}
  return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK){RequestMessage=req,Content=new ByteArrayContent(gz)});
 }
}

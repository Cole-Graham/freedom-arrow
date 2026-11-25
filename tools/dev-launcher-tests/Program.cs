// Dev launcher FreedomArrowDev.exe (Lateralus 24 Nov 2026: "select various test builds and dev builds ... incremental asset updates").
// Compiled with FA_DEVCHANNEL like the dev launcher. Offline: dev-list rules, the build choice, and switching Models + Music/Voices to an
// older build file by file. --live: the real signed dev list on freedomarrow.app, every file list in it, and what each switch downloads.
using BAModManager.Core;
using System.IO.Compression;
using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
int count=0;
void Check(bool value,string label){if(!value)throw new Exception("FAIL "+label);count++;Console.WriteLine("PASS "+label);}
void Throws<T>(Action f,string label) where T:Exception{try{f();}catch(T){Check(true,label);return;}throw new Exception("FAIL (no "+typeof(T).Name+") "+label);}
string Sha(byte[] b)=>Convert.ToHexString(SHA256.HashData(b)).ToLowerInvariant();
var json=new JsonSerializerOptions{PropertyNameCaseInsensitive=true};
Check(HostedDistribution.DevChannel && HostedDistribution.Channel=="dev" && SignedManifest.Url.EndsWith("/manifest/dev.signed.json"),"compiled as the dev launcher: dev list address");
Check(Path.GetFileName(HostedDistribution.ManifestFile)=="dev-manifest.signed.json","accepted dev list cached apart from the live one");
if(args.Contains("--live"))
{
 using var web=new HttpClient{Timeout=TimeSpan.FromMinutes(5)};
 var m=HostedDistribution.Parse(SignedManifest.Open(await web.GetByteArrayAsync(SignedManifest.Url+"?t="+DateTime.UtcNow.Ticks)));
 Check(m.Channel=="dev" && m.Releases.Count>0,$"real dev list verifies with the compiled-in key: serial {m.Serial}, {m.Releases.Count} builds, newest {m.Current}");
 Throws<InvalidDataException>(()=>HostedDistribution.Parse(SignedManifest.Open(web.GetByteArrayAsync("https://freedomarrow.app/manifest/live.signed.json").Result)),"the player list (channel live) is refused by the dev launcher");
 var lists=new Dictionary<string,AssetsIndex>();
 foreach(var r in m.Releases)
 {
  var i=r.Assets.Index!;if(lists.ContainsKey(r.Assets.Version))continue;
  var b=await web.GetByteArrayAsync(i.Url);Check(b.LongLength==i.Size && Sha(b)==i.Sha256.ToLowerInvariant(),$"{r.Version}: Models & music {r.Assets.Version} file list matches the signed list");
  var f=Path.Combine(Path.GetTempPath(),"fa-dev-"+i.Sha256+".json");File.WriteAllBytes(f,b);lists[r.Assets.Version]=AssetsIndexInstall.Load(f,r.Assets);File.Delete(f);
 }
 // What PLAY downloads when switching from one build's Models & music to another's (changed or new files; identical content once).
 var order=m.Releases.Select(r=>r.Assets.Version).Distinct().ToList();
 for(int k=0;k+1<order.Count;k++)
 {
  var to=lists[order[k]];var from=lists[order[k+1]].Files.ToDictionary(f=>f.Path,f=>f.Sha256,StringComparer.OrdinalIgnoreCase);
  var need=to.Files.Where(f=>!from.TryGetValue(f.Path,out var s)||!s.Equals(f.Sha256,StringComparison.OrdinalIgnoreCase)).ToList();
  var distinct=need.DistinctBy(f=>f.Sha256.ToLowerInvariant()).ToList();
  Console.WriteLine($"   {order[k+1]} -> {order[k]}: {need.Count} of {to.Files.Count} files, {distinct.Sum(f=>f.Size)/1048576.0:0} MB unpacked (full package {to.Files.Sum(f=>f.Size)/1073741824.0:0.0} GB)");
  // and the way back
  var back=lists[order[k+1]];var toMap=to.Files.ToDictionary(f=>f.Path,f=>f.Sha256,StringComparer.OrdinalIgnoreCase);
  var needBack=back.Files.Where(f=>!toMap.TryGetValue(f.Path,out var s)||!s.Equals(f.Sha256,StringComparison.OrdinalIgnoreCase)).DistinctBy(f=>f.Sha256.ToLowerInvariant()).ToList();
  Console.WriteLine($"   {order[k]} -> {order[k+1]}: {needBack.Count} files, {needBack.Sum(f=>f.Size)/1048576.0:0} MB unpacked");
 }
 Console.WriteLine(JsonSerializer.Serialize(new{checks=count,live=true}));
 return;
}
var root=Path.Combine(Path.GetTempPath(),"fa-dev-launcher-test-"+Guid.NewGuid().ToString("N"));var game=Path.Combine(root,"game");Directory.CreateDirectory(game);
try{Directory.Delete(HostedDistribution.CacheRoot,true);}catch(DirectoryNotFoundException){}
var server=new Server();AssetsIndexInstall.Client=new HttpClient(server);
var log=new List<string>();void Log(string s){lock(log)log.Add(s);}
var prefs=new HashSet<string>(StringComparer.OrdinalIgnoreCase);
byte[] B(string s)=>Encoding.UTF8.GetBytes(s);
string G(string rel)=>Path.Combine(game,rel.Replace('/',Path.DirectorySeparatorChar));
(string index,DistributionPackage pkg) Publish(string version,Dictionary<string,byte[]> files)
{
 foreach(var b in files.Values){using var ms=new MemoryStream();using(var gz=new GZipStream(ms,CompressionLevel.Fastest,true))gz.Write(b);server.Files[Sha(b)]=ms.ToArray();}
 var mod=JsonSerializer.Serialize(new{id="freedomarrow.assets.live",name="Freedom Arrow Assets",version});
 var idx=JsonSerializer.Serialize(new{schema=1,id="freedomarrow.assets.live",version,package=$"FreedomArrow-Assets-{version}.bamod",files_base="https://fixture.test/assets/files/",mod_json=mod,
  files=files.Select(kv=>new{path=kv.Key,size=kv.Value.LongLength,sha256=Sha(kv.Value)})});
 var bytes=Encoding.UTF8.GetBytes(idx);var file=Path.Combine(root,version+".files.json");File.WriteAllBytes(file,bytes);
 return (file,new DistributionPackage("freedomarrow.assets.live",version,$"FreedomArrow-Assets-{version}.bamod","https://freedomarrow.app/assets/x.bamod",1,new string('0',64),new DistributionIndex("https://freedomarrow.app/assets/index/x.json",bytes.Length,Sha(bytes))));
}
string List(string channel,bool withIndex=true,string current="0.9.7-dev.2")=>$$"""
{"schema":1,"channel":"{{channel}}","current":"{{current}}","locked_version":null,"serial":5,"releases":[
 {"version":"0.9.7-dev.2","note":"dev build · 25 Nov 10:00","gameplay":{"id":"freedomarrow.gameplay","version":"0.9.7-dev.2","filename":"g2.bamod","url":"https://freedomarrow.app/gameplay/g2.bamod","size":1,"sha256":"{{new string('b',64)}}"},
  "assets":{"id":"freedomarrow.assets.live","version":"0.2.96","filename":"a2.bamod","url":"https://freedomarrow.app/assets/a2.bamod","size":1,"sha256":"{{new string('c',64)}}"
   {{(withIndex?",\"index\":{\"url\":\"https://freedomarrow.app/assets/index/a2.files.json\",\"size\":10,\"sha256\":\""+new string('d',64)+"\"}":"")}} } },
 {"version":"0.9.6","note":"live release · 24 Nov 03:51","gameplay":{"id":"freedomarrow.gameplay","version":"0.9.6","filename":"g1.bamod","url":"https://freedomarrow.app/gameplay/g1.bamod","size":1,"sha256":"{{new string('b',64)}}"},
  "assets":{"id":"freedomarrow.assets.live","version":"0.2.94","filename":"a1.bamod","url":"https://freedomarrow.app/assets/a1.bamod","size":1,"sha256":"{{new string('c',64)}}",
   "index":{"url":"https://freedomarrow.app/assets/index/a1.files.json","size":10,"sha256":"{{new string('d',64)}}" } } }]}
""";
try{
 // --- the dev list ---
 var m=HostedDistribution.Parse(List("dev"));
 Check(m.Releases.Count==2 && m.Releases[0].Note=="dev build · 25 Nov 10:00","dev list parses, with the build note shown in the picker");
 Throws<InvalidDataException>(()=>HostedDistribution.Parse(List("live")),"a list for the player launcher (channel live) is refused");
 Throws<InvalidDataException>(()=>HostedDistribution.Parse(List("dev",withIndex:false)),"a dev build without a Models & music file list is refused (never the full 10+ GB package)");
 // --- the build choice ---
 HostedDistribution.Chosen=null;Check(HostedDistribution.Select(m).Version=="0.9.7-dev.2","no choice: the newest build");
 HostedDistribution.Chosen="0.9.6";Check(HostedDistribution.Select(m).Version=="0.9.6" && HostedDistribution.Chosen=="0.9.6","picked 0.9.6: PLAY uses 0.9.6, and the choice is saved");
 HostedDistribution.Chosen="0.9.5-dev.1";Check(HostedDistribution.Select(m).Version=="0.9.7-dev.2","a picked build no longer on the list falls back to the newest");
 HostedDistribution.Chosen=null;
 // --- Models & music: newer build, then back to the older one, file by file ---
 var v1=new Dictionary<string,byte[]>{["UserData/FAModels/a.fam"]=B("A v1"),["UserData/FAModels/b.fam"]=B("B same"),["Mods/FAModels.dll"]=B("dll v1"),["UserData/FAModels/old.fam"]=B("only in v1")};
 var v2=new Dictionary<string,byte[]>{["UserData/FAModels/a.fam"]=B("A v2"),["UserData/FAModels/b.fam"]=B("B same"),["Mods/FAModels.dll"]=B("dll v2"),["UserData/FAModels/new.fam"]=B("only in v2")};
 var (i1,p1)=Publish("0.2.94",v1);var (i2,p2)=Publish("0.2.96",v2);
 AssetsIndexInstall.Ensure(game,i1,p1,prefs,Log,CancellationToken.None);server.Requests=0;
 AssetsIndexInstall.Ensure(game,i2,p2,prefs,Log,CancellationToken.None);
 Check(server.Requests==3,"switch to the newer build downloads only the 3 changed or new files ("+server.Requests+")");
 Check(v2.All(kv=>File.ReadAllBytes(G(kv.Key)).SequenceEqual(kv.Value)) && !File.Exists(G("UserData/FAModels/old.fam")),"newer build installed exactly");
 server.Requests=0;AssetsIndexInstall.Ensure(game,i1,p1,prefs,Log,CancellationToken.None);
 Check(server.Requests==3,"switch back to the OLDER build downloads only the 3 files that differ ("+server.Requests+")");
 Check(v1.All(kv=>File.ReadAllBytes(G(kv.Key)).SequenceEqual(kv.Value)) && !File.Exists(G("UserData/FAModels/new.fam")),"older build installed exactly (the player launcher would keep the newer files)");
 Check(Manifest.Load(game).Packages.Single(p=>p.Info?.Id=="freedomarrow.assets.live").Info!.Version=="0.2.94","package record shows the picked older version");
 server.Requests=0;AssetsIndexInstall.Ensure(game,i1,p1,prefs,Log,CancellationToken.None);
 Check(server.Requests==0,"PLAY again on the same build downloads nothing");
}
finally{Directory.Delete(root,true);try{Directory.Delete(HostedDistribution.CacheRoot,true);}catch(DirectoryNotFoundException){}}
Console.WriteLine(JsonSerializer.Serialize(new{checks=count,live=false}));

sealed class Server:HttpMessageHandler
{
 public readonly Dictionary<string,byte[]> Files=new();public int Requests;
 protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage req,CancellationToken ct)
 {
  lock(this)Requests++;
  var name=Path.GetFileName(req.RequestUri!.AbsolutePath).Replace(".gz","");
  if(!Files.TryGetValue(name,out var gz))return Task.FromResult(new HttpResponseMessage(HttpStatusCode.NotFound){RequestMessage=req});
  return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK){RequestMessage=req,Content=new ByteArrayContent(gz)});
 }
}

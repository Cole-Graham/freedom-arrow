using BAModManager.Core;
using System.Net;
using System.Security.Cryptography;
using System.Text.Json;
int count=0;
void Check(bool value,string label){if(!value)throw new Exception(label);count++;Console.WriteLine("PASS "+label);}
void Reject(Action action,string label){try{action();throw new Exception("Accepted bad manifest: "+label);}catch(InvalidDataException){Check(true,label);}}
var source=File.ReadAllText(args[0]);var m=HostedDistribution.Parse(source);
Check(HostedDistribution.Select(m).Version=="0.7.0-dev.45","published manifest selects locked dev45");
var newer=m.Releases[0] with {Version="0.7.0-dev.47",Gameplay=m.Releases[0].Gameplay with {Version="0.7.0-dev.47"}};
var changed=m with {Current=newer.Version,Releases=new(){m.Releases[0],newer}};
Check(HostedDistribution.Select(HostedDistribution.Parse(JsonSerializer.Serialize(changed))).Version=="0.7.0-dev.45","lock beats newer current release");
Check(HostedDistribution.Select(HostedDistribution.Parse(JsonSerializer.Serialize(changed with{LockedVersion=null}))).Version=="0.7.0-dev.47","unlocked manifest selects configured current");
Reject(()=>HostedDistribution.Parse(source.Replace("\"schema\": 1","\"schema\": 2")),"unsupported schema rejected");
Reject(()=>HostedDistribution.Parse(source.Replace("0.7.0-dev.45\",\n  \"releases","0.7.0-dev.99\",\n  \"releases")),"missing locked release rejected");
Reject(()=>HostedDistribution.Parse(source.Replace("https://","http://")),"non HTTPS package rejected");
Reject(()=>HostedDistribution.Parse(source.Replace("FreedomArrow-0.7.0-dev.45.bamod","../escape.bamod")),"unsafe filename rejected");
Reject(()=>HostedDistribution.Parse(source.Replace("33323fc1c760acabcc87cc1e237e99251d2d2495a14c858977791b0cf7d2ab5d","bad")),"bad hash rejected");
var root=Path.Combine(Path.GetTempPath(),"fa-manifest-test-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(root);
try{
 var cachedManifest=Path.Combine(root,"manifest.json");File.WriteAllText(cachedManifest,source);
 using(var offline=new HttpClient(new DelegateHandler(_=>throw new HttpRequestException("offline"))))
 {
  var fallback=await HostedDistribution.ReadManifestAsync(offline,"https://example.test/manifest",cachedManifest,null,CancellationToken.None);
  Check(HostedDistribution.Select(fallback).Version=="0.7.0-dev.45","offline cached manifest retains locked release");
 }
 using(var invalid=new HttpClient(new DelegateHandler(req=>new HttpResponseMessage(HttpStatusCode.OK){RequestMessage=req,Content=new StringContent("{}",System.Text.Encoding.UTF8,"application/json")})))
 {
  bool bad=false;try{await HostedDistribution.ReadManifestAsync(invalid,"https://example.test/manifest",cachedManifest,null,CancellationToken.None);}catch(InvalidDataException){bad=true;}
  Check(bad,"invalid online manifest blocks instead of silently falling back");
 }
 var bytes=Enumerable.Range(0,4096).Select(x=>(byte)(x%251)).ToArray();
 var p=new DistributionPackage("freedomarrow.gameplay","fixture","fixture.bamod","https://drive.google.com/uc?id=fixture",bytes.Length,Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant());
 var handler=new FixtureHandler(bytes);using var http=new HttpClient(handler);
 var path=await HostedDistribution.EnsurePackageAsync(p,http,root,null,CancellationToken.None);
 Check(File.ReadAllBytes(path).SequenceEqual(bytes),"Drive confirmation download verifies bytes");
 Check(handler.Requests==2,"Drive confirmation followed once");
 var before=handler.Requests;await HostedDistribution.EnsurePackageAsync(p,http,root,null,CancellationToken.None);
 Check(handler.Requests==before,"verified cache causes no network calls");
 File.Delete(path);File.WriteAllBytes(path+".part",bytes.Take(777).ToArray());handler.Confirm=false;
 path=await HostedDistribution.EnsurePackageAsync(p,http,root,null,CancellationToken.None);
 Check(handler.LastRange==777 && File.ReadAllBytes(path).SequenceEqual(bytes),"partial download resumes and verifies");
 File.Delete(path);File.WriteAllBytes(path+".part",bytes.Take(99).ToArray());handler.IgnoreRange=true;
 path=await HostedDistribution.EnsurePackageAsync(p,http,root,null,CancellationToken.None);
 Check(File.ReadAllBytes(path).SequenceEqual(bytes),"server ignoring range restarts safely");
 File.WriteAllText(path,"damaged cache");handler.IgnoreRange=false;
 path=await HostedDistribution.EnsurePackageAsync(p,http,root,null,CancellationToken.None);
 Check(File.ReadAllBytes(path).SequenceEqual(bytes),"damaged cache downloaded again");
 File.Delete(path);handler.Corrupt=true;
 bool rejected=false;try{await HostedDistribution.EnsurePackageAsync(p,http,root,null,CancellationToken.None);}catch(InvalidDataException){rejected=true;}
 Check(rejected && !File.Exists(path),"bad download checksum never committed");
 Check(!File.Exists(path+".part"),"bad checksum partial removed");
 handler.Corrupt=false;handler.FailOnce=true;
 path=await HostedDistribution.EnsurePackageAsync(p,http,root,null,CancellationToken.None);
 Check(File.ReadAllBytes(path).SequenceEqual(bytes),"transient network failure retries successfully");
 using var stop=new CancellationTokenSource();stop.Cancel();bool cancelled=false;File.Delete(path);
 try{await HostedDistribution.EnsurePackageAsync(p,http,root,null,stop.Token);}catch(OperationCanceledException){cancelled=true;}
 Check(cancelled && !File.Exists(path),"cancelled transfer does not commit package");
 Console.WriteLine(JsonSerializer.Serialize(new{checks=count,real_network_tested=false,game_started=false}));
}finally{Directory.Delete(root,true);}
if(args.Contains("--network") || args.Contains("--network-reuse"))
{
 if(!args.Contains("--network-reuse") && Directory.Exists(HostedDistribution.CacheRoot)) throw new Exception("Network test cache already exists; inspect first");
 Console.WriteLine("NETWORK: reading live manifest and downloading both real packages");
 await HostedDistribution.PrepareAsync(new Progress<LaunchProgress>(p=>{if(p.Fraction==null)Console.WriteLine(p.Text);}),CancellationToken.None);
 Check(HostedDistribution.Active.Version=="0.7.0-dev.45","real public manifest respects dev45 lock");
 var g=HostedDistribution.ArchivePath(HostedDistribution.Active.Gameplay);var a=HostedDistribution.ArchivePath(HostedDistribution.Active.Assets);
 Check(HostedDistribution.ValidFile(g,HostedDistribution.Active.Gameplay)&&HostedDistribution.ValidFile(a,HostedDistribution.Active.Assets),"both real public package downloads verify");
 var gt=File.GetLastWriteTimeUtc(g);var at=File.GetLastWriteTimeUtc(a);
 await HostedDistribution.PrepareAsync(new Progress<LaunchProgress>(p=>{if(p.Fraction==null)Console.WriteLine(p.Text);}),CancellationToken.None);
 Check(gt==File.GetLastWriteTimeUtc(g)&&at==File.GetLastWriteTimeUtc(a),"second real check reuses both cached archives");
 Console.WriteLine(JsonSerializer.Serialize(new{checks=count,real_network_tested=true,game_started=false,gameplay_bytes=new FileInfo(g).Length,asset_bytes=new FileInfo(a).Length}));
}
sealed class FixtureHandler(byte[] data):HttpMessageHandler
{
 public int Requests;public bool Confirm=true,IgnoreRange,Corrupt,FailOnce;public long? LastRange;
 protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage req,CancellationToken ct)
 {
  ct.ThrowIfCancellationRequested();Requests++;if(FailOnce){FailOnce=false;throw new HttpRequestException("temporary");}
  if(Confirm && req.RequestUri!.Host=="drive.google.com")
   return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK){RequestMessage=req,Content=new StringContent("<form action=\"https://drive.usercontent.google.com/download\"><input name=\"id\" value=\"fixture\"></form>",System.Text.Encoding.UTF8,"text/html")});
  LastRange=req.Headers.Range?.Ranges.Single().From;long from=IgnoreRange?0:LastRange??0;var payload=data.Skip((int)from).ToArray();if(Corrupt)payload[0]^=0xff;
  var r=new HttpResponseMessage(from>0?HttpStatusCode.PartialContent:HttpStatusCode.OK){RequestMessage=req,Content=new ByteArrayContent(payload)};
  if(from>0)r.Content.Headers.ContentRange=new System.Net.Http.Headers.ContentRangeHeaderValue(from,data.Length-1,data.Length);
  return Task.FromResult(r);
 }
}

sealed class DelegateHandler(Func<HttpRequestMessage,HttpResponseMessage> handle):HttpMessageHandler
{
 protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage req,CancellationToken ct)=>Task.FromResult(handle(req));
}

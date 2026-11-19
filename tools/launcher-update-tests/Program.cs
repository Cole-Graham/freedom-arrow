// Launcher 1.1.9 (Lateralus 19 Nov 2026): signed version list and self-update. Fixture tests use a throw-away test key; --live checks the
// real list on freedomarrow.app against the real public key compiled into the launcher; --self-swap replaces this running exe (run it
// under Windows or Wine to check that a running exe can be renamed).
using BAModManager.Core;
using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
int count=0;
void Check(bool value,string label){if(!value)throw new Exception("FAIL "+label);count++;Console.WriteLine("PASS "+label);}
async Task Throws<T>(Func<Task> f,string label) where T:Exception{try{await f();}catch(T){Check(true,label);return;}throw new Exception("FAIL (no "+typeof(T).Name+") "+label);}
string Sha(byte[] b)=>Convert.ToHexString(SHA256.HashData(b)).ToLowerInvariant();
var realKeys=SignedManifest.TrustedKeys;
if(args.Contains("--live"))
{
 using var web=new HttpClient();var env=await web.GetByteArrayAsync(SignedManifest.Url+"?t="+DateTime.UtcNow.Ticks);
 var m=HostedDistribution.Parse(SignedManifest.Open(env));
 Check(m.Serial>0,"live signed list verifies with the compiled-in key, serial "+m.Serial);
 Console.WriteLine(JsonSerializer.Serialize(new{m.Serial,m.Current,m.LockedVersion,m.Launcher,m.MelonLoader}));
 if(m.MelonLoader is {} ml){var z=await web.GetByteArrayAsync(ml.Url);Check(z.LongLength==ml.Size&&Sha(z)==ml.Sha256.ToLowerInvariant(),"live MelonLoader zip matches its signed SHA-256");}
 if(m.Launcher is {} l){var x=await web.GetByteArrayAsync(l.Url);Check(x.LongLength==l.Size&&Sha(x)==l.Sha256.ToLowerInvariant(),"live launcher exe "+l.Version+" matches its signed SHA-256");}
 return;
}
using var key=ECDsa.Create(ECCurve.NamedCurves.nistP256);
SignedManifest.TrustedKeys=new[]{Convert.ToBase64String(key.ExportSubjectPublicKeyInfo())};
byte[] Envelope(string manifest,ECDsa k){var body=Encoding.UTF8.GetBytes(manifest);var sig=k.SignData(Encoding.UTF8.GetBytes("freedomarrow-manifest-v1\n").Concat(body).ToArray(),HashAlgorithmName.SHA256,DSASignatureFormat.Rfc3279DerSequence);
 return JsonSerializer.SerializeToUtf8Bytes(new{manifest=Convert.ToBase64String(body),signature=Convert.ToBase64String(sig)});}
var exeBytes=Enumerable.Range(0,300000).Select(i=>(byte)(i*7%256)).ToArray();
string Manifest(long serial,string launcherVersion="1.2.0",string? launcherSha=null,string host="freedomarrow.app",long? size=null)=>"""
{"schema":1,"channel":"live","current":"0.9.0-dev.41","locked_version":"0.9.0-dev.41","serial":SERIAL,
 "launcher":{"version":"LVER","url":"https://HOST/launcher/FreedomArrow-LVER.exe","size":LSIZE,"sha256":"LSHA"},
 "melonloader":{"tag":"v0.7.3","asset":"MelonLoader.x64.zip","url":"https://freedomarrow.app/launcher/ml.zip","size":10,"sha256":"HA"},
 "releases":[{"version":"0.9.0-dev.41","gameplay":{"id":"freedomarrow.gameplay","version":"0.9.0-dev.41","filename":"g.bamod","url":"https://freedomarrow.app/gameplay/g.bamod","size":1,"sha256":"HB"},
  "assets":{"id":"freedomarrow.assets.live","version":"0.2.46","filename":"a.bamod","url":"https://freedomarrow.app/assets/a.bamod","size":1,"sha256":"HC"}}]}
""".Replace("SERIAL",serial.ToString()).Replace("LVER",launcherVersion).Replace("HOST",host).Replace("LSIZE",(size??exeBytes.Length).ToString())
 .Replace("LSHA",launcherSha??Sha(exeBytes)).Replace("HA",new string('a',64)).Replace("HB",new string('b',64)).Replace("HC",new string('c',64));
var root=Path.Combine(Path.GetTempPath(),"fa-update-test-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(root);
try{
 // --- signature ---
 var good=Envelope(Manifest(100),key);
 Check(HostedDistribution.Parse(SignedManifest.Open(good)).Serial==100,"signed list accepted");
 var tampered=JsonSerializer.Deserialize<Dictionary<string,string>>(good)!;var body=Convert.FromBase64String(tampered["manifest"]);body[body.Length/2]^=1;tampered["manifest"]=Convert.ToBase64String(body);
 await Throws<InvalidDataException>(()=>{SignedManifest.Open(JsonSerializer.SerializeToUtf8Bytes(tampered));return Task.CompletedTask;},"one changed byte in the list is refused");
 using(var other=ECDsa.Create(ECCurve.NamedCurves.nistP256))
  await Throws<InvalidDataException>(()=>{SignedManifest.Open(Envelope(Manifest(100),other));return Task.CompletedTask;},"list signed by another key is refused");
 await Throws<InvalidDataException>(()=>{SignedManifest.Open(Encoding.UTF8.GetBytes(Manifest(100)));return Task.CompletedTask;},"unsigned live.json is refused");
 var swapped=JsonSerializer.Deserialize<Dictionary<string,string>>(good)!;swapped["manifest"]=Convert.ToBase64String(Encoding.UTF8.GetBytes(Manifest(100,launcherSha:new string('d',64))));
 await Throws<InvalidDataException>(()=>{SignedManifest.Open(JsonSerializer.SerializeToUtf8Bytes(swapped));return Task.CompletedTask;},"good signature with a swapped launcher checksum is refused");
 await Throws<InvalidDataException>(()=>{HostedDistribution.Parse(SignedManifest.Open(Envelope(Manifest(100,host:"evil.example"),key)));return Task.CompletedTask;},"launcher from another host is refused");
 SignedManifest.TrustedKeys=realKeys;
 await Throws<InvalidDataException>(()=>{SignedManifest.Open(good);return Task.CompletedTask;},"real launcher key refuses the test-key list");
 SignedManifest.TrustedKeys=new[]{Convert.ToBase64String(key.ExportSubjectPublicKeyInfo())};
 // --- network, cache and rollback ---
 var cache=Path.Combine(root,"live-manifest.signed.json");var served=good;
 using var web=new HttpClient(new Handler(_=>served));
 var (m1,e1)=await HostedDistribution.ReadManifestAsync(web,"https://freedomarrow.app/manifest/live.signed.json",cache,null,CancellationToken.None);
 Check(m1.Serial==100&&e1.SequenceEqual(good),"signed list read from the network");File.WriteAllBytes(cache,e1);
 served=Envelope(Manifest(99),key);
 await Throws<InvalidDataException>(()=>HostedDistribution.ReadManifestAsync(web,"https://freedomarrow.app/manifest/live.signed.json",cache,null,CancellationToken.None),"older signed list (rollback) is refused");
 served=Envelope(Manifest(101),key);
 Check((await HostedDistribution.ReadManifestAsync(web,"https://freedomarrow.app/manifest/live.signed.json",cache,null,CancellationToken.None)).Manifest.Serial==101,"newer signed list accepted");
 served=Encoding.UTF8.GetBytes(Manifest(200));
 await Throws<InvalidDataException>(()=>HostedDistribution.ReadManifestAsync(web,"https://freedomarrow.app/manifest/live.signed.json",cache,null,CancellationToken.None),"unsigned list online is refused, not replaced by the cache");
 using var offline=new HttpClient(new Handler(_=>throw new HttpRequestException("offline")));
 Check((await HostedDistribution.ReadManifestAsync(offline,"https://freedomarrow.app/manifest/live.signed.json",cache,null,CancellationToken.None)).Manifest.Serial==100,"offline uses the verified cached list");
 var bad=File.ReadAllBytes(cache);bad[bad.Length/2]^=1;File.WriteAllBytes(cache,bad);
 await Throws<HttpRequestException>(()=>HostedDistribution.ReadManifestAsync(offline,"https://freedomarrow.app/manifest/live.signed.json",cache,null,CancellationToken.None),"offline with a damaged cache is refused");
 // --- self-update ---
 var exe=Path.Combine(root,"FreedomArrow.exe");var oldExe=Encoding.UTF8.GetBytes("old launcher");
 HttpClient Exe(byte[] b,long? length=null)=>new(new Handler(_=>b,length));
 File.WriteAllBytes(exe,oldExe);
 Check(!await SelfUpdate.ApplyAsync(HostedDistribution.Parse(Manifest(1,"1.1.9")).Launcher,exe,Exe(exeBytes),null,CancellationToken.None)&&File.ReadAllBytes(exe).SequenceEqual(oldExe),"same version is not installed");
 Check(!await SelfUpdate.ApplyAsync(HostedDistribution.Parse(Manifest(1,"1.1.8")).Launcher,exe,Exe(exeBytes),null,CancellationToken.None)&&File.ReadAllBytes(exe).SequenceEqual(oldExe),"older version is never installed");
 var corrupt=exeBytes.ToArray();corrupt[1234]^=1;
 await Throws<InvalidDataException>(()=>SelfUpdate.ApplyAsync(HostedDistribution.Parse(Manifest(1)).Launcher,exe,Exe(corrupt),null,CancellationToken.None),"tampered launcher download refused");
 Check(File.ReadAllBytes(exe).SequenceEqual(oldExe)&&!File.Exists(exe+".new")&&!File.Exists(exe+".old"),"after a refused download the old launcher is untouched and nothing is left");
 await Throws<InvalidDataException>(()=>SelfUpdate.ApplyAsync(HostedDistribution.Parse(Manifest(1)).Launcher,exe,Exe(exeBytes.Concat(new byte[]{1}).ToArray()),null,CancellationToken.None),"oversized launcher download refused");
 Check(File.ReadAllBytes(exe).SequenceEqual(oldExe),"old launcher untouched after the oversized download");
 Check(await SelfUpdate.ApplyAsync(HostedDistribution.Parse(Manifest(1)).Launcher,exe,Exe(exeBytes),null,CancellationToken.None),"newer signed launcher installed");
 Check(File.ReadAllBytes(exe).SequenceEqual(exeBytes)&&File.ReadAllBytes(exe+".old").SequenceEqual(oldExe),"new exe in place, previous kept as .old");
 SelfUpdate.CleanUp(exe);Check(!File.Exists(exe+".old"),"next start removes .old");
 if(args.Contains("--self-swap"))
 {
  var self=Environment.ProcessPath!;var mine=File.ReadAllBytes(self);var copy=Path.Combine(root,"self.bak");File.WriteAllBytes(copy,mine);
  var marker=Encoding.UTF8.GetBytes("replacement for the running exe");
  var release=new LauncherRelease("9.0.0","https://freedomarrow.app/launcher/x.exe",marker.Length,Sha(marker));
  Check(await SelfUpdate.ApplyAsync(release,self,Exe(marker),null,CancellationToken.None),"running exe renamed and replaced ("+self+")");
  Check(File.ReadAllBytes(self).SequenceEqual(marker),"running exe path now holds the new file");
  File.Move(self,self+".test",true);File.Move(self+".old",self,true);File.Delete(self+".test");
  Check(File.ReadAllBytes(self).SequenceEqual(mine),"running exe restored after the test");
 }
 Console.WriteLine(JsonSerializer.Serialize(new{checks=count}));
}finally{Directory.Delete(root,true);}
sealed class Handler(Func<HttpRequestMessage,byte[]> body,long? length=null):HttpMessageHandler
{
 protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage req,CancellationToken ct)
 {
  var r=new HttpResponseMessage(HttpStatusCode.OK){RequestMessage=req,Content=new ByteArrayContent(body(req))};
  if(length!=null)r.Content.Headers.ContentLength=length;return Task.FromResult(r);
 }
}

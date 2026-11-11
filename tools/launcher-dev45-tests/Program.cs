using BAModManager.Core;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Nodes;
int checks = 0;
void Check(bool ok, string name) { if (!ok) throw new Exception(name); checks++; Console.WriteLine("PASS " + name); }
void Rejected(Action action, string name) { bool rejected = false; try { action(); } catch(InvalidDataException) { rejected = true; } catch(FileNotFoundException) { rejected = true; } Check(rejected,name); }
var archive = Path.Combine(AppContext.BaseDirectory,PinnedFreedomArrow.FileName);
File.Copy(args[0],archive,true);
var assets = PinnedFreedomArrow.AssetsArchivePath; File.Copy(args[1],assets,true);
var temp = Path.Combine(Path.GetTempPath(), "fa-launcher45-"+Guid.NewGuid().ToString("N"));
Directory.CreateDirectory(temp);
var settings = AppSettings.FolderPath;
if (Directory.Exists(settings)) throw new Exception("Test settings already exist; inspect first");
try {
 Check(PinnedFreedomArrow.Enabled,"dedicated pin enabled");
 Check(LauncherService.Channels.Count == 1 && LauncherService.ActiveRepo() == PinnedFreedomArrow.Repo,"only dedicated stable channel");
 PinnedFreedomArrow.VerifyArchive(archive); Check(true,"original dev45 archive accepted");
 var invalid = Path.Combine(temp,"wrong.bamod"); File.WriteAllText(invalid,"bad");
 var service = new LauncherService(new ManagerConfig());
 Rejected(()=>service.InstallPackFile(temp,invalid,_=>{}),"wrong archive rejected before game writes");
 Check(Manifest.Load(temp).Packages.Count==0,"rejection leaves install record empty");
 // Existing shared add-on and preferences must survive gameplay install and repair.
 var assetRel="UserData/FAAssets/sentinel.txt"; var asset=PathUtil.ToFull(temp,assetRel);Directory.CreateDirectory(Path.GetDirectoryName(asset)!);File.WriteAllText(asset,"approved asset");
 var voice=PathUtil.ToFull(temp,"UserData/FAMusic/voice-presets.txt");Directory.CreateDirectory(Path.GetDirectoryName(voice)!);
 var m=new Manifest();m.Packages.Add(new InstalledPackage{Name="Models and Music",Info=new ModInfo{Id="freedomarrow.assets",Type="addon",Version="0.1.14"},Files=new(){assetRel},Enabled=true});m.Save(temp);
 PinnedFreedomArrow.Ensure(service,temp,_=>{},CancellationToken.None);
 m=Manifest.Load(temp);var pack=service.FindPack(m);
 Check(pack?.Info?.Version==PinnedFreedomArrow.Version && pack.Enabled,"fresh metadata-less dev45 install found by stable ID and enabled");
 Check(PinnedFreedomArrow.PayloadMatches(temp,archive,CancellationToken.None),"every installed payload hash matches dev45");
 Check(PinnedFreedomArrow.PayloadMatches(temp,assets,CancellationToken.None),"fresh complete asset installation matches all bundled payload hashes");
 Check(m.Packages.Single(p=>p.Info?.Id==PinnedFreedomArrow.AssetsId).Enabled,"real Models Music Voices package tracked and enabled");
 File.WriteAllText(voice,"approved preference");
 var skin=PathUtil.ToFull(temp,"UserData/FAModels/m_f14_lo_tex2_mask.png");Check(File.Exists(skin),"custom model texture included");File.WriteAllText(skin,"approved skin");
 Check(File.ReadAllText(asset)=="approved asset" && m.Packages.Single(p=>p.Info?.Id=="freedomarrow.assets").Enabled,"separate existing addon retained");
 var registryPath=PathUtil.ToFull(temp,"UserData/FAModels/models.json");
 var registry=JsonNode.Parse(File.ReadAllText(registryPath))!.AsObject();registry.Remove("MGM-166 LOSAT");registry["Abrams X"]!["scale"]=1.234;File.WriteAllText(registryPath,registry.ToJsonString());
 var at=pack!.InstalledAt;
 PinnedFreedomArrow.Ensure(service,temp,_=>{},CancellationToken.None);
 Check(service.FindPack(Manifest.Load(temp))!.InstalledAt==at,"repeat PLAY validates without reinstall");
 registry=JsonNode.Parse(File.ReadAllText(registryPath))!.AsObject();
 Check(registry.ContainsKey("MGM-166 LOSAT"),"older model registry gains missing required model binding");
 Check((double)registry["Abrams X"]!["scale"]! == 1.234,"existing model alignment retained during registry merge");
 // Repair a same-version changed DLL, then restore a newer installation to the locked version.
 var dll=PathUtil.ToFull(temp,"Mods/FreedomArrow.Runtime.dll");File.WriteAllText(dll,"corrupted");
 PinnedFreedomArrow.Ensure(service,temp,_=>{},CancellationToken.None);
 Check(PinnedFreedomArrow.PayloadMatches(temp,archive,CancellationToken.None),"same-version changed payload repaired");
 m=Manifest.Load(temp);service.FindPack(m)!.Info!.Version="0.7.0-dev.47";m.Save(temp);
 PinnedFreedomArrow.Ensure(service,temp,_=>{},CancellationToken.None);
 Check(service.FindPack(Manifest.Load(temp))!.Info!.Version==PinnedFreedomArrow.Version,"newer version replaced with pinned dev45");
 m=Manifest.Load(temp);pack=service.FindPack(m)!;var mods=new ModService(new ManagerConfig());var entry=mods.Scan(temp,m).Single(p=>p.Package==pack);mods.SetEnabled(temp,entry,false,_=>{});m.Save(temp);
 PinnedFreedomArrow.Ensure(service,temp,_=>{},CancellationToken.None);
 Check(File.Exists(dll)&&!File.Exists(dll+PathUtil.DisabledSuffix),"disabled gameplay reenabled");
 Check(File.ReadAllText(skin)=="approved skin" && File.ReadAllText(voice)=="approved preference","approved skins and voice preferences preserved");
 var assetDll=PathUtil.ToFull(temp,"Mods/FAModels.dll");File.WriteAllText(assetDll,"broken library");
 var missing=PathUtil.ToFull(temp,"UserData/FAMusic/Voice/sentinel-missing.txt");
 using(var z=ZipFile.OpenRead(assets)){var path=z.Entries.First(e=>e.FullName.StartsWith("UserData/FAMusic/Voice/")).FullName;missing=PathUtil.ToFull(temp,path);}
 File.Delete(missing);PinnedFreedomArrow.Ensure(service,temp,_=>{},CancellationToken.None);
 Check(File.Exists(missing) && new FileInfo(assetDll).Length>100,"missing voice restored and baseline asset DLL repaired");
 m=Manifest.Load(temp);var assetPack=m.Packages.Single(p=>p.Info?.Id==PinnedFreedomArrow.AssetsId);assetPack.Info!.Version="0.1.15";m.Save(temp);File.WriteAllText(assetDll,"newer approved library");
 PinnedFreedomArrow.Ensure(service,temp,_=>{},CancellationToken.None);
 Check(File.ReadAllText(assetDll)=="newer approved library" && Manifest.Load(temp).Packages.Single(p=>p.Info?.Id==PinnedFreedomArrow.AssetsId).Info!.Version=="0.1.15","newer installed assets preserved");
 var assetsBackup=assets+".saved";File.Move(assets,assetsBackup);
 Rejected(()=>PinnedFreedomArrow.Ensure(service,temp,_=>{},CancellationToken.None),"missing bundled assets block launch preparation");File.Move(assetsBackup,assets);
 using(var f=new FileStream(assets,FileMode.Open,FileAccess.ReadWrite)){f.Position=f.Length-10;f.WriteByte(123);}
 Rejected(()=>PinnedFreedomArrow.Ensure(service,temp,_=>{},CancellationToken.None),"damaged asset archive blocks launch preparation");
 using(var f=new FileStream(archive,FileMode.Open,FileAccess.ReadWrite)){f.Position=f.Length-10;f.WriteByte(123);}
 Rejected(()=>PinnedFreedomArrow.Ensure(service,temp,_=>{},CancellationToken.None),"damaged bundle blocks launch preparation");
 Check(File.ReadAllText(asset)=="approved asset" && File.ReadAllText(voice)=="approved preference","assets and preferences survive repair and enable");
 Console.WriteLine(JsonSerializer.Serialize(new{checks,gameplay="0.7.0-dev.45",network_download_tested=false,windows_ui_tested=false,game_started=false}));
} finally {File.Delete(assets);File.Delete(archive);Directory.Delete(temp,true);if(Directory.Exists(settings)) Directory.Delete(settings,true);}

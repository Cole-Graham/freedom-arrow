using BAModManager.Core;
using System.IO.Compression;
using System.Text.Json;

if(args.Length!=1)throw new ArgumentException("Path to bamod required");
string temp=Path.Combine(Path.GetTempPath(),"ba-launcher-compat-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(temp);
string settings=AppSettings.FolderPath;Directory.CreateDirectory(settings);
if(File.Exists(Path.Combine(settings,"settings.json")))throw new InvalidOperationException("Compatibility-only settings already exist; inspect before testing");
if(File.Exists(LauncherService.ConfigFile))throw new InvalidOperationException("Test launcher.json already exists; inspect before testing");
try
{
 File.WriteAllText(LauncherService.ConfigFile,"{\"modpack\":\"Cole-Graham/freedom-arrow\"}");
 var service=new LauncherService(new ManagerConfig());
 using var archive=ZipFile.OpenRead(args[0]);using var metadata=JsonDocument.Parse(archive.GetEntry("mod.json")!.Open());
 string? repo=metadata.RootElement.TryGetProperty("repo",out var r)?r.GetString():null;
 bool accepted=service.InstallPackFile(temp,args[0],_=>{});
 if(accepted!=(repo=="Cole-Graham/freedom-arrow"))throw new Exception("Unexpected fresh launcher package acceptance");
 if(accepted)
 {
  var installed=Manifest.Load(temp);var pack=service.FindPack(installed)??throw new Exception("Launcher cannot find installed package");
  if(pack.Info?.Id!="freedomarrow.gameplay"||!pack.Enabled)throw new Exception("Wrong active package");
  if(!pack.Files.All(f=>File.Exists(PathUtil.ToFull(temp,f))))throw new Exception("Missing installed payload");
  Console.WriteLine(JsonSerializer.Serialize(new{result="accepted-fresh-file-install",pack.Name,pack.Info.Version,files=pack.Files.Count,windows_ui_tested=false,network_download_tested=false}));
 }
 else Console.WriteLine(JsonSerializer.Serialize(new{result="rejected-fresh-file-install",reason="Package has no matching repository metadata and there is no existing matching installed package",windows_ui_tested=false,network_download_tested=false}));
}
finally
{
 File.Delete(LauncherService.ConfigFile);if(Directory.Exists(settings))Directory.Delete(settings,true);Directory.Delete(temp,true);
}

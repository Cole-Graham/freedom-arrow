"""Build only the manifest launcher; all mod content downloads from Drive on PLAY."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,zipfile
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--dotnet',default='dotnet');a=p.parse_args();r=Path(__file__).resolve().parents[2];out=a.out.resolve();out.mkdir(parents=True,exist_ok=True);folder=out/'FreedomArrow-Launcher';folder.mkdir(exist_ok=True)
subprocess.run([a.dotnet,'publish',str(r/'thirdparty-tools/BAModManager-main/BAModManager.csproj'),'-c','Release','-r','win-x64','--self-contained','true','-p:AppFlavor=Launcher','-p:PinnedFreedomArrow=true','-p:DefaultModPack=Cole-Graham/freedom-arrow','-p:PublishSingleFile=true','-p:EnableCompressionInSingleFile=true','-p:EnableWindowsTargeting=true','-p:DebugType=none','-o',str(folder)],check=True)
for source,name in [(r/'thirdparty-tools/BAModManager-main/LICENSE','BAModManager-LICENSE.txt'),(r/'thirdparty-tools/BAModManager-main/Fonts/Inter-LICENSE.txt','Inter-LICENSE.txt'),(Path(__file__).with_name('INSTALL.txt'),'README.txt')]:shutil.copy2(source,folder/name)
archive=out/'FreedomArrow-Launcher-v3.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for file in sorted(folder.iterdir()):
  if file.is_file():z.write(file,folder.name+'/'+file.name)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None;assert not any(x.endswith('.bamod') for x in z.namelist())
result={'file':str(archive),'size':archive.stat().st_size,'sha256':hashlib.file_digest(archive.open('rb'),'sha256').hexdigest(),'launcher_version':3,'manifest_url':'https://drive.google.com/uc?export=download&id=1NvdXaFJrqkuOeZAceTo9s8iSyedAfRqE','content_downloaded_on_play':True}
(out/'launcher-archive.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

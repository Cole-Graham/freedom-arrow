"""Build the dedicated BAModLauncher and bundle the immutable dev.45 archive. Never builds gameplay."""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, zipfile
p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--dotnet',default='dotnet');a=p.parse_args()
r=Path(__file__).resolve().parents[2];out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
sha='33323fc1c760acabcc87cc1e237e99251d2d2495a14c858977791b0cf7d2ab5d'
assert hashlib.sha256(a.archive.read_bytes()).hexdigest()==sha,'Use the unchanged published dev.45 package'
with zipfile.ZipFile(a.archive) as z:
 m=json.loads(z.read('mod.json'));assert m['id']=='freedomarrow.gameplay' and m['version']=='0.7.0-dev.45'
folder=out/'FreedomArrow-Launcher-dev45';folder.mkdir(exist_ok=True)
subprocess.run([a.dotnet,'publish',str(r/'thirdparty-tools/BAModManager-main/BAModManager.csproj'),'-c','Release','-r','win-x64','--self-contained','true','-p:AppFlavor=Launcher','-p:PinnedFreedomArrow=true','-p:DefaultModPack=Cole-Graham/freedom-arrow','-p:PublishSingleFile=true','-p:EnableCompressionInSingleFile=true','-p:EnableWindowsTargeting=true','-p:DebugType=none','-o',str(folder)],check=True)
shutil.copy2(a.archive,folder/'FreedomArrow-0.7.0-dev.45.bamod')
shutil.copy2(r/'thirdparty-tools/BAModManager-main/LICENSE',folder/'BAModManager-LICENSE.txt')
shutil.copy2(r/'thirdparty-tools/BAModManager-main/Fonts/Inter-LICENSE.txt',folder/'Inter-LICENSE.txt')
shutil.copy2(Path(__file__).with_name('README.txt'),folder/'README.txt')
archive=out/'FreedomArrow-Launcher-dev45-v1.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in sorted(folder.iterdir()):
  if f.is_file():z.write(f,folder.name+'/'+f.name)
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 assert hashlib.sha256(z.read(folder.name+'/FreedomArrow-0.7.0-dev.45.bamod')).hexdigest()==sha
result={'file':str(archive),'size':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'gameplay_version':'0.7.0-dev.45','gameplay_sha256':sha}
(out/'archive.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

"""Build the frozen deployment candidate; never install or launch a game."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,zipfile
R=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-dir',required=True,type=Path);p.add_argument('--dotnet',default='dotnet');args=p.parse_args()
 game=args.game_dir.resolve()
 if not (game/'MelonLoader/Il2CppAssemblies/Il2CppBrokenArrow.dll').is_file():p.error('GameDir must contain generated MelonLoader/Il2CppAssemblies')
 payload=R/'build/payload'
 if payload.exists():shutil.rmtree(payload)
 shutil.copytree(R/'source/UserData',payload/'UserData');(payload/'Mods').mkdir()
 for folder,project,dll,tf in [('runtime-qa','FreedomArrow.Runtime.csproj','FreedomArrow.Runtime.dll','net6.0/'),('conquest','FreedomArrow.ConquestPrototype.csproj','FreedomArrow.ConquestBatch.dll','net6.0/'),('offline-mod','BALocalSkirmish.csproj','BALocalSkirmish.dll','')]:
  source=R/'source'/folder
  subprocess.run([args.dotnet,'build',str(source/project),'-c','Release',f'-p:GameDir={game}','--nologo'],check=True)
  shutil.copy2(source/f'bin/Release/{tf}{dll}',payload/'Mods'/dll)
 pins=payload/'UserData/FAConquestPrototype/compatibility.json';data=json.loads(pins.read_text())
 for f in ['Mods/BALocalSkirmish.dll','UserData/FAConquestPrototype/settings.json']:data[f]=sha(payload/f)
 pins.write_text(json.dumps(data,indent=2)+'\n')
 hashes={f.relative_to(payload).as_posix():sha(f) for f in sorted(payload.rglob('*')) if f.is_file() and f.name!='payload-manifest.json'}
 (payload/'UserData/FreedomArrow/payload-manifest.json').write_text(json.dumps({'version':'0.1.1','sha256':hashes},indent=2)+'\n')
 out=R/'out';out.mkdir(exist_ok=True);archive=out/'FreedomArrow-0.1.1.bamod'
 # Copy metadata from the reviewed artifact rather than infer a new release scope.
 with zipfile.ZipFile(R/'FreedomArrow-0.1.1.bamod') as original:
  with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
   for f in sorted(payload.rglob('*')):
    if f.is_file():z.write(f,f.relative_to(payload).as_posix())
   for name in ['mod.json','README.md']:z.writestr(name,original.read(name))
 (out/'SHA256SUMS.txt').write_text(sha(archive)+'  '+archive.name+'\n');print(archive)
if __name__=='__main__':main()

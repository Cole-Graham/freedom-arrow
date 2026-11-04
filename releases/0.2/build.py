"""Build the isolated 0.2 development candidate. Never install or launch."""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, zipfile
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-dir',required=True,type=Path);p.add_argument('--dotnet',default='dotnet');a=p.parse_args()
 game=a.game_dir.resolve()
 if not (game/'MelonLoader/Il2CppAssemblies/Il2CppBrokenArrow.dll').is_file():p.error('Generated MelonLoader assemblies are required')
 metadata=json.loads((R/'mod.json').read_text());version=metadata['version']
 payload=R/'build/payload'
 if payload.exists():shutil.rmtree(payload)
 shutil.copytree(R/'source/UserData',payload/'UserData');(payload/'Mods').mkdir()
 for folder,project,dll,tf in [('runtime-qa','FreedomArrow.Runtime.csproj','FreedomArrow.Runtime.dll','net6.0/'),('conquest','FreedomArrow.ConquestPrototype.csproj','FreedomArrow.ConquestBatch.dll','net6.0/'),('offline-mod','BALocalSkirmish.csproj','BALocalSkirmish.dll','')]:
  s=R/'source'/folder
  subprocess.run([a.dotnet,'build',str(s/project),'-c','Release',f'-p:GameDir={game}','--nologo'],check=True)
  shutil.copy2(s/f'bin/Release/{tf}{dll}',payload/'Mods'/dll)
 pin=payload/'UserData/FAConquestPrototype/compatibility.json';j=json.loads(pin.read_text())
 for f in ['Mods/BALocalSkirmish.dll','UserData/FAConquestPrototype/settings.json']:j[f]=sha(payload/f)
 pin.write_text(json.dumps(j,indent=2)+'\n')
 channel=json.loads((payload/'UserData/FreedomArrow/channel.json').read_text());assert channel['package_version']==version
 manifest={f.relative_to(payload).as_posix():sha(f) for f in sorted(payload.rglob('*')) if f.is_file() and f.name!='payload-manifest.json'}
 (payload/'UserData/FreedomArrow/payload-manifest.json').write_text(json.dumps({'version':version,'sha256':manifest},indent=2)+'\n')
 out=R/'out';out.mkdir(exist_ok=True);archive=out/f'FreedomArrow-{version}.bamod'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for f in sorted(payload.rglob('*')):
   if f.is_file():z.write(f,f.relative_to(payload).as_posix())
  z.write(R/'mod.json','mod.json');z.write(R/'README.md','README.md')
 (out/'SHA256SUMS.txt').write_text(sha(archive)+'  '+archive.name+'\n');print(archive)
if __name__=='__main__':main()

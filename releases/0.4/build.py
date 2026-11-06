"""Build the 0.4 development candidate. It never launches the game.

After the build, if config.YAML at the repo root sets game_root, the built scenarios are copied to
{game_root}/Mods/Scenarios, the folder online lobbies read. Use --no-scenario-copy to skip this."""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, sys, zipfile
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-dir',required=True,type=Path);p.add_argument('--dotnet',default='dotnet');p.add_argument('--no-scenario-copy',action='store_true');a=p.parse_args()
 game=a.game_dir.resolve()
 if not (game/'MelonLoader/Il2CppAssemblies/Il2CppBrokenArrow.dll').is_file():p.error('Generated MelonLoader assemblies are required')
 metadata=json.loads((R/'mod.json').read_text());version=metadata['version']
 audit=R/'constant-audit.json'
 if not audit.is_file() or json.loads(audit.read_text())['version']!=version:p.error(f'Generated data is missing or not for {version}. Run build_constants.py first.')
 payload=R/'build/payload'
 if payload.exists():shutil.rmtree(payload)
 shutil.copytree(R/'source/UserData',payload/'UserData');(payload/'Mods').mkdir()
 subprocess.run([sys.executable,str(R/'scenarios'/'make_scenario.py'),'--game-dir',str(game),'--out',str(payload/'UserData/FreedomArrow/scenarios')],check=True)
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
 if not a.no_scenario_copy:copy_scenarios(payload,version)
# Every player in a lobby needs byte-identical scenario files, so copy this build's maps to the install named in config.YAML.
# The mod also copies its packaged maps to Mods/Scenarios at each launch. An older installed package would put its own maps back.
def copy_scenarios(payload,version):
 sys.path.insert(0,str(R.parents[1]))
 from pipeline.config import load_config
 from pipeline.errors import PipelineError
 try:root=load_config().game_root
 except PipelineError as e:print('scenario copy skipped:',e);return
 if not (root/'BrokenArrow_Data').is_dir():print('scenario copy skipped: no BrokenArrow_Data in',root);return
 target=root/'Mods'/'Scenarios'
 for folder in sorted((payload/'UserData/FreedomArrow/scenarios').iterdir()):
  dest=target/folder.name;dest.mkdir(parents=True,exist_ok=True)
  for f in folder.iterdir():shutil.copy2(f,dest/f.name)
  print('scenario copied:',dest)
 channel=root/'UserData/FreedomArrow/channel.json'
 installed=json.loads(channel.read_text()).get('package_version') if channel.is_file() else None
 if installed!=version:print(f'WARNING: the installed package is {installed}, not {version}. At launch the mod puts back the installed package maps. Install the new .bamod so every player has the same maps.')
if __name__=='__main__':main()

"""Build the complete identity correction from the immutable Build 3 pack.

The system zip tool retains the original compressed entries for unchanged assets.
Run identity-tests and compile the runtime before using this packaging recipe.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,tempfile,zipfile
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'releases/0.6'
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def enc(j):return (json.dumps(j,indent=2)+'\n').encode()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--zip',default='zip');a=p.parse_args()
 assert digest(a.base)=='b8d0752be4b9a3242adb8685627c75dcaac4e8d55fb99df27bfed941772dbdd3'
 info=json.loads((R/'mod.json').read_text());version=info['version'];label=info['name'];assert version=='4' and label=='PLA TEST Build 4'
 runtime=R/'source/runtime-qa/bin/Release/net6.0/FreedomArrow.Runtime.dll';assert runtime.is_file()
 with zipfile.ZipFile(a.base) as base:
  assert len(base.namelist())==len(set(base.namelist()))
  whole=json.loads(base.read('UserData/FreedomArrow/pla-package-manifest.json'));oldpins=whole['sha256'].copy()
  overrides={'Mods/FreedomArrow.Runtime.dll':runtime.read_bytes(),'mod.json':enc(info),'README.md':(R/'README.md').read_bytes(),'UserData/FreedomArrow/release-notes.md':(R/'source/UserData/FreedomArrow/release-notes.md').read_bytes()}
  for n in ['UserData/FreedomArrow/channel.json','UserData/FreedomArrow/pla-build.json']:
   j=json.loads(base.read(n))
   if n.endswith('channel.json'):j.update(package_version=version)
   else:j.update(build=int(version),label=label)
   overrides[n]=enc(j)
  n='UserData/FAAssets/manifest.json';j=json.loads(base.read(n));j['version']=label;overrides[n]=enc(j)
  core=json.loads(base.read('UserData/FreedomArrow/payload-manifest.json'));core['version']=version
  for n,b in overrides.items():
   if n in core['sha256']:core['sha256'][n]=hashlib.sha256(b).hexdigest()
  overrides['UserData/FreedomArrow/payload-manifest.json']=enc(core)
  for n,b in overrides.items():
   if n in whole['sha256']:whole['sha256'][n]=hashlib.sha256(b).hexdigest()
  whole.update(build=int(version),label=label);overrides['UserData/FreedomArrow/pla-package-manifest.json']=enc(whole)
  a.out.parent.mkdir(parents=True,exist_ok=True);subprocess.run(['cp','--reflink=auto',str(a.base.resolve()),str(a.out.resolve())],check=True)
  with tempfile.TemporaryDirectory() as tmp:
   stage=Path(tmp)
   for n,b in overrides.items():f=stage/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
   subprocess.run([a.zip,'-q',str(a.out.resolve()),*sorted(overrides)],cwd=stage,check=True)
 with zipfile.ZipFile(a.out) as result:
  assert len(result.namelist())==len(set(result.namelist()))
  for n,h in whole['sha256'].items():
   with result.open(n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==h,n
  unchanged=sum(oldpins[n]==h for n,h in whole['sha256'].items());assert unchanged==len(oldpins)-6,(unchanged,len(oldpins))
  # All infantry meshes, rules, textures, weapons, constants and music are byte-identical to Build 3.
  assert all(oldpins[n]==h for n,h in whole['sha256'].items() if n.startswith(('UserData/FAModels/','UserData/FAMusic/','UserData/FreedomArrow/constants/')) or n in ('Mods/FAModels.dll','Mods/FAMusic.dll'))
 receipt={'label':label,'sha256':digest(a.out),'bytes':a.out.stat().st_size,'verified_payloads':len(oldpins),'unchanged_payloads':unchanged,'changed_paths':sorted(overrides),'models_music_constants_unchanged':True,'native_verified':False}
 a.out.with_suffix('.json').write_bytes(enc(receipt));print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()

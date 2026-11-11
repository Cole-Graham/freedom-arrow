"""Overlay only immediate-hide loader and Build 10 identity onto pinned Build 8."""
from pathlib import Path
import argparse,hashlib,json,subprocess,tempfile,zipfile
R=Path(__file__).resolve().parents[2]/'releases/0.6'
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def enc(d):return (json.dumps(d,indent=2)+'\n').encode()
ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--zip',required=True);a=ap.parse_args()
assert digest(a.base)=='5fa558c9e592505032ec1cb891fca8e8b7759840370621d6d6f7bf9ba440be97'
z=zipfile.ZipFile(a.base);whole=json.loads(z.read('UserData/FreedomArrow/pla-package-manifest.json'));oldpins=whole['sha256'].copy()
over={'mod.json':(R/'mod.json').read_bytes(),'README.md':(R/'README.md').read_bytes(),'Mods/FAModels.dll':(R/'experimental-model-loader/bin/Release/net6.0/FAModels.dll').read_bytes(),'Mods/FreedomArrow.Runtime.dll':(R/'source/runtime-qa/bin/Release/net6.0/FreedomArrow.Runtime.dll').read_bytes()}
for fn in ['channel.json','pla-build.json','release-notes.md']:over['UserData/FreedomArrow/'+fn]=(R/'source/UserData/FreedomArrow'/fn).read_bytes()
assert json.loads(over['mod.json'])['version']=='10'
asset=json.loads(z.read('UserData/FAAssets/manifest.json'));asset['version']='PLA TEST Build 10'
for n,b in over.items():
 if n in asset['files']:asset['files'][n]=hashlib.sha256(b).hexdigest()
over['UserData/FAAssets/manifest.json']=enc(asset)
core=json.loads(z.read('UserData/FreedomArrow/payload-manifest.json'));core['version']='10'
for n,b in over.items():
 if n in core['sha256']:core['sha256'][n]=hashlib.sha256(b).hexdigest()
over['UserData/FreedomArrow/payload-manifest.json']=enc(core)
for n,b in over.items():
 if n.startswith(('Mods/','UserData/')):whole['sha256'][n]=hashlib.sha256(b).hexdigest()
whole.update(build=10,label='PLA TEST Build 10');over['UserData/FreedomArrow/pla-package-manifest.json']=enc(whole)
a.out.parent.mkdir(parents=True,exist_ok=True);subprocess.run(['cp','--reflink=auto',str(a.base.resolve()),str(a.out.resolve())],check=True)
with tempfile.TemporaryDirectory() as tmp:
 for n,b in over.items():p=Path(tmp)/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 subprocess.run([a.zip,'-q',str(a.out.resolve()),*sorted(over)],cwd=tmp,check=True)
with zipfile.ZipFile(a.out) as zz:
 assert len(zz.namelist())==len(set(zz.namelist()))
 for n,h in whole['sha256'].items():
  with zz.open(n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==h,n
 assert all(whole['sha256'][n]==h for n,h in oldpins.items() if n not in over)
 assert not any(n.startswith(('UserData/FAModels/','UserData/FAMusic/','UserData/FreedomArrow/constants/')) for n in over)
 assert json.loads(zz.read('UserData/FreedomArrow/pla-build.json'))['build']==10
result={'label':'PLA TEST Build 10','sha256':digest(a.out),'bytes':a.out.stat().st_size,'verified_payloads':len(whole['sha256']),'changed_paths':sorted(over),'models_materials_gameplay_infantry_audio_unchanged':True,'native_transition_verified':False};a.out.with_suffix('.json').write_bytes(enc(result));print(json.dumps(result,indent=2))

"""Overlay the cockpit candidate onto the immutable complete Build 4 pack."""
from pathlib import Path
import argparse,hashlib,json,subprocess,tempfile,zipfile
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'releases/0.6'
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def enc(d):return (json.dumps(d,indent=2)+'\n').encode()
ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--prepared',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--zip',default='zip');a=ap.parse_args()
assert digest(a.base)=='8eca43e9f4ecd6bfcbb0b4a9ffe666a38d9b5121c66825106669d35c3ca94656'
z=zipfile.ZipFile(a.base);whole=json.loads(z.read('UserData/FreedomArrow/pla-package-manifest.json'));oldpins=whole['sha256'].copy();policy=json.loads((a.prepared/'cockpit-policy.json').read_text());assert len(policy['units'])==20 and len(policy['files'])==36
info=json.loads((R/'mod.json').read_text());assert info['version']=='5' and info['name']=='PLA TEST Build 5'
over={'mod.json':enc(info),'README.md':(R/'README.md').read_bytes(),'Mods/FAModels.dll':(R/'experimental-model-loader/bin/Release/net6.0/FAModels.dll').read_bytes(),'Mods/FreedomArrow.Runtime.dll':(R/'source/runtime-qa/bin/Release/net6.0/FreedomArrow.Runtime.dll').read_bytes()}
for fn in ['channel.json','pla-build.json','release-notes.md']:over['UserData/FreedomArrow/'+fn]=(R/'source/UserData/FreedomArrow'/fn).read_bytes()
for f in a.prepared.iterdir():
 if f.suffix in ['.fam','.json']:over['UserData/FAModels/'+f.name]=f.read_bytes()
asset=json.loads(z.read('UserData/FAAssets/manifest.json'));asset['version']=info['name']
for n,b in over.items():
 if n.startswith('UserData/FAModels/') or n=='Mods/FAModels.dll':asset['files'][n]=hashlib.sha256(b).hexdigest()
asset.setdefault('notes',[]).append('Build 5 canopy donor policy; geometry/non-canopy UVs checked offline; native appearance pending.');over['UserData/FAAssets/manifest.json']=enc(asset)
core=json.loads(z.read('UserData/FreedomArrow/payload-manifest.json'));core['version']='5'
for n,b in over.items():
 if n in core['sha256']:core['sha256'][n]=hashlib.sha256(b).hexdigest()
core['sha256']['UserData/FAModels/cockpit-policy.json']=hashlib.sha256(over['UserData/FAModels/cockpit-policy.json']).hexdigest();over['UserData/FreedomArrow/payload-manifest.json']=enc(core)
for n,b in over.items():
 if n.startswith(('Mods/','UserData/')):whole['sha256'][n]=hashlib.sha256(b).hexdigest()
whole.update(build=5,label=info['name']);over['UserData/FreedomArrow/pla-package-manifest.json']=enc(whole)
a.out.parent.mkdir(parents=True,exist_ok=True);subprocess.run(['cp','--reflink=auto',str(a.base.resolve()),str(a.out.resolve())],check=True)
with tempfile.TemporaryDirectory() as tmp:
 t=Path(tmp)
 for n,b in over.items():p=t/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 subprocess.run([a.zip,'-q',str(a.out.resolve()),*sorted(over)],cwd=t,check=True)
with zipfile.ZipFile(a.out) as zz:
 assert len(zz.namelist())==len(set(zz.namelist()))
 for n,h in whole['sha256'].items():
  with zz.open(n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==h,n
 # Do not let a cockpit package reset gameplay, infantry alignment/skins, audio or weapons.
 protected=('UserData/FreedomArrow/constants/','UserData/FAMusic/','UserData/FAModels/pla2_')
 protected_files={'UserData/FAModels/models.json','UserData/FAModels/infantry-bodies.json','UserData/FAModels/infantry-weapons.json','Mods/FAMusic.dll'}
 assert all(whole['sha256'][n]==h for n,h in oldpins.items() if n.startswith(protected) or n in protected_files)
 assert json.loads(zz.read('UserData/FreedomArrow/channel.json'))['package_version']=='5'
 assert json.loads(zz.read('UserData/FreedomArrow/pla-build.json'))['label']=='PLA TEST Build 5'
result={'label':info['name'],'sha256':digest(a.out),'bytes':a.out.stat().st_size,'verified_payloads':len(whole['sha256']),'changed_paths':sorted(over),'entries':20,'model_copies':36,'glass_faces':sum(d['glass_faces'] for d in policy['files'].values()),'gameplay_infantry_audio_unchanged':True,'native_verified':False};a.out.with_suffix('.json').write_bytes(enc(result));print(json.dumps(result,indent=2))

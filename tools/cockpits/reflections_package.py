"""Build 8 overlay: no geometry or image changes from pinned Build 7."""
from pathlib import Path
import argparse,hashlib,json,subprocess,tempfile,zipfile
R=Path(__file__).resolve().parents[2]/'releases/0.6'
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def enc(d):return (json.dumps(d,indent=2)+'\n').encode()
ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--zip',required=True);a=ap.parse_args()
assert digest(a.base)=='9aff0b30a217dbad37a438aad5072eb610390e76c0946c384719a54b5f85af22'
z=zipfile.ZipFile(a.base);whole=json.loads(z.read('UserData/FreedomArrow/pla-package-manifest.json'));oldpins=whole['sha256'].copy();policy=json.loads(z.read('UserData/FAModels/cockpit-policy.json'))
over={'mod.json':(R/'mod.json').read_bytes(),'README.md':(R/'README.md').read_bytes(),'Mods/FAModels.dll':(R/'experimental-model-loader/bin/Release/net6.0/FAModels.dll').read_bytes(),'Mods/FreedomArrow.Runtime.dll':(R/'source/runtime-qa/bin/Release/net6.0/FreedomArrow.Runtime.dll').read_bytes()}
for fn in ['channel.json','pla-build.json','release-notes.md']:over['UserData/FreedomArrow/'+fn]=(R/'source/UserData/FreedomArrow'/fn).read_bytes()
opted=[]
for fn,rule in policy['files'].items():
 if rule['donor']!='SOURCE':continue
 path='UserData/FAModels/'+str(Path(fn).with_suffix('.mat.json'));mp=json.loads(z.read(path));keys=[]
 for key,settings in mp.items():
  if '_source_canopy.png|' in key or (fn.startswith('m_yf23') and key.startswith('|') and settings.get('alpha')=='BLEND'):
   settings['sourceCanopy']=True;keys.append(key)
 assert keys,(fn,mp)
 over[path]=enc(mp);opted.append({'file':fn,'materials':keys})
assert len(opted)==14
policy['reflection_finish']={'build':8,'source_copies':opted,'preserve_specular':True,'metallic':0,'smoothness':.95,'smoothness_remap':[.90,.98],'native_verified':False};over['UserData/FAModels/cockpit-policy.json']=enc(policy)
asset=json.loads(z.read('UserData/FAAssets/manifest.json'));asset['version']='PLA TEST Build 8'
for n,b in over.items():
 if n in asset['files']:asset['files'][n]=hashlib.sha256(b).hexdigest()
over['UserData/FAAssets/manifest.json']=enc(asset)
core=json.loads(z.read('UserData/FreedomArrow/payload-manifest.json'));core['version']='8'
for n,b in over.items():
 if n in core['sha256']:core['sha256'][n]=hashlib.sha256(b).hexdigest()
over['UserData/FreedomArrow/payload-manifest.json']=enc(core)
for n,b in over.items():
 if n.startswith(('Mods/','UserData/')):whole['sha256'][n]=hashlib.sha256(b).hexdigest()
whole.update(build=8,label='PLA TEST Build 8');over['UserData/FreedomArrow/pla-package-manifest.json']=enc(whole)
a.out.parent.mkdir(parents=True,exist_ok=True);subprocess.run(['cp','--reflink=auto',str(a.base.resolve()),str(a.out.resolve())],check=True)
with tempfile.TemporaryDirectory() as tmp:
 for n,b in over.items():p=Path(tmp)/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 subprocess.run([a.zip,'-q',str(a.out.resolve()),*sorted(over)],cwd=tmp,check=True)
with zipfile.ZipFile(a.out) as zz:
 assert len(zz.namelist())==len(set(zz.namelist()))
 for n,h in whole['sha256'].items():
  with zz.open(n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==h,n
 # Only the explicit allowlist may differ; all .fam meshes, source PNGs, gameplay, infantry and audio stay byte-identical.
 assert all(whole['sha256'][n]==h for n,h in oldpins.items() if n not in over)
 assert not any(n.endswith(('.fam','.png')) for n in over)
 assert json.loads(zz.read('mod.json'))['version']=='8'
 assert json.loads(zz.read('UserData/FreedomArrow/pla-build.json'))['build']==8
result={'label':'PLA TEST Build 8','sha256':digest(a.out),'bytes':a.out.stat().st_size,'verified_payloads':len(whole['sha256']),'source_canopy_copies':len(opted),'changed_paths':sorted(over),'geometry_images_gameplay_infantry_audio_unchanged':True,'native_verified':False};a.out.with_suffix('.json').write_bytes(enc(result));print(json.dumps(result,indent=2))

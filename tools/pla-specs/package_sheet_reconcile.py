from pathlib import Path
import argparse,json,hashlib,zipfile,subprocess,tempfile
root=Path(__file__).resolve().parents[2] if 'tools/pla-specs' in str(Path(__file__)) else Path('/home/sam/tars/work/ba-dev/replicas/codex/work/pla-sheet-reconcile-source');rel=root/'releases/0.6';src=rel/'source';p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--zip',required=True);a=p.parse_args();enc=lambda d:(json.dumps(d,indent=2)+'\n').encode();sha=lambda b:hashlib.sha256(b).hexdigest()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()=='6474690619db697d6daadbb6343bb86ebb37c321cd8615bcd1195b6b905e0009'
with zipfile.ZipFile(a.base) as z:
 whole=json.loads(z.read('UserData/FreedomArrow/pla-package-manifest.json'));assert whole['build']==31;oldpins=whole['sha256'].copy();core=json.loads(z.read('UserData/FreedomArrow/payload-manifest.json'));assets=json.loads(z.read('UserData/FAAssets/manifest.json'))
 override={'mod.json':(rel/'mod.json').read_bytes(),'README.md':(root/'README.md').read_bytes(),'Mods/FreedomArrow.Runtime.dll':(src/'runtime-qa/bin/Release/net6.0/FreedomArrow.Runtime.dll').read_bytes()}
 for f in (src/'UserData/FreedomArrow/constants').glob('*.json'):
  n=f.relative_to(src).as_posix()
  if f.read_bytes()!=z.read(n):override[n]=f.read_bytes()
 for name in ['channel.json','release-notes.md','pla-build.json','pla-infantry-designer.json','pla-infantry-identity.json','pla-spec-assignments.json','pla-sheet-reconcile.json','pla-weapon-hud.json']:
  key='UserData/FreedomArrow/'+name;override[key]=(src/key).read_bytes()
 # No body, weapon-model binding, geometry, material, music or other DLL changes.
 assert (src/'UserData/FAModels/infantry-weapons.json').read_bytes()==z.read('UserData/FAModels/infantry-weapons.json')
 assets['version']='PLA TEST Build 32'
 for n,b in override.items():
  if n in assets['files']:assets['files'][n]=sha(b)
 override['UserData/FAAssets/manifest.json']=enc(assets);core['version']='32'
 for n,b in override.items():
  if n in core['sha256'] or n.startswith('UserData/FreedomArrow/'):core['sha256'][n]=sha(b)
 override['UserData/FreedomArrow/payload-manifest.json']=enc(core);whole.update(build=32,label='PLA TEST Build 32')
 for n,b in override.items():
  if n not in ['mod.json','README.md']:whole['sha256'][n]=sha(b)
 whole['core_paths']=sorted(set(whole['core_paths'])|{n for n in override if n.startswith('UserData/FreedomArrow/')});override['UserData/FreedomArrow/pla-package-manifest.json']=enc(whole)
 a.out.parent.mkdir(parents=True,exist_ok=True);subprocess.run(['cp','--reflink=auto',str(a.base.resolve()),str(a.out.resolve())],check=True)
 with tempfile.TemporaryDirectory() as temp:
  t=Path(temp)
  for n,b in override.items():f=t/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
  subprocess.run([a.zip,'-q',str(a.out.resolve()),*sorted(override)],cwd=t,check=True)
with zipfile.ZipFile(a.out) as z,zipfile.ZipFile(a.base) as base:
 assert len(z.namelist())==len(set(z.namelist()))
 for n,w in whole['sha256'].items():
  with z.open(n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==w,n
 for n,w in core['sha256'].items():assert sha(z.read(n))==w,n
 for n in base.namelist():
  if n.startswith(('UserData/FAModels/','UserData/FAMusic/')) or n in ['Mods/FAModels.dll','Mods/FAMusic.dll','Mods/FlatIncomeMod.dll']:assert z.read(n)==base.read(n),n
with a.out.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
receipt={'build':32,'label':'PLA TEST Build 32','base_build':31,'sha256':digest,'bytes':a.out.stat().st_size,'verified_payloads':len(whole['sha256']),'verified_core_hashes':len(core['sha256']),'changed_paths':sorted(override),'native_verified':False,'installed':False};a.out.with_suffix('.json').write_bytes(enc(receipt));print(json.dumps(receipt,indent=2))

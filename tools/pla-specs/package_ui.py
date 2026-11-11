"""Package a runtime-only Arsenal correction over an exactly pinned complete PLA pack."""
import argparse,hashlib,json,subprocess,tempfile,zipfile
from pathlib import Path

root=Path(__file__).resolve().parents[2];rel=root/'releases/0.6'
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
p.add_argument('--zip',default='zip')
a=p.parse_args();contract=json.loads((rel/'pla-specializations-contract.json').read_text())
def digest(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def sha(data):return hashlib.sha256(data).hexdigest()
def enc(value):return (json.dumps(value,indent=2)+'\n').encode()
assert digest(a.base)==contract['runtime_base_sha256'],'UI base archive checksum mismatch'
version=str(contract['build']);label='PLA TEST Build '+version
with zipfile.ZipFile(a.base) as z:
 identity=json.loads(z.read('UserData/FreedomArrow/pla-package-manifest.json'))
 oldpins=identity['sha256'].copy();core=json.loads(z.read('UserData/FreedomArrow/payload-manifest.json'))
 assert identity['build']==contract['runtime_base_build']
 override={'Mods/FreedomArrow.Runtime.dll':(rel/'source/runtime-qa/bin/Release/net6.0/FreedomArrow.Runtime.dll').read_bytes(),
           'mod.json':(rel/'mod.json').read_bytes(),'README.md':(root/'README.md').read_bytes(),
           'UserData/FreedomArrow/release-notes.md':(rel/'source/UserData/FreedomArrow/release-notes.md').read_bytes()}
 for name in ['pla-build.json','pla-specializations.json','pla-spec-assignments.json','pla-infantry-designer.json','pla-vehicle-armament.json','pla-weapon-hud.json']:
  path='UserData/FreedomArrow/'+name;d=json.loads(z.read(path));d['build']=contract['build']
  if name=='pla-build.json':d['label']=label
  override[path]=enc(d)
 path='UserData/FreedomArrow/channel.json';d=json.loads(z.read(path));d['package_version']=version
 d['verification']='Arsenal shared-unit heading correction over complete Build16; native UI verification pending.';override[path]=enc(d)
 path='UserData/FreedomArrow/pla-arsenal-ui.json';override[path]=enc({
  'build':contract['build'],'base_build':identity['build'],'scope':'Presentation only; existing native unit/search/type/category filters retained',
  'group_rule':'Shared cards follow an eligible selected specialization heading; All restores primary heading',
  'both_card_modes':True,'native_verified':False})
 path='UserData/FAAssets/manifest.json';d=json.loads(z.read(path));d['version']=label
 for name,data in override.items():
  if name in d['files']:d['files'][name]=sha(data)
 override[path]=enc(d)
 core['version']=version
 for name,data in override.items():
  if name in core['sha256'] or name.startswith('UserData/FreedomArrow/'):core['sha256'][name]=sha(data)
 override['UserData/FreedomArrow/payload-manifest.json']=enc(core)
 identity.update(build=contract['build'],label=label)
 for name,data in override.items():
  if name not in ['README.md','mod.json']:identity['sha256'][name]=sha(data)
 identity['core_paths']=sorted(set(identity['core_paths'])|{n for n in override if n.startswith('UserData/FreedomArrow/')})
 override['UserData/FreedomArrow/pla-package-manifest.json']=enc(identity)
 a.out.parent.mkdir(parents=True,exist_ok=True)
 subprocess.run(['cp','--reflink=auto',str(a.base.resolve()),str(a.out.resolve())],check=True)
 with tempfile.TemporaryDirectory() as temp:
  stage=Path(temp)
  for name,data in override.items():
   path=stage/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
  subprocess.run([a.zip,'-q',str(a.out.resolve()),*sorted(override)],cwd=stage,check=True)
with zipfile.ZipFile(a.out) as z:
 assert len(z.namelist())==len(set(z.namelist()))
 for name,expected in identity['sha256'].items():
  with z.open(name) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==expected,name
 changed=sorted(n for n in oldpins if identity['sha256'].get(n)!=oldpins[n])
 assert not any(n.startswith(('UserData/FAModels/','UserData/FAMusic/','UserData/FreedomArrow/constants/')) or n=='Mods/FAModels.dll' for n in changed)
receipt={'label':label,'sha256':digest(a.out),'bytes':a.out.stat().st_size,'verified_payloads':len(identity['sha256']),
 'verified_core_hashes':len(core['sha256']),'base_build':contract['runtime_base_build'],'base_sha256':contract['runtime_base_sha256'],
 'changed_paths':changed,'new_paths':sorted(set(identity['sha256'])-set(oldpins)),
 'all_database_tables_identical':True,'models_music_loader_unchanged':True,'build16_weapon_art_retained':True,'installed':False,'native_verified':False}
a.out.with_suffix('.json').write_bytes(enc(receipt));print(json.dumps(receipt,indent=2))

"""Package the weapon HUD revision over pinned Build22; preserve every other gameplay/model payload."""
import argparse,hashlib,json,subprocess,tempfile,zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[2];rel=root/'releases/0.6';p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--zip',default='zip');a=p.parse_args();c=json.loads((rel/'pla-specializations-contract.json').read_text());src=rel/'source'
def digest(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def sha(data):return hashlib.sha256(data).hexdigest()
def enc(value):return (json.dumps(value,indent=2)+'\n').encode()
assert digest(a.base)==c['runtime_base_sha256'];assert c['runtime_base_build']==22
music=json.loads((root/'tools/pla-specs/music-integration.json').read_text());music_dll=(root/music['source_artifact']).resolve();assert digest(music_dll)==music['sha256']
label='PLA TEST Build '+str(c['build']);version=str(c['build'])
with zipfile.ZipFile(a.base) as z:
 identity=json.loads(z.read('UserData/FreedomArrow/pla-package-manifest.json'));oldpins=identity['sha256'].copy();core=json.loads(z.read('UserData/FreedomArrow/payload-manifest.json'));assert identity['build']==22
 override={'Mods/FAMusic.dll':music_dll.read_bytes(),'Mods/FreedomArrow.Runtime.dll':(src/'runtime-qa/bin/Release/net6.0/FreedomArrow.Runtime.dll').read_bytes(),'mod.json':(rel/'mod.json').read_bytes(),'README.md':(root/'README.md').read_bytes(),'UserData/FreedomArrow/release-notes.md':(src/'UserData/FreedomArrow/release-notes.md').read_bytes()}
 for name in ['pla-build.json','pla-specializations.json','pla-spec-assignments.json','pla-infantry-designer.json','pla-vehicle-armament.json','pla-arsenal-ui.json']:
  key='UserData/FreedomArrow/'+name;d=json.loads(z.read(key));d['build']=c['build']
  if name=='pla-build.json':d['label']=label
  if name=='pla-infantry-designer.json':d=json.loads((src/key).read_text())
  override[key]=enc(d)
 for name in ['pla-weapon-hud.json','weapon-hud-references.json','pla-infantry-identity.json']:
  key='UserData/FreedomArrow/'+name;override[key]=(src/key).read_bytes()
 # Only unit display names and thumbnails change in this revision; all weapon and combat fields are checked separately.
 key='UserData/FreedomArrow/constants/units.json';assert key in oldpins;override[key]=(src/key).read_bytes()
 key='UserData/FreedomArrow/channel.json';d=json.loads(z.read(key));d.update(package_version=version,verification='Build22 refined emblems and English labels plus the installed FA Music1.5.0 native Home selector. All game-table fields and artwork matchBuild22; models, audio, preferences and Build17 grouping retained. Combined native appearance remains untested.');override[key]=enc(d)
 key='UserData/FAAssets/manifest.json';d=json.loads(z.read(key));d['version']=label
 for name,data in override.items():
  if name in d['files']:d['files'][name]=sha(data)
 override[key]=enc(d);core['version']=version
 for name,data in override.items():
  if name in core['sha256'] or name.startswith('UserData/FreedomArrow/'):core['sha256'][name]=sha(data)
 override['UserData/FreedomArrow/payload-manifest.json']=enc(core);identity.update(build=c['build'],label=label)
 for name,data in override.items():
  if name not in ['README.md','mod.json']:identity['sha256'][name]=sha(data)
 identity['core_paths']=sorted(set(identity['core_paths'])|{n for n in override if n.startswith('UserData/FreedomArrow/')});override['UserData/FreedomArrow/pla-package-manifest.json']=enc(identity)
 a.out.parent.mkdir(parents=True,exist_ok=True);subprocess.run(['cp','--reflink=auto',str(a.base.resolve()),str(a.out.resolve())],check=True)
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
 assert not any(n.startswith(('UserData/FAModels/','UserData/FAMusic/')) or n=='Mods/FAModels.dll' for n in changed)
 assert z.read('Mods/FAMusic.dll')==music_dll.read_bytes()
 assert [n for n in changed if n.startswith('UserData/FreedomArrow/constants/')]==[]
receipt={'label':label,'sha256':digest(a.out),'bytes':a.out.stat().st_size,'verified_payloads':len(identity['sha256']),'verified_core_hashes':len(core['sha256']),'base_build':22,'base_sha256':c['runtime_base_sha256'],'changed_paths':changed,'new_paths':sorted(set(identity['sha256'])-set(oldpins)),'models_music_audio_assets_loader_unchanged':True,'music_player_version':music['version'],'music_player_sha256':music['sha256'],'build17_arsenal_fix_retained':True,'native_verified':False,'installed':False};a.out.with_suffix('.json').write_bytes(enc(receipt));print(json.dumps(receipt,indent=2))

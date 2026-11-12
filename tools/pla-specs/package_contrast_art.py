"""Build26: approved unit/spec art over the exact complete Build25; preserve all game tables/assets."""
from pathlib import Path
import argparse,json,hashlib,subprocess,tempfile,zipfile
root=Path(__file__).resolve().parents[2];rel=root/'releases/0.6';src=rel/'source'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--zip',default='zip');a=p.parse_args();c=json.loads((rel/'pla-specializations-contract.json').read_text());assert c['build']==26 and c['test_spec']==22
enc=lambda x:(json.dumps(x,indent=2)+'\n').encode();sha=lambda b:hashlib.sha256(b).hexdigest()
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert digest(a.base)==c['runtime_base_sha256'] and c['runtime_base_build']==25
with zipfile.ZipFile(a.base) as z:
 whole=json.loads(z.read('UserData/FreedomArrow/pla-package-manifest.json'));assert whole['build']==25;oldpins=whole['sha256'].copy();core=json.loads(z.read('UserData/FreedomArrow/payload-manifest.json'))
 override={'mod.json':(rel/'mod.json').read_bytes(),'README.md':(root/'README.md').read_bytes(),'Mods/FreedomArrow.Runtime.dll':(src/'runtime-qa/bin/Release/net6.0/FreedomArrow.Runtime.dll').read_bytes(),'UserData/FreedomArrow/release-notes.md':(src/'UserData/FreedomArrow/release-notes.md').read_bytes()}
 for f in (src/'UserData/FreedomArrow').glob('pla-*.json'):
  key='UserData/FreedomArrow/'+f.name
  if key in oldpins or f.name=='pla-approved-art.json':override[key]=f.read_bytes()
 # Receipts not present in the checkout are taken from the exact base, changing only the build label.
 for name in ['pla-arsenal-ui.json']:
  key='UserData/FreedomArrow/'+name
  if key not in override:
   d=json.loads(z.read(key));d['build']=26;override[key]=enc(d)
 key='UserData/FreedomArrow/channel.json';d=json.loads(z.read(key));d.update(package_version='26',verification='Compiled runtime identity corrected; exact Build25 artwork retained; all Build25 gameplay table bytes, weapon HUD, models, rigging, music and audio retained. Native appearance pending.');override[key]=enc(d)
 # No constants/table override is permitted.
 assert not any(n.startswith('UserData/FreedomArrow/constants/') for n in override)
 key='UserData/FAAssets/manifest.json';assets=json.loads(z.read(key));assets['version']='PLA TEST Build 26'
 for n,b in override.items():
  if n in assets['files']:assets['files'][n]=sha(b)
 override[key]=enc(assets);core['version']='26'
 for n,b in override.items():
  if n in core['sha256'] or n.startswith('UserData/FreedomArrow/'):core['sha256'][n]=sha(b)
 override['UserData/FreedomArrow/payload-manifest.json']=enc(core);whole.update(build=26,label='PLA TEST Build 26')
 for n,b in override.items():
  if n not in ['mod.json','README.md']:whole['sha256'][n]=sha(b)
 whole['core_paths']=sorted(set(whole['core_paths'])|{n for n in override if n.startswith('UserData/FreedomArrow/')});override['UserData/FreedomArrow/pla-package-manifest.json']=enc(whole)
 a.out.parent.mkdir(parents=True,exist_ok=True);subprocess.run(['cp','--reflink=auto',str(a.base.resolve()),str(a.out.resolve())],check=True)
 with tempfile.TemporaryDirectory() as t:
  stage=Path(t)
  for n,b in override.items():f=stage/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
  subprocess.run([a.zip,'-q',str(a.out.resolve()),*sorted(override)],cwd=stage,check=True)
with zipfile.ZipFile(a.out) as z,zipfile.ZipFile(a.base) as base:
 assert len(z.namelist())==len(set(z.namelist()))
 for n,s in whole['sha256'].items():
  with z.open(n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==s,n
 for n,s in core['sha256'].items():assert sha(z.read(n))==s,n
 changed=[n for n in oldpins if whole['sha256'].get(n)!=oldpins[n]]
 for n in base.namelist():
  if n.startswith(('UserData/FAModels/','UserData/FAMusic/','UserData/FreedomArrow/constants/')) or n in ['Mods/FAMusic.dll','Mods/FAModels.dll']:assert z.read(n)==base.read(n),n
 assert z.read('UserData/FreedomArrow/constants/units.json')==base.read('UserData/FreedomArrow/constants/units.json')
 table_count=sum(n.startswith('UserData/FreedomArrow/constants/') and n.endswith('.json') for n in base.namelist());assert table_count==24
receipt={'label':'PLA TEST Build 26','sha256':digest(a.out),'bytes':a.out.stat().st_size,'base_build':25,'base_sha256':c['runtime_base_sha256'],'verified_payloads':len(whole['sha256']),'verified_core_hashes':len(core['sha256']),'gameplay_tables_byte_identical':24,'models_music_rigging_audio_unchanged':True,'music_player_version':'1.5.0','changed_paths':sorted(changed),'new_paths':sorted(set(whole['sha256'])-set(oldpins)),'native_verified':False,'installed':False};a.out.with_suffix('.json').write_bytes(enc(receipt));print(json.dumps(receipt,indent=2))

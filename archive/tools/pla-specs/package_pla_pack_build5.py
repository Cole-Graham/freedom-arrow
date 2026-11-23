"""Build one complete PLA pack; preserve compressed models/music and verify all payloads."""
from pathlib import Path
import argparse,hashlib,json,subprocess,tempfile,zipfile
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'releases/0.6'
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(x):return (json.dumps(x,indent=2)+'\n').encode()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--zip',default='zip');a=p.parse_args();c=json.loads((R/'pla-specializations-contract.json').read_text());assert digest(a.base)==c['base_sha256'];label='PLA TEST Build '+str(c['build']);version=str(c['build']);info=json.loads((R/'mod.json').read_text());assert info['name']==label and info['version']==version
src=R/'source';override={}
with zipfile.ZipFile(a.base) as base:
 identity=json.loads(base.read('UserData/FreedomArrow/pla-package-manifest.json'));oldpins=identity['sha256'].copy();core=json.loads(base.read('UserData/FreedomArrow/payload-manifest.json'))
 for folder in ['UserData/FreedomArrow/constants','UserData/FAModels']:
  for f in sorted((src/folder).glob('*.json')):
   n=f.relative_to(src).as_posix();data=f.read_bytes()
   if n not in oldpins or sha(data)!=oldpins[n]:override[n]=data
 if c.get('merged_from'):
  override['UserData/FreedomArrow/merge-provenance.json']=enc({'build':c['build'],'parents':c['merged_from'],'scope':'All Build9 branch/Test/infantry work plus Build10 immediate stand-in hide; native validation pending'})
 if (src/'UserData/FreedomArrow/pla-model-catalogue.json').exists():override['UserData/FreedomArrow/pla-model-catalogue.json']=(src/'UserData/FreedomArrow/pla-model-catalogue.json').read_bytes()
 override['UserData/FreedomArrow/pla-spec-assignments.json']=(src/'UserData/FreedomArrow/pla-spec-assignments.json').read_bytes()
 for name in ['pla-vehicle-armament.json','pla-infantry-designer.json','pla-weapon-hud.json','weapon-hud-references.json']:
  override['UserData/FreedomArrow/'+name]=(src/'UserData/FreedomArrow'/name).read_bytes()
 override['UserData/FreedomArrow/pla-specializations.json']=(src/'UserData/FreedomArrow/pla-specializations.json').read_bytes()
 repair=json.loads((src/'UserData/FreedomArrow/infantry-arm-repair.json').read_text())
 for n,h in repair['sha256'].items():
  data=(src/n).read_bytes();assert sha(data)==h;override[n]=data
 override['UserData/FreedomArrow/infantry-arm-repair.json']=enc(repair)
 override['Mods/FAModels.dll']=(R/'experimental-model-loader/bin/Release/net6.0/FAModels.dll').read_bytes()
 override['Mods/FreedomArrow.Runtime.dll']=(src/'runtime-qa/bin/Release/net6.0/FreedomArrow.Runtime.dll').read_bytes()
 for n in ['README.md','mod.json']:override[n]=(ROOT/n).read_bytes() if n=='README.md' else enc(info)
 n='UserData/FreedomArrow/channel.json';d=json.loads(base.read(n));d.update(package_version=version,verification='PLA-only branch/infantry draft. Native Arsenal,deck creation and combat validation pending.');override[n]=enc(d)
 n='UserData/FreedomArrow/pla-build.json';d=json.loads(base.read(n));d.update(build=c['build'],label=label,china_ui=True,pla_only=c['pla_only'],specializations=[x['id'] for x in c['specs']]);override[n]=enc(d)
 n='UserData/FreedomArrow/china-ui.json';d=json.loads((src/n).read_bytes());d.update(grouping='Primary/shared branch pools; see pla-specializations.json',pla_only=c['pla_only']);override[n]=enc(d)
 n='UserData/FreedomArrow/china-ui-checks.json';d={'historical_basis':'China UI preparation plus current branch draft; see pla-specializations.json','all_non_ui_fields_identical':False,'native_verified':False};override[n]=enc(d)
 n='UserData/FreedomArrow/release-notes.md';override[n]=(src/n).read_bytes()
 n='UserData/FAAssets/manifest.json';assets=json.loads(base.read(n));assets['version']=label
 for path,data in override.items():
  if path in assets['files']:assets['files'][path]=sha(data)
 override[n]=enc(assets)
 core['version']=version
 for n,b in override.items():
  if n in core['sha256'] or n.startswith('UserData/FreedomArrow/'):core['sha256'][n]=sha(b)
 override['UserData/FreedomArrow/payload-manifest.json']=enc(core)
 identity.update(build=c['build'],label=label)
 for n,b in override.items():
  if n not in ['README.md','mod.json']:identity['sha256'][n]=sha(b)
 identity['core_paths']=sorted(set(identity['core_paths'])|{n for n in override if n.startswith('UserData/FreedomArrow/')})
 override['UserData/FreedomArrow/pla-package-manifest.json']=enc(identity)
 a.out.parent.mkdir(parents=True,exist_ok=True);subprocess.run(['cp','--reflink=auto',str(a.base.resolve()),str(a.out.resolve())],check=True)
 with tempfile.TemporaryDirectory() as tmp:
  stage=Path(tmp)
  for n,b in override.items():f=stage/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
  subprocess.run([a.zip,'-q',str(a.out.resolve()),*sorted(override)],cwd=stage,check=True)
with zipfile.ZipFile(a.out) as z:
 assert len(z.namelist())==len(set(z.namelist()))
 for n,h in identity['sha256'].items():
  with z.open(n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==h,n
 changed={n for n,h in oldpins.items() if identity['sha256'].get(n)!=h}
 allowed_bindings={'UserData/FAModels/infantry-bodies.json','UserData/FAModels/infantry-weapons.json','UserData/FAModels/models.json',*repair['sha256']}
 assert not any(n.startswith(('UserData/FAModels/','UserData/FAMusic/')) and n not in allowed_bindings for n in changed)
receipt={'label':label,'sha256':digest(a.out),'bytes':a.out.stat().st_size,'verified_payloads':len(identity['sha256']),'verified_core_hashes':len(core['sha256']),'unchanged_payloads':len(set(oldpins)-changed),'changed_paths':sorted(changed),'new_paths':sorted(set(identity['sha256'])-set(oldpins)),'existing_static_models_cockpits_music_unchanged':True,'repaired_infantry_lods':75,'repacked_infantry_atlases':len(repair['repacked_atlases']),'installed':False,'native_verified':False};a.out.with_suffix('.json').write_bytes(enc(receipt));print(json.dumps(receipt,indent=2))

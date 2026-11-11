"""One complete PLA Build5 candidate from Build4: preserve all assets, replace only checked UI data/runtime."""
from pathlib import Path
import argparse,hashlib,json,sys,zipfile
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'releases/0.6'
sys.path.insert(0,str(ROOT));from pipeline.tables import FIELD_TO_FILE
ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
def sha(b):return hashlib.sha256(b).hexdigest()
def sha_file(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(4*1024*1024):h.update(b)
 return h.hexdigest()
def enc(x):return (json.dumps(x,indent=2)+'\n').encode()
assert sha_file(a.base)=='8eca43e9f4ecd6bfcbb0b4a9ffe666a38d9b5121c66825106669d35c3ca94656'
checks=json.loads((R/'source/UserData/FreedomArrow/china-ui-checks.json').read_text());assert checks['all_non_ui_fields_identical']
override={}
with zipfile.ZipFile(a.base) as z:
 identity=json.loads(z.read('UserData/FreedomArrow/pla-package-manifest.json'));basepins=identity['sha256']
 for t in checks['changed_rows']:
  n='UserData/FreedomArrow/constants/'+FIELD_TO_FILE[t];override[n]=(R/'source'/n).read_bytes()
 for n in ['china-ui.json','china-ui-checks.json']:override['UserData/FreedomArrow/'+n]=(R/'source/UserData/FreedomArrow'/n).read_bytes()
 override['Mods/FreedomArrow.Runtime.dll']=(R/'source/runtime-qa/bin/Release/net6.0/FreedomArrow.Runtime.dll').read_bytes()
 channel=json.loads(z.read('UserData/FreedomArrow/channel.json'));channel.update(package_version='5',verification='China UI prototype; native layout and network support unverified.');override['UserData/FreedomArrow/channel.json']=enc(channel)
 build=json.loads(z.read('UserData/FreedomArrow/pla-build.json'));build.update(build=5,label='PLA TEST Build 5',china_ui=True);override['UserData/FreedomArrow/pla-build.json']=enc(build)
 override['UserData/FreedomArrow/release-notes.md']=(R/'source/UserData/FreedomArrow/release-notes.md').read_bytes()
 core=json.loads(z.read('UserData/FreedomArrow/payload-manifest.json'));core['version']='5'
 for n,b in override.items():core['sha256'][n]=sha(b)
 override['UserData/FreedomArrow/payload-manifest.json']=enc(core)
 assets=json.loads(z.read('UserData/FAAssets/manifest.json'));assets['version']='PLA TEST Build 5';override['UserData/FAAssets/manifest.json']=enc(assets)
 info=json.loads((R/'mod.json').read_text());assert info['version']=='5';info['repo']='Cole-Graham/freedom-arrow'
 pins={};retained=0;a.out.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(a.out,'w',zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as out:
  for n in sorted(set(basepins)|set(override)):
   if n in override:b=override[n]
   else:b=z.read(n);assert sha(b)==basepins[n],n;retained+=1
   pins[n]=sha(b);out.writestr(n,b)
  identity.update(build=5,label='PLA TEST Build 5',sha256=pins)
  identity['core_paths']=sorted(set(identity['core_paths'])|{n for n in override if n.startswith('UserData/FreedomArrow/')})
  out.writestr('UserData/FreedomArrow/pla-package-manifest.json',enc(identity));out.writestr('mod.json',enc(info));out.writestr('README.md',(R/'README.md').read_bytes())
receipt={'label':'PLA TEST Build 5','sha256':sha_file(a.out),'bytes':a.out.stat().st_size,'payload_files':len(pins),'unchanged_payloads_verified':retained,'changed_paths':sorted(override),'models_music_and_infantry_assets_byte_identical':True,'native_verified':False,'installed':False}
a.out.with_suffix('.json').write_bytes(enc(receipt));print(json.dumps(receipt,indent=2))

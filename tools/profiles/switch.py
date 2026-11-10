"""Select an explicitly pinned PLA or live package while retaining shared assets."""
from pathlib import Path
import argparse,datetime,fcntl,hashlib,json,shutil,sys,zipfile

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(4*1024*1024):h.update(b)
 return h.hexdigest()
def closed():
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   if 'brokenarrow' in (p/'comm').read_text().lower():raise RuntimeError('Close Broken Arrow before switching builds.')
  except (FileNotFoundError,PermissionError,ProcessLookupError):pass

def install(profile,g,h,check=False):
 closed();pkg=h/'Downloads'/profile['file'];assert sha(pkg)==profile['sha256'],'Package checksum mismatch'
 z=zipfile.ZipFile(pkg);names=[n for n in z.namelist() if not n.endswith('/')];assert len(names)==len(set(names));assert all(not Path(n).is_absolute() and '..' not in Path(n).parts and '\\' not in n for n in names)
 info=json.loads(z.read('mod.json'));assert info['id']=='freedomarrow.gameplay' and info['version']==profile['version']
 core=json.loads(z.read('UserData/FreedomArrow/payload-manifest.json'));assert core['version']==profile['version']
 if profile['kind']=='pla':
  whole=json.loads(z.read('UserData/FreedomArrow/pla-package-manifest.json'));assert whole['label']=='PLA Build 1' and whole['build']==profile['build'];pins=whole['sha256']
  cfg=json.loads(z.read('UserData/FreedomArrow/pla-build.json'));assert cfg['build']==profile['build']
  infantry=cfg['infantry'];assert {'QLU11','QTS11','QTS11_GL'}<=set(infantry['weapons'])
  rules=json.loads(z.read('UserData/FAModels/infantry-weapons.json'))
  for key,offset in [('QLU11',[0,-.17,.22]),('QTS11',[0,-.17,.196]),('QTS11_GL',[0,-.17,.196])]:assert any(r['weaponId']==infantry['weapons'][key]['weaponId'] and r['offset']==offset for r in rules)
 else:
  assert 'UserData/FreedomArrow/pla-build.json' not in names;assert 'UserData/FreedomArrow/pla-infantry-prototype.json' not in names;pins=core['sha256']
 for n,s in pins.items():assert hashlib.sha256(z.read(n)).hexdigest()==s,n
 assert sha(g/'GameAssembly.dll')==json.loads(z.read('UserData/FreedomArrow/compatibility.json'))['game_assembly_sha256']
 if check:return {'checked':profile['label'],'hashes':len(pins),'installed':False}
 manifest=g/'UserData/BAModManager/manifest.json';oldmanifest=manifest.read_bytes();m=json.loads(oldmanifest)
 pk=next(p for p in m['packages'] if p.get('info',{}).get('id')=='freedomarrow.gameplay')
 assert pk['enabled'];oldfiles=list(pk['files'])
 shared=lambda n:n.startswith(('UserData/FAModels/','UserData/FAMusic/','UserData/FAAssets/')) or n in ('Mods/FAModels.dll','Mods/FAMusic.dll')
 pay=[n for n in names if n.startswith(('Mods/','UserData/'))];preserve={'UserData/FAMusic/voice-presets.txt','UserData/FAMusic/music-history.txt'}
 write=[n for n in pay if not (n in preserve and (g/n).exists()) and (not (g/n).is_file() or sha(g/n)!=hashlib.sha256(z.read(n)).hexdigest())]
 remove=[n for n in set(oldfiles)-set(pay) if not shared(n)];targets=sorted(set(write)|set(remove)|{'UserData/FreedomArrow/selected-build.json'});backup=h/'Games/BA-Backups'/('pre-'+profile['label'].replace(' ','-')+'-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'));backup.mkdir(parents=True);existed=[]
 for n in targets:
  p=g/n
  if p.is_file():d=backup/n;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d);existed.append(n)
 (backup/'manifest.json').write_bytes(oldmanifest)
 restore='from pathlib import Path\nimport shutil\nb=Path('+repr(str(backup))+');g=Path('+repr(str(g))+')\nfor n in '+repr(targets)+':\n p=g/n\n if n in '+repr(existed)+':\n  p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(b/n,p)\n else:p.unlink(missing_ok=True)\nshutil.copy2(b/"manifest.json",g/"UserData/BAModManager/manifest.json")\n';(backup/'restore.py').write_text(restore)
 with (h/'.agent-changes.log').open('a') as f:f.write(datetime.datetime.now().astimezone().isoformat()+' | BA Codex | '+profile['label']+' complete profile; shared models/music retained | undo: python3 '+str(backup/'restore.py')+'\n')
 try:
  closed();assert manifest.read_bytes()==oldmanifest,'Manager changed during preflight'
  for n in write:
   p=g/n;p.parent.mkdir(parents=True,exist_ok=True);temp=p.with_name(p.name+'.fatmp');temp.write_bytes(z.read(n));temp.replace(p)
  for n in remove:(g/n).unlink(missing_ok=True)
  retained={str(p.relative_to(g)) for folder in ('UserData/FAModels','UserData/FAMusic','UserData/FAAssets') if (g/folder).exists() for p in (g/folder).rglob('*') if p.is_file()}
  pk.update(name=profile['label'],info=info,files=sorted(set(pay)|retained|{'Mods/FAModels.dll','Mods/FAMusic.dll'}),source='Z:'+str(pkg).replace('/','\\'),installedAt=datetime.datetime.now().astimezone().isoformat(),enabled=True)
  for other in m['packages']:
   if other is not pk:other['enabled']=False
  temp=manifest.with_suffix('.json.fatmp');temp.write_text(json.dumps(m,indent=2)+'\n');temp.replace(manifest)
  for n,s in pins.items():
   if n not in preserve:assert sha(g/n)==s,n
  assert json.loads(manifest.read_text())['packages'][m['packages'].index(pk)]['info']['version']==profile['version']
 except Exception:exec(compile(restore,str(backup/'restore.py'),'exec'));raise
 result={'installed':profile['label'],'verified_hashes':len(pins),'preserved_user_preferences':[n for n in preserve if (g/n).exists()],'shared_models_music_retained':True,'changed_files':len(write),'removed_old_gameplay_files':len(remove),'undo':'python3 '+str(backup/'restore.py'),'runtime_verified':False}
 (g/'UserData/FreedomArrow/selected-build.json').write_text(json.dumps(result,indent=2)+'\n');return result

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('profile',choices=['pla','live']);ap.add_argument('--check',action='store_true');ap.add_argument('--profiles',type=Path,default=Path.home()/'Games/FreedomArrow-Profiles/profiles.json');args=ap.parse_args();h=Path.home();g=h/'.local/share/Steam/steamapps/common/broken_arrow';p=json.loads(args.profiles.read_text())[args.profile]
 with (h/'Games/FreedomArrow-Profiles/switch.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);print(json.dumps(install(p,g,h,args.check),indent=2))
if __name__=='__main__':main()

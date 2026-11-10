#!/usr/bin/env python3
"""Install a verified music-only sample after the game closes. Keep a guarded undo."""
from pathlib import Path
from datetime import datetime
import hashlib, json, os, re, shutil, sys, zipfile

task=Path(__file__).resolve().parent
root=Path.home()/'.local/share/Steam/steamapps/common/broken_arrow'
backup=task/'backup'
status=task/'install-status.json'
manifest=json.loads((task/'payload-manifest.json').read_text())
menus=[Path('UserData/FAMusic/Packs')/p/'Menu' for p in ['China','Black Hawk Down']]
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def busy():
 for p in Path('/proc').iterdir():
  try:
   if p.name.isdigit() and (p/'comm').read_text().strip().lower()=='brokenarrow.exe':return True
  except OSError:pass
 return False
def save(state,**kw):
 data={'status':state,'time':datetime.now().astimezone().isoformat(),**kw}
 status.write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data),flush=True)
def music09():
 p=root/'UserData/FAMusic/Packs/Black Hawk Down'
 return [f.relative_to(root) for f in p.rglob('*') if f.is_file() and re.search(r'\btheme\s*0?9\b',f.stem,re.I)]
def scoped(rel):
 return (rel=='Mods/FAMusic.dll' or any(rel.startswith(str(p)+'/') for p in menus)
         or (rel.startswith('UserData/FAMusic/Packs/Black Hawk Down/') and re.search(r'\btheme\s*0?9\b',Path(rel).stem,re.I)))
def others():
 return {str(p.relative_to(root)):digest(p) for top in ['Mods','UserData'] for p in (root/top).rglob('*') if p.is_file() and not scoped(str(p.relative_to(root))) and not p.is_symlink()}
def restore():
 before=json.loads((backup/'before.json').read_text())
 for rel in menus:
  if (root/rel).exists():shutil.rmtree(root/rel)
 for rel in before['affected']:
  dst=root/rel;src=backup/'files'/rel
  if src.exists():dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
  elif dst.exists():dst.unlink()
 if not all(digest(root/p)==v for p,v in before['hashes'].items()):raise RuntimeError('Undo readback failed')
if busy():
 print('PENDING: close Broken Arrow before install or undo');raise SystemExit(2)
if '--undo' in sys.argv:
 for rel,h in manifest['files'].items():
  if not (root/rel).exists() or digest(root/rel)!=h:raise SystemExit('Refusing to undo over a subsequent music update')
 restore();save('restored');raise SystemExit()
if status.exists() and json.loads(status.read_text())['status']=='installed':
 assert all(digest(root/p)==h for p,h in manifest['files'].items())
 print('Already installed and hashes match');raise SystemExit()
assert digest(root/'Mods/FAMusic.dll')==manifest['expected_old_player_sha256'],'Installed player changed; inspect before install'
assert not backup.exists(),'Backup already exists; inspect previous attempt'
with zipfile.ZipFile(task/'music-sample-1.4.2.zip') as z:
 assert set(z.namelist())==set(manifest['files'])
 for n in z.namelist():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts
  assert hashlib.sha256(z.read(n)).hexdigest()==manifest['files'][n]
 z.extractall(task/'payload')
affected=set(manifest['files'])|{str(p) for p in music09()}
for m in menus:
 affected|={str(p.relative_to(root)) for p in (root/m).rglob('*') if p.is_file()}
untouched=others();before={'affected':sorted(affected),'hashes':{p:digest(root/p) for p in affected if (root/p).is_file()},'unchanged':untouched}
backup.mkdir()
for rel in affected:
 p=root/rel
 if p.is_file():
  dst=backup/'files'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
(backup/'before.json').write_text(json.dumps(before,indent=2)+'\n')
undo=f'python3 {task}/install.py --undo'
with (Path.home()/'.agent-changes.log').open('a') as f:
 f.write(f'{datetime.now().astimezone().isoformat()} | BA Codex | music-only sample1.4.2: replace China/BHD menu compilations, remove BHD theme09, preserve pack choice and game data | undo: {undo}\n')
try:
 if busy():raise RuntimeError('Game opened before install; no changes applied')
 for m in menus:
  if (root/m).exists():shutil.rmtree(root/m)
 for rel in music09():(root/rel).unlink()
 for rel,h in manifest['files'].items():
  dst=root/rel;dst.parent.mkdir(parents=True,exist_ok=True)
  tmp=dst.with_name(dst.name+'.music142-tmp');shutil.copy2(task/'payload'/rel,tmp);os.replace(tmp,dst)
 assert all(digest(root/p)==h for p,h in manifest['files'].items())
 assert all(len([p for p in (root/m).rglob('*') if p.is_file()])==2 for m in menus)
 assert not music09()
 after=others();assert untouched==after,'Unexpected changes outside requested music scope'
 save('installed',version='1.4.2',files=manifest['files'],unchanged_files=len(untouched),
      current_pack=(root/'UserData/FAMusic/pack.txt').read_text().strip(),game_running=False,
      native_playback_verified=False,undo=undo)
except Exception:
 restore();raise

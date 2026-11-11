"""Install only the two grey-panel metallic/smoothness masks while Broken Arrow is closed."""
from pathlib import Path
import argparse,datetime,fcntl,hashlib,json,shutil,struct,zipfile

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def closed():
 for p in Path('/proc').glob('[0-9]*/comm'):
  try:
   if 'brokenarrow' in p.read_text().lower():raise RuntimeError('Close Broken Arrow before changing textures.')
  except (FileNotFoundError,PermissionError,ProcessLookupError):pass

def install(archive,pin,game):
 closed();assert sha(archive)==pin,'Archive checksum mismatch'
 with zipfile.ZipFile(archive) as z:
  recipe=json.loads(z.read('sheen-trial.json'))
  allowed={'UserData/FAModels/'+p+'_tex0_mask.png' for p in ['m_abramsx_cg','m_abramsx_lo']}
  assert set(recipe['files'])==allowed and len(z.namelist())==3 and set(z.namelist())==allowed|{'sheen-trial.json'}
  payload={n:z.read(n) for n in allowed}
  for n,data in payload.items():
   assert hashlib.sha256(data).hexdigest()==recipe['files'][n]
   limit=2048 if '_cg_' in n else 1024;assert struct.unpack('>II',data[16:24])==(limit,limit)
   assert sha(game/n)==recipe['base_files'][n],'Existing material mask changed; inspect before writing'
 for n,pin in recipe['required_files'].items():assert sha(game/n)==pin,'Existing silver colour changed'
 for n,pin in recipe['mesh_sha256'].items():assert sha(game/'UserData/FAModels'/n)==pin,'Current mesh changed'
 metadata='UserData/FAAssets/manifest.json';original=(game/metadata).read_bytes();m=json.loads(original)
 m['files'].update(recipe['files']);m.setdefault('local_overrides',{})['abramsx_grey_sheen_trial']={'armory_max':2048,'battle_max':1024,'files':recipe['files'],'native_verified':False}
 writes={**payload,metadata:(json.dumps(m,indent=2)+'\n').encode()}
 protected={str(p.relative_to(game)):sha(p) for folder in ['UserData/FAModels','UserData/FAMusic','UserData/FAAssets','UserData/FreedomArrow'] for p in (game/folder).rglob('*') if p.is_file() and str(p.relative_to(game)) not in writes}
 for n in ['Mods/FAModels.dll','Mods/FAMusic.dll','Mods/FreedomArrow.Runtime.dll','UserData/BAModManager/manifest.json']:protected[n]=sha(game/n)
 b=Path.home()/'Games/BA-Backups'/('pre-abramsx-grey-sheen-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'));b.mkdir(parents=True)
 for n in writes:p=b/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(game/n,p)
 restore='from pathlib import Path\nimport shutil\ng=Path('+repr(str(game))+');b=Path('+repr(str(b))+')\nfor p in Path("/proc").glob("[0-9]*/comm"):\n try: assert "brokenarrow" not in p.read_text().lower(),"Close Broken Arrow before restoring previous silver finish"\n except (FileNotFoundError,PermissionError,ProcessLookupError): pass\nfor n in '+repr(list(writes))+':shutil.copy2(b/n,g/n)\nprint("Previous silver material masks and asset receipt restored.")\n'
 (b/'restore.py').write_text(restore)
 with (Path.home()/'.agent-changes.log').open('a') as f:f.write(datetime.datetime.now().astimezone().isoformat()+' | BA Codex | Abrams X grey sheen trial; same armory2K,battle1K masks; grey metallic/smoothness channels only, meshes and gameplay retained | undo: python3 '+str(b/'restore.py')+'\n')
 try:
  closed();assert (game/metadata).read_bytes()==original,'Asset metadata changed during preflight'
  for n,data in writes.items():p=game/n;tmp=p.with_name(p.name+'.fatmp');tmp.write_bytes(data);tmp.replace(p)
  for n,pin in recipe['files'].items():assert sha(game/n)==pin
  changed=[n for n,pin in protected.items() if not (game/n).is_file() or sha(game/n)!=pin];assert not changed,changed
 except Exception:exec(compile(restore,str(b/'restore.py'),'exec'));raise
 return {'installed':recipe['label'],'material_masks_changed':2,'asset_manifest_updated':True,'armory_resolution':2048,'battle_resolution':1024,'mesh_and_other_files_preserved':len(protected),'native_verified':False,'undo':'python3 '+str(b/'restore.py')}

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('archive',type=Path);ap.add_argument('--sha256',required=True);ap.add_argument('--game-root',type=Path,default=Path.home()/'.local/share/Steam/steamapps/common/broken_arrow');a=ap.parse_args()
 with (Path.home()/'Games/FreedomArrow-Profiles/switch.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);print(json.dumps(install(a.archive,a.sha256,a.game_root),indent=2))
if __name__=='__main__':main()

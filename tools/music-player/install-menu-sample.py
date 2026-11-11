"""Guarded one-DLL music UI sample; current gameplay/profile and all audio retained."""
from pathlib import Path
import os,hashlib,json,shutil,datetime,fcntl
h=Path.home();root=h/'Games/BA-Codex-MusicUI-20261111';g=h/'.local/share/Steam/steamapps/common/broken_arrow'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old='6f7d03261d2e6dfbc1e18bcecf8b54a561853de053fba61d57abf8ceef2f4ca5'
new='2e4befa630f3bd953aace65b06b4b5887742f69ca347be3f2a1cbc83e4acd90b'
def closed():
 for p in Path('/proc').iterdir():
  try:
   if p.name.isdigit() and 'brokenarrow' in (p/'comm').read_text().lower():raise SystemExit('Game is running; no install')
  except (FileNotFoundError,PermissionError,ProcessLookupError):pass
with (h/'Games/FreedomArrow-Profiles/switch.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);closed()
 dst=g/'Mods/FAMusic.dll';src=root/'FAMusic-1.5.0.dll';assert sha(src)==new;assert sha(dst)==old,'Music changed; recheck before replacing'
 core=json.loads((g/'UserData/FreedomArrow/payload-manifest.json').read_text())['sha256']
 assert 'Mods/FAMusic.dll' not in core
 for n,s in core.items():assert sha(g/n)==s,n
 before={n:sha(g/n) for n in ['UserData/FAMusic/pack.txt','UserData/FAMusic/voice-presets.txt','UserData/BAModManager/manifest.json','UserData/FreedomArrow/selected-build.json'] if (g/n).is_file()}
 backup=root/'live-backup';backup.mkdir(exist_ok=False);shutil.copy2(dst,backup/'FAMusic.dll')
 undo='from pathlib import Path\nimport hashlib,shutil\nh=Path.home();g=h/".local/share/Steam/steamapps/common/broken_arrow"\nfor p in Path("/proc").iterdir():\n try:\n  if p.name.isdigit() and "brokenarrow" in (p/"comm").read_text().lower():raise SystemExit("Close Broken Arrow first")\n except (FileNotFoundError,PermissionError,ProcessLookupError):pass\np=g/"Mods/FAMusic.dll"\nassert hashlib.sha256(p.read_bytes()).hexdigest()=='+repr(new)+',"Music changed after this update; inspect before undo"\nshutil.copy2('+repr(str(backup/'FAMusic.dll'))+',p)\nprint("Restored FA Music 1.4.2; preferences retained")\n'
 (root/'undo-music.py').write_text(undo)
 with (h/'.agent-changes.log').open('a') as f:f.write(datetime.datetime.now().astimezone().isoformat()+' BA Codex music-only 1.5.0 native menu selector; one DLL. Undo: python3 '+str(root/'undo-music.py')+'\n')
 closed();temp=dst.with_suffix('.dll.music-ui-tmp');shutil.copy2(src,temp);temp.replace(dst)
 assert sha(dst)==new
 for n,s in before.items():assert sha(g/n)==s,n
 for n,s in core.items():assert sha(g/n)==s,n
 result={'installed':'FA Music 1.5.0','sha256':new,'old_sha256':old,'core_hashes_verified':len(core),'preferences_and_manager_unchanged':before,'gameplay_label':json.loads((g/'UserData/FreedomArrow/selected-build.json').read_text())['installed'],'undo':'python3 '+str(root/'undo-music.py'),'scope':'one DLL local sample; full PLA archives retain their existing music until next integration'}
 (root/'install-result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

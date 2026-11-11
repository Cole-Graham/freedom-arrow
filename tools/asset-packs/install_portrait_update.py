"""Install a pinned portrait-only gameplay revision, preserving every shared asset."""
from pathlib import Path
import argparse,fcntl,json,runpy,subprocess,shlex
p=argparse.ArgumentParser(description=__doc__);p.add_argument('profile',type=Path);a=p.parse_args()
h=Path.home();g=h/'.local/share/Steam/steamapps/common/broken_arrow';s=runpy.run_path(str(h/'Games/FreedomArrow-Profiles/switch.py'));profile=json.loads(a.profile.read_text())
with (h/'Games/FreedomArrow-Profiles/switch.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);s['closed']();s['install'](profile,g,h,check=True)
 before={}
 for folder in ['UserData/FAModels','UserData/FAMusic','UserData/FAAssets']:
  for f in (g/folder).rglob('*'):
   if f.is_file():before[f.relative_to(g).as_posix()]=s['sha'](f)
 for n in ['Mods/FAModels.dll','Mods/FAMusic.dll']:before[n]=s['sha'](g/n)
 result=s['install'](profile,g,h)
 try:
  for n,digest in before.items():assert s['sha'](g/n)==digest,n
 except Exception:
  subprocess.run(shlex.split(result['undo']),check=True);raise
 result.update(preserved_shared_files=len(before),asset_files_changed=0,public_feed_changed=False)
 (a.profile.parent/'installed-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

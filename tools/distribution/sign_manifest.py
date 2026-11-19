#!/home/sam/tars/work/ba-dev/replicas/codex/.venv/bin/python
"""Set the launcher / MelonLoader entries of the live version list, then publish it signed (fa_manifest.publish).
Lateralus 19 Nov 2026: launchers from 1.1.9 replace themselves with the listed launcher and install only the listed MelonLoader,
each checked by SHA-256; the list itself must carry our signature.

  ba-sign-manifest --check                       read the live signed list, verify it, print what it names (no writes)
  ba-sign-manifest --launcher EXE VERSION        upload EXE to R2 launcher/FreedomArrow-VERSION.exe and list it
  ba-sign-manifest --melonloader                 list the MelonLoader zip named by freedomarrow.app/launcher/melonloader.json
"""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,sys,urllib.request
ROOT=Path('/home/sam/tars/work/ba-dev/replicas/codex');sys.path.insert(0,str(ROOT/'bin'))
import fa_manifest as fm
p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('--check',action='store_true');p.add_argument('--launcher',nargs=2,metavar=('EXE','VERSION'));p.add_argument('--melonloader',action='store_true')
a=p.parse_args()
if a.check:
    d=json.loads(fm.opened(fm.get('https://freedomarrow.app/manifest/live.signed.json')))
    print(json.dumps({'signature':'valid','serial':d.get('serial'),'locked':d.get('locked_version'),'current':d.get('current'),'launcher':d.get('launcher'),'melonloader':d.get('melonloader')},indent=1));sys.exit()
if not (a.launcher or a.melonloader):p.error('nothing to do')
state=json.loads((ROOT/'work/build-install/state.json').read_text());manifest=json.loads(fm.LOCAL.read_text())
def sha(b):return hashlib.sha256(b).hexdigest()
if a.launcher:
    exe,version=Path(a.launcher[0]),a.launcher[1];assert re.fullmatch(r'\d+\.\d+\.\d+',version),version
    blob=exe.read_bytes();u=lambda s:s.encode('utf-16-le')
    # The exe's own version resource: ProductName "Freedom Arrow Launcher", then ProductVersion VERSION+<commit>.
    i=blob.rfind(u('ProductName\0\0Freedom Arrow Launcher'));j=blob.find(u('ProductVersion\0'),i)
    assert i>0 and j>0 and blob[j:j+200].decode('utf-16-le','ignore').split('\0')[1].strip().startswith(version+'+'),'exe is not Freedom Arrow Launcher '+version
    name=f'FreedomArrow-{version}.exe';staged=ROOT/'scratch'/name;staged.write_bytes(blob)
    out=json.loads(subprocess.run([str(ROOT/'bin/ba-r2-put'),str(staged),'launcher'],check=True,capture_output=True,text=True).stdout.strip().splitlines()[-1])
    assert out['sha256']==sha(blob) and out['size']==len(blob)
    manifest['launcher']={'version':version,'url':out['link'],'size':len(blob),'sha256':sha(blob)}
if a.melonloader:
    m=json.loads(fm.get('https://freedomarrow.app/launcher/melonloader.json'));assert m['url'].startswith('https://freedomarrow.app/launcher/'),m['url']
    z=fm.get(m['url']);assert sha(z)==m['sha256'],'MelonLoader zip differs from melonloader.json'
    manifest['melonloader']={'tag':m['tag'],'asset':m['asset'],'url':m['url'],'size':len(z),'sha256':sha(z)}
manifest=fm.publish(manifest,state['manifest_file_id'])
print(json.dumps({'published':True,'serial':manifest['serial'],'launcher':manifest.get('launcher'),'melonloader':manifest.get('melonloader')},indent=1))

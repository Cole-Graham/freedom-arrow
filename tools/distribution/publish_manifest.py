#!/home/sam/tars/work/ba-dev/replicas/codex/.venv/bin/python
"""Publish verified package references to the stable manifest; obey the live playtest lock.
Osama 14 Nov 2026 20:38 PST: "please use cloudflare from now on instead of google drive". New packages must be on R2
(https://freedomarrow.app/..., uploaded with bin/ba-r2-put). The manifest goes to R2 (manifest/live.json) and, until every
player has a launcher that reads R2, also to its old Drive file, which launchers up to 1.1.4 read.
Lateralus 19 Nov 2026: fa_manifest.publish also signs it (manifest/live.signed.json), the only list launchers from 1.1.9 accept."""
from pathlib import Path
import argparse,datetime,hashlib,json,re,subprocess,sys,tempfile,urllib.parse,urllib.request,zipfile
RCLONE='/nix/store/42rnb5c0v5pjzhlcx46ww02jpa917f23-rclone-1.74.4/bin/rclone';RCONF=str(Path.home()/'.config/ba-codex/r2-rclone.conf')
def rc(*args):return subprocess.run([RCLONE,'--config',RCONF,*args],check=True,capture_output=True,text=True).stdout
ROOT=Path('/home/sam/tars/work/ba-dev/replicas/codex');sys.path.insert(0,str(ROOT/'bin'))
from virgil_google import api,access_token
p=argparse.ArgumentParser();p.add_argument('version');p.add_argument('gameplay',type=Path);p.add_argument('url');p.add_argument('--assets',type=Path);a=p.parse_args()
h=ROOT/'work/build-install';state=json.loads((h/'state.json').read_text());path=h/'live-manifest.json';old=json.loads(path.read_text())
if state.get('locked') and state['locked']!=a.version:raise SystemExit('Live manifest locked to '+state['locked'])
file_id=state['manifest_file_id']
def package(file,url,expected_id):
 with zipfile.ZipFile(file) as z:m=json.loads(z.read('mod.json'))
 assert m['id']==expected_id
 sha=hashlib.file_digest(file.open('rb'),'sha256').hexdigest();md5=hashlib.file_digest(file.open('rb'),'md5').hexdigest()
 match=re.fullmatch(r'https://freedomarrow\.app/(gameplay|assets)/([^/?#]+)',url);assert match and match[2]==file.name,'Use the R2 address https://freedomarrow.app/<gameplay|assets>/<file> (bin/ba-r2-put)'
 r=json.loads(rc('lsjson','--hash','r2:freedomarrow/'+match[1]+'/','--include='+file.name) or '[]')
 assert r and r[0]['Size']==file.stat().st_size and r[0].get('Hashes',{}).get('md5')==md5,('R2 object differs from the local file',r)
 with urllib.request.urlopen(urllib.request.Request(url,method='HEAD',headers={'User-Agent':'ba-publish-manifest'}),timeout=60) as resp:assert resp.status==200 and int(resp.headers['Content-Length'])==file.stat().st_size
 return {'id':m['id'],'version':m['version'],'filename':file.name,'url':url,'size':file.stat().st_size,'sha256':sha}
game=package(a.gameplay,a.url,'freedomarrow.gameplay');assert game['version']==a.version
assets=package(a.assets,state['assets_link'],'freedomarrow.assets.live') if a.assets else next(r for r in old['releases'] if r['version']==old['current'])['assets']
assert assets['version']==state['assets_version'],'Asset version changed: pass --assets with its exact archive'
# Lateralus 17 Nov 2026: launchers from 1.1.5 update Assets file by file from the list that tools/distribution/publish_assets_index.py puts on
# R2. Link it when it exists for this exact package; launchers up to 1.1.4 ignore the field and keep using the full package.
def assets_index(pkg):
 name=pkg['filename'].removesuffix('.bamod')+'.files.json'
 if not rc('lsf','r2:freedomarrow/assets/index/','--include='+name).strip():return None
 url='https://freedomarrow.app/assets/index/'+name
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ba-publish-manifest'}),timeout=60) as resp:data=resp.read()
 idx=json.loads(data);assert idx['id']==pkg['id'] and idx['version']==pkg['version'] and idx['package']==pkg['filename'],('file list does not match the package',name)
 return {'url':url,'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}
assets={k:v for k,v in assets.items() if k!='index'}
if (index:=assets_index(assets)):assets['index']=index
new={'version':a.version,'gameplay':game,'assets':assets};by_version={r['version']:r for r in old['releases']};by_version[a.version]=new
latest=sorted(by_version,key=lambda v:tuple(map(int,re.findall(r'\d+',v))),reverse=True)[:2];protected={a.version,state.get('locked')};keep=set(latest)|protected
manifest={'schema':1,'channel':'live','current':a.version,'locked_version':state.get('locked'),'releases':[by_version[v] for v in sorted(by_version,key=lambda v:tuple(map(int,re.findall(r'\d+',v))),reverse=True) if v in keep]}
from fa_manifest import publish
manifest=publish(manifest,file_id)
print('Live version manifest published, signed and read back (R2 live.signed.json for 1.1.9+, live.json, Drive file for <=1.1.4):',a.version,'assets',assets['version'],'serial',manifest['serial'])

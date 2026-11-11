"""Publish verified package references to the stable manifest; obey the live playtest lock."""
from pathlib import Path
import argparse,datetime,hashlib,json,re,sys,urllib.parse,urllib.request,zipfile
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
 match=re.search(r'(?:/d/|[?&]id=)([A-Za-z0-9_-]+)',url);assert match,'Use a public Drive package URL'
 meta=api('https://www.googleapis.com/drive/v3/files/'+match[1]+'?fields=id,name,size,md5Checksum,permissions(type,role)')
 assert int(meta['size'])==file.stat().st_size and meta['md5Checksum']==md5
 assert any(x['type']=='anyone' and x['role']=='reader' for x in meta.get('permissions',[]))
 return {'id':m['id'],'version':m['version'],'filename':file.name,'url':'https://drive.google.com/uc?export=download&id='+match[1],'size':file.stat().st_size,'sha256':sha}
game=package(a.gameplay,a.url,'freedomarrow.gameplay');assert game['version']==a.version
assets=package(a.assets,state['assets_link'],'freedomarrow.assets.live') if a.assets else next(r for r in old['releases'] if r['version']==old['current'])['assets']
assert assets['version']==state['assets_version'],'Asset version changed: pass --assets with its exact archive'
new={'version':a.version,'gameplay':game,'assets':assets};by_version={r['version']:r for r in old['releases']};by_version[a.version]=new
latest=sorted(by_version,key=lambda v:tuple(map(int,re.findall(r'\d+',v))),reverse=True)[:2];protected={a.version,state.get('locked')};keep=set(latest)|protected
manifest={'schema':1,'channel':'live','current':a.version,'locked_version':state.get('locked'),'releases':[by_version[v] for v in sorted(by_version,key=lambda v:tuple(map(int,re.findall(r'\d+',v))),reverse=True) if v in keep]}
data=(json.dumps(manifest,indent=2)+'\n').encode()
req=urllib.request.Request('https://www.googleapis.com/upload/drive/v3/files/'+file_id+'?uploadType=media',data=data,method='PATCH',headers={'Authorization':'Bearer '+access_token(),'Content-Type':'application/json'})
with urllib.request.urlopen(req,timeout=60) as response:response.read()
url='https://drive.google.com/uc?export=download&id='+file_id+'&revision='+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')
with urllib.request.urlopen(url,timeout=60) as response:readback=json.load(response)
assert readback==manifest
path.with_suffix('.json.tmp').write_bytes(data);path.with_suffix('.json.tmp').replace(path)
print('Live version manifest published and read back:',a.version,'assets',assets['version'])

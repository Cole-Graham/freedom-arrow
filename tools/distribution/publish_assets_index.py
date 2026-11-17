"""Publish an Assets package as single files for the launcher (Lateralus 17 Nov 2026, thread 1571554273639006392: "change the updates for
the assets on the dedicated launcher, so that only changed and new models have to be downloaded, instead of the entire assets pack").
Each installed file of the .bamod (Mods/, Plugins/, UserData/, UserLibs/) goes to R2 once, gzipped, named by the SHA-256 of its content:
https://freedomarrow.app/assets/files/<sha256>.gz. Files already on R2 are not uploaded again, so a new Assets version uploads only its
changed files. The file list goes to https://freedomarrow.app/assets/index/<package>.files.json. The full .bamod stays as it is for dev
builds and for launchers up to 1.1.4; bin/ba-publish-manifest links the list from the manifest when it exists.
Nothing on R2 is replaced or deleted. Usage: publish_assets_index.py ASSETS.bamod [--dry-run]"""
import argparse,gzip,hashlib,json,shutil,subprocess,tempfile,urllib.request,zipfile
from pathlib import Path
RCLONE='/nix/store/42rnb5c0v5pjzhlcx46ww02jpa917f23-rclone-1.74.4/bin/rclone';RCONF=str(Path.home()/'.config/ba-codex/r2-rclone.conf')
BASE='https://freedomarrow.app/assets/files/';ROOTS=('Mods/','Plugins/','UserData/','UserLibs/');BATCH=1<<30
def rc(*args):return subprocess.run([RCLONE,'--config',RCONF,*args],check=True,capture_output=True,text=True).stdout
p=argparse.ArgumentParser();p.add_argument('bamod',type=Path);p.add_argument('--dry-run',action='store_true');a=p.parse_args()
z=zipfile.ZipFile(a.bamod);mod=json.loads(z.read('mod.json'))
assert mod['id']=='freedomarrow.assets.live',mod['id']
entries=[i for i in z.infolist() if not i.is_dir() and i.filename.replace('\\','/').startswith(ROOTS)]
paths=[i.filename.replace('\\','/') for i in entries];assert len(set(p.lower() for p in paths))==len(paths),'two entries differ only in case'
have={x.removesuffix('.gz') for x in rc('lsf','r2:freedomarrow/assets/files/').split()}
files,todo=[],{}
for i,path in zip(entries,paths):
    h=hashlib.sha256()
    with z.open(i) as s:
        for chunk in iter(lambda:s.read(1<<20),b''):h.update(chunk)
    sha=h.hexdigest();files.append({'path':path,'size':i.file_size,'sha256':sha})
    if sha not in have:todo.setdefault(sha,i)
todo=[(i,sha) for sha,i in todo.items()]
print(f'{a.bamod.name}: {len(files)} files, {sum(f["size"] for f in files)/1e9:.2f} GB; {len(todo)} not on R2 yet ({sum(i.file_size for i,_ in todo)/1e9:.2f} GB)')
if a.dry_run:raise SystemExit
uploaded=0
with tempfile.TemporaryDirectory(dir=a.bamod.parent) as tmp:   # on disk next to the package, not in RAM-backed /tmp
    tmp=Path(tmp);batch=0
    def flush():
        global uploaded
        if not any(tmp.iterdir()):return
        rc('copy',str(tmp),'r2:freedomarrow/assets/files/','--transfers','8','--no-traverse','--header-upload','Cache-Control: public, max-age=31536000, immutable')
        uploaded+=sum(1 for _ in tmp.iterdir());shutil.rmtree(tmp);tmp.mkdir()
        print(f'  uploaded {uploaded}/{len(todo)}',flush=True)
    for i,sha in todo:
        with z.open(i) as s,gzip.GzipFile(tmp/(sha+'.gz'),'wb',compresslevel=6,mtime=0) as g:shutil.copyfileobj(s,g,1<<20)
        batch+=i.file_size
        if batch>=BATCH:flush();batch=0
    flush()
index={'schema':1,'id':mod['id'],'version':mod['version'],'package':a.bamod.name,'files_base':BASE,'mod_json':z.read('mod.json').decode('utf-8'),
       'files':sorted(files,key=lambda f:f['path'].lower())}
data=(json.dumps(index,separators=(',',':'))+'\n').encode()
name=a.bamod.name.removesuffix('.bamod')+'.files.json'
with tempfile.TemporaryDirectory() as tmp:
    (Path(tmp)/name).write_bytes(data);rc('copyto',str(Path(tmp)/name),'r2:freedomarrow/assets/index/'+name)
url='https://freedomarrow.app/assets/index/'+name
with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'publish_assets_index'}),timeout=60) as r:assert r.read()==data,'index readback differs'
# Spot-check three uploaded files through the public address.
for f in files[:1]+files[len(files)//2:len(files)//2+1]+files[-1:]:
    with urllib.request.urlopen(urllib.request.Request(BASE+f['sha256']+'.gz',headers={'User-Agent':'publish_assets_index'}),timeout=120) as r:
        assert hashlib.sha256(gzip.decompress(r.read())).hexdigest()==f['sha256'],f['path']
print(json.dumps({'index':url,'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),'files':len(files),'uploaded':uploaded}))

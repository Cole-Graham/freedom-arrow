"""Assemble one PLA Build1 package from compiled gameplay and the approved installed asset snapshot."""
from pathlib import Path
import argparse,tarfile,zipfile,json,hashlib,struct,io,datetime
from zoneinfo import ZoneInfo
R=Path(__file__).resolve().parent
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--assets',type=Path,required=True);ap.add_argument('--models',type=Path,required=True);a=ap.parse_args()
sha=lambda b:hashlib.sha256(b).hexdigest();enc=lambda x:(json.dumps(x,indent=2)+'\n').encode()
core=zipfile.ZipFile(R/'out/FreedomArrow-1.bamod');assets=zipfile.ZipFile(a.assets);tar=tarfile.open(a.models);members={x.name:x for x in tar.getmembers() if x.isfile()}
def tb(n):return tar.extractfile(members[n]).read()
def need(n):
 assert not Path(n).is_absolute() and '..' not in Path(n).parts,n
 assert n in members,'Missing approved asset '+n
 chosen.add(n)
def fields(data,skin=False):
 f=io.BytesIO(data)
 def n():return struct.unpack('<i',f.read(4))[0]
 def s():return f.read(n()).decode()
 assert f.read(4)==(b'FAS1' if skin else b'FAM1')
 if skin:
  assert n()==40
  for _ in range(40):s()
  count=n()
  for _ in range(count):
   tex=s();nv=n();f.seek(nv*64,1);ni=n();f.seek(ni*4,1)
   if tex:yield tex
 else:
  for _ in range(n()):
   s()
   for _ in range(n()):
    tex=s();f.seek(16,1);nv=n();f.seek(nv*32,1);ni=n();f.seek(ni*4,1)
    if tex:yield tex
 assert not f.read()
mapname='UserData/FAModels/models.json';modelmap=json.loads(tb(mapname));chosen={mapname};mesh=set()
for rule in modelmap.values():
 for key in ['file','battle']:
  if rule.get(key):mesh.add('UserData/FAModels/'+rule[key])
wr='UserData/FAModels/infantry-weapons.json';br='UserData/FAModels/infantry-bodies.json';need(wr);need(br);rules=json.loads(tb(wr));body=json.loads(tb(br))
old={2003971:'QBZ191',2003973:'QBU191',2003975:'QLU11',2003977:'QTS11',2003979:'QTS11_GL'};binding=json.loads(core.read('UserData/FreedomArrow/pla-infantry-prototype.json'));newrules=[]
for row in rules:
 if row['weaponId'] in old:row['weaponId']=binding['weapons'][old[row['weaponId']]]['weaponId']
 elif row['unitId']==901:continue
 newrules.append(row)
 for key in ['file','battle']:
  if row.get(key):mesh.add('UserData/FAModels/'+row[key])
for row in body:
 for file in row['lods']:mesh.add('UserData/FAModels/'+file)
for name in sorted(mesh):
 need(name)
 side=str(Path(name).with_suffix('.mat.json'))
 if side in members:need(side)
 for tex in fields(tb(name),name.endswith('.fas')):
  p='UserData/FAModels/'+tex;need(p);stem=str(Path(p).with_suffix(''))
  for suffix in ['_n.png','_mask.png']:
   if stem+suffix in members:need(stem+suffix)
# All shared live/PLA model bytes use the approved installed snapshot, including bounded F14 maps.
payload={n:('core',n) for n in core.namelist() if n.startswith(('Mods/','UserData/'))}
for n in assets.namelist():
 if n.startswith(('Mods/','UserData/')):payload.setdefault(n,('assets',n))
for n in chosen:payload[n]=('tar',n)
override={wr:enc(newrules)}
# Core and asset manifests remain readable; the complete manifest pins every delivered payload member.
am='UserData/FAAssets/manifest.json';ameta=json.loads(assets.read(am));ameta['version']='PLA Build 1';ameta['notes'].append('One complete PLA Build1 with all referenced installed PLA/infantry models; approved poses and skins retained.')
for n in chosen:ameta['files'][n]=sha(override.get(n,tb(n)))
override[am]=enc(ameta)
info=json.loads(core.read('mod.json'));assert info['version']=='1';info['name']='PLA Build 1';info['description']='One complete PLA Build 1: all PLA vehicles, aircraft, fitted infantry, models, replacement textures, music and voices.'
output=R/'out/PLA-Build-1.bamod';pins={}
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
 for n,(origin,path) in sorted(payload.items()):
  b=override[n] if n in override else (core.read(path) if origin=='core' else assets.read(path) if origin=='assets' else tb(path));z.writestr(n,b);pins[n]=sha(b)
 manifest={'build':1,'label':'PLA Build 1','sha256':pins,'shared_asset_paths':[n for n in pins if n.startswith(('UserData/FAModels/','UserData/FAMusic/','UserData/FAAssets/')) or n in ('Mods/FAModels.dll','Mods/FAMusic.dll')],'core_paths':[n for n in pins if n not in [] and n.startswith(('Mods/','UserData/')) and n not in [x for x in pins if x.startswith(('UserData/FAModels/','UserData/FAMusic/','UserData/FAAssets/')) or x in ('Mods/FAModels.dll','Mods/FAMusic.dll')]]}
 z.writestr('UserData/FreedomArrow/pla-package-manifest.json',enc(manifest));z.writestr('mod.json',enc(info));z.writestr('README.md',core.read('README.md'))
result={'label':'PLA Build 1','path':str(output),'bytes':output.stat().st_size,'sha256':sha(output.read_bytes()),'payload_files':len(pins),'referenced_model_files':len(mesh),'approved_asset_snapshot_files':len(chosen),'infantry_bindings':binding['weapons'],'runtime_verified':False}
(R/'out/PLA-Build-1.json').write_bytes(enc(result));print(json.dumps(result,indent=2))

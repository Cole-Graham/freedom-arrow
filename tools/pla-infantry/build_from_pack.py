"""Reproducible infantry overlay on the SHA-pinned, complete PLA TEST Build1.

Retains the already-shipped data and assets; adds only comparison cards and rigs.
The older historical generator is not required to reproduce the published pack.
"""
from pathlib import Path
import argparse,copy,hashlib,json,sys,zipfile
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'releases/0.6';sys.path.insert(0,str(ROOT));sys.path.insert(0,str(R))
from pipeline.tables import FIELD_TO_FILE
from pipeline.crypto import aes_decrypt
from pla_configs import apply
ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--runtime',type=Path,required=True);ap.add_argument('--vanilla',type=Path,required=True);ap.add_argument('--rigs',type=Path,required=True);ap.add_argument('--music-update',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
sha=lambda b:hashlib.sha256(b).hexdigest();enc=lambda x:(json.dumps(x,indent=2)+'\n').encode()
version=json.loads((R/'mod.json').read_text())['version'];build=int(version);label='PLA TEST Build '+version
assert sha(a.base.read_bytes())=='ea2058ba5852df3b41a8dd9981ec9070d2bb4f223e10d39738631b03434a8364'
z=zipfile.ZipFile(a.base);oldpins=json.loads(z.read('UserData/FreedomArrow/pla-package-manifest.json'))['sha256'];assert all(sha(z.read(n))==h for n,h in oldpins.items())
compat=json.loads(z.read('UserData/FreedomArrow/compatibility.json'));effective={};patches={}
for table,digest in compat['source_plaintext_sha256'].items():
 raw=aes_decrypt((a.vanilla/(table+'.b64')).read_text());assert sha(raw)==digest
 rows={r['Id']:r for r in json.loads(raw)};p='UserData/FreedomArrow/constants/'+FIELD_TO_FILE[table];patches[table]=json.loads(z.read(p))
 for key,fields in patches[table].items():
  if fields is None:rows.pop(int(key),None)
  else:rows.setdefault(int(key),{'Id':int(key)}).update(fields)
 effective[table]=rows
nextid=max(i for rows in effective.values() for i in rows)+1;before=copy.deepcopy(effective)
def put(t,i,fields,why):effective[t].setdefault(i,{'Id':i}).update(fields);patches[t].setdefault(str(i),{}).update(fields)
def clone(t,i,fields,why):
 global nextid
 k=nextid;nextid+=1;r=copy.deepcopy(effective[t][i]);r.pop('Id');r.update(fields);put(t,k,r,why);return k
def add_unit(i,parent,fields,why):r=copy.deepcopy(effective['Units'][parent]);r.pop('Id');r.update(fields);put('Units',i,r,why)
def rows_of(t,u):return [r['Id'] for r in effective[t].values() if r.get('UnitId')==u]
src=R/'source/UserData/FreedomArrow';src.mkdir(parents=True,exist_ok=True);(src/'pla-build.json').write_bytes(z.read('UserData/FreedomArrow/pla-build.json'));apply(R,effective,put,clone,add_unit,rows_of)
configs=json.loads((src/'pla-infantry-configurations.json').read_text());assert len(configs)==25
assert all(before[t][i]==effective[t][i] for t in before for i in before[t]),'Existing data changed'
changes={}
for t in patches:
 for i in effective[t]:
  if i not in before[t]:changes.setdefault(t,[]).append(i)
override={}
for table,p in patches.items():override['UserData/FreedomArrow/constants/'+FIELD_TO_FILE[table]]=enc(p)
for n in ['pla-build.json','pla-infantry-configurations.json']:override['UserData/FreedomArrow/'+n]=(src/n).read_bytes()
body=json.loads(z.read('UserData/FAModels/infantry-bodies.json'));weapons=json.loads(z.read('UserData/FAModels/infantry-weapons.json'));originalweapons=copy.deepcopy([w for w in weapons if w['unitId']==901]);assert body[0]['offset']==[0,-.05,0]
for c in configs:
 assert all((a.rigs/f"pla2_{c['key']}_{l}.fas").is_file() and (a.rigs/f"pla2_{c['key']}_{l}.png").is_file() for l in range(3)),c
 body.append({'unitId':c['unit'],'lods':[f"pla2_{c['key']}_{l}.fas" for l in range(3)],'offset':c['body_offset'],'anchorHands':True})
 for w in originalweapons:weapons.append({**w,'unitId':c['unit']})
override['UserData/FAModels/infantry-bodies.json']=enc(body);override['UserData/FAModels/infantry-weapons.json']=enc(weapons)
for p in a.rigs.iterdir():
 if p.suffix in ['.png','.fas']:override['UserData/FAModels/'+p.name]=p.read_bytes()
override['Mods/FreedomArrow.Runtime.dll']=a.runtime.read_bytes()
override['Mods/FAModels.dll']=(R/'experimental-model-loader/bin/Release/net6.0/FAModels.dll').read_bytes()
channel=json.loads(z.read('UserData/FreedomArrow/channel.json'));channel['package_version']=version;override['UserData/FreedomArrow/channel.json']=enc(channel)
override['UserData/FreedomArrow/release-notes.md']=(R/'source/UserData/FreedomArrow/release-notes.md').read_bytes()
# Carry the accepted music sample into the complete pack; no old menu songs or BHD09.
excluded=set()
if a.music_update:
 receipt=json.loads(Path(__file__).with_name('music-update.json').read_text())
 assert sha(a.music_update.read_bytes())==receipt['zip_sha256'],'Music update archive mismatch'
 with zipfile.ZipFile(a.music_update) as music:
  assert set(music.namelist())==set(receipt['files'])
  for n,h in receipt['files'].items():
   b=music.read(n);assert sha(b)==h,n;override[n]=b
 for n in oldpins:
  if n.startswith(('UserData/FAMusic/Packs/China/Menu/','UserData/FAMusic/Packs/Black Hawk Down/Menu/')) or n=='UserData/FAMusic/Packs/Black Hawk Down/Battle/GLA theme 09.mp3':excluded.add(n)
 excluded-=set(override)

core=json.loads(z.read('UserData/FreedomArrow/payload-manifest.json'));core['version']=version
for n in list(core['sha256']):core['sha256'][n]=sha(override.get(n,z.read(n)))
core['sha256']['UserData/FreedomArrow/pla-infantry-configurations.json']=sha(override['UserData/FreedomArrow/pla-infantry-configurations.json']);override['UserData/FreedomArrow/payload-manifest.json']=enc(core)
assetname='UserData/FAAssets/manifest.json';assets=json.loads(z.read(assetname));assets['version']=label
for n,b in override.items():
 if n.startswith(('UserData/FAModels/','UserData/FAMusic/')) or n in ('Mods/FAModels.dll','Mods/FAMusic.dll'):assets['files'][n]=sha(b)
for n in excluded:assets['files'].pop(n,None)
override[assetname]=enc(assets)
info=json.loads(z.read('mod.json'));info.update(version=version,name=label,description='Complete PLA pack with 25 infantry comparison squads, refined arm fit and woodland helmets. Battle animation fit remains provisional.')
a.out.parent.mkdir(parents=True,exist_ok=True);pins={}
with zipfile.ZipFile(a.out,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as out:
 for n in sorted((set(oldpins)|set(override))-excluded):
  b=override[n] if n in override else z.read(n);out.writestr(n,b);pins[n]=sha(b)
 old=json.loads(z.read('UserData/FreedomArrow/pla-package-manifest.json'));old.update(build=build,label=label,sha256=pins);out.writestr('UserData/FreedomArrow/pla-package-manifest.json',enc(old));out.writestr('mod.json',enc(info));out.writestr('README.md',(R/'README.md').read_bytes())
result={'build':build,'label':label,'source_build1_sha256':sha(a.base.read_bytes()),'sha256':sha(a.out.read_bytes()),'bytes':a.out.stat().st_size,'payload_files':len(pins),'new_rows':changes,'existing_rows_unchanged':True,'configs':configs,'native_verified':False};a.out.with_suffix('.json').write_bytes(enc(result));print(json.dumps(result,indent=2))

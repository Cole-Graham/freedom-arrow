"""Freedom Arrow 0.8.0-dev.80 over exact 0.8.0-dev.79 (Osama 13 Nov 20:07-20:14 PST, thread 1571014792016171120):
"Lateralus uploaded 3 more models, can you please add them to our build?" and "PLAAF ZSD-89A should be the desert skin
while the others can stay woodlands."
- ZTL-11 and AFT-10: Lateralus's purchased ShuyangXi models (Drive "Subscription model drop 2", MD5-checked) replace the
  old stand-ins. Static (not rigged), seller scale, seller woodland digital coating (ZTL-11 "Mix", AFT-10 "Camo").
  Files m_ztl11s / m_aft10s, built by work/pla-0.8/drop2-20261113/build_all.py. The HJ-10 keeps sharing the AFT-10 model.
- PCL-181 / SH-15: the upload is byte-identical (inner archives) to the cart copy already in the game; no change.
- ZSD-89A PLAAF card (1249): the model loader keys models by unit Name and all four ZSD-89A cards shared
  'PLA Catalogue Type 89A', so card 1249 gets its own Name 'PLA Catalogue Type 89A PLAAF' and the seller's
  Textures_03_desert set (m_zsd89ad, same mesh and 1.2 scale). Cards 1065, 1248 and 1250 stay woodland.
Purchased files stay out of git; the complete package carries them.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.80';PREV='0.8.0-dev.79'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True)
p.add_argument('--stage',type=Path,action='append',required=True,help='directories holding the new .fam/.mat.json/.png files');a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];SA=t['SpecializationAvailabilitiesJson']
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
OLD,NEW='PLA Catalogue Type 89A','PLA Catalogue Type 89A PLAAF'
cards={u:U[u]['Name'] for u in (1065,1248,1249,1250)}
ok(all(n==OLD for n in cards.values()) and all(U[u]['HUDName']=='ZSD-89A' for u in cards),cards)
ok(sorted(r['SpecializationId'] for r in SA.values() if r.get('UnitId')==1249)==[17],'1249 is the PLAAF (spec 17) card only')
ok(1249 not in native['Units'],'1249 is a mod row')
ok(not any(u.get('Name')==NEW for u in U.values()),'new Name unused')
g.put('Units',1249,{'Name':NEW})
ok(U[1249]['Name']==NEW and all(U[u]['Name']==OLD for u in (1065,1248,1250)),'only 1249 renamed')
MJ='UserData/FAModels/models.json';raw=z.read(MJ);models=json.loads(raw)
before={k:dict(models[k]) for k in ('PLA ZTL-11','PLA Catalogue AFT-10','PLA HJ-10',OLD)}
ok(before['PLA ZTL-11']['file']=='m_ztl11_static.fam' and before['PLA Catalogue AFT-10']['file']==before['PLA HJ-10']['file']=='m_aft10_static.fam',before)
ok(before[OLD]=={'file':'m_zsd89a_static.fam','battle':'m_zsd89a_lo_static.fam','align':False,'scale':1.2},before[OLD])
ok(NEW not in models,'no PLAAF entry yet')
models['PLA ZTL-11']={'file':'m_ztl11s_static.fam','battle':'m_ztl11s_lo_static.fam','align':False}
for k in ('PLA Catalogue AFT-10','PLA HJ-10'):models[k]={'file':'m_aft10s_static.fam','battle':'m_aft10s_lo_static.fam','align':False}
models[NEW]={**before[OLD],'file':'m_zsd89ad_static.fam','battle':'m_zsd89ad_lo_static.fam'}
files={}
for d in a.stage:
    for f in sorted(d.iterdir()):
        if f.suffix in ('.fam','.json','.png'):files['UserData/FAModels/'+f.name]=str(f)
need={f'm_{s}_{q}static.{e}' for s in ('ztl11s','aft10s','zsd89ad') for q in ('','lo_') for e in ('fam','mat.json')}
ok(need<={k.split('/')[-1] for k in files},'all model files staged')
ok(not any(k in z.namelist() for k in files),'no staged file overwrites a shipped file')
for e in (models['PLA ZTL-11'],models['PLA HJ-10'],models[NEW]):
    for q in ('file','battle'):
        mat=json.loads(Path(files['UserData/FAModels/'+e[q].replace('.fam','.mat.json')]).read_text())
        for key in mat:
            tex=key.split('|')[0]
            if tex:ok('UserData/FAModels/'+tex in files,('texture staged',tex))
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=raw.isascii())+'\n').encode())
(ROOT/f'tools/pla-specs/{V}-assets.txt').write_text(''.join(f'{k}={v}\n' for k,v in sorted(files.items())))
receipt={'version':V,'base':PREV,'base_sha256':BASE,'request':'Osama 13 Nov 20:07 PST: add Lateralus\'s 3 uploaded models; 20:14 PST: PLAAF ZSD-89A desert, others woodland',
 'models_json':{k:{'before':before.get(k),'after':models[k]} for k in ('PLA ZTL-11','PLA Catalogue AFT-10','PLA HJ-10',NEW)},
 'units':{'1249':{'Name':[OLD,NEW]}},'pcl181':'upload identical to the cart copy already shipped; unchanged',
 'files':sorted(k.split('/')[-1] for k in files),'checks':checks,'verified':'data and file checks only'}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,'files',len(files))

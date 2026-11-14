"""Freedom Arrow 0.8.0-dev.96 over exact 0.8.0-dev.95 (Osama 13 Nov 22:59-23:13 PST, thread 1571014792016171120).
- Aircraft glass back as before my glass passes: the dev.92 opacity change had also hit four aircraft whose glass was already
  clear at 0.025 (F-14, Su-47, Su-57D, YF-23; 8 files), raising it to 0.1. Those files are restored byte-for-byte from dev.84.
  The aircraft that use the vanilla F-16 glass were never changed.
- Helicopter and ground-vehicle clear glass: 0.1 -> 0.025, the value those aircraft use.
- PHL-191 Cruise (AR3): launcher moved back so it no longer clips into the cab structure (front now behind it); nothing else
  sticks out (checked from three views). New file m_phl191cg.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.96';PREV='0.8.0-dev.95'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--stage',type=Path,required=True);a=p.parse_args()
base=REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);z84=zipfile.ZipFile(REL/'out/0.8/FreedomArrow-0.8.0-dev.84-complete.bamod');t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
U=t['Units'];checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
MJ='UserData/FAModels/models.json';raw=z.read(MJ);models=json.loads(raw)
cat={}
for u in U.values():
    e=models.get(u.get('Name'))
    if e:
        for q in ('file','battle'):
            if e.get(q):cat.setdefault('UserData/FAModels/'+e[q].replace('.fam','.mat.json'),set()).add(u.get('CategoryType'))
gdir=ROOT/f'tools/pla-specs/{V}-mats';gdir.mkdir(exist_ok=True);files={}
REV=['m_f14_cg','m_f14_lo','m_su47','m_su47_lo','m_su57d_cg','m_su57d_lo','m_yf23','m_yf23_lo']
for n in REV:
    k=f'UserData/FAModels/{n}.mat.json';ok(6 in cat.get(k,set()),('aircraft file',n));b=z84.read(k)
    ok(z.read(k)!=b,('changed since dev.84',n));f=gdir/(n+'.mat.json');f.write_bytes(b);files[k]=str(f)
rec['aircraft_glass_restored_from_dev84']=REV
cg=0;cgf=[]
for k in z.namelist():
    if not(k.startswith('UserData/FAModels/') and k.endswith('.mat.json')) or k in files:continue
    cs=cat.get(k,set())
    if 6 in cs or not cs:continue
    mj=json.loads(z.read(k));hit=0
    for v in mj.values():
        if v.get('clearGlass') and v.get('opacity')==0.1:v['opacity']=0.025;hit+=1
    if hit:f=gdir/k.split('/')[-1];f.write_text(json.dumps(mj,indent=1)+'\n');files[k]=str(f);cg+=hit;cgf.append(k.split('/')[-1])
ok(cg>=40,('helo/ground clear glass',cg));rec['helo_ground_clear_glass']={'opacity':[0.1,0.025],'materials':cg,'files':len(cgf)}
k='PLA PHL-191 Cruise';ok(models[k]['file']=='m_phl191cf_static.fam',k);before=dict(models[k]);models[k]={'file':'m_phl191cg_static.fam','battle':'m_phl191cg_lo_static.fam','align':False}
rec['models_json']={k:{'before':before,'after':models[k]}}
for f in sorted(a.stage.iterdir()):
    if f.suffix in ('.fam','.json','.png') and f.name.split('_static')[0].replace('_lo','')=='m_phl191cg':files['UserData/FAModels/'+f.name]=str(f)
ok(len([k for k in files if k.endswith('.fam')])==2,'phl191cg fams');ok(not any(k in z.namelist() for k in files if 'phl191cg' in k),'no overwrite')
for k in [k for k in files if 'phl191cg' in k and k.endswith('.mat.json')]:
    for key in json.loads(Path(files[k]).read_text()):
        tex=key.split('|')[0]
        if tex:ok('UserData/FAModels/'+tex in files,('texture',tex))
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=raw.isascii())+'\n').encode())
(ROOT/f'tools/pla-specs/{V}-assets.txt').write_text(''.join(f'{k}={v}\n' for k,v in sorted(files.items())))
rec.update(version=V,base=PREV,base_sha256=BASE,request='Osama 13 Nov 22:59-23:13 PST',checks=checks,verified='data and file checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,rec['helo_ground_clear_glass'])

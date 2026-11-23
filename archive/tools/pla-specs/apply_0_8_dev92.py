"""Freedom Arrow 0.8.0-dev.92 over exact 0.8.0-dev.91 (Osama 13 Nov 22:30-22:40 PST, thread 1571014792016171120).
- Clear glass was "very frosted white": FAModels draws it white at the mat.json opacity, which was 0.3; every clearGlass
  material now uses 0.1.
- HQ-6A model 75%. VT-5 Recon in the seller desert digital (Dust_Camo, m_vt5d, MG position fixed). VT-5 stays green.
- HQ-16 (PLAGF Armored, had no model): Osama's seller HQ-16 (woodland digital, static, 10.7 m, clear glass).
- CSK-131: the 4x4 seller model is the CSK-131 ("the current wrong CSK-181 model is supposed to be the CSK-131"). The dev.90
  card is renamed CSK-131 (same four forces and squad transport slots as the CSK-181 6x6); CSK-131 Mengshi and the hidden
  CSK-131 Transport use the 4x4 model too. CSK-181 stays the 6x6.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.92';PREV='0.8.0-dev.91'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--stage',type=Path,required=True);a=p.parse_args()
base=REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(U[1266]['Name']=='PLA CSK-181 4x4' and U[1266]['HUDName']=='CSK-181 4x4','1266');g.put('Units',1266,{'HUDName':'CSK-131'});rec['card_1266_hud']=['CSK-181 4x4','CSK-131']
MJ='UserData/FAModels/models.json';raw=z.read(MJ);models=json.loads(raw);before={}
def setm(k,f,keep=('hide',)):
    ok(k in {u.get('Name') for u in U.values()},k);before[k]=models.get(k);e={kk:vv for kk,vv in (models.get(k) or {}).items() if kk in keep}
    models[k]={'file':f+'_static.fam','battle':f+'_lo_static.fam','align':False,**e}
setm('PLA VT-5 Recon','m_vt5d');setm('PLA Catalogue HQ-16','m_hq16')
for k in ('PLA CSK-131 Mengshi','PLA CSK-131 Transport'):setm(k,'m_csk4b')
ok(models['PLA CSK-181 4x4']['file']=='m_csk4b_static.fam' and models['PLA CSK-181 Transport']['file']=='m_csk181_static.fam','csk models')
k='PLA Catalogue HQ-6A';ok('scale' not in models[k],k);before[k]=dict(models[k]);models[k]['scale']=0.75
rec['models_json']={k:{'before':before[k],'after':models[k]} for k in before}
files={'UserData/FAModels/'+f.name:str(f) for f in sorted(a.stage.iterdir()) if f.suffix in ('.fam','.json','.png') and f.name.split('_static')[0].replace('_lo','') in ('m_vt5d','m_hq16')}
ok(len([k for k in files if k.endswith('.fam')])==4,sorted(files));ok(not any(k in z.namelist() for k in files),'no overwrite')
over={}
for k in [k for k in files if k.endswith('.mat.json')]:
    mj=json.loads(Path(files[k]).read_text())
    for v in mj.values():
        if v.get('cockpitDonor'):v.pop('cockpitDonor');v.update(clearGlass=True,alpha='BLEND',metallic=0.0,smoothness=0.95)
    over[k]=mj
    for key in mj:
        tex=key.split('|')[0]
        if tex:ok('UserData/FAModels/'+tex in files,('texture',tex))
for n in z.namelist():
    if n.startswith('UserData/FAModels/') and n.endswith('.mat.json') and n not in over:
        mj=json.loads(z.read(n))
        if any(v.get('clearGlass') for v in mj.values()):over[n]=mj
cg=0
for n,mj in over.items():
    for v in mj.values():
        if v.get('clearGlass'):v['opacity']=0.1;cg+=1
ok(cg>=40,('clear glass materials',cg));rec['clear_glass_opacity']={'from':0.3,'to':0.1,'materials':cg,'files':len([1 for mj in over.values() if any(v.get('clearGlass') for v in mj.values())])}
gdir=ROOT/f'tools/pla-specs/{V}-mats';gdir.mkdir(exist_ok=True)
for n,mj in over.items():
    f=gdir/n.split('/')[-1];f.write_text(json.dumps(mj,indent=1)+'\n');files[n]=str(f)
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=raw.isascii())+'\n').encode())
(ROOT/f'tools/pla-specs/{V}-assets.txt').write_text(''.join(f'{k}={v}\n' for k,v in sorted(files.items())))
rec.update(version=V,base=PREV,base_sha256=BASE,request='Osama 13 Nov 22:30-22:40 PST',checks=checks,verified='data and file checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,rec['clear_glass_opacity'])

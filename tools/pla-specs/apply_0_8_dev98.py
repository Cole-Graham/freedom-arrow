"""Freedom Arrow 0.8.0-dev.98 over exact 0.8.0-dev.97 (Osama 13 Nov 23:30-23:55 PST, thread 1571014792016171120).
- Type 59D and ZTZ-59D1: the re-downloaded seller 59D (byte-identical inside to the first copy) rebuilt as m_ztz59d2. It is a
  SketchUp model whose flat colours were read as linear (pale); now converted to linear (dark olive). Base ZTZ-59 stays m_ztz59a.
- HQ-9 / HQ-9A / HQ-9B (HQ-22 model): paint 2x lighter than the HQ-16 (mean 106 vs 55) -> textures x0.58; the 1005 tile had no
  mask map so it was fully metallic -> mask map from the seller metal/roughness tile; the windows were only painted dark into
  the camo atlas -> 269 window faces (windscreen, cab doors, crew cab) cut out as clear glass (m_hq22g).
- HQ-7B / HQ-7: window alpha was cut out by the MASK material (no glass) -> 358 see-through faces as clear glass (m_hq7g).
- ZTL-191 Recon: seller DustCamo coat (m_ztl191d). The ZTL-191 card keeps the woodland model.
- PHL-03: darker (camo textures colorScale 0.6, tyres 0.3-0.35, light greys 0.4, other flat colours 0.7).
- Mengshi Recon: darker and more metallic (colorScale 0.75, metallic 0.55, smoothness 0.5). The seller model has no glass parts
  (the window openings are empty and the mesh is unwelded triangles), so no glass yet.
- Ambush Team (1173) 60 -> 40 pts. YJ-18 (1129) PLARF -> PLAN SOF. PHL-191 Cruise (1267) PLAGF Motorized -> PLARF.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.98';PREV='0.8.0-dev.97'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--stage',type=Path,action='append',required=True);a=p.parse_args()
base=REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];rows=g.rows
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
# Stats
ok(U[1173]['HUDName'].startswith('Ambush Team') and U[1173]['Cost']==60 and U[1173].get('DisplayInArmory') is not False,'ambush 60');g.put('Units',1173,{'Cost':40})
def move(uid,hud,frm,to):
    ok(U[uid]['HUDName']==hud,hud);r=rows('SpecializationAvailabilitiesJson',uid);ok([x['SpecializationId'] for x in r]==[frm],(hud,frm))
    g.put('SpecializationAvailabilitiesJson',r[0]['Id'],{'SpecializationId':to});ok(assign['assignments'].get(str(uid))==[frm],(hud,'assign'));assign['assignments'][str(uid)]=[to]
    rec.setdefault('spec_moves',[]).append({'unit':uid,'name':hud,'from':frm,'to':to,'row':r[0]['Id']})
move(1129,'YJ-18',19,20);move(1267,'PHL-191 Cruise',21,19)
rec['ambush_team']={'unit':1173,'cost':[60,40]}
# Models
MJ='UserData/FAModels/models.json';raw=z.read(MJ);models=json.loads(raw);before={}
def setm(k,f,was):
    ok(models[k]['file']==was+'_static.fam',(k,was));before[k]=dict(models[k]);e={kk:vv for kk,vv in models[k].items() if kk in ('hide','scale')}
    models[k]={'file':f+'_static.fam','battle':f+'_lo_static.fam','align':False,**e}
for k in ('PLA Catalogue Type 59D','PLA ZTZ-59D1'):setm(k,'m_ztz59d2','m_ztz59a')
ok(models['PLA Catalogue Type 59 — FlashPoint']['file']=='m_ztz59a_static.fam','base ZTZ-59 unchanged')
for k in ('PLA HQ-9','PLA HQ-9B','PLA HQ-9A'):setm(k,'m_hq22g','m_hq22')
for k in ('PLA HQ-7B','PLA HQ-7'):setm(k,'m_hq7g','m_hq7s')
setm('PLA ZTL-191 Recon','m_ztl191d','m_ztl191');ok(models['PLA Catalogue ZTL-191']['file']=='m_ztl191_static.fam','ZTL-191 woodland')
rec['models_json']={k:{'before':before[k],'after':models[k]} for k in before}
gdir=ROOT/f'tools/pla-specs/{V}-mats';gdir.mkdir(exist_ok=True);files={}
NEW=('m_ztz59d2','m_hq22g','m_hq7g','m_ztl191d')
for d in a.stage:
    for f in sorted(d.iterdir()):
        if f.suffix in ('.fam','.json','.png') and f.name.split('_static')[0].replace('_lo','') in NEW:
            k='UserData/FAModels/'+f.name;ok(k not in files,('one source',k));files[k]=str(f)
ok(len([k for k in files if k.endswith('.fam')])==8,sorted(files));ok(not any(k in z.namelist() for k in files),'no overwrite')
for k in [k for k in files if k.endswith('.mat.json')]:
    mj=json.loads(Path(files[k]).read_text());ok(not any(v.get('cockpitDonor') for v in mj.values()),('no donor',k))
    gl=[v for v in mj.values() if v.get('clearGlass')];ok(all(v['opacity']==0.025 for v in gl),('opacity',k))
    if 'hq22g' in k or 'hq7g' in k or 'ztz59d2' in k:ok(len(gl)==1,('one glass material',k))
    for key in mj:
        tex=key.split('|')[0]
        if tex:ok('UserData/FAModels/'+tex in files,('texture',tex))
rec['glass']={'m_hq22g':'269 window faces','m_hq7g':'358 see-through faces'}
# PHL-03 darker: material-only colour scale (FAModels colorScale), on the dev.96 materials
def scale(key):
    if not key.startswith('|'):return 0.6
    r,gg,b,_=(float(x) for x in key[1:].split(','))
    if key in ('|0.0500,0.0500,0.0500,1.0000',):return 0.35
    if key=='|0.1333,0.1216,0.1176,1.0000':return 0.3
    if min(r,gg,b)>=0.4:return 0.4
    return 0.7
for n in ('m_phl03_static','m_phl03_lo_static'):
    k=f'UserData/FAModels/{n}.mat.json';mj=json.loads(z.read(k));ok(mj==json.loads((ROOT/f'tools/pla-specs/0.8.0-dev.96-mats/{n}.mat.json').read_text()),('dev.96 mat',n));c={}
    for key,v in mj.items():
        if v.get('clearGlass'):continue
        s=scale(key);v['colorScale']=[s,s,s];c[s]=c.get(s,0)+1
    ok(sum(c.values())==39,(n,c));f=gdir/(n+'.mat.json');f.write_text(json.dumps(mj,indent=1)+'\n');files[k]=str(f);rec.setdefault('phl03_colorScale',{})[n]=c
for n in ('m_mengshird_static','m_mengshird_lo_static'):
    k=f'UserData/FAModels/{n}.mat.json';mj=json.loads(z.read(k));ok(len(mj)==1,n)
    for v in mj.values():ok(v['metallic']==0.0,n);v.update(metallic=0.55,smoothness=0.5,colorScale=[0.75,0.75,0.75])
    f=gdir/(n+'.mat.json');f.write_text(json.dumps(mj,indent=1)+'\n');files[k]=str(f)
rec['mengshi_recon']={'metallic':0.55,'smoothness':0.5,'colorScale':0.75,'glass':'none in the seller model'}
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=raw.isascii())+'\n').encode())
(ROOT/f'tools/pla-specs/{V}-assets.txt').write_text(''.join(f'{k}={v}\n' for k,v in sorted(files.items())))
rec.update(version=V,base=PREV,base_sha256=BASE,request='Osama 13 Nov 23:30-23:55 PST',checks=checks,verified='data and file checks only',
  not_done={'HMV3 Cargo 15000':'ResupplyPoints is already 15000 (Build66); truck cargo comes from the US_HEMTT prefab, not the tables',
            'Mengshi Recon windows':'seller model has no glass parts','PHL-191 Cruise loadout':'copy of Ballistic until specified'})
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,'files',len(files))

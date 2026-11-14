"""Freedom Arrow 0.8.0-dev.89 over exact 0.8.0-dev.88 (Osama 13 Nov 21:52-22:12 PST, thread 1571014792016171120).
- HQ-9C, HQ-9B and HQ-9A: Osama's new seller model (CGTrader "HQ-22 air defense missile"; its 9 UDIM tiles packed into one
  5x2 atlas, UVs scaled, ground plane dropped; static, seller scale 10.6 m).
- Mengshi Recon: seller colours darkened to 40% ("a lot darker similar to other color schemes").
- ZTZ-99 back on the dev.83 model m_ztz99: the dev.85 position fix (m_ztz99b) moved both seller objects named 'Track_R'
  (one is the left track) to the right side, leaving one side without a track. Its roof MG stays 0.35 m off.
- HJ-16 uses the vehicle Spike icon (VEH_SPIKE_LR): the ZBD-251 "HJ-16" launcher (2014655) changes from the HJ-10 icon;
  the ZBD-20/ZBL-191 HJ-16 and HJ-16 IIR already use it.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.89';PREV='0.8.0-dev.88'
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
g=Graph(t,patches,native);W=t['WeaponsJson'];checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(W[2014655]['HUDName']=='HJ-16' and W[2014655]['HUDIcon']=='FA_PLA_HJ10','zbd-251 hj-16');g.put('WeaponsJson',2014655,{'HUDIcon':'VEH_SPIKE_LR'})
ok(all(W[w]['HUDIcon']=='VEH_SPIKE_LR' for w in W if str(W[w].get('HUDName')).startswith('HJ-16') and w!=2010337),'all live HJ-16 icons')
rec['hj16_icon']={'2014655':['FA_PLA_HJ10','VEH_SPIKE_LR']}
MJ='UserData/FAModels/models.json';raw=z.read(MJ);models=json.loads(raw);before={}
for k in ('PLA HQ-9','PLA HQ-9B','PLA HQ-9A'):
    ok(models[k]['file']=='hq9.fam',k);before[k]=dict(models[k]);models[k]={'file':'m_hq22_static.fam','battle':'m_hq22_lo_static.fam','align':False}
k='PLA Catalogue ZTZ-99';ok(models[k]['file']=='m_ztz99b_static.fam' and 'UserData/FAModels/m_ztz99_static.fam' in z.namelist(),k);before[k]=dict(models[k]);models[k]={**models[k],'file':'m_ztz99_static.fam','battle':'m_ztz99_lo_static.fam'}
k='PLA Mengshi Recon';ok(models[k]['file']=='m_mengshir_static.fam',k);before[k]=dict(models[k]);models[k]={**models[k],'file':'m_mengshird_static.fam','battle':'m_mengshird_lo_static.fam'}
rec['models_json']={k:{'before':before[k],'after':models[k]} for k in before}
files={'UserData/FAModels/'+f.name:str(f) for f in sorted(a.stage.iterdir()) if f.suffix in ('.fam','.json','.png') and f.name.split('_static')[0].replace('_lo','') in ('m_hq22','m_mengshird')}
ok(len([k for k in files if k.endswith('.fam')])==4,sorted(files));ok(not any(k in z.namelist() for k in files),'no overwrite')
for k in [k for k in files if k.endswith('.mat.json')]:
    for key in json.loads(Path(files[k]).read_text()):
        tex=key.split('|')[0]
        if tex:ok('UserData/FAModels/'+tex in files,('texture',tex))
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=raw.isascii())+'\n').encode())
(ROOT/f'tools/pla-specs/{V}-assets.txt').write_text(''.join(f'{k}={v}\n' for k,v in sorted(files.items())))
rec.update(version=V,base=PREV,base_sha256=BASE,request='Osama 13 Nov 21:52-22:12 PST',checks=checks,verified='data and file checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,'files',len(files))

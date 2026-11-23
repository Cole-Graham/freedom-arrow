"""Freedom Arrow 0.8.0-dev.38 over exact 0.8.0-dev.37 (Osama 13 Nov 12:26-12:31 PST, thread 1567745029781454889):
- HQ-17 (910) and HQ-17A (1049) move at wheeled speed: the vanilla Tor-M2KM (wheeled Tor) values, road 90, cross-country 45,
  reverse 20, turn rate 80 (were the tracked Tor's 65 / 50 / 20 / 60).
- Model fixes (Shawn's set, rebuilt with tools in work/pla-0.8/shawn-20261113): PLZ-05 gun moved back 1.66 m into the
  turret and the roof MG 1.52 m (positions from Shawn's PLZ-05.blend); HQ-17/HQ-17A search radar raised 2.56 m onto the
  turret roof (top at 5.1 m, the Tor's deployed height) and tracking radar 1.34 m onto the turret front.
- ZBD-04, ZBD-04A and ZBD-04A Recon (all PLAGF Armored): woodland digital m_zbd04_wdigi (were plain green).
- ZTZ-100 (PLAGF): woodland digital m_ztz100_wd / m_ztz100_lw (Osama 12:33).
- ZTZ-96A and ZTZ-96B swap models (Osama 12:34): ZTZ-96B takes Shawn's woodland-digital ZTZ-96A model; ZTZ-96A takes the
  old plain-green ZTZ-96B model ("96A can be the non-digital camo").
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.38'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.37.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U,UP,M=t['Units'],t['UnitPropulsionsJson'],t['MobilityJson']
TOR_M2KM=634;ref=[M[r['MobilityId']] for r in UP.values() if r['UnitId']==TOR_M2KM];assert len(ref)==1 and U[TOR_M2KM]['HUDName']=='Tor-M2KM';ref=ref[0]
FIELDS=('MaxSpeedRoad','MaxCrossCountrySpeed','MaxSpeedReverse','TurnRate','Acceleration')
assert [ref[k] for k in FIELDS]==[90.0,45.0,20.0,80.0,10.0]
mob={}
for uid,name in ((910,'HQ-17'),(1049,'HQ-17A')):
    assert U[uid]['HUDName']==name;rows=[r for r in UP.values() if r['UnitId']==uid];assert len(rows)==1;mid=rows[0]['MobilityId']
    assert [r['UnitId'] for r in UP.values() if r['MobilityId']==mid]==[uid],('shared mobility row',mid)
    mob[name]={'before':{k:M[mid][k] for k in FIELDS}};g.put('MobilityJson',mid,{k:ref[k] for k in FIELDS});mob[name]['after']={k:M[mid][k] for k in FIELDS}
MJ='UserData/FAModels/models.json';models=json.loads(z.read(MJ))
zbd=[k for k,v in models.items() if v['file']=='m_zbd04_green_static.fam'];assert sorted(zbd)==['PLA Catalogue ZBD-04','PLA ZBD-04A'],zbd
for k in zbd:models[k].update(file='m_zbd04_wdigi_static.fam',battle='m_zbd04_wdigi_lo_static.fam')
assert models['PLA ZTZ-100']['file']=='m_ztz100_cg.fam';models['PLA ZTZ-100'].update(file='m_ztz100_wd.fam',battle='m_ztz100_lw.fam')
assert models['PLA Catalogue ZTZ-96A']['file']=='m_ztz96a_static.fam' and models['PLA ZTZ-96B']['file']=='m_ztz96b_wdigi.fam'
models['PLA ZTZ-96B']=dict(models['PLA Catalogue ZTZ-96A'])
models['PLA Catalogue ZTZ-96A'].update(file='m_ztz96b_green.fam',battle='m_ztz96b_green_lo.fam');models['PLA Catalogue ZTZ-96A'].pop('align',None)
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
for uid in (910,1049):
    m=M[[r for r in UP.values() if r['UnitId']==uid][0]['MobilityId']];ok([m[k] for k in FIELDS]==[ref[k] for k in FIELDS],('wheeled speed',uid))
ok(all(models[k]['file']=='m_zbd04_wdigi_static.fam' for k in zbd),'ZBD-04 woodland')
ok(models['PLA ZTZ-100']['file']=='m_ztz100_wd.fam' and models['PLA ZTZ-96B']['file']=='m_ztz96a_static.fam' and models['PLA Catalogue ZTZ-96A']['file']=='m_ztz96b_green.fam','ZTZ-100 woodland; 96A/96B swap')
ok(models['PLA PLZ-05']['file']=='m_plz05_static.fam' and models['PLA HQ-17']['file']==models['PLA Catalogue HQ-17A']['file']=='m_hq17a_static.fam','fixed model files keep their names')
receipt={'version':V,'base':'0.8.0-dev.37','base_sha256':BASE,'request':'Osama 13 Nov 12:26-12:34 PST: ZTZ-100 needs its woodland digital camo; ZTZ-96A and B can swap models, 96A can be the non-digital camo; PLZ-05 gun sticking out in front; HQ-17 speed of a wheeled vehicle, HQ-17 model looks off, radar dish sunk into the model; ZBD-04 in PLAGF does not use their digital camo',
 'mobility':mob,'mobility_source':'vanilla Tor-M2KM (634)','models':{'PLZ-05':'PLZ05Gun +1.66 m back, CN_MG +1.52 m back +0.10 m up (Shawn PLZ-05.blend positions)','HQ-17/HQ-17A':'HQ17_Rada_01 +2.56 m up (top 5.1 m), HQ17_Rada_02 +1.34 m up','ZBD-04':'woodland digital m_zbd04_wdigi','ZTZ-100':'woodland digital m_ztz100_wd','ZTZ-96B':'Shawn woodland-digital ZTZ-96A model','ZTZ-96A':'old plain-green ZTZ-96B model'},'checks':checks}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=z.read(MJ).isascii())+'\n').encode())
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,json.dumps(mob))

"""Freedom Arrow 0.8.0-dev.52 over exact 0.8.0-dev.51 (Osama 13 Nov 15:0x PST, thread 1567745029781454889):
DF-17/ZF flew flat (the Kinzhal climb-then-dive profile from Build67 had no climb height on a ground launcher).
Osama: "just make it a ballistic missile that accelerates twice as fast".
- Ammo 2010351 takes the ballistic flight fields of the DF-21 missile (2010375; same as vanilla Iskander-M 218):
  trajectory 300, no loft, launch margin 180, rotation 10, 8 s motor, motor at launch.
- Acceleration 100 -> 200 and top speed 1500 -> 1600: twice the DF-21 / ATACMS / Iskander-M (100 and 800) (Osama: double the top speed too).
Damage, blast, range, targetability (air defence can engage it) unchanged.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.52'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.51.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);A=t['AmmunitionsJson']
ZF,DF21=2010351,2010375
FLIGHT=['TrajectoryType','LoftAngle','LoftHeight','LaunchMarginAngle','RotationSpeed','BurnTime','MainEngineIgnitionDelay','PreEgnitionRotationSpeed','OverflyHeight','MinimalRange']
assert A[ZF]['TrajectoryType']==200 and A[DF21]['TrajectoryType']==300 and A[DF21]['Acceleration']==100.0 and A[ZF]['MaxSpeed']==1500.0
before={k:A[ZF].get(k) for k in FLIGHT+['Acceleration','MaxSpeed']}
g.put('AmmunitionsJson',ZF,{**{k:A[DF21][k] for k in FLIGHT if k in A[DF21]},'Acceleration':200.0,'MaxSpeed':1600.0})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
for k in FLIGHT:
    if k in A[DF21]:ok(A[ZF][k]==A[DF21][k],('ballistic flight',k))
ok(A[ZF]['Acceleration']==200.0 and A[ZF]['MaxSpeed']==1600.0==2*A[DF21]['MaxSpeed'] and A[ZF]['MainEngineIgnitionDelay']==0.0,'double acceleration and top speed')
ok(A[ZF]['CanBeTargeted'] is True,'air defence can engage')
receipt={'version':V,'base':'0.8.0-dev.51','base_sha256':BASE,'request':'Osama 13 Nov PST: DF-ZF has a really flat trajectory, no climb; make it a ballistic missile that accelerates twice as fast; double the top speed too',
 'ammo':ZF,'before':before,'after':{k:A[ZF].get(k) for k in FLIGHT+['Acceleration','MaxSpeed']},'source_of_flight':'DF-21 missile 2010375 (= vanilla Iskander-M 218)','checks':checks,'verified':'data only; not yet observed in a game'}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,receipt['before'],receipt['after'])

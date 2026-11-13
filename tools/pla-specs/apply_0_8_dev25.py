"""Freedom Arrow 0.8.0-dev.25 over exact 0.8.0-dev.24 (Osama 13 Nov 01:52 PST, thread 1567745029781454889):
- CTL-181 NLOS missile (ammunition 2018321): laser guidance off. Lasering targets for it made the missile go haywire; it
  flies its precision (cruise) path to the aimed point, like a cruise missile. No NLOS hook involved (it was never in nlos.json).
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.25'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.24.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
before=copy.deepcopy(t);g=Graph(t,patches,native);U,W,WA,TU,T=t['Units'],t['WeaponsJson'],t['WeaponAmmunitionsJson'],t['TurretUnitsJson'],t['TurretsJson']
CTL=2018321;A=t['AmmunitionsJson'];assert A[CTL]['Name']=='PLA CTL-181 NLOS missile' and A[CTL]['LaserGuided']
g.put('AmmunitionsJson',CTL,{'LaserGuided':False})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(not A[CTL]['LaserGuided'] and A[CTL]['TrajectoryType']==200,'CTL-181 no laser')
for tab in t:
    for key,row in before[tab].items():
        if (tab,key)!=('AmmunitionsJson',CTL):ok(t[tab].get(key)==row,('row changed',tab,key))
receipt={'version':V,'base':'0.8.0-dev.24','base_sha256':BASE,'request':'Osama 13 Nov 01:52 PST: lasering for the CTL-181 NLOS made the missile go haywire; it is already a cruise missile','ctl181_ammo':{'id':CTL,'LaserGuided':[True,False]},'checks':checks}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)

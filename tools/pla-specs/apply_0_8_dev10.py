"""Freedom Arrow 0.8.0-dev.10 over exact 0.8.0-dev.9 (Osama 12 Nov PST): "CTL-181 needs to be called CTL-181 NLOS and only
do 10 damage" / "and its range should only be 1800".
- Unit 1054 name: CTL-181 NLOS (was "CTL-181 loitering munition launcher").
- NLOS missile (ammo 2018321, CTL-181 only): damage 15 -> 10; range 1000 -> 900 in data = 2000 -> 1800 m displayed
  (JSON ranges are half the displayed metres).
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.10'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.9.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
before=copy.deepcopy(t);g=Graph(t,patches,native);U=t['Units'];A=t['AmmunitionsJson'];WA=t['WeaponAmmunitionsJson']
CTL,AMMO=1054,2018321
assert U[CTL]['HUDName']=='CTL-181 loitering munition launcher' and A[AMMO]['HUDName']=='NLOS missile' and {x['UnitId'] for x in WA.values() if x['AmmunitionId']==AMMO}=={CTL}
g.put('Units',CTL,{'HUDName':'CTL-181 NLOS'})
g.put('AmmunitionsJson',AMMO,{'Damage':10.0,'GroundRange':900.0})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(A[AMMO]['GroundRange']>=A[AMMO]['MinimalRange'],'range above minimum')
for tab in t:
    for key,r in before[tab].items():
        if (tab,key) not in(('Units',CTL),('AmmunitionsJson',AMMO)):ok(t[tab].get(key)==r,('row changed',tab,key))
receipt={'version':V,'base':'0.8.0-dev.9','base_sha256':BASE,'request':'Osama 12 Nov PST: CTL-181 NLOS name, 10 damage, 1800 m',
 'unit':U[CTL]['HUDName'],'missile':{k:A[AMMO][k] for k in('HUDName','Damage','GroundRange','PenetrationAtGroundRange','IgnoreCover')},'displayed_range_m':int(A[AMMO]['GroundRange']*2),'checks':checks}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(receipt,indent=1))

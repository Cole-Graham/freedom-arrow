"""Freedom Arrow 0.8.0-dev.13 over exact 0.8.0-dev.12 (Osama 12 Nov PST): "CH-901 is ok to not be intercepted".
- CH-901 (ammo 2018448): CanBeIntercepted False again. The ground HJ-10 (2009623) stays interceptable (dev.12).
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.13'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.12.json').read_text())['complete']['sha256']
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
NL=(2018448,)
assert A[2018448]['HUDName']=='CH-901' and A[2018448]['CanBeIntercepted'] is True and A[2009623]['CanBeIntercepted'] is True
g.put('AmmunitionsJson',2018448,{'CanBeIntercepted':False})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
for tab in t:
    for key,r in before[tab].items():
        if not(tab=='AmmunitionsJson' and key in NL):ok(t[tab].get(key)==r,('row changed',tab,key))
receipt={'version':V,'base':'0.8.0-dev.12','base_sha256':BASE,'request':'Osama 12 Nov PST: CH-901 not interceptable','ammo':{i:{k:A[i][k] for k in ('HUDName','CanBeIntercepted','CanBeTargeted','TrajectoryType')} for i in (2009623,2018448)},'checks':checks}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(receipt,indent=1))

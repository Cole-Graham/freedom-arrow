"""Freedom Arrow 0.8.0-dev.26 over exact 0.8.0-dev.25 (Osama 13 Nov PST, thread 1567745029781454889):
- QN-202 anti-personnel missile (ammunition 2014237): damage 4 -> 9. Build 39 had copied the RPG-7 OG-7V HE warhead (damage 4).
  Used by Whistling Arrows and the test QN-202 card; the CTL-181 has had its own missile since dev.7.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.26'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.25.json').read_text())['complete']['sha256']
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
QN=2014237;A=t['AmmunitionsJson'];assert A[QN]['HUDName']=='QN-202 anti-personnel missile' and A[QN]['Damage']==4.0
g.put('AmmunitionsJson',QN,{'Damage':9.0})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(A[QN]['Damage']==9.0,'QN-202 9')
for tab in t:
    for key,row in before[tab].items():
        if (tab,key)!=('AmmunitionsJson',QN):ok(t[tab].get(key)==row,('row changed',tab,key))
receipt={'version':V,'base':'0.8.0-dev.25','base_sha256':BASE,'request':'Osama 13 Nov: QN-202 should be 9 damage','qn202':{'id':QN,'Damage':[4.0,9.0]},'checks':checks}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)

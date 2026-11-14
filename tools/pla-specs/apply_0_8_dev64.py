"""Freedom Arrow 0.8.0-dev.64 over exact 0.8.0-dev.63 (Osama 13 Nov 17:57 PST, thread 1569806740139282476):
"CH-901 to 15 damage" (corrected from 165). CH-901 is the Blood Wolves NLOS missile (ammo 2018448, only on unit 1183): Damage 8 -> 15.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.64';PREV='0.8.0-dev.63'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser();p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
base=REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);A=t['AmmunitionsJson'];checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
CH=2018448
ok(A[CH]['HUDName']=='CH-901' and A[CH]['Damage']==8.0,'CH-901 before')
users=sorted({r['UnitId'] for r in t['WeaponAmmunitionsJson'].values() if r.get('AmmunitionId')==CH});ok(users==[1183],('CH-901 users',users))
g.put('AmmunitionsJson',CH,{'Damage':15.0});ok(A[CH]['Damage']==15.0,'CH-901 after')
rec={'version':V,'base':PREV,'base_sha256':BASE,'request':'Osama 13 Nov 17:57 PST: CH-901 to 15 damage (corrected from 165)',
 'ammo':CH,'users':users,'before':{'Damage':8.0},'after':{'Damage':A[CH]['Damage']},'checks':checks,'verified':'data only; not yet observed in a game'}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,json.dumps(rec['after']))

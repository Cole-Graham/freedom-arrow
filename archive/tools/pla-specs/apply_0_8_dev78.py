"""Freedom Arrow 0.8.0-dev.78 over exact 0.8.0-dev.77 (Osama 13 Nov 20:1x PST, thread 1567745029781454889):
- ZTL-191, VT-5, ZTQ-15 (and their Recon cards): 105 mm DU APFSDS penetration 525 close, 475 at full range (was 550/500).
  Ammo 2009131 (ZTQ-15/VT-5) and 2011301 (ZTL-191).
- ZTZ-100 (968): 125 mm APFSDS 2010195 penetration 550 close, 525 at full range (was 525/500).
- ZTZ-100 gun range 2000 m as shown in game (data 1000; the game shows ranges at 2x): APFSDS, HE and HEAT 700 -> 1000.
  The GP125 gun-launched missile keeps 900 (1800 m).
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.78'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.77.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U,A,WA=(t[k] for k in ('Units','AmmunitionsJson','WeaponAmmunitionsJson'))
def users(aid):return sorted({r['UnitId'] for r in WA.values() if r['AmmunitionId']==aid})
rec={}
PEN={2009131:((906,1240,1261,1262),'105 mm DU APFSDS',(525.0,475.0)),2011301:((1080,1263),'105 mm DU APFSDS',(525.0,475.0)),2010195:((968,),'Prototype 125 mm gun APFSDS',(550.0,525.0))}
for aid,(us,name,(lo,hi)) in PEN.items():
    assert A[aid]['HUDName']==name and users(aid)==sorted(us),(aid,users(aid))
    rec[str(aid)]={'pen':[[A[aid]['PenetrationAtMinRange'],A[aid]['PenetrationAtGroundRange']],[lo,hi]]}
    g.put('AmmunitionsJson',aid,{'PenetrationAtMinRange':lo,'PenetrationAtGroundRange':hi})
assert U[968]['HUDName']=='ZTZ-100'
for aid in (2010195,2010197,2010199):
    assert users(aid)==[968] and A[aid]['GroundRange']==700.0
    rec.setdefault(str(aid),{})['range']=[700.0,1000.0];g.put('AmmunitionsJson',aid,{'GroundRange':1000.0})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
for aid,(us,name,pen) in PEN.items():ok((A[aid]['PenetrationAtMinRange'],A[aid]['PenetrationAtGroundRange'])==pen,('pen',aid))
ok(all(A[aid]['GroundRange']==1000.0 for aid in (2010195,2010197,2010199)) and A[2017420]['GroundRange']==900.0,'ZTZ-100 gun 2000 m, missile unchanged')
receipt={'version':V,'base':'0.8.0-dev.77','base_sha256':BASE,'request':'Osama 13 Nov 20:1x PST: ZTL-191 and VT-5 and ZTQ-15 should have 475-525 pen. ZTZ-100 525-550. ZTZ-100 2000m range.','ammo':rec,'checks':checks,'verified':'data only'}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,json.dumps(rec))

"""Freedom Arrow 0.8.0-dev.81 over exact 0.8.0-dev.80 (Osama 13 Nov 20:2x PST, thread 1567745029781454889):
- ZTZ-100 (968): gun range back to 1400 m (data 700) for APFSDS, HE and HEAT. Osama: dev.78's 2000 m was "not what I meant".
  The dev.78 penetration (APFSDS 550/525) stays.
- CSK-181 (1058/1230): model files rebuilt (complete package and assets only, see the receipt). The seller FBX groups each
  tyre's tread lugs under a 3ds Max helper whose pivot imports wrongly, so all six lug rings and the spare-tyre ring sat about
  one wheel radius too high (floating on the fenders; smooth tyres; spare over the roof). The converter now moves each lug
  group onto its tyre carcass (work/pla-0.8/cart-20261113 anyconv.py RECENTER_LUGS). Its plain grey side/rear window
  material (Material #503385/#503485) is now clear glass.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.81'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.80.json').read_text())['complete']['sha256']
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
assert U[968]['HUDName']=='ZTZ-100'
for aid in (2010195,2010197,2010199):
    assert sorted({r['UnitId'] for r in WA.values() if r['AmmunitionId']==aid})==[968] and A[aid]['GroundRange']==1000.0
    g.put('AmmunitionsJson',aid,{'GroundRange':700.0})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(all(A[aid]['GroundRange']==700.0 for aid in (2010195,2010197,2010199)),'ZTZ-100 gun 1400 m again')
ok((A[2010195]['PenetrationAtMinRange'],A[2010195]['PenetrationAtGroundRange'])==(550.0,525.0),'ZTZ-100 APFSDS 550/525 kept')
receipt={'version':V,'base':'0.8.0-dev.80','base_sha256':BASE,'request':'Osama 13 Nov 20:2x PST: dig in on the CSK-181 model; ZTZ-100 range change was not what he meant',
 'ztz100_range':[1000.0,700.0],'csk181_model':'tread lug groups recentred on tyres; windows clear glass (complete/assets files)','checks':checks,'verified':'data only'}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)

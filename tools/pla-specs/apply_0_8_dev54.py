"""Freedom Arrow 0.8.0-dev.54 over exact 0.8.0-dev.53 (Osama 13 Nov 15:08 PST, thread 1567745029781454889):
DF-31A needs a 10 minute cooldown and 30000 kg resupply.
- DF-31A warhead (ammo 2010399): ResupplyTime 1300 -> 600 s (10 minutes to rearm the single round; the vanilla nuclear
  missiles use 1300, the B61-12 bomb 700). SupplyCost 27500 -> 30000.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.54'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.53.json').read_text())['complete']['sha256']
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
DF31=2010399
assert (A[DF31]['ResupplyTime'],A[DF31]['SupplyCost'])==(1300.0,27500.0),(A[DF31]['ResupplyTime'],A[DF31]['SupplyCost'])
g.put('AmmunitionsJson',DF31,{'ResupplyTime':600.0,'SupplyCost':30000.0})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok((A[DF31]['ResupplyTime'],A[DF31]['SupplyCost'])==(600.0,30000.0),'DF-31A 10 min / 30000')
ok(A[DF31]['HealthAOERadius']==250.0,'dev.50 blast kept')
receipt={'version':V,'base':'0.8.0-dev.53','base_sha256':BASE,'request':'Osama 13 Nov 15:08 PST: DF-31A needs a 10 minutes CD and 30000 kg resupply',
 'ammo':DF31,'ResupplyTime':[1300,600],'SupplyCost':[27500,30000],'checks':checks,'verified':'data only'}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)

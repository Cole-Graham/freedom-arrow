"""Freedom Arrow 0.8.0-dev.63 over exact 0.8.0-dev.62 (Osama 13 Nov 17:19 PST, thread 1569806740139282476):
"build it and reduce the price of the DFZF to 250".
- DF-ZF (ammo 2010351) top speed 2400 -> 1200, acceleration kept at 300 (3x DF-21): an interceptability test between the
  800 that vanilla SAMs engage and the 1600 that HQ-9s ignored in Osama's dev.59 match. It reaches 1200 after 4 s of the 8 s burn.
- DF-17/ZF (unit 1028) cost 300 -> 250.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.63';PREV='0.8.0-dev.62'
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
ZF,DF21=2010351,2010375
U=t['Units']
ok(A[ZF]['Acceleration']==300.0 and A[ZF]['MaxSpeed']==2400.0 and A[ZF]['BurnTime']==8.0 and A[ZF]['TrajectoryType']==300,'DF-ZF before')
ok(U[1028]['HUDName']=='DF-17/ZF' and U[1028]['Cost']==300,'DF-17/ZF cost before')
before={k:A[ZF][k] for k in ('Acceleration','MaxSpeed','BurnTime')};before['cost']=U[1028]['Cost']
g.put('AmmunitionsJson',ZF,{'MaxSpeed':1200.0});g.put('Units',1028,{'Cost':250})
ok(A[ZF]['Acceleration']==300.0 and A[ZF]['MaxSpeed']==1200.0 and A[ZF]['CanBeTargeted'] is True and U[1028]['Cost']==250,'DF-ZF after')
rec={'version':V,'base':PREV,'base_sha256':BASE,'request':'Osama 13 Nov 17:19 PST: build the 1200 DF-ZF interceptability test and reduce the DF-ZF price to 250',
 'ammo':ZF,'before':before,'after':{**{k:A[ZF][k] for k in ('Acceleration','MaxSpeed','BurnTime')},'cost':U[1028]['Cost']},'checks':checks,
 'native':{'RocketEngineSystem.IntenalUpdate':'0x80BEB0','TrajectoryShellSystem.InternalUpdate':'0x82C4B0','IsKinematicallyAbleToInterceptTarget':'0x7D9420'},
 'verified':'data and native code read only; not yet observed in a game'}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,json.dumps(rec['after']))

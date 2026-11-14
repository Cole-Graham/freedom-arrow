"""Freedom Arrow 0.8.0-dev.62 over exact 0.8.0-dev.61 (Osama 13 Nov ~16:55 PST, thread 1569806740139282476).
- DF-ZF (DF-17 ammo 2010351): acceleration 3x the DF-21/Iskander-M (100 -> 300; was 200).
  MaxSpeed = Acceleration x BurnTime (300 x 8 = 2400), so the cap never stops the boost ("unlock its top speed").
  Native RocketEngineSystem (RVA 0x80BEB0): a trajectory shell gains Acceleration only while TimeSinceActivation < BurnTime,
  capped at MaxSpeed; TrajectoryShellSystem (RVA 0x82C4B0) then holds that horizontal speed to impact. There is no
  descent speed-up in the data, so a faster dive needs a runtime hook.
- FAModels 0.3.21: the copied F-16 glass survives scene loads (DF-15/17/21/21D/31A were rejected in matches).
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.62';PREV='0.8.0-dev.61'
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
ok(A[ZF]['Acceleration']==200.0 and A[ZF]['MaxSpeed']==1600.0 and A[ZF]['BurnTime']==8.0 and A[ZF]['TrajectoryType']==300,'DF-ZF before')
before={k:A[ZF][k] for k in ('Acceleration','MaxSpeed','BurnTime')}
acc=3*A[DF21]['Acceleration'];g.put('AmmunitionsJson',ZF,{'Acceleration':acc,'MaxSpeed':acc*A[ZF]['BurnTime']})
ok(A[ZF]['Acceleration']==300.0 and A[ZF]['MaxSpeed']==2400.0 and A[ZF]['CanBeTargeted'] is True,'DF-ZF after')
rec={'version':V,'base':PREV,'base_sha256':BASE,'request':'Osama 13 Nov PST: DF-ZF should be 3x acceleration rather than 2x; unlock its top speed so it never hits a cap',
 'ammo':ZF,'before':before,'after':{k:A[ZF][k] for k in ('Acceleration','MaxSpeed','BurnTime')},'checks':checks,
 'native':{'RocketEngineSystem.IntenalUpdate':'0x80BEB0','TrajectoryShellSystem.InternalUpdate':'0x82C4B0','IsKinematicallyAbleToInterceptTarget':'0x7D9420'},
 'verified':'data and native code read only; not yet observed in a game'}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,json.dumps(rec['after']))

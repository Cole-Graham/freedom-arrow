"""Freedom Arrow 0.8.0-dev.50 over exact 0.8.0-dev.49 (Osama 13 Nov 14:47-14:52 PST, thread 1567745029781454889):
- DF-17/ZF kills itself when it fires. Its missile (2010351) uses the air-launched Kh-47M2 Kinzhal profile from Build67:
  MainEngineIgnitionDelay 2.0 s, i.e. the motor lights 2 s after release. From a ground launcher the missile drops onto its
  own truck first, and its 50 m blast hits the launcher. Ignition delay 2.0 -> 0.0, as on every vanilla ground-launched
  ballistic missile (ATACMS, Iskander-M). The steep loft, dive and 1500 top speed stay.
- DF-31A (weapon 2010395, ammo 2010399): aim time 120 s -> the vanilla ballistic 10-12 s (ATACMS, Iskander-M).
  Blast 500 m as shown in game (the game shows 2x the data value; 45 data = 90 m): health radius 350 -> 250 in data,
  stress 400 -> 286 and overpressure 175 -> 125 scaled the same (x 250/350).
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.50'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.49.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);W,A=t['WeaponsJson'],t['AmmunitionsJson']
DFZF,DF31W,DF31A=2010351,2010395,2010399
assert A[DFZF]['MainEngineIgnitionDelay']==2.0 and A[DFZF]['TrajectoryType']==200
assert (W[DF31W]['AimTimeMin'],W[DF31W]['AimTimeMax'])==(120.0,120.0) and (A[DF31A]['HealthAOERadius'],A[DF31A]['StressAOERadius'],A[DF31A]['OverpressureRadius'])==(350.0,400.0,175.0)
assert (W[37]['AimTimeMin'],W[37]['AimTimeMax'])==(10.0,12.0) and A[34]['MainEngineIgnitionDelay']==0.0 and A[218]['MainEngineIgnitionDelay']==0.0
g.put('AmmunitionsJson',DFZF,{'MainEngineIgnitionDelay':0.0})
g.put('WeaponsJson',DF31W,{'AimTimeMin':10.0,'AimTimeMax':12.0})
f=250/350;g.put('AmmunitionsJson',DF31A,{'HealthAOERadius':250.0,'StressAOERadius':round(400*f),'OverpressureRadius':round(175*f)})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(A[DFZF]['MainEngineIgnitionDelay']==0.0 and A[DFZF]['LoftAngle']==85 and A[DFZF]['MaxSpeed']==1500.0,'DF-ZF ignition 0, flight kept')
ok((W[DF31W]['AimTimeMin'],W[DF31W]['AimTimeMax'])==(10.0,12.0),'DF-31A aim 10-12 s')
ok((A[DF31A]['HealthAOERadius'],A[DF31A]['StressAOERadius'],A[DF31A]['OverpressureRadius'])==(250.0,286,125),'DF-31A blast')
receipt={'version':V,'base':'0.8.0-dev.49','base_sha256':BASE,'request':'Osama 13 Nov 14:47-14:52 PST: DF-ZF kills itself when it shoots; DF-31 nuclear missile aim time normal, blast radius down 20%, 500 m blast radius is fine',
 'df_zf':{'ammo':DFZF,'MainEngineIgnitionDelay':[2.0,0.0],'cause':'air-launch ignition delay on a ground launcher; theoretical, not yet proven in a game'},
 'df_31a':{'aim_time':[[120,120],[10,12]],'HealthAOERadius':[350,250],'StressAOERadius':[400,286],'OverpressureRadius':[175,125],'displayed_blast_m':[700,500]},'checks':checks}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)

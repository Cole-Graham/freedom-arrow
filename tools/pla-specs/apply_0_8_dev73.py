"""Freedom Arrow 0.8.0-dev.73 over exact 0.8.0-dev.72 (Osama 13 Nov 19:10 PST, thread 1567745029781454889):
- FK-2000 (935) guns: the PGL-625 gun stats from dev.71. Weapon 2009599 keeps the Pantsir 2A38M cycle (2.561 rounds/s,
  dpm_visualizer rate_of_fire_second), so damage per round 3.0 -> 7.8: 20 damage per second for each of its two gun
  mounts (turret weapons 2009602 and 2018729), 40 for the unit. The FK-2000 SAM is unchanged.
- No speed data change. Osama 13 Nov: keep the road-speed hook in reserve (draft in work/road-speed-hook-20261113).
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(ROOT.parent/'model-pack-v1/dev-tools')]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
from dpm_visualizer import calculations as calc
V='0.8.0-dev.73'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.72.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U,W,A,WA,TW=(t[k] for k in ('Units','WeaponsJson','AmmunitionsJson','WeaponAmmunitionsJson','TurretWeaponsJson'))
FK,GW,GA,PGW,PGA=935,2009599,2009603,2009365,2009369
assert U[FK]['HUDName']=='FK-2000' and sorted({r['UnitId'] for r in WA.values() if r['AmmunitionId']==GA})==[FK]
assert sorted(r['Id'] for r in TW.values() if r['WeaponId']==GW)==[2009602,2018729]
rof=calc.rate_of_fire_second(W[GW]);assert abs(rof-calc.rate_of_fire_second(W[PGW]))<1e-9
before_dmg=A[GA]['Damage'];mob_before=json.dumps(patches['MobilityJson'],sort_keys=True)
g.put('AmmunitionsJson',GA,{'Damage':A[PGA]['Damage']})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(abs(rof*A[GA]['Damage']-20)<0.1,'FK-2000 gun 20 dps per mount')
ok(A[GA]['Damage']==A[PGA]['Damage']==7.8,'same damage as the PGL-625 gun')
ok(json.dumps(patches['MobilityJson'],sort_keys=True)==mob_before,'no unit speed data changed')
receipt={'version':V,'base':'0.8.0-dev.72','base_sha256':BASE,'request':'Osama 13 Nov 19:10 PST: fk-2000 should be updated (road-speed hook: not implemented, kept in reserve)',
 'fk2000':{'rounds_per_s':round(rof,3),'damage':[before_dmg,A[GA]['Damage']],'dps_per_mount':round(rof*A[GA]['Damage'],2),'mounts':2},
 'checks':checks,'verified':'data only'}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,receipt['fk2000'])

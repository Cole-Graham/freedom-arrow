"""Freedom Arrow 0.8.0-dev.4 over exact 0.8.0-dev.3 (Osama 12 Nov 13:53 PST).

- CTL-181 NLOS: "the animation shows a mortar shooting several times ... maybe we give it cruise missile animation ...
  should be small ... attacking with precision strike". The launcher and missile now copy the vanilla Iskander-K
  cruise missile (cruise launcher type, vertical launch, cruise trajectory, precision strike on spotted targets),
  scaled down: Hellfire-size missile model and AT-missile impact effect, 48 missiles in launchers of 4, 15 damage,
  20 penetration, 50% ignore cover, 12.5 m blast, 2000 m (1000 data), quick aim (3-4 s).
- ZBD-20 and ZBD-20 Recon: "doesn't have missiles". The 100 mm gun / HJ-9 launcher is removed; the 30 mm is the main gun.
  Price 175 -> 165 (Recon 180 -> 170).
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.3.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
before=copy.deepcopy(t);g=Graph(t,patches,native)
U=t['Units'];W=t['WeaponsJson'];A=t['AmmunitionsJson'];WA=t['WeaponAmmunitionsJson'];TW=t['TurretWeaponsJson'];TU=t['TurretUnitsJson']
CTL,ZBD20,ZBD20R=1054,945,1256
assert U[CTL]['HUDName'].startswith('CTL-181') and U[ZBD20]['HUDName']=='ZBD-20' and U[ZBD20R]['HUDName']=='ZBD-20 Recon'
receipt={'version':'0.8.0-dev.4','base':'0.8.0-dev.3','base_sha256':BASE,'request':'Osama 12 Nov 13:53 PST'}
# ---- CTL-181: small precision cruise missile
r=[x for x in WA.values() if x['UnitId']==CTL];assert len(r)==1;r=r[0];wid,aid=r['WeaponId'],r['AmmunitionId']
for f,v in(('WeaponId',wid),('AmmunitionId',aid)):assert {x['UnitId'] for x in WA.values() if x[f]==v}=={CTL}
isk=next(x for x in WA.values() if x['UnitId']==226 and A[x['AmmunitionId']]['HUDName']=='9M728')
iw,ia=W[isk['WeaponId']],A[isk['AmmunitionId']]
hell=next(x for x in A.values() if x['HUDName']=='AGM-114L Hellfire')
g.put('WeaponsJson',wid,{**{k:copy.deepcopy(v) for k,v in iw.items() if k not in('Id','Name','HUDName','HUDIcon')},
    'MagazineSize':4,'MagazineReloadTimeMin':8.0,'MagazineReloadTimeMax':12.0,'AimTimeMin':3.0,'AimTimeMax':4.0,'TimeBetweenBurstsMin':2.0,'TimeBetweenBurstsMax':3.0})
g.put('AmmunitionsJson',aid,{**{k:copy.deepcopy(v) for k,v in ia.items() if k not in('Id','Name','HUDName','HUDIcon')},
    'ModelFileName':hell['ModelFileName'],'FXPreset':hell['FXPreset'],'AudioPreset':hell['AudioPreset'],'SupplyCost':hell['SupplyCost'],'ResupplyTime':hell['ResupplyTime'],
    'Damage':15.0,'StressDamage':hell['StressDamage'],'PenetrationAtMinRange':20.0,'PenetrationAtGroundRange':20.0,'IgnoreCover':0.5,'HealthAOERadius':12.5,'StressAOERadius':25.0,'OverpressureRadius':0.0,
    'GroundRange':1000.0,'MinimalRange':100.0,'TargetType':1})
receipt['ctl181']={'flight':'Iskander-K 9M728 cruise (trajectory %s, vertical launch %s)'%(A[aid]['TrajectoryType'],W[wid]['IsVerticalLauncher']),'model':A[aid]['ModelFileName'],'damage':15,'penetration':20,'ignore_cover':0.5,'range_data':1000,'missiles':r['Quantity']}
# ---- ZBD-20: no missiles
gun=next(x for x in WA.values() if x['UnitId']==ZBD20 and W[x['WeaponId']]['HUDName']=='100 mm gun / HJ-9 launcher')['WeaponId']
mount=next(x['TurretId'] for x in TU.values() if x['UnitId']==ZBD20)
assert {x['UnitId'] for x in TU.values() if x['TurretId']==mount}=={ZBD20,ZBD20R} and {x['UnitId'] for x in WA.values() if x['WeaponId']==gun}<={ZBD20,ZBD20R}
for x in [x for x in TW.values() if x['TurretId']==mount and x['WeaponId']==gun]:g.remove('TurretWeaponsJson',x['Id'])
for x in [x for x in WA.values() if x['WeaponId']==gun]:g.remove('WeaponAmmunitionsJson',x['Id'])
for i,x in enumerate(sorted([x for x in TW.values() if x['TurretId']==mount],key=lambda x:x['Order'])):g.put('TurretWeaponsJson',x['Id'],{'Order':i})
g.put('Units',ZBD20,{'Cost':165});g.put('Units',ZBD20R,{'Cost':170})
receipt['zbd20']={'removed':'100 mm gun / HJ-9 launcher','weapons_now':[W[x['WeaponId']]['HUDName'] for x in sorted([x for x in TW.values() if x['TurretId']==mount],key=lambda x:x['Order'])],'cost':[165,170]}
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(A[aid]['TrajectoryType']==ia['TrajectoryType'] and W[wid]['Type']==iw['Type'],'cruise launcher')
ok(not any(x['WeaponId']==gun for x in WA.values()),'no 100 mm')
for uid in (ZBD20,ZBD20R):
    for x in [x for x in TW.values() if x['TurretId']==mount]:ok(any(y['UnitId']==uid and y['WeaponId']==x['WeaponId'] for y in WA.values()),('ammo row',uid))
for uid,u in before['Units'].items():
    if u.get('CountryId')!=4:ok(t['Units'][uid]==u,('non-China unit changed',uid))
for tab in t:
    for key,row in before[tab].items():
        if key in native[tab]:ok(t[tab].get(key)==row,('vanilla row changed',tab,key))
receipt['checks']=checks
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save('UserData/FreedomArrow/pla-0.8.0-dev.4.json',receipt)
(ROOT/'tools/pla-specs/0.8.0-dev.4-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(receipt,indent=1,ensure_ascii=False))

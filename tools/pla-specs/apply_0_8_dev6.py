"""Freedom Arrow 0.8.0-dev.6 over exact 0.8.0-dev.5 (Osama 12 Nov 14:01-14:03 PST).

"The CTL-181 is perfect! But it needs to be laser guided" / "it needs to constantly shoot if it right clicks a unit" /
"CTL-181 NLOS needs 30mm of penetration" / "and no dispersion" / "same with the ZBD-20 missile".
- Laser guidance: already in 0.8.0-dev.5 for both missiles (KAB-500 seeker fields); kept.
- Penetration: CTL-181 missile 20 -> 30. ZBD-20 keeps its 65 AT warhead.
- Dispersion: horizontal, vertical and minimal dispersion 0 on both missiles (Iskander-K copy had 20/20/1).
- Repeat fire: the Iskander-K launcher fires one missile per order (NormalGroundAttackBurst 1, as on 40 of 42 vanilla
  cruise launchers). The attack-order bursts now cover the whole load: CTL-181 4/48/48 (short/normal/long),
  ZBD-20 2/4/4, so an attack order keeps firing. Whether a unit order uses these counts needs the in-game check.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.5.json').read_text())['complete']['sha256']
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
U=t['Units'];W=t['WeaponsJson'];A=t['AmmunitionsJson'];WA=t['WeaponAmmunitionsJson']
CTL,ZBD20=1054,945
ctl=next(x for x in WA.values() if x['UnitId']==CTL)
zbd=next(x for x in WA.values() if x['UnitId']==ZBD20 and A[x['AmmunitionId']]['HUDName']=='Precision AT missile')
for x in (ctl,zbd):
    for f in ('WeaponId','AmmunitionId'):assert {r['UnitId'] for r in WA.values() if r[f]==x[f]}<={CTL,ZBD20,1256},(f,x[f])
NODISP={'DispersionHorizontalRadius':0.0,'DispersionVerticalRadius':0.0,'DispersionMinimal':0.0}
g.put('AmmunitionsJson',ctl['AmmunitionId'],{**NODISP,'PenetrationAtMinRange':30.0,'PenetrationAtGroundRange':30.0})
g.put('AmmunitionsJson',zbd['AmmunitionId'],NODISP)
g.put('WeaponsJson',ctl['WeaponId'],{'ShortGroundAttackBurst':4,'NormalGroundAttackBurst':48,'LongGroundAttackBurst':48})
g.put('WeaponsJson',zbd['WeaponId'],{'ShortGroundAttackBurst':2,'NormalGroundAttackBurst':4,'LongGroundAttackBurst':4})
row=lambda x:{**{k:A[x['AmmunitionId']][k] for k in ('PenetrationAtGroundRange','LaserGuided',*NODISP)},**{k:W[x['WeaponId']][k] for k in ('ShortGroundAttackBurst','NormalGroundAttackBurst','LongGroundAttackBurst')}}
receipt={'version':'0.8.0-dev.6','base':'0.8.0-dev.5','base_sha256':BASE,'request':'Osama 12 Nov 14:01-14:03 PST','ctl181':row(ctl),'zbd20':row(zbd)}
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(A[ctl['AmmunitionId']]['LaserGuided'] and A[zbd['AmmunitionId']]['LaserGuided'],'laser guided')
for uid,u in before['Units'].items():ok(t['Units'][uid]==u,('unit changed',uid))
for tab in t:
    for key,r in before[tab].items():
        if key in native[tab]:ok(t[tab].get(key)==r,('vanilla row changed',tab,key))
receipt['checks']=checks
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save('UserData/FreedomArrow/pla-0.8.0-dev.6.json',receipt)
(ROOT/'tools/pla-specs/0.8.0-dev.6-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(receipt,indent=1,ensure_ascii=False))

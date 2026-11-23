"""Freedom Arrow 0.8.0-dev.5 over exact 0.8.0-dev.4 (Osama 12 Nov 13:58 PST).

"The ZBD-20 has the same munition as the CTL-181 NLOS. Except it only has 4 but should kill a tank in 2 hits for low
end and 3 hits for high end but also do 20 damage to infantry in the open. It doesn't have HJ's traditionally."

ZBD-20 and ZBD-20 Recon get the CTL-181 launcher and missile (small precision-strike cruise missile), 4 rounds, with a
top-attack anti-tank warhead: base damage 20, penetration 65. Native HEAT damage = B x P^2 / (P^2 + A^2) (report
ba-at-lethality). All MBTs have 14 HP; top HEAT armour is 80 on low-end tanks (T-72B3, ZTZ-96B) and 100 on high-end
(T-90M, ZTZ-99A, M1A2): 7.95 per hit -> 2 hits, 5.94 per hit -> 3 hits. Infantry (armour value about 6): about 19.8.
CTL-181 keeps its own anti-infantry missile. Price 165 -> 175 (Recon 170 -> 180). Calculated, not measured.

13:59: "the ZBD-20 can laze and its missile can be lazed". ZBD-20 and ZBD-20 Recon get the vanilla vehicle laser
designator (ability 8 "Laser Veh", as on M7 BFIST, 1500 range, usable on the move). The ZBD-20 missile and the CTL-181
missile (the same munition) take the vanilla laser-guided bomb seeker fields (KAB-500: LaserGuided, seeker angle 90,
seeker distance 300, reacquire), so either can follow a laser spot.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.4.json').read_text())['complete']['sha256']
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
U=t['Units'];W=t['WeaponsJson'];A=t['AmmunitionsJson'];WA=t['WeaponAmmunitionsJson'];TW=t['TurretWeaponsJson'];TU=t['TurretUnitsJson'];UA=t['UnitArmorsJson'];AR=t['ArmorsJson']
CTL,ZBD20,ZBD20R=1054,945,1256
ctl=next(x for x in WA.values() if x['UnitId']==CTL)
wid=g.add('WeaponsJson',W[ctl['WeaponId']],{'Name':'PLA ZBD-20 precision missile launcher','HUDName':'Precision missile launcher','MagazineSize':4})
aid=g.add('AmmunitionsJson',A[ctl['AmmunitionId']],{'Name':'PLA ZBD-20 precision missile','HUDName':'Precision AT missile','Damage':20.0,'PenetrationAtMinRange':65.0,'PenetrationAtGroundRange':65.0,'IsTopArmorArmorAttack':True,'ArmorTargeted':2})
mount=next(x['TurretId'] for x in TU.values() if x['UnitId']==ZBD20)
order=sorted([x for x in TW.values() if x['TurretId']==mount],key=lambda x:x['Order'])
g.add('TurretWeaponsJson',order[0],{'WeaponId':wid,'Order':len(order)})
for uid in (ZBD20,ZBD20R):g.add('WeaponAmmunitionsJson',ctl,{'UnitId':uid,'WeaponId':wid,'AmmunitionId':aid,'Quantity':4})
g.put('Units',ZBD20,{'Cost':175});g.put('Units',ZBD20R,{'Cost':180})
laser=t['AbilitiesJson'][8];assert laser['IsLaserDesignator'] and laser['Name']=='Laser Veh'
for uid in (ZBD20,ZBD20R):g.add('UnitAbilitiesJson',next(iter(t['UnitAbilitiesJson'].values())),{'UnitId':uid,'AbilityId':8})
SEEK=('LaserGuided','SeekerAngle','MaxSeekerDistance','CanReaquire')
for x in (aid,ctl['AmmunitionId']):
    assert {r['UnitId'] for r in WA.values() if r['AmmunitionId']==x}<={CTL,ZBD20,ZBD20R}
    g.put('AmmunitionsJson',x,{k:A[325][k] for k in SEEK})
heat=lambda B,P,Ar:B*P*P/(P*P+Ar*Ar)
calc={}
for n in ('T-72B3','ZTZ-96B','T-90M','ZTZ-99A','M1A2 SEP v3','T-14 Armata'):
    uid=next(k for k,u in U.items() if u['HUDName']==n);ar=next(AR[r['ArmorId']] for r in UA.values() if r['UnitId']==uid and AR[r['ArmorId']].get('IsDefault'))
    d=heat(20,65,ar['HeatArmorTop']);import math;calc[n]={'hp':ar['MaxHealthPoints'],'top_heat':ar['HeatArmorTop'],'damage':round(d,2),'hits':math.ceil(ar['MaxHealthPoints']/d)}
calc['infantry (armour value 6)']={'damage':round(heat(20,65,6),2)}
receipt={'laser':'ability 8 Laser Veh on ZBD-20 and Recon; ZBD-20 and CTL-181 missiles laser-guided (KAB-500 seeker fields)','version':'0.8.0-dev.5','base':'0.8.0-dev.4','base_sha256':BASE,'request':'Osama 12 Nov 13:58 PST','weapon':wid,'ammo':aid,'calculated':calc,'cost':[175,180]}
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(calc['T-72B3']['hits']==2 and calc['ZTZ-96B']['hits']==2 and calc['T-90M']['hits']==3 and calc['ZTZ-99A']['hits']==3,'hit counts')
for uid in (ZBD20,ZBD20R):
    for x in [x for x in TW.values() if x['TurretId']==mount]:ok(any(y['UnitId']==uid and y['WeaponId']==x['WeaponId'] for y in WA.values()),('ammo row',uid))
ok(A[ctl['AmmunitionId']]['Damage']==15.0 and A[ctl['AmmunitionId']]['LaserGuided'] and A[aid]['LaserGuided'],'CTL-181 damage unchanged; both lazable')
for uid,u in before['Units'].items():
    if u.get('CountryId')!=4:ok(t['Units'][uid]==u,('non-China unit changed',uid))
for tab in t:
    for key,row in before[tab].items():
        if key in native[tab]:ok(t[tab].get(key)==row,('vanilla row changed',tab,key))
receipt['checks']=checks
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save('UserData/FreedomArrow/pla-0.8.0-dev.5.json',receipt)
(ROOT/'tools/pla-specs/0.8.0-dev.5-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(receipt,indent=1,ensure_ascii=False))

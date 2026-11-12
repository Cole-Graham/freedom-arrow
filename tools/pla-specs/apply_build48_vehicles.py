"""Build48 ground-vehicle pass over exact Build47 (Osama 12 Nov 05:00 PST).

"Start with the ZTZ-99A being the same armor and penetration as Armata (almost same stats).
Fill in all the vehicles pricing and weapons performance ... ATGMs being 10.5 damage."

- Tanks and gun vehicles: armour, gun penetration (our +25 close-range KE rule) and ammunition
  counts set against the vanilla tank of the same generation; modern MBTs get a 125 mm
  gun-launched missile (3 rounds, Sprinter performance).
- Every PLA ground-vehicle ATGM uses the 10.5 damage standard.
- Prices set against the vanilla counterpart (see VEH).
Rows shared with another unit are cloned first, so no other unit changes.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
BASE=json.loads((REL/'out/PLA-TEST-Build-47.json').read_text())['sha256']
def arm(kf,ks,kr,kt,hf,hs,hr,ht,hp=14):return dict(KinArmorFront=kf,KinArmorSides=ks,KinArmorRear=kr,KinArmorTop=kt,HeatArmorFront=hf,HeatArmorSides=hs,HeatArmorRear=hr,HeatArmorTop=ht,MaxHealthPoints=hp)
ARMATA=arm(850,150,100,80,1300,500,100,100)
# uid: cost, armour (None = keep), KE (long,close), HEAT pen, rounds {ke,he,heat,gl}, basis
VEH={
 904:dict(cost=320,armor=ARMATA,ke=(500,525),heat=850,rounds=dict(ke=16,he=17,heat=5,gl=3),basis='T-14 Armata (Osama: same armour and penetration)'),
 927:dict(cost=320,armor=ARMATA,ke=(500,525),heat=850,rounds=dict(ke=16,he=17,heat=5,gl=3),basis='T-14 Armata class'),
 968:dict(cost=340,armor=arm(800,180,100,80,1200,500,100,100),ke=(500,525),heat=850,rounds=dict(ke=16,he=17,heat=5,gl=3),basis='T-14 class next-generation tank, lighter hull'),
 1083:dict(cost=160,armor=arm(650,120,100,80,900,200,100,80),ke=(425,450),heat=750,rounds=dict(ke=16,he=17,heat=5,gl=3),basis='T-90A class (first-generation ZTZ-99)'),
 905:dict(cost=125,armor=None,ke=(425,450),heat=750,rounds=dict(ke=16,he=20,heat=6,gl=3),basis='T-72B3 (donor kept)'),
 1082:dict(cost=105,armor=arm(600,120,100,80,700,200,100,80),ke=(400,425),heat=750,rounds=dict(ke=16,he=20,heat=6),basis='between T-72B3 and T-72B'),
 949:dict(cost=80,armor=arm(550,100,100,60,650,200,100,80),ke=(325,350),heat=650,rounds=dict(ke=14,he=22,heat=6),basis='T-72B'),
 1061:dict(cost=60,armor=None,ke=(325,350),heat=450,rounds=dict(ke=16,he=16,heat=8),basis='T-62M (donor kept), 105 mm'),
 1060:dict(cost=40,armor=arm(250,80,60,40,300,100,60,40,12),ke=(225,250),heat=350,rounds=dict(ke=12,he=18,heat=8),basis='T-55 class, 100 mm'),
 930:dict(cost=65,armor=None,ke=(325,350),heat=None,rounds=dict(ke=18,he=20),basis='Sprut-SD class amphibious 105 mm'),
 938:dict(cost=70,armor=None,ke=(325,350),heat=None,rounds=dict(ke=18,he=20),basis='Stryker MGS class 105 mm'),
 947:dict(cost=60,armor=None,ke=(400,425),heat=400,rounds=dict(ke=16,heat=14),basis='120 mm towed-gun tank destroyer'),
 906:dict(cost=95,basis='Osama: 475/500 DU (kept)'),1240:dict(cost=100,basis='ZTQ-15 + Very Good optics (kept)'),
 1080:dict(cost=115,basis='Osama: 550/575 DU (kept)'),1059:dict(cost=40,basis='Osama: cheap, low pen (kept)'),958:dict(cost=25,basis='PT-76 class'),
 937:dict(cost=140,basis='BMPT class'),
 902:dict(cost=55,basis='BMP-3 class, newer'),1075:dict(cost=50,basis='BMP-3 class'),945:dict(cost=55,basis='BMP-3 class, new production'),
 903:dict(cost=40,basis='BTR-82A class + ATGM'),979:dict(cost=40,basis='Bumerang class'),1076:dict(cost=45,basis='amphibious 30 mm IFV'),
 1074:dict(cost=45,basis='BMD-4M class airborne IFV'),1063:dict(cost=25,basis='BMP-1 copy'),1056:dict(cost=75,basis='Kurganets class airborne IFV with HJ-10/ABZ-13'),
 1079:dict(cost=35,basis='BTR-82A class'),951:dict(cost=50,basis='BRDM ATGM class'),1053:dict(cost=65,basis='HJ-9 long-range ATGM carrier'),936:dict(cost=90,basis='M6/AFT-10 class'),
}
NO_ATGM_NORMALISE={'ABZ-13 anti-personnel','QN-202 anti-personnel missile','QN-201 guided support missile ammunition'}
enc=lambda d:(json.dumps(d,indent=2)+'\n').encode()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
before=copy.deepcopy(t);g=Graph(t,patches,native);U=t['Units'];A=t['AmmunitionsJson'];WA=t['WeaponAmmunitionsJson'];AR=t['ArmorsJson']
SPRINTER=2000175;assert A[SPRINTER]['HUDName'].startswith('Sprinter')
def own_ammo(uid,wa):
    aid=wa['AmmunitionId']
    if any(r['AmmunitionId']==aid and r['UnitId']!=uid for r in WA.values()):
        aid=g.add('AmmunitionsJson',A[aid],{'Name':A[aid]['Name']+' PLA '+str(uid)});g.put('WeaponAmmunitionsJson',wa['Id'],{'AmmunitionId':aid})
    return aid
def kind(am,wa):
    if am['Seeker'] in (50,100) and am['ArmorTargeted']==2:return 'gl' if 'gun' in t['WeaponsJson'][wa['WeaponId']]['HUDName'].lower() or 'mm' in t['WeaponsJson'][wa['WeaponId']]['HUDName'] else 'atgm'
    if am['ArmorTargeted']==1 and am['Damage']>=8:return 'ke'
    if am['ArmorTargeted']==2 and am['Seeker']==0 and am['PenetrationAtGroundRange']>=300 and am['Damage']>=6:return 'heat'
    if am['ArmorTargeted']==2 and am['Seeker']==0 and am['Damage']>=8:return 'he'
    return None
receipt={'build':48,'base_build':47,'base_sha256':BASE,'vehicles':{},'atgm_normalised':[]}
for uid,v in VEH.items():
    u=U[uid];rec={'name':u['HUDName'],'cost':[u['Cost'],v['cost']],'basis':v['basis']}
    g.put('Units',uid,{'Cost':v['cost']})
    if v.get('armor'):
        links=[r for r in t['UnitArmorsJson'].values() if r['UnitId']==uid]
        for r in links:
            aid=r['ArmorId']
            if any(x['ArmorId']==aid and x['UnitId']!=uid for x in t['UnitArmorsJson'].values()):
                aid=g.add('ArmorsJson',AR[aid],{});g.put('UnitArmorsJson',r['Id'],{'ArmorId':aid})
            g.put('ArmorsJson',aid,v['armor'])
        rec['armor']=v['armor']
    if v.get('ke') or v.get('rounds'):
        gun=None
        for wa in [r for r in WA.values() if r['UnitId']==uid]:
            am=A[wa['AmmunitionId']];k=kind(am,wa)
            if k=='ke' and v.get('ke'):
                aid=own_ammo(uid,wa);g.put('AmmunitionsJson',aid,{'PenetrationAtGroundRange':float(v['ke'][0]),'PenetrationAtMinRange':float(v['ke'][1])});gun=wa
            if k=='heat' and v.get('heat'):
                aid=own_ammo(uid,wa);g.put('AmmunitionsJson',aid,{'PenetrationAtGroundRange':float(v['heat']),'PenetrationAtMinRange':float(v['heat'])})
            if k and k in v.get('rounds',{}):g.put('WeaponAmmunitionsJson',wa['Id'],{'Quantity':v['rounds'][k]})
        gl=v.get('rounds',{}).get('gl')
        if gl and gun and not any(A[r['AmmunitionId']]['Seeker'] in(50,100) and r['WeaponId']==gun['WeaponId'] for r in WA.values() if r['UnitId']==uid):
            aid=g.add('AmmunitionsJson',A[SPRINTER],{'Name':'PLA GP125 gun-launched missile '+str(uid),'HUDName':'GP125 gun-launched missile'})
            g.add('WeaponAmmunitionsJson',gun,{'UnitId':uid,'WeaponId':gun['WeaponId'],'AmmunitionId':aid,'Quantity':gl})
        rec['ke']=v.get('ke');rec['rounds']=v.get('rounds')
    receipt['vehicles'][str(uid)]=rec
# ATGM 10.5 standard on every PLA ground vehicle
pla=[u['Id'] for u in U.values() if u.get('CountryId')==4 and u['Type']==4 and u.get('DisplayInArmory')]
for uid in pla:
    for wa in [r for r in WA.values() if r['UnitId']==uid]:
        am=A[wa['AmmunitionId']]
        if am['Seeker'] in(50,100) and am['ArmorTargeted']==2 and am['GroundRange']>0 and am['LowAltRange']==0 and am['HUDName'] not in NO_ATGM_NORMALISE and am['Damage']!=10.5 and am['PenetrationAtGroundRange']>=300:
            aid=own_ammo(uid,wa);receipt['atgm_normalised'].append([uid,U[uid]['HUDName'],am['HUDName'],am['Damage']]);g.put('AmmunitionsJson',aid,{'Damage':10.5})
# checks
checks=0
def ok(c,label):
    global checks
    assert c,label;checks+=1
for uid in pla:
    for wa in [r for r in WA.values() if r['UnitId']==uid]:
        am=A[wa['AmmunitionId']]
        if am['Seeker'] in(50,100) and am['ArmorTargeted']==2 and am['GroundRange']>0 and am['LowAltRange']==0 and am['HUDName'] not in NO_ATGM_NORMALISE and am['PenetrationAtGroundRange']>=300:ok(am['Damage']==10.5,('atgm',uid,am['HUDName']))
for uid,v in VEH.items():
    ok(U[uid]['Cost']==v['cost'],('cost',uid))
    if v.get('armor'):ok(all(AR[r['ArmorId']][k]==val for r in t['UnitArmorsJson'].values() if r['UnitId']==uid for k,val in v['armor'].items()),('armor',uid))
ok(t['ArmorsJson'][2000422]==before['ArmorsJson'][2000422],'T-14 armour untouched')
for uid,u in before['Units'].items():
    if u.get('CountryId')!=4:ok(t['Units'][uid]==u,('non-PLA unit changed',uid))
for key,row in before['AmmunitionsJson'].items():
    users={r['UnitId'] for r in WA.values() if r['AmmunitionId']==key}|{r['UnitId'] for r in before['WeaponAmmunitionsJson'].values() if r['AmmunitionId']==key}
    if any(U[x].get('CountryId')!=4 for x in users if x in U):ok(t['AmmunitionsJson'][key]==row,('shared ammo changed',key))
receipt['checks']=checks
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save('UserData/FreedomArrow/pla-vehicle-pass.json',receipt)
(ROOT/'tools/pla-specs/build48-vehicle-checks.json').write_bytes(enc({k:v for k,v in receipt.items() if k!='vehicles'}))
print(json.dumps({'checks':checks,'atgm_normalised':len(receipt['atgm_normalised'])},indent=1))
for uid,r in receipt['vehicles'].items():print(uid,r['name'],r['cost'],r.get('ke'),r.get('rounds'))

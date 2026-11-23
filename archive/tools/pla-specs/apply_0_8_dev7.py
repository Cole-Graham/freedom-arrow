"""Freedom Arrow 0.8.0-dev.7 over exact 0.8.0-dev.6 (Osama 12 Nov PST): the NLOS trait.

"is there a way to have the HJ-10 bypass LOS checks?" / "if the target moves and there's no laser it loses track right?
I think a special hook for this unit is ok" / "Blood wolves is the unit we will give the NLOS to. replace the HJ-12" /
"Any future weapon with this NLOS trait will receive the same benefits".
- NLOS firing: the missile flies the CTL-181 precision path (TrajectoryType 200), which the game fires at any enemy the
  side has spotted, without the launcher's own line of sight (CTL-181, verified by Osama in 0.8.0-dev.4).
- Moving targets: the missile gets its own fire-and-forget seeker (Seeker 10) with a 180 degree cone and a seeker range
  equal to the missile range. The runtime hook (NlosTrait.cs) keeps that seeker on the target while it is alive, so the
  missile follows a moving target with no laser. Laser guidance is off on NLOS missiles so two guidance modes do not mix.
- The trait list is UserData/FreedomArrow/nlos.json (ammunition IDs). Any missile in it gets the hook.
- Ground HJ-10 (unit 936): its own launcher and missile rows (used by no other unit) get the precision flight and the
  trait. The warhead stays HJ-10: 13 damage, 90 penetration, top attack, range 900 (1800 m).
- Blood Wolves (unit 1183): the HJ-12 (shared with 3 other units) is replaced by a new NLOS launcher that fires the
  ZBD-20 precision AT missile (20 damage, 65 penetration, top attack, range 1000) with the trait. 2 missiles, as the HJ-12.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.7'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.6.json').read_text())['complete']['sha256']
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
W=t['WeaponsJson'];A=t['AmmunitionsJson'];WA=t['WeaponAmmunitionsJson'];SW=t['SquadWeaponsJson'];SM=t['SquadMembersJson']
HJ10U,BW,ZBD20=936,1183,945
CTLW,CTLA,ZBDA=2018322,2018321,2018441
HJ10W,HJ10A,HJ12W,BWMEMBER,BWSW,BWWA=2009619,2009623,2011864,2015320,2018056,2018059
assert W[CTLW]['HUDName']=='CTL-181 NLOS launcher' and A[CTLA]['HUDName']=='NLOS missile' and A[ZBDA]['HUDName']=='Precision AT missile'
hj=next(x for x in WA.values() if x['UnitId']==HJ10U)
assert (hj['WeaponId'],hj['AmmunitionId'])==(HJ10W,HJ10A)
for f,v in (('WeaponId',HJ10W),('AmmunitionId',HJ10A)):assert {x['UnitId'] for x in WA.values() if x[f]==v}=={HJ10U},('HJ-10 rows shared',f)
assert SM[BWMEMBER]['UnitId']==BW and SM[BWMEMBER]['SpecialWeaponId']==HJ12W and SW[BWSW]=={'Id':BWSW,'WeaponId':HJ12W,'UnitId':BW,'Order':1}
assert WA[BWWA]['UnitId']==BW and WA[BWWA]['WeaponId']==HJ12W
# Flight and launcher behaviour of the CTL-181 precision missile (TrajectoryType 200).
FLIGHT=('TargetType','CanBeIntercepted','CanBeTargeted','TrajectoryType','LowAltRange','MuzzleVelocity','MaxSpeed','Acceleration',
        'DispersionHorizontalRadius','DispersionVerticalRadius','DispersionMinimal','LaunchMarginAngle','LoftAngle','MainEngineIgnitionDelay',
        'RotationSpeed','BurnTime','RadioFuseDistance')
LAUNCHER=('Type','AudioPreset','IsVerticalLauncher','CanShootOnTheMove','LowerVerticalAngle','UpperVerticalAngles','VerticalRotationSpeed')
def trait(rng):return {'Seeker':10,'SeekerAngle':180.0,'MaxSeekerDistance':float(rng),'LaserGuided':False}
# Ground HJ-10: precision flight + trait, HJ-10 warhead and range kept.
g.put('AmmunitionsJson',HJ10A,{**{k:A[CTLA][k] for k in FLIGHT},**trait(A[HJ10A]['GroundRange'])})
g.put('WeaponsJson',HJ10W,{**{k:W[CTLW][k] for k in LAUNCHER},'ShortGroundAttackBurst':2,'NormalGroundAttackBurst':8,'LongGroundAttackBurst':8})
# Blood Wolves: new infantry launcher (HJ-12 copy, infantry weapon type kept) firing the ZBD-20 missile with the trait.
bww=g.add('WeaponsJson',W[HJ12W],{'Name':'PLA Blood Wolves NLOS launcher','HUDName':'NLOS missile launcher','ShortGroundAttackBurst':1,'NormalGroundAttackBurst':2,'LongGroundAttackBurst':2})
bwa=g.add('AmmunitionsJson',A[ZBDA],{'Name':'PLA Blood Wolves NLOS missile','HUDName':'NLOS AT missile',**trait(A[ZBDA]['GroundRange'])})
g.put('SquadMembersJson',BWMEMBER,{'SpecialWeaponId':bww})
g.put('SquadWeaponsJson',BWSW,{'WeaponId':bww})
g.put('WeaponAmmunitionsJson',BWWA,{'WeaponId':bww,'AmmunitionId':bwa})
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
for aid in (HJ10A,bwa):
    x=A[aid];ok(x['TrajectoryType']==200 and x['Seeker']==10 and not x['LaserGuided'] and x['MaxSeekerDistance']==x['GroundRange'] and x['DispersionHorizontalRadius']==0,('trait',aid))
ok({k:A[HJ10A][k] for k in ('Damage','PenetrationAtGroundRange','GroundRange','IsTopArmorArmorAttack')}=={'Damage':13.0,'PenetrationAtGroundRange':90.0,'GroundRange':900.0,'IsTopArmorArmorAttack':True},'HJ-10 warhead kept')
ok({k:A[bwa][k] for k in ('Damage','PenetrationAtGroundRange','GroundRange','IsTopArmorArmorAttack')}=={'Damage':20.0,'PenetrationAtGroundRange':65.0,'GroundRange':1000.0,'IsTopArmorArmorAttack':True},'ZBD-20 warhead')
ok(A[ZBDA]==before['AmmunitionsJson'][ZBDA] and A[CTLA]==before['AmmunitionsJson'][CTLA] and W[HJ12W]==before['WeaponsJson'][HJ12W],'CTL-181, ZBD-20 and HJ-12 rows unchanged')
ok(WA[BWWA]['Quantity']==before['WeaponAmmunitionsJson'][BWWA]['Quantity'],'Blood Wolves keep 2 missiles')
ok(not any(r.get('WeaponId')==HJ12W for r in [*SW.values(),*WA.values()] if r.get('UnitId')==BW) and not any(SM[m].get('SpecialWeaponId')==HJ12W or SM[m].get('PrimaryWeaponId')==HJ12W for m in SM if SM[m].get('UnitId')==BW),'no HJ-12 left on Blood Wolves')
for uid in (1137,1186,1198):ok(any(r['WeaponId']==HJ12W for r in WA.values() if r['UnitId']==uid),('other HJ-12 users kept',uid))
for uid,u in before['Units'].items():ok(t['Units'][uid]==u,('unit changed',uid))
for tab in t:
    for key,r in before[tab].items():
        if key in native[tab]:ok(t[tab].get(key)==r,('vanilla row changed',tab,key))
nlos={'trait':'NLOS','version':V,'note':'Missiles listed here keep their seeker on a live target without line of sight or a laser (runtime NlosTrait.cs).',
 'ammunition':sorted([HJ10A,bwa]),'weapons':sorted([HJ10W,bww]),'units':{str(HJ10U):'HJ-10',str(BW):'Blood Wolves'}}
row=lambda aid:{k:A[aid][k] for k in ('HUDName','Damage','PenetrationAtGroundRange','GroundRange','TrajectoryType','Seeker','SeekerAngle','MaxSeekerDistance','LaserGuided')}
receipt={'version':V,'base':'0.8.0-dev.6','base_sha256':BASE,'request':'Osama 12 Nov PST (NLOS trait, HJ-10, Blood Wolves)','nlos':nlos,
 'hj10':{'weapon':HJ10W,'ammo':row(HJ10A)},'blood_wolves':{'weapon':bww,'ammo_id':bwa,'ammo':row(bwa),'replaced':HJ12W},'checks':checks}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save('UserData/FreedomArrow/nlos.json',nlos)
save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(receipt,indent=1,ensure_ascii=False))

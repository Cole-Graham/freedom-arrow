"""Build67 over exact Build66 (Osama 12 Nov 13:17 PST).

- PHL-191 (name without "/ AR3") moves to Rocket Force; PHL-03 moves to Motorized and becomes a Smerch
  copy: the vanilla Smerch mounts, rockets and its HE / Cluster / Guided HE / Guided Cluster menu.
- PHL-16: only the default loadout's launcher is a default mount; before, all three were, so the
  vehicle carried every weapon.
- DF-21: KAB-1500 damage and blast (82 damage, 90 m radius), 180 points.
- DF-17/ZF: Kh-47M2 Kinzhal flight (aero-ballistic, steep loft then dive, 20 s motor) with top speed
  1500 instead of 800, so it keeps accelerating into the dive; not interceptable; 300 points.
- DF-31A: 120 s aim time, 1000 points.
- PCL-181: 2S35 Koalitsiya-SV weapons and menu: HE (70) by default; "Extended range" option with HE-RAP
  (50) and guided (20), shown as "155 mm Guided". 152 mm values copied as they are.
- JRVG-1: 76 mm HE 8 damage (about 8 per second at the 57 mm cadence), 20 m blast, low-altitude range
  1200 in data (2400 m displayed), the vanilla SHORAD radar ability, and the Arleigh Burke Mark 45 naval gun sound.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
BASE=json.loads((REL/'out/PLA-TEST-Build-66.json').read_text())['sha256']
IDENT=('Id','Name','HUDName','HUDIcon')
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
U=t['Units'];W=t['WeaponsJson'];A=t['AmmunitionsJson'];T=t['TurretsJson'];WA=t['WeaponAmmunitionsJson'];TU=t['TurretUnitsJson'];TW=t['TurretWeaponsJson'];M=t['ModificationsJson'];O=t['OptionsJson'];SA=t['SpecializationAvailabilitiesJson'];UA=t['UnitAbilitiesJson']
PHL191,PHL03,PHL16,DF21,DF17,DF31,PCL,JRVG,SMERCH,KOAL=1036,908,1035,1030,1028,1032,1034,952,93,232
for uid,n in [(PHL191,'PHL-191 / AR3'),(PHL03,'PHL-03'),(PHL16,'PHL-16'),(DF21,'DF-21'),(DF17,'DF-17/ZF'),(DF31,'DF-31A Nuclear'),(PCL,'PCL-181 / SH-15'),(JRVG,'JRVG-1'),(SMERCH,'9K58 Smerch'),(KOAL,'2S35 Koalitsiya-SV')]:assert U[uid]['HUDName']==n,(uid,U[uid]['HUDName'])
receipt={'build':67,'base_build':66,'base_sha256':BASE,'request':'Osama 12 Nov 13:17 PST'}
spec=json.loads(z.read('UserData/FreedomArrow/pla-spec-assignments.json'))
rows=lambda tab,uid:[r for r in list(t[tab].values()) if r.get('UnitId')==uid]
def only(field,val,uid):assert {r['UnitId'] for r in WA.values() if r[field]==val}=={uid},(field,val)
def move(uid,old,new):
    r=[x for x in SA.values() if x['UnitId']==uid and x['SpecializationId']==old];assert len(r)==1
    g.put('SpecializationAvailabilitiesJson',r[0]['Id'],{'SpecializationId':new});spec['assignments'][str(uid)]=[new]
# ---- PHL-191 / PHL-03
g.put('Units',PHL191,{'HUDName':'PHL-191'});move(PHL191,21,19);move(PHL03,19,21)
for r in rows('WeaponAmmunitionsJson',PHL03):g.remove('WeaponAmmunitionsJson',r['Id'])
for r in rows('TurretUnitsJson',PHL03):g.remove('TurretUnitsJson',r['Id'])
for r in rows('TurretUnitsJson',SMERCH):g.add('TurretUnitsJson',r,{'UnitId':PHL03})
for r in rows('WeaponAmmunitionsJson',SMERCH):g.add('WeaponAmmunitionsJson',r,{'UnitId':PHL03})
for m in [m for m in M.values() if m['UnitId']==SMERCH]:
    mid=g.add('ModificationsJson',m,{'UnitId':PHL03,'Name':'PLA PHL-03 '+m['Name']})
    for o in [o for o in O.values() if o['ModificationId']==m['Id']]:g.add('OptionsJson',o,{'ModificationId':mid,'Name':'PLA PHL-03 '+o['Name']})
receipt['phl03']={'copied_from':'9K58 Smerch','options':[o['UIName'] for o in O.values() if M.get(o['ModificationId'],{}).get('UnitId')==PHL03]}
# ---- PHL-16 default mount only
mod=next(m for m in M.values() if m['UnitId']==PHL16 and m['Type']==3)
opts=[o for o in O.values() if o['ModificationId']==mod['Id']];dflt=next(o for o in opts if o['IsDefault'])
for o in opts:g.put('TurretsJson',o['Turret0Id'],{'IsDefault':o['Id']==dflt['Id']})
receipt['phl16']={'default':dflt['UIName'],'non_default_mounts':[T[o['Turret0Id']]['Name'] for o in opts if o is not dflt]}
# ---- DF-21, DF-17/ZF, DF-31A
kab=next(x for x in A.values() if x['HUDName']=='KAB-1500 1500kg');kinz=next(x for x in A.values() if x['HUDName']=='Kh-47M2 Kinzhal')
aid=next(r['AmmunitionId'] for r in rows('WeaponAmmunitionsJson',DF21));only('AmmunitionId',aid,DF21)
g.put('AmmunitionsJson',aid,{k:kab[k] for k in ('Damage','StressDamage','HealthAOERadius','StressAOERadius','OverpressureRadius')});g.put('Units',DF21,{'Cost':180})
aid=next(r['AmmunitionId'] for r in rows('WeaponAmmunitionsJson',DF17));only('AmmunitionId',aid,DF17)
FLIGHT=('TrajectoryType','LoftAngle','Acceleration','BurnTime','MainEngineIgnitionDelay','RotationSpeed','LaunchMarginAngle','CanBeIntercepted')
g.put('AmmunitionsJson',aid,{**{k:kinz[k] for k in FLIGHT},'MaxSpeed':1500.0});g.put('Units',DF17,{'Cost':300})
receipt['df17']={k:A[aid][k] for k in FLIGHT+('MaxSpeed',)}
wid=next(r['WeaponId'] for r in rows('WeaponAmmunitionsJson',DF31));only('WeaponId',wid,DF31)
g.put('WeaponsJson',wid,{'AimTimeMin':120.0,'AimTimeMax':120.0});g.put('Units',DF31,{'Cost':1000})
# ---- PCL-181 = Koalitsiya
kwa=rows('WeaponAmmunitionsJson',KOAL)
def kw(wid_,amm):return next(r for r in kwa if r['WeaponId']==wid_ and A[r['AmmunitionId']]['HUDName']==amm)
he,rap,gd=kw(325,'152mm HE'),kw(326,'152mm HE-RAP'),kw(326,'152mm Krasnopol-D')
old=rows('WeaponAmmunitionsJson',PCL);assert len(old)==1;mount=next(r['TurretId'] for r in rows('TurretUnitsJson',PCL))
wA=g.add('WeaponsJson',W[325],{'Name':'PLA PCL-181 155 mm HE','HUDName':'155 mm howitzer'})
wB=g.add('WeaponsJson',W[326],{'Name':'PLA PCL-181 155 mm extended range','HUDName':'155 mm howitzer'})
aHE=g.add('AmmunitionsJson',A[he['AmmunitionId']],{'Name':'PLA PCL-181 155 mm HE','HUDName':'155 mm HE'})
aRAP=g.add('AmmunitionsJson',A[rap['AmmunitionId']],{'Name':'PLA PCL-181 155 mm HE-RAP','HUDName':'155 mm HE-RAP'})
aGD=g.add('AmmunitionsJson',A[gd['AmmunitionId']],{'Name':'PLA PCL-181 155 mm guided','HUDName':'155 mm Guided'})
g.remove('WeaponAmmunitionsJson',old[0]['Id'])
for tw in [x for x in TW.values() if x['TurretId']==mount]:g.put('TurretWeaponsJson',tw['Id'],{'WeaponId':wA})
tB=g.add('TurretsJson',T[mount],{'Name':'PLA PCL-181 mount extended range','IsDefault':False})
g.add('TurretWeaponsJson',next(x for x in TW.values() if x['TurretId']==mount),{'TurretId':tB,'WeaponId':wB})
g.add('TurretUnitsJson',next(r for r in rows('TurretUnitsJson',PCL)),{'TurretId':tB})
for w_,a_,r_ in [(wA,aHE,he),(wB,aRAP,rap),(wB,aGD,gd)]:g.add('WeaponAmmunitionsJson',r_,{'UnitId':PCL,'WeaponId':w_,'AmmunitionId':a_})
km=next(m for m in M.values() if m['UnitId']==KOAL and m['Type']==3)
mid=g.add('ModificationsJson',km,{'UnitId':PCL,'Name':'PLA PCL-181 '+km['Name']})
for o in [o for o in O.values() if o['ModificationId']==km['Id']]:
    g.add('OptionsJson',o,{'ModificationId':mid,'Name':'PLA PCL-181 '+o['Name'],'Turret0Id':mount if o['UIName']=='Custom_Option_HE_rounds' else tB})
receipt['pcl181']={'HE':he['Quantity'],'HE-RAP':rap['Quantity'],'Guided':gd['Quantity'],'reload':W[wA]['MagazineReloadTimeMin'],'aim':[W[wA]['AimTimeMin'],W[wA]['AimTimeMax']]}
# ---- JRVG-1
he76=next(r for r in rows('WeaponAmmunitionsJson',JRVG) if A[r['AmmunitionId']]['LowAltRange']>0);only('AmmunitionId',he76['AmmunitionId'],JRVG)
g.put('AmmunitionsJson',he76['AmmunitionId'],{'Damage':8.0,'HealthAOERadius':20.0,'StressAOERadius':20.0,'LowAltRange':1200.0})
# Osama 13:21: "does vanilla have a naval gun? ... use that stats and sound effects". The only vanilla naval gun is the
# Arleigh Burke Mark 45 127 mm (ground-only howitzer: 10 damage, 40 m, no air targets), so JRVG takes its firing sound and a
# heavy-shell impact sound; the AA numbers above stay.
mk45=W[598];assert mk45['HUDName']=='Mark 45'
only('WeaponId',he76['WeaponId'],JRVG);g.put('WeaponsJson',he76['WeaponId'],{'AudioPreset':mk45['AudioPreset']})
for r in rows('WeaponAmmunitionsJson',JRVG):
    if r['WeaponId']==he76['WeaponId']:g.put('AmmunitionsJson',r['AmmunitionId'],{'AudioPreset':'AmmunitionSoundsPreset_SFX_ROUND_SHELL_OBUS_80-105'})
radar=t['AbilitiesJson'][60];assert radar['IsRadar'] and radar['Name']=='Radar SHORAD'
g.add('UnitAbilitiesJson',next(iter(UA.values())),{'UnitId':JRVG,'AbilityId':60})
w=W[he76['WeaponId']];cyc=((w['ShotsPerBurstMin']+w['ShotsPerBurstMax'])/2-1)*w['TimeBetweenShotsInBurst']+(w['TimeBetweenBurstsMin']+w['TimeBetweenBurstsMax'])/2
rate=(w['ShotsPerBurstMin']+w['ShotsPerBurstMax'])/2/cyc
receipt['jrvg']={'sound':'Mark 45 (Arleigh Burke) firing, 80-105 mm shell impact','damage':8.0,'aoe':20.0,'low_alt_range_data':1200,'shots_per_second_est':round(rate,3),'dps_est':round(8.0*rate,2),'radar_ability':60}
# ---- checks
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
links=lambda uid:sorted(r['SpecializationId'] for r in SA.values() if r['UnitId']==uid)
ok(links(PHL191)==[19] and links(PHL03)==[21],'moves')
ok(sum(T[o['Turret0Id']]['IsDefault'] for o in opts)==1,'PHL-16 one default mount')
for uid in (PHL03,PCL):
    for r in rows('TurretUnitsJson',uid):
        for tw in [x for x in TW.values() if x['TurretId']==r['TurretId']]:ok(any(x['WeaponId']==tw['WeaponId'] for x in rows('WeaponAmmunitionsJson',uid)),('ammo row',uid,tw['WeaponId']))
    for o in [o for o in O.values() if M.get(o['ModificationId'],{}).get('UnitId')==uid]:ok(any(r['TurretId']==o['Turret0Id'] for r in rows('TurretUnitsJson',uid)) and o['Id']<=32767,('option turret',uid))
for uid,u in before['Units'].items():
    if u.get('CountryId')!=4:ok(t['Units'][uid]==u,('non-China unit changed',uid))
for tab in t:
    for key,row in before[tab].items():
        if key in native[tab]:ok(t[tab].get(key)==row,('vanilla row changed',tab,key))
receipt['checks']=checks
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save('UserData/FreedomArrow/pla-spec-assignments.json',spec);save('UserData/FreedomArrow/pla-build67.json',receipt)
(ROOT/'tools/pla-specs/build67-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(receipt,indent=1,ensure_ascii=False))

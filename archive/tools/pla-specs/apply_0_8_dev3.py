"""Freedom Arrow 0.8.0-dev.3 over exact 0.8.0-dev.2 (Osama 12 Nov 13:51 PST, ZBD batch).

- ZBD-03 / ZLC-2000 -> "ZBD-03" (ZBD-86 model in desert digital camo is a later assets change).
- ZBD-04A (uparmoured): Bradley BUSK armour (vanilla "Armor Bradley BUSK": KE 100/80/60/40, HEAT 400/250/60/40,
  12 HP) with weaker sides (KE 60, HEAT 150); Bradley M2A2 mobility (60/20), so it is slower than ZBD-04. 65 points.
- ZBD-04 (light): Bradley base armour (100/80/60/40 KE and HEAT, 12 HP); keeps 70/25, faster than ZBD-04A.
- ZBD-20: ZTZ-96B armour (650/120 KE, 750/200 HEAT, 14 HP) and ZTZ-96B mobility (80/40); the ZPT-99 30 mm uses the
  vanilla Bushmaster II (Mk44) firing profile and 30x173 rounds, with the 57 mm HE blast (8 m) and ignore cover (12.5%)
  and the 57 mm ground range (550); Iron Fist APS (2 charges). Priced 175 (T-15 200 with 850/1300 armour, XM30 200,
  T-72B3 125 with this armour).
- ZTZ-99: T-90M armour with 750 KE front (was 800).
- Recon copies (Recon tab, same weapons, own unit IDs; internal Name kept so the same 3D model loads):
  ZBD-04A Recon (PLAGF, Exceptional Optics, +10), ZBD-20 Recon (PLAGF), ZBD-03 Recon (Airborne),
  ZBD-86 Recon (Rocket Force) and ZBD-86 Recon (PLAN SOF): Very Good Optics, +5.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.2.json').read_text())['complete']['sha256']
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
U=t['Units'];AR=t['ArmorsJson'];Mo=t['MobilityJson'];W=t['WeaponsJson'];A=t['AmmunitionsJson'];WA=t['WeaponAmmunitionsJson'];SA=t['SpecializationAvailabilitiesJson']
rows=lambda tab,uid:g.rows(tab,uid)
ZBD03,ZBD04A,ZBD04,ZBD20,ZBD86,ZTZ99,ZTZ96B,M2A2=1074,902,1075,945,1063,1083,905,15
for uid,n in [(ZBD03,'ZBD-03 / ZLC-2000'),(ZBD04A,'ZBD-04A'),(ZBD04,'ZBD-04'),(ZBD20,'ZBD-20'),(ZBD86,'ZBD-86'),(ZTZ99,'ZTZ-99'),(ZTZ96B,'ZTZ-96B'),(M2A2,'M2A2 Bradley')]:assert U[uid]['HUDName']==n,(uid,U[uid]['HUDName'])
spec=json.loads(z.read('UserData/FreedomArrow/pla-spec-assignments.json'))
receipt={'version':'0.8.0-dev.3','base':'0.8.0-dev.2','base_sha256':BASE,'request':'Osama 12 Nov 13:51 PST','changes':{}}
ARMF=('KinArmorFront','KinArmorSides','KinArmorRear','KinArmorTop','HeatArmorFront','HeatArmorSides','HeatArmorRear','HeatArmorTop','MaxHealthPoints','ArmorValue')
MOBF=('Acceleration','Agility','TurnRate','MaxSpeedRoad','MaxSpeedReverse','MaxCrossCountrySpeed','ClimbRate')
def own(tab,field,uid):
    r=[x for x in rows(tab,uid)];assert len(r)==1,(tab,uid,len(r));rid=r[0][field]
    assert {x['UnitId'] for x in t[tab].values() if x[field]==rid}=={uid},(tab,uid,'shared row');return rid
def set_armor(uid,src,**over):
    aid=own('UnitArmorsJson','ArmorId',uid);old={f:AR[aid][f] for f in ARMF};g.put('ArmorsJson',aid,{**{f:src[f] for f in ARMF},**over})
    receipt['changes'].setdefault(U[uid]['HUDName'],{})['armor']=[old,{f:AR[aid][f] for f in ARMF}]
def set_mob(uid,src):
    mid=own('UnitPropulsionsJson','MobilityId',uid);old={f:Mo[mid][f] for f in MOBF};g.put('MobilityJson',mid,{f:src[f] for f in MOBF})
    receipt['changes'].setdefault(U[uid]['HUDName'],{})['mobility']=[old,{f:Mo[mid][f] for f in MOBF}]
mobof=lambda uid:Mo[next(r['MobilityId'] for r in t['UnitPropulsionsJson'].values() if r['UnitId']==uid)]
armof=lambda uid:AR[next(r['ArmorId'] for r in t['UnitArmorsJson'].values() if r['UnitId']==uid)]
# ---- ZBD-03 name
g.put('Units',ZBD03,{'HUDName':'ZBD-03'})
# ---- ZBD-04A / ZBD-04 / ZTZ-99
busk,base=AR[2000014],AR[2000013];assert busk['Name']=='Armor Bradley BUSK' and base['Name']=='Armor Bradley Base'
set_armor(ZBD04A,busk,KinArmorSides=60,HeatArmorSides=150);set_mob(ZBD04A,mobof(M2A2));g.put('Units',ZBD04A,{'Cost':65})
set_armor(ZBD04,base)
set_armor(ZTZ99,armof(238),KinArmorFront=750)
# ---- ZBD-20
set_armor(ZBD20,armof(ZTZ96B));set_mob(ZBD20,mobof(ZTZ96B));g.put('Units',ZBD20,{'Cost':175})
bm=W[23];assert bm['HUDName']=='Bushmaster II'
bmap=next(r['AmmunitionId'] for r in WA.values() if r['WeaponId']==23 and A[r['AmmunitionId']]['HUDName']=='30x173mm API')
bmhe=next(r['AmmunitionId'] for r in WA.values() if r['WeaponId']==23 and A[r['AmmunitionId']]['HUDName']=='30x173mm HEI-T')
he57=next(A[r['AmmunitionId']] for r in WA.values() if r['UnitId']==211 and A[r['AmmunitionId']]['HUDName']=='57x348mm HE')
gun=[r for r in rows('WeaponAmmunitionsJson',ZBD20) if W[r['WeaponId']]['HUDName']=='ZPT-99 30 mm'];assert len(gun)==2
wid=gun[0]['WeaponId'];assert {x['UnitId'] for x in WA.values() if x['WeaponId']==wid}=={ZBD20}
IDW=('Id','Name','HUDName','HUDIcon','ModelFileName')
g.put('WeaponsJson',wid,{k:copy.deepcopy(v) for k,v in bm.items() if k not in IDW})
for r in gun:
    aid=r['AmmunitionId'];assert {x['UnitId'] for x in WA.values() if x['AmmunitionId']==aid}=={ZBD20}
    src=A[bmhe] if A[aid]['HUDName'].endswith('HE') else A[bmap]
    f={k:copy.deepcopy(v) for k,v in src.items() if k not in ('Id','Name','HUDName','HUDIcon')};f['GroundRange']=he57['GroundRange']
    if src is A[bmhe]:f.update(HealthAOERadius=he57['HealthAOERadius'],StressAOERadius=he57['StressAOERadius'],IgnoreCover=he57['IgnoreCover'])
    g.put('AmmunitionsJson',aid,f)
aps=t['AbilitiesJson'][82];assert aps['IsAPS'] and aps['Name']=='APS IronFist NoModel'
g.add('UnitAbilitiesJson',next(iter(t['UnitAbilitiesJson'].values())),{'UnitId':ZBD20,'AbilityId':82})
receipt['changes']['ZBD-20'].update(gun={'weapon':'Bushmaster II profile','he':{k:A[[r for r in gun if A[r['AmmunitionId']]['HUDName'].endswith('HE')][0]['AmmunitionId']][k] for k in ('Damage','HealthAOERadius','IgnoreCover','GroundRange','LowAltRange')}},aps='Iron Fist (2 charges)',cost=175)
# ---- recon copies
def clone_unit(parent,fields):
    uid=max(U)+1;assert uid not in U
    d=copy.deepcopy(U[parent]);d.pop('Id');d.update(fields);g.put('Units',uid,d);defs={}
    for table,field,target in [('UnitArmorsJson','ArmorId','ArmorsJson'),('UnitPropulsionsJson','MobilityId','MobilityJson'),('UnitAbilitiesJson','AbilityId','AbilitiesJson')]:
        for r in rows(table,parent):
            if (target,r[field]) not in defs:defs[target,r[field]]=g.add(target,t[target][r[field]])
            g.add(table,r,{'UnitId':uid,field:defs[target,r[field]]})
    for table in ['TurretUnitsJson','WeaponAmmunitionsJson','SensorUnitsJson']:
        for r in rows(table,parent):g.add(table,r,{'UnitId':uid})
    for mod in rows('ModificationsJson',parent):
        opts=sorted([o for o in t['OptionsJson'].values() if o['ModificationId']==mod['Id'] and not o.get('ReplaceUnitId')],key=lambda o:(o['Order'],o['Id']))
        if not opts:continue
        mid=g.add('ModificationsJson',mod,{'UnitId':uid})
        for order,o in enumerate(opts):
            f={'ModificationId':mid,'Order':order}
            for key,target in [('ArmorId','ArmorsJson'),('MobilityId','MobilityJson'),('Ability1Id','AbilitiesJson'),('Ability2Id','AbilitiesJson'),('Ability3Id','AbilitiesJson')]:
                if (target,o[key]) in defs:f[key]=defs[target,o[key]]
            g.add('OptionsJson',o,f)
    return uid
RECON=[(ZBD04A,'ZBD-04A Recon',18,5,10),(ZBD20,'ZBD-20 Recon',18,3,5),(ZBD03,'ZBD-03 Recon',17,3,5),(ZBD86,'ZBD-86 Recon',19,3,5),(ZBD86,'ZBD-86 Recon',20,3,5)]
receipt['recon']=[]
for parent,name,sid,sensor,extra in RECON:
    uid=clone_unit(parent,{'HUDName':name,'CategoryType':0,'Cost':U[parent]['Cost']+extra})
    src=next(r for r in SA.values() if r['UnitId']==parent)
    g.add('SpecializationAvailabilitiesJson',src,{'UnitId':uid,'SpecializationId':sid})
    for su in rows('SensorUnitsJson',uid):g.put('SensorUnitsJson',su['Id'],{'SensorId':sensor})
    spec['assignments'][str(uid)]=[sid];spec['recon_variants'].append({'unit':uid,'parent':parent,'name':name,'specs':[sid]})
    receipt['recon'].append({'unit':uid,'name':name,'spec':sid,'optics':t['SensorsJson'][sensor]['Name'],'cost':U[uid]['Cost']})
# ---- checks
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(armof(ZTZ99)['KinArmorFront']==750,'ZTZ-99 750')
ok(mobof(ZBD04)['MaxSpeedRoad']>mobof(ZBD04A)['MaxSpeedRoad'],'ZBD-04 faster than 04A')
ok(armof(ZBD04A)['HeatArmorFront']>armof(ZBD04)['HeatArmorFront'],'04A heavier')
for r in receipt['recon']:
    uid=r['unit'];ok(U[uid]['CategoryType']==0 and sorted(x['SpecializationId'] for x in SA.values() if x['UnitId']==uid)==[r['spec']],('recon',uid))
    ok(U[uid]['Name']==U[next(x for x in RECON if x[1]==r['name'])[0]]['Name'],('model name kept',uid))
for uid,u in before['Units'].items():
    if u.get('CountryId')!=4:ok(t['Units'][uid]==u,('non-China unit changed',uid))
for tab in t:
    for key,row in before[tab].items():
        if key in native[tab]:ok(t[tab].get(key)==row,('vanilla row changed',tab,key))
receipt['checks']=checks
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save('UserData/FreedomArrow/pla-spec-assignments.json',spec);save('UserData/FreedomArrow/pla-0.8.0-dev.3.json',receipt)
(ROOT/'tools/pla-specs/0.8.0-dev.3-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(receipt,indent=1,ensure_ascii=False)[:5000])

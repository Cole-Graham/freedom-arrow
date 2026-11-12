"""Independent structural and numeric checks for the packaged PLA31 batch."""
import argparse,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from pipeline.tables import FIELD_TO_FILE
p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
t={}
with zipfile.ZipFile(a.package) as z:
 for tab,fn in FIELD_TO_FILE.items():
  t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())}
  for k,v in json.loads(z.read('UserData/FreedomArrow/constants/'+fn)).items():
   if v is None:t[tab].pop(int(k),None)
   else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
 models=json.loads(z.read('UserData/FAModels/models.json'))
 checks=0
 def ok(value,msg):
  global checks
  assert value,msg;checks+=1
 for tab,field,target in [('UnitArmorsJson','UnitId','Units'),('UnitArmorsJson','ArmorId','ArmorsJson'),('UnitPropulsionsJson','UnitId','Units'),('UnitPropulsionsJson','MobilityId','MobilityJson'),('UnitAbilitiesJson','UnitId','Units'),('UnitAbilitiesJson','AbilityId','AbilitiesJson'),('SensorUnitsJson','UnitId','Units'),('SensorUnitsJson','SensorId','SensorsJson'),('TurretUnitsJson','UnitId','Units'),('TurretUnitsJson','TurretId','TurretsJson'),('TurretWeaponsJson','TurretId','TurretsJson'),('TurretWeaponsJson','WeaponId','WeaponsJson'),('WeaponAmmunitionsJson','UnitId','Units'),('WeaponAmmunitionsJson','WeaponId','WeaponsJson'),('WeaponAmmunitionsJson','AmmunitionId','AmmunitionsJson'),('SpecializationAvailabilitiesJson','UnitId','Units'),('SpecializationAvailabilitiesJson','SpecializationId','SpecializationsJson'),('TransportAvailabilitiesJson','UnitId','Units'),('TransportAvailabilitiesJson','SpecializationAvailabilityId','SpecializationAvailabilitiesJson')]:
  for r in t[tab].values():ok(r[field] in t[target],(tab,r['Id'],field,r[field]))
 def ammo(uid):return [t['AmmunitionsJson'][r['AmmunitionId']] for r in t['WeaponAmmunitionsJson'].values() if r['UnitId']==uid]
 def rounds(uid):return sum(r['Quantity']*t['AmmunitionsJson'][r['AmmunitionId']]['HUDMultiplier'] for r in t['WeaponAmmunitionsJson'].values() if r['UnitId']==uid)
 ok(rounds(910)==rounds(1049)==8,'TOR inventory')
 for uid,donor in [(910,28),(1049,77)]:
  new=ammo(uid)[0];native=t['AmmunitionsJson'][donor]
  ok(all(new[k]==v for k,v in native.items() if k not in ['Id','Name','HUDName']),'TOR numeric donor drift')
 for uid in [906,1080,1059]:
  ke=next(r for r in ammo(uid) if r['ArmorTargeted']==1)
  ok(ke['PenetrationAtMinRange']==ke['PenetrationAtGroundRange']+25,'KE close bonus')
 ok(ammo(1233)[0]['Seeker']==50,'HQ9B FNF');ok(ammo(1234)[0]['Seeker']==100,'HQ9A SA')
 for uid in [1233,1234]:ok(ammo(uid)[0]['LowAltRange']==t['AmmunitionsJson'][154]['LowAltRange'] and ammo(uid)[0]['HighAltRange']==t['AmmunitionsJson'][154]['HighAltRange'],'GEM+ ranges')
 ok(ammo(911)[0]['Seeker']==50 and ammo(911)[0]['HighAltRange']==t['AmmunitionsJson'][220]['HighAltRange'],'S400 profile')
 missiles=[(am['HUDName'],r['Quantity']) for r in t['WeaponAmmunitionsJson'].values() if r['UnitId']==1056 for am in [t['AmmunitionsJson'][r['AmmunitionId']]] if am['HUDName'] in ['HJ-10','ABZ-13 anti-personnel']]
 ok(sorted(missiles)==[('ABZ-13 anti-personnel',4),('HJ-10',2)],'ZBD missile counts')
 ok(any(t['AbilitiesJson'][r['AbilityId']]['IsLaserDesignator'] for r in t['UnitAbilitiesJson'].values() if r['UnitId']==1056),'ZBD laser')
 ok(not ammo(1085),'recon drone must be unarmed')
 for name,entry in models.items():
  for field in ['file','battle']:
   if entry.get(field):ok('UserData/FAModels/'+entry[field] in z.namelist(),('missing model',name,entry[field]))
 for uid in [1227,1228,1229,1230,1231]:ok(not ammo(uid),('cargo armed',uid))
 for sid in range(17,22):ok(any(r['UnitId']==1227 and r['SpecializationId']==sid for r in t['SpecializationAvailabilitiesJson'].values()),('Mi8 spec missing',sid))
 for r in t['SpecializationAvailabilitiesJson'].values():
  if r['UnitId']==1032:ok(sum(r['MaxAvailabilityXp'+str(i)] for i in range(4))==1,'DF31 availability')
 print(json.dumps({'checks':checks,'passed':True,'native_verified':False},indent=2))

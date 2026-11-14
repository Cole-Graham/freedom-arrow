"""Independent structural and numeric checks for the packaged PLA31+ batches."""
import argparse,json,re,sys,zipfile
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from pipeline.tables import FIELD_TO_FILE
p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
t={};rowrule=[]
with zipfile.ZipFile(a.package) as z:
 for tab,fn in FIELD_TO_FILE.items():
  t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())}
  fields=set(next(iter(t[tab].values())))-{'Id'}
  for k,v in json.loads(z.read('UserData/FreedomArrow/constants/'+fn)).items():
   # RowPlanner rule: a new row has exactly the table's fields; a patch uses only existing fields. One violation and the game loads vanilla (Builds33-39, BaseSquadSize).
   if v is not None and ((int(k) not in t[tab] and set(v)!=fields) or (int(k) in t[tab] and set(v)-set(t[tab][int(k)]))):rowrule.append((tab,k,sorted(set(v)^fields)[:3]))
   if v is None:t[tab].pop(int(k),None)
   else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
 models=json.loads(z.read('UserData/FAModels/models.json'))
 whole=json.loads(z.read('UserData/FreedomArrow/pla-package-manifest.json'));build=whole['build']
 checks=0
 def ok(value,msg):
  global checks
  assert value,msg;checks+=1
 # Same identity rule the runtime enforces at game start (BuildIdentity.ResolveLabel); Builds34-37 shipped the Build33 DLL and failed it.
 dll=z.read('Mods/FreedomArrow.Runtime.dll');compiled=[dll[m.end():m.end()+m.group(2)[0]].decode() for m in re.finditer(rb'(\x08PLA TEST|\x0dFreedom Arrow)(.)',dll)]
 version=json.loads(z.read('UserData/FreedomArrow/channel.json'))['package_version']
 release=whole['label'].startswith('Freedom Arrow ')  # 0.8 live line: version string, build stays the internal counter
 ok(compiled==[version] and (release or version==str(build)),('runtime DLL compiled version',compiled,build,version))
 ok(version==(version if release else str(build)),'channel package_version')
 ok(json.loads(z.read('mod.json'))['version']==version and whole['label']==('Freedom Arrow '+version if release else 'PLA TEST Build '+str(build)),'mod.json version / package label')
 ok(not rowrule,('constants break the runtime row rule',len(rowrule),rowrule[:3]))
 for tab,rs in t.items():
  for key,r in rs.items():ok(key==r['Id'],('row identity mismatch',tab,key,r['Id']))
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
  # Osama 13 Nov 18:0x PST (0.8.0-dev.65, build 133): ZTL-191, VT-5, ZTQ-15 AP "500-550" = 550 close, 500 at range.
  # Osama 13 Nov 20:1x PST (0.8.0-dev.78, build 146): "475-525 pen" = 525 close, 475 at range.
  if build>=146 and uid in (906,1080):ok((ke['PenetrationAtMinRange'],ke['PenetrationAtGroundRange'])==(525.0,475.0),'AP 475-525')
  elif build>=133 and uid in (906,1080):ok((ke['PenetrationAtMinRange'],ke['PenetrationAtGroundRange'])==(550.0,500.0),'AP 500-550')
  else:ok(ke['PenetrationAtMinRange']==ke['PenetrationAtGroundRange']+25,'KE close bonus')
 ok(ammo(1233)[0]['Seeker']==50,'HQ9B FNF');ok(ammo(1234)[0]['Seeker']==100,'HQ9A SA')
 for uid in [1233,1234]:ok(ammo(uid)[0]['LowAltRange']==t['AmmunitionsJson'][154]['LowAltRange'] and ammo(uid)[0]['HighAltRange']==t['AmmunitionsJson'][154]['HighAltRange'],'GEM+ ranges')
 ok(ammo(911)[0]['Seeker']==50 and ammo(911)[0]['HighAltRange']==t['AmmunitionsJson'][220]['HighAltRange'],'S400 profile')
 missiles=[(am['HUDName'],r['Quantity']) for r in t['WeaponAmmunitionsJson'].values() if r['UnitId']==1056 for am in [t['AmmunitionsJson'][r['AmmunitionId']]] if am['HUDName'] in ['HJ-10','HJ-16','ABZ-13 anti-personnel']]
 ok(sorted(missiles) in ([('ABZ-13 anti-personnel',4),('HJ-10',2)],[('ABZ-13 anti-personnel',4),('HJ-16',2)]),'ZBD missile counts (HJ-16 name since dev.55, Osama 13 Nov)')
 ok(any(t['AbilitiesJson'][r['AbilityId']]['IsLaserDesignator'] for r in t['UnitAbilitiesJson'].values() if r['UnitId']==1056),'ZBD laser')
 ok(not ammo(1085),'recon drone must be unarmed')
 for name,entry in models.items():
  for field in ['file','battle']:
   if entry.get(field):ok('UserData/FAModels/'+entry[field] in z.namelist(),('missing model',name,entry[field]))
 # Build43: Lynx ATV (1228) carries the M1301 ISV weapons (Osama 12 Nov); the other carriers stay unarmed.
 for uid in [1227,1229,1230,1231]+([1228] if build<43 else []):ok(not ammo(uid),('cargo armed',uid))
 for sid in range(17,22):ok(any(r['UnitId']==1227 and r['SpecializationId']==sid for r in t['SpecializationAvailabilitiesJson'].values()),('Mi8 spec missing',sid))
 for r in t['SpecializationAvailabilitiesJson'].values():
  if r['UnitId']==1032:ok(sum(r['MaxAvailabilityXp'+str(i)] for i in range(4))==1,'DF31 availability')
 if build>=33:
  for uid in [1058,1230]:ok(t['Units'][uid]['InfantrySlots']==12,('CSK181 capacity',uid))
  for uid in [1049,943,974,1063,1054]+([918] if build<144 else [])+([961] if build<50 else []):ok(any(r['UnitId']==uid and r['SpecializationId']==20 for r in t['SpecializationAvailabilitiesJson'].values()),('PLAN move',uid))
  # Build144 (0.8.0-dev.76): JH-7A removed for now (Osama 13 Nov).
  if build>=144:ok(not t['Units'][918]['DisplayInArmory'] and not any(r['UnitId']==918 for r in t['SpecializationAvailabilitiesJson'].values()),('JH-7A removed',918))
  # Build41: CSK-181 recon card removed; transport 1230 stays
  for uid in [909,1230]+([1058] if build<41 else []):ok(any(r['UnitId']==uid and r['SpecializationId']==19 for r in t['SpecializationAvailabilitiesJson'].values()),('Rocket move',uid))
 if build>=36:
  for uid in [1084,1085,1086,1105]:ok(not t['Units'][uid]['DisplayInArmory'] and not any(r['UnitId']==uid for r in t['SpecializationAvailabilitiesJson'].values()),('drone removed',uid))
  n=t['AmmunitionsJson'][2010399];k=t['AmmunitionsJson'][340]
  # Osama 13 Nov 14:47-14:52 PST (0.8.0-dev.50, build 118): DF-31A blast 500 m as shown in game (250 data), stress/overpressure scaled x250/350.
  blast=['HealthAOERadius','OverpressureRadius','StressAOERadius'] if build<118 else []
  ok(all(n[f]==k[f] for f in ['Damage','FXPreset','AudioPreset']+blast) and n['TrajectoryType']==300,'DF31 nuclear Kinzhal warhead, ballistic flight')
  if build>=118:ok((n['HealthAOERadius'],n['StressAOERadius'],n['OverpressureRadius'])==(250.0,286,125),'DF31 500 m displayed blast')
 if build>=34:
  hmv=t['Units'][1235];ok(hmv['HUDName']=='Shaanxi HMV3' and hmv['ModelFileName']=='US_HEMTT' and hmv['CountryId']==4,'HMV3 identity')
  ok(sorted(r['SpecializationId'] for r in t['SpecializationAvailabilitiesJson'].values() if r['UnitId']==1235)==([18,19,21] if build<46 else [17,18,19,20,21]),'HMV3 specs')  # Build46: every spec
  if build<46:ok(not ammo(1235) and not any(r['UnitId']==1235 for r in t['TurretUnitsJson'].values()),'HMV3 unarmed')  # Build46: HEMTT mounts/options so the model draws
 if build>=32:
  links=defaultdict(list)
  spec_file=json.loads(z.read('UserData/FreedomArrow/pla-spec-assignments.json'));assignments=spec_file['assignments']
  shared=spec_file.get('shared_transports') or {'1227':list(range(17,22))}
  for r in t['SpecializationAvailabilitiesJson'].values():links[r['UnitId']].append(r['SpecializationId'])
  for uid,expected in assignments.items():
   uid=int(uid);ok(sorted(links[uid])==sorted(expected),('assignment metadata',uid))
   if expected:ok(sorted(expected)==sorted(shared[str(uid)]) if str(uid) in shared else len(expected)==1,('single spec',uid))
  for r in t['TransportAvailabilitiesJson'].values():
   sid=t['SpecializationAvailabilitiesJson'][r['SpecializationAvailabilityId']]['SpecializationId']
   if sid>=17:ok(sid in links[r['UnitId']],('carrier crosses spec',r['Id']))
 # Runtime "Field type mismatch" rule (Build56): patched fields keep the vanilla JSON type; no null where vanilla never has null.
 for tab,fn in FIELD_TO_FILE.items():
  vt={}
  for r in json.loads((a.vanilla/(tab+'.json')).read_text()):
   for k2,v2 in r.items():vt.setdefault(k2,set()).add(type(v2).__name__)
  for key,row in json.loads(z.read('UserData/FreedomArrow/constants/'+fn)).items():
   if row is None:continue
   for f2,v2 in row.items():
    if f2 in vt:ok(type(v2).__name__ in vt[f2] or (type(v2).__name__ in('int','float') and vt[f2]&{'int','float'} and 'bool' not in vt[f2]),('field type mismatch',tab,key,f2,type(v2).__name__))
 result={'build':build,'checks':checks,'passed':True,'native_verified':False}
 (ROOT/f'tools/pla-specs/build{build}-regression-checks.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))

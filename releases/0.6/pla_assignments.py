"""Assign the complete PLA equipment draft; retain rigging fixtures in Test."""
import copy,json

def apply(root,t,patches,models,native_ids):
 c=json.loads((root.parents[1]/'tools/pla-specs/spec-assignment-contract.json').read_text())
 nextrow=max(i for rs in t.values() for i in rs)+1;nextoption=max(t['OptionsJson'])+1
 def put(table,uid,fields):
  t[table].setdefault(uid,{'Id':uid}).update(fields);patches[table].setdefault(str(uid),{}).update(fields)
 def clone(table,rid,fields):
  nonlocal nextrow,nextoption
  uid=nextoption if table=='OptionsJson' else nextrow
  if table=='OptionsJson':nextoption+=1;assert uid<=32767
  else:nextrow+=1
  row=copy.deepcopy(t[table][rid]);row.pop('Id');row.update(fields);put(table,uid,row);return uid
 def remove(table,uid):
  t[table].pop(uid)
  if uid in native_ids[table]:patches[table][str(uid)]=None
  else:patches[table].pop(str(uid),None)
 # YJ-18 is a ground cruise-launcher draft, using the native Iskander-K baseline.
 uid=1129;parent=226
 mids={r['Id'] for r in t['ModificationsJson'].values() if r['UnitId']==uid}
 for table in ['UnitArmorsJson','UnitPropulsionsJson','UnitAbilitiesJson','SensorUnitsJson','TurretUnitsJson','WeaponAmmunitionsJson','SquadMembersJson','SquadWeaponsJson','ModificationsJson']:
  for row in list(t[table].values()):
   if row['UnitId']==uid:remove(table,row['Id'])
 for row in list(t['OptionsJson'].values()):
  if row['ModificationId'] in mids:remove('OptionsJson',row['Id'])
 u=copy.deepcopy(t['Units'][parent]);u.pop('Id');u.update(Name='PLA Catalogue YJ-18 ship launcher',HUDName='YJ-18',CountryId=4,DisplayInArmory=True,ContentMembership=-1,IsUnitModification=False,Description='Ground cruise missile launcher draft. Native Iskander-K vehicle, two cruise missiles and donor performance; final YJ-18 art, missile statistics and loadout await design.');put('Units',uid,u)
 for table,field,target in [('UnitArmorsJson','ArmorId','ArmorsJson'),('UnitPropulsionsJson','MobilityId','MobilityJson'),('UnitAbilitiesJson','AbilityId','AbilitiesJson')]:
  for row in list(t[table].values()):
   if row['UnitId']==parent:clone(table,row['Id'],{'UnitId':uid,field:clone(target,row[field],{})})
 for row in list(t['SensorUnitsJson'].values()):
  if row['UnitId']==parent:clone('SensorUnitsJson',row['Id'],{'UnitId':uid})
 clone('TurretUnitsJson',562,{'UnitId':uid});clone('WeaponAmmunitionsJson',935,{'UnitId':uid})
 mid=clone('ModificationsJson',201,{'UnitId':uid});clone('OptionsJson',528,{'ModificationId':mid,'IsDefault':True,'Order':0,'Name':'YJ-18 ground cruise draft','ConcatenateWithUnitName':None})
 for excluded in c['excluded_units']:put('Units',excluded,{'DisplayInArmory':False})
 pools=list(t['SpecializationAvailabilitiesJson'].values());templates={}
 for r in pools:
  if r['SpecializationId'] in range(17,23):templates.setdefault(r['UnitId'],r.copy())
 assignments={}
 for r in pools:
  if r['SpecializationId'] in range(17,23):assignments.setdefault(r['UnitId'],set()).add(r['SpecializationId'])
 for spec,ids in c['assign_unassigned'].items():
  for uid in ids:
   assert assignments.get(uid,set())<= {22},('not unassigned',uid)
   assignments[uid]={int(spec)}
 for uid,specs in c['shared_transports'].items():assignments[int(uid)]=set(specs)
 for uid in c['excluded_units']:assignments.pop(uid,None)
 # Explicit gunships must never be offered as troop transports by a donor capacity.
 for uid in c['gunships']:put('Units',uid,{'Role':73,'InfantrySlots':0})
 recon=[]
 for parent in c['gunships']:
  uid=max(t['Units'])+1;u=copy.deepcopy(t['Units'][parent]);u.pop('Id');u.update(Name='PLA Recon '+u['HUDName'],HUDName=u['HUDName']+' Recon',CategoryType=0,Role=73,InfantrySlots=0,Description='Separate recon gunship design. Inherits the gunship donor weapons, cost and sensor baseline; final optics, loadouts and price await unit design.');put('Units',uid,u)
  defs={}
  for table,field,target in [('UnitArmorsJson','ArmorId','ArmorsJson'),('UnitPropulsionsJson','MobilityId','MobilityJson'),('UnitAbilitiesJson','AbilityId','AbilitiesJson')]:
   for row in list(t[table].values()):
    if row['UnitId']!=parent:continue
    key=(target,row[field])
    if key not in defs:defs[key]=clone(target,row[field],{})
    clone(table,row['Id'],{'UnitId':uid,field:defs[key]})
  for table in ['TurretUnitsJson','WeaponAmmunitionsJson','SensorUnitsJson']:
   for row in list(t[table].values()):
    if row['UnitId']==parent:clone(table,row['Id'],{'UnitId':uid})
  for mod in list(t['ModificationsJson'].values()):
   if mod['UnitId']!=parent:continue
   opts=[o for o in t['OptionsJson'].values() if o['ModificationId']==mod['Id'] and not o.get('ReplaceUnitId')]
   if not opts:continue
   mid=clone('ModificationsJson',mod['Id'],{'UnitId':uid})
   for o in opts:
    fields={'ModificationId':mid}
    if o.get('ReplaceUnitName'):fields['ReplaceUnitName']=u['HUDName']
    for key,target in [('ArmorId','ArmorsJson'),('MobilityId','MobilityJson'),('Ability1Id','AbilitiesJson'),('Ability2Id','AbilitiesJson'),('Ability3Id','AbilitiesJson')]:
     if (target,o.get(key)) in defs:fields[key]=defs[target,o[key]]
    clone('OptionsJson',o['Id'],fields)
  name=t['Units'][parent]['Name']
  if name in models:models[u['Name']]=copy.deepcopy(models[name])
  assignments[uid]=assignments[parent].copy();templates[uid]=templates[parent]
  recon.append({'unit':uid,'parent':parent,'old_plan_key':'PLAN-'+str(parent)+'-RECON','name':u['HUDName'],'specs':sorted(assignments[uid])})
 # Rebuild country 4 only, with complete, capacity-checked troop transport links.
 oldids={r['Id'] for r in pools if r['SpecializationId'] in range(17,23)}
 for r in list(t['TransportAvailabilitiesJson'].values()):
  if r['SpecializationAvailabilityId'] in oldids:remove('TransportAvailabilitiesJson',r['Id'])
 for r in pools:
  if r['Id'] in oldids:remove('SpecializationAvailabilitiesJson',r['Id'])
 fallback=next(iter(t['SpecializationAvailabilitiesJson']))
 for uid,u in list(t['Units'].items()):
  if u['CountryId']!=4 or not u['DisplayInArmory']:continue
  assert uid in assignments,('missing assignment',uid,u['HUDName'])
  if u['Type']!=2:assert assignments[uid] and 22 not in assignments[uid],('equipment left in Test',uid)
  template=templates.get(uid, t['SpecializationAvailabilitiesJson'][fallback])
  for spec in sorted(assignments[uid]):
   fields={k:v for k,v in template.items() if k!='Id'};fields.update(UnitId=uid,SpecializationId=spec);pool=clone('SpecializationAvailabilitiesJson',fallback,fields)
   if u['Type']==2:
    men=sum(r['UnitId']==uid for r in t['SquadMembersJson'].values())
    for carrier in c['carriers'][str(spec)]:
     v=t['Units'][carrier];assert v['CountryId']==4 and v['Type'] in (4,8) and not carrier in c['gunships']
     if v['InfantrySlots']>=men:clone('TransportAvailabilitiesJson',next(iter(t['TransportAvailabilitiesJson'])),{'SpecializationAvailabilityId':pool,'UnitId':carrier})
  if u['Type']==2 and uid in c['test_infantry']:assert assignments[uid]=={22}
 receipt={'build':13,'assignments':{str(k):sorted(v) for k,v in assignments.items()},'excluded_units':c['excluded_units'],'yj18':{'unit':1129,'parent':226,'weapon':317,'ammo':219,'quantity':2,'prototype':True},'recon_variants':recon,'shared_transports':c['shared_transports'],'carriers':c['carriers'],'test_infantry':c['test_infantry'],'pool_counts':{str(i):sum(r['SpecializationId']==i for r in t['SpecializationAvailabilitiesJson'].values()) for i in range(17,23)},'native_verified':False,'recon_stats':'Inherited gunship weapons, cost and sensors; no speculative recon bonus.'}
 (root/'source/UserData/FreedomArrow/pla-spec-assignments.json').write_text(json.dumps(receipt,indent=2)+'\n')
 return receipt

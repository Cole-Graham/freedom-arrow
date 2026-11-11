"""Create named stand-ins for each model-link/description row, preserving existing roles."""
import copy,json,re

def apply(root,t,patches,bodies,weapons,models):
 entries=json.loads((root.parents[1]/'tools/pla-specs/model-sheet-entries.json').read_text());before=copy.deepcopy(t);nextrow=max(i for rs in t.values() for i in rs)+1;nextunit=max(t['Units'])+1;nextoption=max(t['OptionsJson'])+1
 def put(table,uid,fields):t[table].setdefault(uid,{'Id':uid}).update(fields);patches[table].setdefault(str(uid),{}).update(fields)
 def clone(table,rid,fields):
  nonlocal nextrow,nextoption
  uid=nextoption if table=='OptionsJson' else nextrow
  if table=='OptionsJson':nextoption+=1;assert uid<=32767
  else:nextrow+=1
  row=copy.deepcopy(t[table][rid]);row.pop('Id');row.update(fields);put(table,uid,row);return uid
 def norm(s):return re.sub('[^a-z0-9]','',s.lower().replace('pla ',''))
 byname={norm(u['HUDName']):i for i,u in t['Units'].items() if u['CountryId']==4 and i<985}
 aliases={'J-8I / J-8A':975,'Chinese Soldier Special Forces — tiger-studio':1012,'J-35 — four paint package':921,'J-20 — alternate seller package':915}
 bodyby={x['unitId']:x for x in bodies};rows=[];newids=[];bodyids=[];row_targets={};same_platform={114:68,102:72,104:73}
 def donor(e):
  n=e['name'].lower();cat=e['category']
  if cat=='Naval':return 321
  if cat=='Infantry / weapons':return 1025 if 'qjy' in n else 1010
  if cat=='AA':return 909 if any(s in n for s in ['pgz','pgl','jrvg']) else 910
  if cat=='Artillery':return 926 if 'pll' in n else 907 if any(s in n for s in ['pcl','plz','sh-15']) else 908
  if cat=='Air':return 914 if any(s in n for s in ['z-','cr-','ar-2000']) and not n.startswith('wz-') else 928 if n.startswith(('y-','kj-','kq-')) else 972 if any(s in n for s in ['uav','wz-','jiutian']) else 917
  if any(s in n for s in ['hj-','aft-','ctl-']):return 936
  if 'ptl' in n or 'ztl' in n:return 938
  if any(s in n for s in ['ztz','vt-','tank','type 59','type 80','wz-1224']):return 905
  if any(s in n for s in ['zbd','vn17','vn20','type 86']):return 902
  if any(s in n for s in ['csk','vn3','vp4']):return 209 if 'vn3' in n else 900
  return 962
 for e in entries:
  uid=row_targets.get(same_platform.get(e['sheet_row']),aliases.get(e['name'],byname.get(norm(e['name']))));created=uid is None;parent=uid if uid is not None else donor(e)
  if e['name']=='ZBD-04':parent=902
  if e['name']=='J-10CE':parent=917
  if created:
   uid=nextunit;nextunit+=1;newids.append(uid);u=copy.deepcopy(t['Units'][parent]);u.pop('Id');u.update(Name='PLA Catalogue '+e['name'],HUDName=e['name'],CountryId=4,DisplayInArmory=True,ContentMembership=-1,IsUnitModification=False,Description='Named model-list stand-in. Donor '+str(parent)+': '+t['Units'][parent]['HUDName']+'. Model link/ownership does not establish final weapons, statistics or behavior.');put('Units',uid,u)
   definitions={}
   for table,field,target in [('UnitArmorsJson','ArmorId','ArmorsJson'),('UnitPropulsionsJson','MobilityId','MobilityJson'),('UnitAbilitiesJson','AbilityId','AbilitiesJson')]:
    for row in list(t[table].values()):
     if row['UnitId']!=parent:continue
     key=(target,row[field])
     if key not in definitions:definitions[key]=clone(target,row[field],{})
     clone(table,row['Id'],{'UnitId':uid,field:definitions[key]})
   for table in ['TurretUnitsJson','WeaponAmmunitionsJson','SensorUnitsJson','SquadMembersJson','SquadWeaponsJson']:
    for row in list(t[table].values()):
     if row['UnitId']==parent:clone(table,row['Id'],{'UnitId':uid})
   for mod in list(t['ModificationsJson'].values()):
    if mod['UnitId']!=parent:continue
    opts=[o for o in t['OptionsJson'].values() if o['ModificationId']==mod['Id'] and not o.get('ReplaceUnitId')]
    if not opts:continue
    mid=clone('ModificationsJson',mod['Id'],{'UnitId':uid})
    for order,o in enumerate(sorted(opts,key=lambda o:(o['Order'],o['Id']))):
     fields={'ModificationId':mid,'Order':order}
     for key,target in [('ArmorId','ArmorsJson'),('MobilityId','MobilityJson'),('Ability1Id','AbilitiesJson'),('Ability2Id','AbilitiesJson'),('Ability3Id','AbilitiesJson')]:
      if (target,o[key]) in definitions:fields[key]=definitions[target,o[key]]
     if o.get('ReplaceUnitName'):fields['ReplaceUnitName']=e['name']
     clone('OptionsJson',o['Id'],fields)
   template=next((r for r in t['SpecializationAvailabilitiesJson'].values() if r['UnitId']==parent),next(iter(t['SpecializationAvailabilitiesJson'].values())))
   pool=clone('SpecializationAvailabilitiesJson',template['Id'],{'UnitId':uid,'SpecializationId':22})
   if parent in bodyby:
    bodies.append({**copy.deepcopy(bodyby[parent]),'unitId':uid});bodyids.append(uid);weapons.extend({**copy.deepcopy(w),'unitId':uid} for w in list(weapons) if w['unitId']==parent)
   if t['Units'][uid]['Type']==2:
    count=sum(m['UnitId']==uid for m in t['SquadMembersJson'].values())
    for carrier in [900,902,903,914,962,979]:
     if t['Units'][carrier]['InfantrySlots']>=count:clone('TransportAvailabilitiesJson',next(iter(t['TransportAvailabilitiesJson'])),{'SpecializationAvailabilityId':pool,'UnitId':carrier})
   # An existing approved family asset is an explicit reusable visual, not an exact-new-model claim.
   if e['name'] in ['ZBD-04','J-10CE','J-35'] or e['category']=='Infantry / weapons':
    if t['Units'][parent]['Name'] in models:models[t['Units'][uid]['Name']]=copy.deepcopy(models[t['Units'][parent]['Name']])
  elif e['name']=='J-8I / J-8A':put('Units',uid,{'HUDName':e['name']})
  if not any(r['UnitId']==uid for r in t['SpecializationAvailabilitiesJson'].values()):
   template=next(iter(t['SpecializationAvailabilitiesJson'].values()));clone('SpecializationAvailabilitiesJson',template['Id'],{'UnitId':uid,'SpecializationId':22})
  row_targets[e['sheet_row']]=uid
  rows.append({**e,'unit':uid,'parent':parent,'new_card':created,'native_model':t['Units'][uid]['ModelFileName'],'custom_model':models.get(t['Units'][uid]['Name']),'implementation':'Existing card' if not created else 'Named stand-in','specs':sorted(r['SpecializationId'] for r in t['SpecializationAvailabilitiesJson'].values() if r['UnitId']==uid)})
 # Explicit visual reuse from the human-edited sheet, without changing weapon statistics.
 put('Units',934,{'ModelFileName':t['Units'][11]['ModelFileName'],'PortraitFileName':t['Units'][11]['PortraitFileName']});models.pop(t['Units'][934]['Name'],None)
 receipt={'entries':rows,'entry_count':len(rows),'new_units':newids,'new_body_units':bodyids,'excluded_no_model':71,'native_verified':False}
 (root/'source/UserData/FreedomArrow/pla-model-catalogue.json').write_text(json.dumps(receipt,indent=2)+'\n')
 return receipt

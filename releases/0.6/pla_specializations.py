"""Five PLA branch pools and donor-based infantry prototypes, isolated from live."""
import copy,json

def apply(root,t,patches,body_rules,weapon_rules,native_ids):
 c=json.loads((root/'pla-specializations-contract.json').read_text());before=copy.deepcopy(t)
 nextid=max(i for rows in t.values() for i in rows)+1
 def put(table,uid,fields):
  t[table].setdefault(uid,{'Id':uid}).update(fields);patches[table].setdefault(str(uid),{}).update(fields)
 def clone(table,uid,fields):
  nonlocal nextid
  new=nextid;nextid+=1;row=copy.deepcopy(t[table][uid]);row.pop('Id');row.update(fields);put(table,new,row);return new
 def rows(table,uid):return [r.copy() for r in t[table].values() if r.get('UnitId')==uid]
 def remove(table,uid):
  t[table].pop(uid)
  if uid in native_ids[table]:patches[table][str(uid)]=None
  else:patches[table].pop(str(uid),None)
 def hud(w):return t['WeaponsJson'][w].get('HUDName','') or ''
 def rifle(w):return hud(w).startswith(('AK-','AKM','G36','M4A1','M27')) or hud(w)=='Kord 6P68'
 prototypes=json.loads((root/'source/UserData/FreedomArrow/pla-build.json').read_text())['infantry']['weapons']
 native={name:data['weaponId'] for name,data in prototypes.items()}
 body_by_unit={x['unitId']:x for x in body_rules};rules901=[r for r in weapon_rules if r['unitId']==901]
 native_fields=['UnitArmorsJson','UnitPropulsionsJson','UnitAbilitiesJson','SensorUnitsJson']
 summaries=[]
 for role in c['infantry']:
  uid,parent=role['unit'],role['parent'];assert uid not in t['Units']
  unit=copy.deepcopy(t['Units'][parent]);unit.pop('Id');unit.update(Name='PLA '+role['name'],HUDName=role['name'],CountryId=4,ContentMembership=-1,DisplayInArmory=True,IsUnitModification=False,Description=role['prototype_note']+' Prototype costs and behavior; not final PLA balance.');put('Units',uid,unit)
  ref_parent=118 if uid==1017 else parent
  if uid==1017:put('Units',uid,{k:t['Units'][118][k] for k in ['Role','CategoryType','Stealth','CurrentStealth']})
  # Own default armor/movement/abilities prevent a future unit-only edit affecting its donor.
  for table in native_fields:
   source=ref_parent if table in ['UnitAbilitiesJson','SensorUnitsJson'] else parent
   for link in rows(table,source):
    fields={'UnitId':uid}
    for field,target in [('ArmorId','ArmorsJson'),('MobilityId','MobilityJson'),('AbilityId','AbilitiesJson')]:
     if field in link:fields[field]=clone(target,link[field],{'IsDefault':True})
    clone(table,link['Id'],fields)
  members=sorted(rows('SquadMembersJson',parent),key=lambda r:r['Id']);remap={};ammo_sources={};heavy_sources={}
  heavy={1018:('MRO','PF-97'),1020:('AGS-30','QLZ-04'),1021:('Konkurs','HJ-8'),1022:('Javelin','HJ-12'),1023:('RPG-29','PF-98'),1024:('Igla','HN-6'),1025:('Kord HMG','QJZ-171'),1026:('SV-98','QBU-10')}
  old_weapons={m[k] for m in members for k in ['PrimaryWeaponId','SpecialWeaponId'] if m[k]}
  if uid in heavy:
   match,name=heavy[uid];found=[w for w in old_weapons if match in hud(w)];assert found,(uid,match,[(w,hud(w)) for w in old_weapons])
   for old in found:
    donor=523 if uid==1026 else old
    new=clone('WeaponsJson',donor,{'Name':'PLA Prototype '+name,'HUDName':name});remap[old]=new;heavy_sources[new]=donor
    ammo_sources[new]=[r for r in t['WeaponAmmunitionsJson'].values() if r['WeaponId']==donor and (uid==1026 or r['UnitId']==parent)]
    assert ammo_sources[new],(uid,donor)
  for old in old_weapons:
   if old in remap:continue
   if rifle(old) and uid!=1016:remap[old]=native['QBZ191']
   if uid==1019 and 'Mk 47' in hud(old):remap[old]=native['QLU11']
   if uid==1026 and hud(old)=='SVD':remap[old]=native['QBU191']
   if hud(old).startswith('GP-') and uid!=1016:remap[old]=0
  out=[]
  for i,m in enumerate(members):
   fields={'UnitId':uid,**{k:remap.get(m[k],m[k]) for k in ['PrimaryWeaponId','SpecialWeaponId']}}
   if uid==1014:fields.update(PrimaryWeaponId=native['QTS11'],SpecialWeaponId=native['QTS11_GL'] if i==0 else 0)
   if uid==1017:fields.update(PrimaryWeaponId=native['QBZ191'],SpecialWeaponId=0)
   if uid==1027:fields.update(PrimaryWeaponId=native['QBU191'] if i==0 else native['QBZ191'],SpecialWeaponId=0)
   clone('SquadMembersJson',m['Id'],fields);out.append(fields)
  desired={m[k] for m in out for k in ['PrimaryWeaponId','SpecialWeaponId'] if m[k]}
  sw=next(iter(t['SquadWeaponsJson']));wa=next(iter(t['WeaponAmmunitionsJson']))
  for order,w in enumerate(sorted(desired)):
   clone('SquadWeaponsJson',sw,{'UnitId':uid,'WeaponId':w,'Order':order})
   if w in native.values():source=next(r for r in rows('WeaponAmmunitionsJson',901) if r['WeaponId']==w);source_rows=[source]
   elif w in ammo_sources:
    # Several unrelated native units can share the QBU-10 donor weapon; keep one row per ammo/order.
    source_rows=list({(r['AmmunitionId'],r.get('Order',0)):r for r in ammo_sources[w]}.values())
   else:source_rows=[r for r in rows('WeaponAmmunitionsJson',parent) if r['WeaponId']==w]
   assert source_rows,(uid,w,hud(w))
   for source in source_rows:
    fields={k:v for k,v in source.items() if k!='Id'};fields.update(UnitId=uid,WeaponId=w)
    if w in heavy_sources:
     name=hud(w);fields['AmmunitionId']=clone('AmmunitionsJson',source['AmmunitionId'],{'Name':'PLA Prototype '+name+' '+str(source['AmmunitionId']),'HUDName':name+' (prototype)'})
    clone('WeaponAmmunitionsJson',wa,fields)
  body_rules.append({**copy.deepcopy(body_by_unit[role['body_from']]),'unitId':uid})
  weapon_rules.extend({**copy.deepcopy(r),'unitId':uid} for r in rules901 if r['weaponId'] in desired)
  summaries.append({**role,'men':len(out),'cost':unit['Cost'],'weapons':[{'id':w,'name':hud(w),'primary_carriers':sum(m['PrimaryWeaponId']==w for m in out),'special_carriers':sum(m['SpecialWeaponId']==w for m in out)} for w in sorted(desired)]})
 # Rebuild just the PLA availability graph. RU/US data remains as mergeable donor data.
 oldpools=[r for r in list(t['SpecializationAvailabilitiesJson'].values()) if r['SpecializationId'] in range(17,22)];templates={}
 for r in oldpools:templates.setdefault(r['UnitId'],r.copy())
 oldids={r['Id'] for r in oldpools}
 for r in list(t['TransportAvailabilitiesJson'].values()):
  if r['SpecializationAvailabilityId'] in oldids:remove('TransportAvailabilitiesJson',r['Id'])
 for r in oldpools:remove('SpecializationAvailabilitiesJson',r['Id'])
 assignments={int(k):v['specs'] for k,v in c['existing_units'].items()};assignments.update({r['unit']:r['specs'] for r in c['infantry']})
 # Keep non-core model variants organized too, without inflating planned-role counts.
 for uid,u in before['Units'].items():
  if u['CountryId']==4 and uid not in c['fixture_units']:assert uid in assignments,('unassigned PLA unit',uid,u['Name'])
 role_by_unit={r['unit']:r for r in c['infantry']};transport_only={int(k) for k,v in c['existing_units'].items() if v.get('category')=='Transport'}
 if not c['hide_comparison_squads']:
  for uid in c['fixture_units']:assignments[uid]=[c['test_spec']]
 for uid,specids in assignments.items():
  if uid in transport_only and c['test_spec'] not in specids:continue
  template=templates.get(uid)
  if template is None:
   if uid in role_by_unit:
    parent=role_by_unit[uid]['parent'];template=next(r for r in before['SpecializationAvailabilitiesJson'].values() if r['UnitId']==parent)
   else:
    assert c['test_spec'] in specids,('missing branch template',uid)
    template=next(r for r in before['SpecializationAvailabilitiesJson'].values() if before['Units'][r['UnitId']]['CountryId']==4)
  for specid in specids:
   pool=clone('SpecializationAvailabilitiesJson',template['Id'] if template['Id'] in t['SpecializationAvailabilitiesJson'] else next(iter(t['SpecializationAvailabilitiesJson'])),{**{k:v for k,v in template.items() if k!='Id'},'UnitId':uid,'SpecializationId':specid})
   if t['Units'][uid]['Type']==2:
    count=sum(r['UnitId']==uid for r in t['SquadMembersJson'].values())
    for carrier in c['transports'][str(specid)]:
     if t['Units'][carrier]['InfantrySlots']>=count:
      clone('TransportAvailabilitiesJson',next(iter(t['TransportAvailabilitiesJson'])),{'SpecializationAvailabilityId':pool,'UnitId':carrier})
 for spec in c['specs']:
  if spec['id'] not in t['SpecializationsJson']:
   template=copy.deepcopy(t['SpecializationsJson'][17]);template.pop('Id');template.update(CountryId=4,Name='PLA '+spec['name'],UIName=spec['name'],Icon='FA_CHINA_FLAG',Illustration='FA_CHINA_FLAG');put('SpecializationsJson',spec['id'],template)
  put('SpecializationsJson',spec['id'],{**spec['fields'],'UIDescription':('Unused models and uniform/helmet comparisons. Developer testing pool; not balanced.' if spec['id']==c['test_spec'] else 'PLA '+spec['name']+'. First branch draft; donor-based weapons and provisional5000-point category budget.')})
 if c['hide_comparison_squads']:
  for uid in c['fixture_units']:put('Units',uid,{'DisplayInArmory':False})
 if c['pla_only']:
  for uid,u in list(t['Units'].items()):
   if u['CountryId']!=4:put('Units',uid,{'DisplayInArmory':False})
  for uid,country in list(t['CountriesJson'].items()):put('CountriesJson',uid,{'Hidden':uid!=4})
  for uid,spec in list(t['SpecializationsJson'].items()):put('SpecializationsJson',uid,{'ShowInHangar':spec['CountryId']==4})
 # Only UI flags changed on any original unit; original stats/weapons/skins remain byte-equivalent.
 for table,original in before.items():
  for uid,old in original.items():
   if table in ['SpecializationAvailabilitiesJson','TransportAvailabilitiesJson']:continue
   now=t[table][uid];allowed={'Units':{'DisplayInArmory'},'CountriesJson':{'Hidden'},'SpecializationsJson':{'UIDescription','ShowInHangar',*{k for sp in c['specs'] for k in sp['fields']}}}.get(table,set())
   assert {k for k in old.keys()|now.keys() if old.get(k)!=now.get(k)}<=allowed,(table,uid)
 counts={sp['id']:sum(r['SpecializationId']==sp['id'] for r in t['SpecializationAvailabilitiesJson'].values()) for sp in c['specs']}
 return {'build':c['build'],'pla_only':c['pla_only'],'hidden_fixture_units':c['fixture_units'] if c['hide_comparison_squads'] else [],'test_spec':c['test_spec'],'test_fixture_units':c['fixture_units'],'new_units':[r['unit'] for r in summaries],'new_infantry':summaries,'pool_counts':counts,'existing_units':c['existing_units'],'transports':c['transports'],'existing_combat_stats_unchanged':True,'native_verified':False}

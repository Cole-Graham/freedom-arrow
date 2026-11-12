"""Import the named squad designer rows as fixed in-game squads, without editing designs."""
import copy,json,math
from pla_graph import Graph

def apply(root,t,patches,native_ids,bodies,weapon_rules,assignments):
 c=json.loads((root.parents[1]/'tools/pla-specs/infantry-designer-contract.json').read_text());g=Graph(t,patches,native_ids)
 specs={'Airforce / Airborne':17,'Ground Force / Armored':18,'Rocket Force / Conscripts':19,'Marines / SF':20,'Motorized':21,'Test':22}
 proto=json.loads((root/'source/UserData/FreedomArrow/pla-build.json').read_text())['infantry']['weapons']
 # Native performance analogs, not claims that differently named weapons are identical.
 choices={
  'QBZ-191':(proto['QBZ191']['weaponId'],'primary','RIFLE'), 'QBZ-192':(proto['QBZ191']['weaponId'],'primary','RIFLE'), 'QBZ-95':(156,'primary','RIFLE'),'QBZ-97':(156,'primary','RIFLE'),
  'QBU-191':(proto['QBU191']['weaponId'],'primary','SNIPER'),'QLU-11':(proto['QLU11']['weaponId'],'primary','GRENADE'),
  'QTS-11':(proto['QTS11']['weaponId'],'primary','RIFLE'),
  'QJB-201':(53,'primary','MG'),'QJS-161':(53,'primary','MG'),'QJY-201':(30,'primary','MG'),'QBB-95':(14,'primary','MG'),
  'QBU-88':(167,'primary','SNIPER'),'QBU-10':(523,'primary','SNIPER'),
  'QBS-09':(45,'primary','SHOTGUN'),'QCQ-05':(508,'primary','SMG'),'QCW-05':(508,'primary','SMG'),
  'PF-89':(168,'special','ROCKET'),'PF-97':(668,'special','ROCKET'),'PF-98':(172,'special','ROCKET'),'PF-98A':(172,'special','ROCKET'),
  'DZJ-08':(200,'special','ROCKET'),'HJ-73D':(175,'special','ATGM'),'HJ-8E':(141,'special','ATGM'),
  'HJ-12':(62,'special','ATGM'),'HJ-12E':(62,'special','ATGM'),'TL-4':(205,'special','ATGM'),'GAM-102LR':(205,'special','ATGM'),
  'HN-6':(583,'special','SAM'),'QW-2':(537,'special','SAM'),'QN-202':(141,'special','ATGM'),
  'QJZ-171':(145,'special','MG'),'QJZ-89':(145,'special','MG'),
  'QLZ-04':(148,'special','GRENADE'),'QLZ-87':(148,'special','GRENADE'),
  'QLG-10A':(31,'special','GRENADE'),'LG5':(203,'primary','GRENADE'),'LG5s':(203,'primary','GRENADE'),
  'LG6':(68,'primary','GRENADE'),'LG4':(68,'primary','GRENADE'),'LG3':(75,'special','GRENADE'),
  'FHJ-02':(698,'special','ROCKET')}
 cache={};ammo_by_weapon={};mesh_sources={};icons=set();summary=[]
 rules901=[r.copy() for r in weapon_rules if r['unitId']==901];body_by_id={r['unitId']:r for r in bodies}
 def create(label,munitions=''):
  name=label.split(' (')[0];variant='smoke' if name=='FHJ-02' and 'smoke' in munitions.lower() else 'mixed' if name in ('PF-98','PF-98A') and any(x in munitions.lower() for x in ['dzt','thermobaric']) else ''
  key=(name,variant)
  if key in cache:return cache[key]
  donor,slot,kind=choices[name];old=t['WeaponsJson'][donor];w=copy.deepcopy(old)
  use_existing=donor in {x['weaponId'] for x in proto.values()} and name!='QBZ-192' and not variant
  if use_existing:new=donor
  else:
   icon='FA_PLA_WP_'+kind;icons.add(icon);w.update(Name='PLA infantry '+name+(' '+variant if variant else ''),HUDName=name,HUDIcon=icon)
   if name=='QCQ-05':w['Silent']=False
   if name=='FHJ-02':w['MagazineSize']=7
   new=g.add('WeaponsJson',w);mesh_sources[new]=donor
  candidates=[r for r in t['WeaponAmmunitionsJson'].values() if r['WeaponId']==donor]
  assert candidates,(name,donor)
  source=min(r['UnitId'] for r in candidates);ars=sorted([r for r in candidates if r['UnitId']==source],key=lambda r:(r['Order'],r['Id']))
  # Exact supported body weapon prototypes use their saved mesh alignment.
  out=[]
  if use_existing:out=[r.copy() for r in ars]
  else:
   for i,ar in enumerate(ars):
    a=copy.deepcopy(t['AmmunitionsJson'][ar['AmmunitionId']]);ammoname=name+' ammunition'
    if name=='FHJ-02':
     if variant=='smoke':
      a=copy.deepcopy(t['AmmunitionsJson'][73]);ammoname='FHJ-02 smoke rocket'
      for field in ['GroundRange','MinimalRange','TrajectoryType','MuzzleVelocity']:a[field]=t['AmmunitionsJson'][550][field]
      a.update(SmokeRadius=8.0,SmokeDuration=45.0)
     else:ammoname='FHJ-02 incendiary rocket'
    if name=='PF-97':a=copy.deepcopy(t['AmmunitionsJson'][108]);ammoname='PF-97 thermobaric rocket'
    if name=='QN-202':a=copy.deepcopy(t['AmmunitionsJson'][578]);ammoname='QN-202 HE-fragmentation'
    if name.startswith('QLZ-'):ammoname='35 mm HE-fragmentation'
    if name=='QLG-10A':ammoname='35 mm HE-fragmentation'
    if name=='QJZ-171' or name=='QJZ-89':ammoname='12.7 mm ammunition'
    if name in ('QJB-201','QJS-161','QBB-95','QBZ-95','QBU-88'):ammoname='5.8 mm ammunition'
    if name=='QJY-201':ammoname='7.62 mm ammunition'
    if name=='QBU-10':ammoname='12.7 mm precision ammunition'
    if name in ('QCW-05','QCQ-05'):ammoname='5.8 mm SMG ammunition'
    ai='FA_PLA_AMMO_'+kind;icons.add(ai);a.update(Name='PLA infantry '+name+' '+str(i),HUDName=ammoname,HUDIcon=ai)
    na=g.add('AmmunitionsJson',a);out.append({**ar,'WeaponId':new,'AmmunitionId':na})
   if variant=='mixed':
    a=copy.deepcopy(t['AmmunitionsJson'][107]);a.update(Name='PLA infantry '+name+' DZT-98',HUDName='DZT-98 thermobaric (analog)',HUDIcon='FA_PLA_AMMO_ROCKET');na=g.add('AmmunitionsJson',a)
    out.append({**ars[0],'WeaponId':new,'AmmunitionId':na,'Order':len(out),'Quantity':4})
  cache[key]=(new,slot,name,donor);ammo_by_weapon[new]=out
  return cache[key]
 # Preserve historical draft definitions/rig bindings, but replace their playable
 # cards with the complete designer roster to avoid duplicate infantry designs.
 retired=list(range(1010,1028));oldpools={r['Id'] for r in t['SpecializationAvailabilitiesJson'].values() if r['UnitId'] in retired}
 for uid in retired:g.put('Units',uid,{'DisplayInArmory':False});assignments['assignments'].pop(str(uid),None)
 for r in list(t['TransportAvailabilitiesJson'].values()):
  if r['SpecializationAvailabilityId'] in oldpools:g.remove('TransportAvailabilitiesJson',r['Id'])
 for rid in oldpools:g.remove('SpecializationAvailabilitiesJson',rid)
 # A shared basic truck covers full-sized squads while IFVs remain capacity-limited.
 for sid in range(17,23):
  if 912 not in assignments['carriers'][str(sid)]:assignments['carriers'][str(sid)].append(912)
 for record in c['rows']:
  cells=record['cells'];sid=specs[cells[0]];name=cells[1];typ=cells[3];men=int(cells[4]);assert 1<=men<=14
  recon=cells[2]=='Yes';sf=typ=='Special forces';engineer=typ=='Engineers';conscript=typ=='Conscripts'
  # Keep the exact live sheet size. Native squad HP is five per soldier.
  parent=118 if conscript else 130 if sf else 117 if engineer else 114 if recon else 60
  uid=max(t['Units'])+1;u=copy.deepcopy(t['Units'][parent]);u.pop('Id')
  u.update(Name='PLA Designer '+str(record['row'])+' '+name,HUDName=name,CountryId=4,ContentMembership=-1,DisplayInArmory=True,IsUnitModification=False,CategoryType=0 if recon else 1,Role=32 if recon else 36 if sf else 31 if engineer or typ=='Elite' else 30,Cost=max(10,round((men*(8 if sf else 5 if conscript else 7))/5)*5),Description=cells[13]+' Fixed kit: '+cells[12]+'. Native weapon analogs and prices are provisional. Sheet row '+str(record['row'])+'.')
  g.put('Units',uid,u)
  for table,field,target in [('UnitArmorsJson','ArmorId','ArmorsJson'),('UnitPropulsionsJson','MobilityId','MobilityJson'),('UnitAbilitiesJson','AbilityId','AbilitiesJson')]:
   ls=g.rows(table,parent)
   if table!='UnitAbilitiesJson':ls=[next((r for r in ls if t[target][r[field]].get('IsDefault')),ls[0])]
   for r in ls:
    fields={'Name':'PLA '+name+' '+target,'IsDefault':True}
    if target=='ArmorsJson':fields.update(MaxHealthPoints=men*5,ArmorValue=10 if sf else 8 if engineer or typ=='Elite' else 6)
    if target=='AbilitiesJson' and conscript and not sf:fields.update(IsInfantrySprint=False,IsSmoke=False,SmokeAmmunitionQuantity=0)
    g.add(table,r,{'UnitId':uid,field:g.add(target,t[target][r[field]],fields)})
  for r in g.rows('SensorUnitsJson',parent):g.add('SensorUnitsJson',r,{'UnitId':uid})
  base_label=cells[5] or ('QBZ-95 (rifle)' if conscript else 'QBZ-191 (rifle)');assert not base_label.startswith('=')
  base=create(base_label);member_template=g.rows('SquadMembersJson',parent)[0]
  members=[{**member_template,'UnitId':uid,'PrimaryWeaponId':base[0],'SpecialWeaponId':0} for _ in range(men)]
  selected=[];primary_used=set();special_used=set()
  # Primary replacements first; launchers and underbarrel weapons may be carried
  # alongside a rifle, but two special weapons never occupy one soldier.
  requested=[]
  for col in (6,8,10):
   label=cells[col];qty=cells[col+1]
   if not label or label=='None':continue
   qty=int(qty);assert 0<qty<=men,(record['row'],label,qty,men)
   w=create(label,cells[12]);requested.append((w,qty,label))
  for (w,qty,label) in sorted(requested,key=lambda r:r[0][1]!='primary'):
   wid,slot,short,donor=w
   if slot=='primary':
    avail=[i for i in range(men) if i not in primary_used];assert len(avail)>=qty,(name,label,'primary slots')
    for i in avail[:qty]:members[i]['PrimaryWeaponId']=wid;primary_used.add(i)
    if short=='QTS-11':
     gl=proto['QTS11_GL']['weaponId'];ammo_by_weapon[gl]=[r.copy() for r in g.rows('WeaponAmmunitionsJson',901) if r['WeaponId']==gl]
     for i in avail[:qty]:members[i]['SpecialWeaponId']=gl;special_used.add(i)
   else:
    avail=[i for i in range(men) if i not in special_used]
    if short=='QLG-10A':avail.sort(key=lambda i:members[i]['PrimaryWeaponId']!=base[0])
    else:avail.sort(key=lambda i:i in primary_used)
    assert len(avail)>=qty,(name,label,'special slots')
    for i in avail[:qty]:members[i]['SpecialWeaponId']=wid;special_used.add(i)
   selected.append({'name':short,'weapon':wid,'quantity':qty,'slot':slot,'native_weapon':donor})
  carried={m[k] for m in members for k in ['PrimaryWeaponId','SpecialWeaponId'] if m[k]}
  for m in members:g.add('SquadMembersJson',m)
  for order,wid in enumerate(sorted(carried)):
   g.add('SquadWeaponsJson',next(iter(t['SquadWeaponsJson'].values())),{'UnitId':uid,'WeaponId':wid,'Order':order})
   for ar in ammo_by_weapon[wid]:
    fields={'UnitId':uid,'WeaponId':wid}
    if t['WeaponsJson'][wid]['HUDName']=='FHJ-02':fields['Quantity']=14
    g.add('WeaponAmmunitionsJson',ar,fields)
  if not recon:
   labels=[x['name'] for x in selected]
   if any(x in labels for x in ['HN-6','QW-2']):g.put('Units',uid,{'Role':34})
   elif any(x in labels for x in ['HJ-12','HJ-12E','HJ-8E','HJ-73D','TL-4','GAM-102LR']) and men<=7:g.put('Units',uid,{'Role':35})
  desert=conscript or sid in (17,19,21)
  body_id=(994 if desert else 989) if engineer else (993 if desert else 988) if sf and recon else (996 if desert else 995) if sf else 990 if desert else 985
  bodies.append({**copy.deepcopy(body_by_id[body_id]),'unitId':uid})
  for rule in rules901:
   if rule['weaponId'] in carried:weapon_rules.append({**copy.deepcopy(rule),'unitId':uid})
   for wid in carried:
    if mesh_sources.get(wid)==rule['weaponId']:weapon_rules.append({**copy.deepcopy(rule),'unitId':uid,'weaponId':wid})
  pool_template=next(iter(t['SpecializationAvailabilitiesJson'].values()));pool=g.add('SpecializationAvailabilitiesJson',pool_template,{'UnitId':uid,'SpecializationId':sid})
  carriers=[]
  for carrier in assignments['carriers'][str(sid)]:
   if t['Units'][carrier]['InfantrySlots']>=men:
    g.add('TransportAvailabilitiesJson',next(iter(t['TransportAvailabilitiesJson'].values())),{'SpecializationAvailabilityId':pool,'UnitId':carrier});carriers.append(carrier)
  assert carriers,(name,men,'no transport')
  assignments['assignments'][str(uid)]=[sid]
  summary.append({'unit':uid,'row':record['row'],'name':name,'spec':sid,'men':men,'recon':recon,'troop_type':typ,'base_rifle':base_label,'weapons':selected,'munitions':cells[12],'notes':cells[13],'body_from':body_id,'camo':'desert' if desert else 'green','armor':10 if sf else 8 if engineer or typ=='Elite' else 6,'health':men*5,'carriers':carriers,'native_verified':False})
 assert len(summary)==90
 assignments['build']=json.loads((root/'pla-specializations-contract.json').read_text())['build'];assignments['retired_infantry_drafts']=retired
 assignments['pool_counts']={str(s):sum(r['SpecializationId']==s for r in t['SpecializationAvailabilitiesJson'].values()) for s in range(17,23)}
 (root/'source/UserData/FreedomArrow/pla-spec-assignments.json').write_text(json.dumps(assignments,indent=2)+'\n')
 receipt={'build':json.loads((root/'pla-specializations-contract.json').read_text())['build'],'source_sheet':c['spreadsheet_id'],'source_range':c['source_range'],'entries':summary,'count':90,'retired_drafts':retired,'icon_keys':sorted(icons),'native_verified':False,'limits':'Names, sizes, selected weapons and quantities match the sheet. Weapon performance, ammo stocks, costs and armor tiers are native analog drafts. Custom meshes used where installed; remaining handhelds use native meshes.'}
 receipt['weapon_sources']={str(v[0]):v[3] for v in cache.values()}
 (root/'source/UserData/FreedomArrow/pla-infantry-designer.json').write_text(json.dumps(receipt,indent=2)+'\n')
 return receipt

"""Fixed PLA equipment armament drafts. Native analog performance is explicit in receipts."""
import copy,json,math,re,collections
from pla_graph import Graph

def apply(root,t,patches,native_ids,vanilla,models):
 g=Graph(t,patches,native_ids);baseline=copy.deepcopy(t);pol=json.loads((root.parents[1]/'tools/pla-specs/vehicle-armament-contract.json').read_text())
 entries=[];icon_keys=set()
 def links(src,tab,uid):return [r for r in src[tab].values() if r.get('UnitId')==uid]
 def icon(kind,ammo=False):
  key='FA_PLA_'+('AMMO_' if ammo else 'WP_')+kind;icon_keys.add(key);return key
 def identify(w,a):
  s=(w['Name']+' '+w['HUDName']).lower();tr=a['TrajectoryType']
  if 'sam ' in s or 'aam ' in s:return 'SAM'
  if 'atgm' in s:return 'ATGM'
  if 'bomb' in s:return 'BOMB'
  if 'cruise' in s or s.startswith('arm '):return 'MISSILE'
  if 'mlrs' in s or 'rocketpod' in s:return 'ROCKET'
  if 'missile' in s:return 'MISSILE'
  if 'mortar' in s:return 'MORTAR'
  if 'howitzer' in s or 'artillery' in s:return 'HOWITZER'
  if 'hmg' in s or 'mmg' in s or 'minigun' in s:return 'MG'
  if 'autocannon' in s or 'aag ' in s:return 'AUTOCANNON'
  if 'planegun' in s:return 'AUTOCANNON'
  if tr in (100,110,120,130,140):return 'MISSILE'
  return 'CANNON'
 def default_armament(src,parent):
  chosen=[];excluded=set()
  for m in links(src,'ModificationsJson',parent):
   os=[o for o in src['OptionsJson'].values() if o['ModificationId']==m['Id'] and not o.get('ReplaceUnitId')]
   if not os:continue
   o=min(os,key=lambda x:(not x['IsDefault'],x['Order'],x['Id']))
   chosen.extend(v for k,v in o.items() if k.startswith('Turret') and k.endswith('Id') and v)
   excluded.update(v for x in os if x!=o for k,v in x.items() if k.startswith('Turret') and k.endswith('Id') and v)
  ts=[r['TurretId'] for r in links(src,'TurretUnitsJson',parent)]
  selected=collections.Counter(chosen)
  for i in ts:
   if i not in selected and src['TurretsJson'][i]['IsDefault'] and i not in excluded:selected[i]=1
  for _ in range(5):
   for i in ts:
    parent_id=src['TurretsJson'][i]['ParentTurretId']
    if i not in selected and parent_id in selected:selected[i]=selected[parent_id]
  ws=collections.Counter()
  for r in src['TurretWeaponsJson'].values():
   if r['TurretId'] in selected:ws[r['WeaponId']]+=selected[r['TurretId']]
  return sorted(ws.items())
 equipment=sorted(u['Id'] for u in t['Units'].values() if u['CountryId']==4 and u['DisplayInArmory'] and u['Type']!=2)
 for uid in equipment:
  u=baseline['Units'][uid];p=copy.deepcopy(pol['units'].get(str(uid),{}));parent=p.get('parent',uid);src=baseline if parent==uid else vanilla
  raw_specs=p.get('weapons')
  if raw_specs is None:
   raw_specs=[]
   for wid,instances in default_armament(src,parent):
    arows=[r for r in links(src,'WeaponAmmunitionsJson',parent) if r['WeaponId']==wid]
    if not arows:continue
    w=src['WeaponsJson'][wid];a=src['AmmunitionsJson'][arows[0]['AmmunitionId']];kind=identify(w,a)
    s=(w['Name']+' '+w['HUDName']).lower()
    name=('PL-10' if kind=='SAM' and a['Seeker']==10 else 'PL-15' if kind=='SAM' else 'YJ-91' if 'sead' in s or s.startswith('arm ') or 'kh31' in s or 'kh-31' in s else 'KD-20' if 'cruise' in s else 'KD-88' if kind in ('MISSILE','ATGM') else 'Chinese guided bomb' if kind=='BOMB' else 'Chinese rocket pod' if kind=='ROCKET' else '30 mm aircraft cannon' if '30' in s else '23 mm aircraft cannon')
    # The Su-30MKK is an imported Russian system; its weapon names remain factual.
    if uid==924:name=w['HUDName']
    raw_specs.append({'donor':wid,'name':name,'kind':kind,'ammo_source_unit':parent,'instances':instances,'count_basis':'Native analog loadout including repeated pylon mounts; provisional Chinese configuration.'})
  g.clear_unit(uid,['TurretUnitsJson','WeaponAmmunitionsJson']);g.clear_options(uid)
  if parent!=uid:
   chassis=baseline
   donor=chassis['Units'][parent];fields={k:donor[k] for k in ['ModelFileName','PortraitFileName','ThumbnailFileName','Length','Width','Height','Weight','WaterDiveOffset']}
   if 'slots' in p:fields['InfantrySlots']=p['slots']
   g.put('Units',uid,fields)
   for table,field,target in [('UnitArmorsJson','ArmorId','ArmorsJson'),('UnitPropulsionsJson','MobilityId','MobilityJson'),('UnitAbilitiesJson','AbilityId','AbilitiesJson')]:
    g.clear_unit(uid,[table]);ls=links(chassis,table,parent)
    if table!='UnitAbilitiesJson':ls=[next((x for x in ls if chassis[target][x[field]].get('IsDefault')),ls[0])] if ls else []
    else:
     ls=[x for x in ls if chassis[target][x[field]]['IsDefault'] or chassis[target][x[field]].get('IsSmoke') or chassis[target][x[field]].get('IsRadar') and (u['Role'] in (15,16) or uid in (936,1055))]
    for link in ls:g.add(table,link,{'UnitId':uid,field:g.add(target,chassis[target][link[field]],{'Name':'PLA '+u['HUDName']+' '+target,'IsDefault':True})})
   g.clear_unit(uid,['SensorUnitsJson'])
   sensor_links=links(src,'SensorUnitsJson',parent)
   chosen_sensor=18 if uid in (936,1055) else 19 if parent==221 else None
   if chosen_sensor:sensor_links=[r for r in sensor_links if r['SensorId']==chosen_sensor]
   else:sensor_links=[next((r for r in sensor_links if src['SensorsJson'][r['SensorId']].get('IsDefault')),sensor_links[0])] if sensor_links else []
   for r in sensor_links:g.add('SensorUnitsJson',r,{'UnitId':uid,'SensorId':g.add('SensorsJson',src['SensorsJson'][r['SensorId']],{'IsDefault':True,'Name':'PLA '+u['HUDName']+' optics'})})
  if 'slots' in p:g.put('Units',uid,{'InfantrySlots':p['slots']})
  if p.get('role') is not None:g.put('Units',uid,{'Role':p['role']})
  if p.get('category') is not None:g.put('Units',uid,{'CategoryType':p['category']})
  built=[];turrets={}
  for order,spec in enumerate(raw_specs):
   wid=spec['donor'];ws=vanilla if spec.get('pure_vanilla',parent!=uid) else baseline
   w=copy.deepcopy(ws['WeaponsJson'][wid]);sourceunit=spec.get('ammo_source_unit',parent)
   arows=[r for r in links(ws,'WeaponAmmunitionsJson',sourceunit) if r['WeaponId']==wid]
   if not arows:
    candidates=[r for r in ws['WeaponAmmunitionsJson'].values() if r['WeaponId']==wid];assert candidates,(uid,wid)
    sourceunit=min(r['UnitId'] for r in candidates);arows=[r for r in candidates if r['UnitId']==sourceunit]
   arows=sorted(arows,key=lambda r:(r['Order'],r['Id']))
   if 'ammo_ids' in spec:arows=sorted([r for r in arows if r['AmmunitionId'] in spec['ammo_ids']],key=lambda r:spec['ammo_ids'].index(r['AmmunitionId']))
   assert arows,(uid,wid,'no ammunition')
   kind=spec.get('kind',identify(w,ws['AmmunitionsJson'][arows[0]['AmmunitionId']]))
   w.update(Name='PLA '+u['HUDName']+' '+spec['name'],HUDName=spec['name'],HUDIcon=icon(kind))
   if spec.get('instances',1)>1:w['MagazineSize']*=spec['instances']
   if 'mag' in spec:w['MagazineSize']=spec['mag']
   neww=g.add('WeaponsJson',w)
   # A complete native mount is retained, including its firing arcs. Fixed draft
   # weapons are defaults, so no discarded donor option can reactivate them.
   candidates=[r for r in ws['TurretWeaponsJson'].values() if r['WeaponId']==wid]
   donor_tids={r['TurretId'] for r in links(ws,'TurretUnitsJson',sourceunit)}
   tw=next((r for r in candidates if r['TurretId'] in donor_tids),candidates[0] if candidates else None)
   if tw:
    tid=tw['TurretId'];key=(id(ws),tid)
    if key not in turrets:
     nt=g.add('TurretsJson',ws['TurretsJson'][tid],{'Name':'PLA '+u['HUDName']+' mount '+str(len(turrets)),'IsDefault':True,'ParentTurretId':None})
     g.add('TurretUnitsJson',next(iter(t['TurretUnitsJson'].values())),{'UnitId':uid,'TurretId':nt,'Order':len(turrets)})
     turrets[key]=nt
    g.add('TurretWeaponsJson',tw,{'TurretId':turrets[key],'WeaponId':neww,'Order':order})
   else:raise AssertionError((uid,wid,'missing native turret'))
   counts=spec.get('counts');stocks=[]
   for ai,ar in enumerate(arows):
    ammo=copy.deepcopy(ws['AmmunitionsJson'][ar['AmmunitionId']]);oldmult=max(1,ammo['HUDMultiplier'])
    assert counts is None or len(counts)==len(arows),(uid,wid,'stock count mismatch',counts,[r['AmmunitionId'] for r in arows])
    count=counts[ai] if counts is not None else ar['Quantity']*oldmult*spec.get('instances',1)
    # Preserve the native visual-round multiplier and logical shot economy.
    # A non-divisible advertised load is rounded by at most one native group;
    # the receipt records both requested and displayed quantities.
    qty=math.ceil(count/oldmult);shown=qty*oldmult
    suffix=spec.get('ammo_names',[])
    if suffix:aname=suffix[ai]
    elif len(arows)>1:
     old=ammo['HUDName'].upper();aname=spec['name']+' '+('APFSDS' if 'APFSDS' in old else 'HEAT' if 'HEAT' in old else 'AP' if any(x in old for x in ['AP','3BM']) else 'HE')
    else:aname=spec['name']+' ammunition'
    ammo.update(Name='PLA '+u['HUDName']+' '+aname,HUDName=aname,HUDIcon=icon(kind,True))
    newa=g.add('AmmunitionsJson',ammo);g.add('WeaponAmmunitionsJson',ar,{'UnitId':uid,'WeaponId':neww,'AmmunitionId':newa,'Quantity':qty,'Order':ai})
    stocks.append({'ammo':newa,'name':aname,'requested_rounds':count,'displayed_rounds':shown,'logical_quantity':qty,'hud_multiplier':oldmult,'native_ammo':ar['AmmunitionId']})
   built.append({'weapon':neww,'name':spec['name'],'native_weapon':wid,'native_unit':sourceunit,'magazine':w['MagazineSize'],'kind':kind,'stocks':stocks,'basis':spec.get('count_basis','Draft capacity and ammunition split; verify before balance lock.'),'performance':'Closest native analog; not measured Chinese weapon performance.'})
  if p.get('model_from'):
   other=baseline['Units'][p['model_from']]['Name']
   if other in models:models[u['Name']]=copy.deepcopy(models[other])
  g.put('Units',uid,{'Description':(u.get('Description') or '')+' Fixed PLA armament draft. Ammunition mix and analog performance remain provisional; see pla-vehicle-armament.json.'})
  entries.append({'unit':uid,'name':u['HUDName'],'type':u['Type'],'native_parent':parent,'weapons':built,'slots':t['Units'][uid]['InfantrySlots'],'custom_model':models.get(u['Name']),'armor_basis':('Selected native chassis analog; not a measured Chinese armor claim.' if parent!=uid else 'Existing PLA draft armor preserved.'),'native_verified':False})
 assert len(entries)==160
 retired_options=sorted(set(baseline['OptionsJson'])-set(t['OptionsJson']))
 assert not set(retired_options)&native_ids['OptionsJson'],'An original vanilla option was removed'
 receipt={'build':14,'entries':entries,'count':len(entries),'icon_keys':sorted(icon_keys),'retired_option_ids':retired_options,'ammo_display':'Quantity × HUDMultiplier. Grouped native shots retained; rounding is explicit per stock.','native_verified':False}
 (root/'source/UserData/FreedomArrow/pla-vehicle-armament.json').write_text(json.dumps(receipt,indent=2)+'\n')
 return receipt

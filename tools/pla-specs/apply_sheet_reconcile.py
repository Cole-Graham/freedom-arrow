"""Reconcile a bounded, formatting-aware sheet snapshot onto exact PLA31.
Stable unit IDs and existing weapon definitions prevent unrelated asset/stat drift.
"""
from pathlib import Path
import argparse,json,copy,hashlib,sys,zipfile
P=argparse.ArgumentParser();P.add_argument('--repo',type=Path,required=True);P.add_argument('--base',type=Path,required=True);P.add_argument('--plan',type=Path,required=True);P.add_argument('--vanilla',type=Path,required=True);P.add_argument('--reserve-rifle',choices=['191','95'],default='191');a=P.parse_args();rel=a.repo/'releases/0.6';src=rel/'source';fa=src/'UserData/FreedomArrow';sys.path[:0]=[str(a.repo),str(rel)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
enc=lambda d:json.dumps(d,ensure_ascii=False,indent=2)+'\n'
with zipfile.ZipFile(a.base) as z:
 whole=json.loads(z.read('UserData/FreedomArrow/pla-package-manifest.json'));assert whole['build']==31
 with a.base.open('rb') as f:base_sha=hashlib.file_digest(f,'sha256').hexdigest()
 vanilla={tab:{r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())} for tab in FIELD_TO_FILE};t=copy.deepcopy(vanilla);patches={tab:json.loads(z.read('UserData/FreedomArrow/constants/'+fn)) for tab,fn in FIELD_TO_FILE.items()}
 for tab,ps in patches.items():
  for k,v in ps.items():
   if v is None:t[tab].pop(int(k),None)
   else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
 before=copy.deepcopy(t);designer=json.loads(z.read('UserData/FreedomArrow/pla-infantry-designer.json'));assign=json.loads(z.read('UserData/FreedomArrow/pla-spec-assignments.json'));identity=json.loads(z.read('UserData/FreedomArrow/pla-infantry-identity.json'));appearance=json.loads(z.read('UserData/FreedomArrow/pla-infantry-appearance.json'));modelrules=json.loads(z.read('UserData/FAModels/infantry-weapons.json'));oldrules=copy.deepcopy(modelrules)
plan=json.loads(a.plan.read_text());byid={r['unit']:r for r in designer['entries']};g=Graph(t,patches,{k:set(v) for k,v in vanilla.items()});removed={p['unit'] for p in plan if p['removed']};receipt={'build':32,'base_build':31,'base_sha256':base_sha,'removed_units':sorted(removed),'entries':[],'native_verified':False,'reserve_rifle':a.reserve_rifle,'weapon_performance_definitions_unchanged':True,'cost_policy':'Existing unit costs retained; squad HP follows five per soldier. Ammunition stocks retained for existing weapons; newly carried weapons reuse their existing unit donor stock.','engineer_loadout':{'parent':1156,'child':1162},'geometry_art_body_preserved':True}
def rows(tab,uid):return g.rows(tab,uid)
def weapon(label,uid,munitions):
 name=label.split(' (')[0].strip(); candidates=[(wid,r) for wid,r in t['WeaponsJson'].items() if r.get('HUDName')==name]
 if name=='QBZ-191':return 2014501 if byid[uid]['troop_type']=='Conscripts' and a.reserve_rifle=='191' else 2014500 if uid in [1149,1164] else 2003998
 if name=='QBZ-95':return 2014501 if a.reserve_rifle=='191' and byid[uid]['troop_type']=='Conscripts' else 2012205
 if name=='FHJ-02':return 2014406 if 'smoke' in munitions.lower() else 2013057
 if name=='PF-98A':return 2011919 if any(x in munitions.lower() for x in ['mixed','mix:','dzt-98','also thermo']) else 2013157
 existing=next((x['weapon'] for x in byid[uid]['weapons'] if x['name']==name),None)
 if existing:return existing
 assert candidates,(uid,name,'No existing weapon')
 valid={int(w) for w in designer['weapon_sources']}|{2013087,2012205,2014501,2003998,2014500}
 candidates=[(wid,r) for wid,r in candidates if wid in valid];assert candidates,(uid,name,'No infantry weapon donor')
 return min(wid for wid,r in candidates)
def slot(wid):
 for entry in designer['entries']:
  for w in entry['weapons']:
   if w['weapon']==wid:return w['slot']
 return 'primary'
def ammo_template(wid,uid):
 same=[r for r in before['WeaponAmmunitionsJson'].values() if r.get('UnitId')==uid and r.get('WeaponId')==wid]
 if same:return same
 donors=[r['UnitId'] for r in before['WeaponAmmunitionsJson'].values() if r.get('WeaponId')==wid and r.get('UnitId') in byid]
 assert donors,(uid,wid,'no ammo donor')
 return [r for r in before['WeaponAmmunitionsJson'].values() if r.get('UnitId')==min(donors) and r.get('WeaponId')==wid]
def hide(uid):
 g.put('Units',uid,{'DisplayInArmory':False});assign['assignments'].pop(str(uid),None);pools={r['Id'] for r in rows('SpecializationAvailabilitiesJson',uid)}
 for r in list(t['TransportAvailabilitiesJson'].values()):
  if r['SpecializationAvailabilityId'] in pools:g.remove('TransportAvailabilitiesJson',r['Id'])
 for rid in pools:g.remove('SpecializationAvailabilitiesJson',rid)
for p in plan:
 uid=p['unit'];old=byid[uid]
 if p['removed']:hide(uid);continue
 c=p['cells'];men=int(c[4]);typ=c[3];base=weapon(c[5],uid,c[12]);requested=[]
 for col in [6,8,10]:
  if not c[col] or c[col]=='None':continue
  qty=int(c[col+1]);assert 0<qty<=men,(uid,c[col],qty)
  wid=weapon(c[col],uid,c[12]);requested.append((wid,slot(wid),qty,c[col].split(' (')[0]))
 template=copy.deepcopy(rows('SquadMembersJson',uid)[0]);members=[{**template,'UnitId':uid,'PrimaryWeaponId':base,'SpecialWeaponId':0} for _ in range(men)];prim=set();spec=set();selected=[]
 for wid,sl,qty,name in sorted(requested,key=lambda r:r[1]!='primary'):
  used=prim if sl=='primary' else spec;available=[i for i in range(men) if i not in used]
  if sl=='special':available.sort(key=lambda i:members[i]['PrimaryWeaponId']!=base if name=='QLG-10A' else i in prim)
  assert len(available)>=qty,(uid,name,'too many assigned weapons')
  for i in available[:qty]:
   members[i]['PrimaryWeaponId' if sl=='primary' else 'SpecialWeaponId']=wid;used.add(i)
   if name=='QTS-11':assert i not in spec;members[i]['SpecialWeaponId']=2004006;spec.add(i)
  selected.append({'name':name,'weapon':wid,'quantity':qty,'slot':sl,'native_weapon':designer['weapon_sources'].get(str(wid),wid)})
 carried={m[k] for m in members for k in ['PrimaryWeaponId','SpecialWeaponId'] if m[k]};stock={wid:ammo_template(wid,uid) for wid in carried}
 g.clear_unit(uid,['SquadMembersJson','SquadWeaponsJson','WeaponAmmunitionsJson'])
 for m in members:g.add('SquadMembersJson',m)
 for order,wid in enumerate(sorted(carried)):
  g.add('SquadWeaponsJson',next(iter(before['SquadWeaponsJson'].values())),{'UnitId':uid,'WeaponId':wid,'Order':order})
  for ar in stock[wid]:g.add('WeaponAmmunitionsJson',ar,{'UnitId':uid,'WeaponId':wid})
 recon=c[2]=='Yes';fields={'HUDName':p['display_name'],'CategoryType':0 if recon else 1,'Role':32 if recon else 36 if typ=='Special forces' else 31 if typ in ['Engineers','Elite'] else 30}
 if typ==old['troop_type'] and recon==old['recon']:fields['Role']=before['Units'][uid]['Role']
 if uid in [1182,1184,1185]:fields['ThumbnailFileName']=byid[{1182:1189,1184:1182,1185:1188}[uid]]['unit_icon']
 g.put('Units',uid,fields)
 for ar in rows('UnitArmorsJson',uid):g.put('ArmorsJson',ar['ArmorId'],{'MaxHealthPoints':men*5,'ArmorValue':10 if typ=='Special forces' else 8 if typ in ['Engineers','Elite'] else 6})
 for ar in rows('UnitAbilitiesJson',uid):
  if typ=='Conscripts':g.put('AbilitiesJson',ar['AbilityId'],{'IsInfantrySprint':False,'IsSmoke':False,'SmokeAmmunitionQuantity':0})
 # Preserve exact approved per-unit rig values; retarget only rifle aliases where necessary.
 # Preserve weapon-model bindings exactly; unused rifle bindings will not match an SMG/carbine.
 for r in list(t['TransportAvailabilitiesJson'].values()):
  pool=t['SpecializationAvailabilitiesJson'].get(r['SpecializationAvailabilityId'])
  if pool and pool['UnitId']==uid and t['Units'][r['UnitId']]['InfantrySlots']<men:g.remove('TransportAvailabilitiesJson',r['Id'])
 sid=old['spec'];poolids={r['Id'] for r in rows('SpecializationAvailabilitiesJson',uid)};linktemplate=next(iter(t['TransportAvailabilitiesJson'].values()))
 for pool in poolids:
  existing={r['UnitId'] for r in t['TransportAvailabilitiesJson'].values() if r['SpecializationAvailabilityId']==pool}
  for carrier in assign['carriers'][str(sid)]:
   if carrier not in existing and t['Units'][carrier]['InfantrySlots']>=men:g.add('TransportAvailabilitiesJson',linktemplate,{'SpecializationAvailabilityId':pool,'UnitId':carrier})
 old.update(row=p.get('current_sheet_row',p['row']),name=p['display_name'],source_design_name=c[1],men=men,recon=recon,troop_type=typ,base_rifle=t['WeaponsJson'][base]['HUDName'],weapons=selected,health=men*5,munitions=c[12],notes=c[13],armor=fields.get('ArmorValue',10 if typ=='Special forces' else 8 if typ in ['Engineers','Elite'] else 6))
 old['unit_icon']=fields.get('ThumbnailFileName',old.get('unit_icon'));receipt['entries'].append({'unit':uid,'row':p.get('current_sheet_row',p['row']),'source_original_row':p['row'],'name':p['display_name'],'men':men,'type':typ,'recon':recon,'base_weapon':base,'weapons':selected})
# One parent card with the native ReplaceUnitId loadout mechanism.
hide(1162);g.put('Units',1162,{'DisplayInArmory':True,'IsUnitModification':True});parent=1156
m=g.add('ModificationsJson',t['ModificationsJson'][571],{'UnitId':parent,'Name':'PLA Engineer fixed loadouts','Order':0})
for child,donor,default,order in [(1156,2030,True,0),(1162,2031,False,1)]:g.add('OptionsJson',t['OptionsJson'][donor],{'ModificationId':m,'ReplaceUnitId':child,'Name':'PLA Engineer '+str(child),'IsDefault':default,'Order':order,'Cost':0,'ReplaceUnitName':None,'ThumbnailOverride':None})
for entry in designer['entries']:
 if entry['unit'] in removed:entry['removed_by_sheet_strikethrough']=True
 if entry['unit']==1162:entry['loadout_parent']=1156
for entry in identity['units']:
 uid=entry['unit'];p=next((x for x in plan if x['unit']==uid),None)
 if p and not p['removed']:entry['display_name']=p['display_name']
 if uid in removed:entry['removed_by_sheet_strikethrough']=True
# Follow the renamed identities with the already approved matching badge.
identity_before=copy.deepcopy(identity['units'])
for uid,donor in [(1182,1189),(1184,1182),(1185,1188)]:
 old_entry=next(x for x in identity_before if x['unit']==donor)
 target=next(x for x in identity['units'] if x['unit']==uid)
 target.update({k:copy.deepcopy(v) for k,v in old_entry.items() if k not in ['unit','display_name','source_design_name','removed_by_sheet_strikethrough']})
 target['display_name']=byid[uid]['name'];byid[uid]['identity']=target['identity'];byid[uid]['unit_icon']=target['address']
# Body presets and all artwork remain exact; only alias mapping may change.
for x,y in zip(oldrules,modelrules):assert {k:v for k,v in x.items() if k!='weaponId'}=={k:v for k,v in y.items() if k!='weaponId'}
assert t['WeaponsJson']==before['WeaponsJson'] and t['AmmunitionsJson']==before['AmmunitionsJson']
for tab,fn in FIELD_TO_FILE.items():
 out=fa/'constants'/fn;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(enc(patches[tab]))
for name,d in [('pla-infantry-designer.json',designer),('pla-spec-assignments.json',assign),('pla-infantry-identity.json',identity)]:
 d['build']=32;(fa/name).write_text(enc(d))
(src/'UserData/FAModels/infantry-weapons.json').write_text(enc(modelrules));receipt['playable_parent_cards']=len(plan)-len(removed)-1;receipt['sheet_rows_retained_as_definitions']=len(plan)-len(removed);receipt['weapon_alias_model_bindings_changed']=sum(x!=y for x,y in zip(oldrules,modelrules));(fa/'pla-sheet-reconcile.json').write_text(enc(receipt));print(json.dumps({k:v for k,v in receipt.items() if k!='entries'},indent=2))

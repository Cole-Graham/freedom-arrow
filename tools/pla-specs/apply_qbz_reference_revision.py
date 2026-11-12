"""Apply Sam's reference-card assignments and conscript ability rule over pinned PLA28.
Only identity/reference fields and the requested conscript abilities change. Existing
weapon performance, ammunition stocks, unit stats, models and alignment are retained.
"""
from pathlib import Path
import argparse,copy,hashlib,json,zipfile
root=Path(__file__).resolve().parents[2];src=root/'releases/0.6/source';p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()=='c1f8f7c3683ab6f4ec05ee3a7a816b1da48631335a0361af86fd67b5cf545496'
enc=lambda x:json.dumps(x,indent=2)+'\n'
with zipfile.ZipFile(a.base) as z:
 assert json.loads(z.read('UserData/FreedomArrow/pla-package-manifest.json'))['build']==28
 tables={k:json.loads(z.read('UserData/FreedomArrow/constants/'+k+'.json')) for k in ['weapons','squad_members','squad_weapons','weapon_ammunitions','abilities','unit_abilities']}
 models=json.loads(z.read('UserData/FAModels/infantry-weapons.json'))
 designer=json.loads(z.read('UserData/FreedomArrow/pla-infantry-designer.json'))
old=copy.deepcopy(tables);oldmodels=copy.deepcopy(models);entries=designer['entries'];reserve={u['unit'] for u in entries if u['troop_type']=='Conscripts'};sf={u['unit'] for u in entries if u['troop_type']=='Special forces'};plain_existing={1108,1149,1164};assert not reserve&sf and len(reserve)==13
# Two presentation aliases retain every donor field except the name and HUD icon.
plain191,plainreserve=2014500,2014501
for new,donor in [(plain191,2003998),(plainreserve,2012205)]:
 assert str(new) not in tables['weapons'];row=copy.deepcopy(tables['weapons'][str(donor)]);row.update(Name='PLA QBZ191 iron sights '+str(donor),HUDName='QBZ-191',HUDIcon='FA_PLA_WP_QBZ191_PLAIN');tables['weapons'][str(new)]=row
changes=[]
def replacement(uid,wid):
 if uid in plain_existing and wid==2003998:return plain191
 if uid in reserve and wid==2012205:return plainreserve
 return wid
for table,fields in [('squad_members',['PrimaryWeaponId','SpecialWeaponId']),('squad_weapons',['WeaponId']),('weapon_ammunitions',['WeaponId'])]:
 for rid,row in tables[table].items():
  if not isinstance(row,dict):continue
  for field in fields:
   if field not in row:continue
   before=row[field];after=replacement(row.get('UnitId'),before)
   if after!=before:row[field]=after;changes.append({'table':table,'id':int(rid),'unit':row['UnitId'],'field':field,'before':before,'after':after})
# Keep the exact same mesh files, soldier slots and approved offsets on observers/crew.
for row in models:
 if row['unitId'] in plain_existing and row['weaponId']==2003998:row['weaponId']=plain191
assert sum(x!=y for x,y in zip(models,oldmodels))==3
for x,y in zip(models,oldmodels):assert {k:v for k,v in x.items() if k!='weaponId'}=={k:v for k,v in y.items() if k!='weaponId'}
# Both references get their own card art. Their behavior/stats remain the donor's.
tables['weapons']['2013087']['HUDIcon']='FA_PLA_WP_QBZ192';tables['weapons']['2013349']['HUDIcon']='FA_PLA_WP_QCW05'
ability_edits=[]
for linkid,link in tables['unit_abilities'].items():
 if not isinstance(link,dict) or link.get('UnitId') not in reserve:continue
 ability=str(link['AbilityId']);row=tables['abilities'][ability];assert not any(isinstance(l,dict) and l.get('AbilityId')==int(ability) and l.get('UnitId') not in reserve for l in tables['unit_abilities'].values())
 for field,value in [('IsInfantrySprint',False),('IsSmoke',False),('SmokeAmmunitionQuantity',0)]:
  if row.get(field)!=value:ability_edits.append({'ability':int(ability),'unit':link['UnitId'],'field':field,'before':row.get(field),'after':value});row[field]=value
assert len(ability_edits)==39
for link in tables['unit_abilities'].values():
 if not isinstance(link,dict):continue
 if link.get('UnitId') in reserve:
  a=tables['abilities'][str(link['AbilityId'])];assert not a['IsSmoke'] and not a['IsInfantrySprint']
 if link.get('UnitId') in sf:assert tables['abilities'][str(link['AbilityId'])]==old['abilities'][str(link['AbilityId'])]
# Verify every previously existing field; only the two requested HUD fields differ on old weapons.
for wid,row in old['weapons'].items():
 if row is None:continue
 expected=copy.deepcopy(row)
 if wid=='2013087':expected['HUDIcon']='FA_PLA_WP_QBZ192'
 if wid=='2013349':expected['HUDIcon']='FA_PLA_WP_QCW05'
 assert tables['weapons'][wid]==expected,wid
for table in ['squad_members','squad_weapons','weapon_ammunitions']:
 assert set(tables[table])==set(old[table])
 for rid,row in old[table].items():
  if row is None:assert tables[table][rid] is None;continue
  allowed={'WeaponId','PrimaryWeaponId','SpecialWeaponId'};assert {k:v for k,v in row.items() if k not in allowed}=={k:v for k,v in tables[table][rid].items() if k not in allowed},(table,rid)
(src/'UserData/FreedomArrow/constants').mkdir(parents=True,exist_ok=True)
for table in ['weapons','squad_members','squad_weapons','weapon_ammunitions','abilities']:(src/'UserData/FreedomArrow/constants'/f'{table}.json').write_text(enc(tables[table]))
f=src/'UserData/FAModels/infantry-weapons.json';f.parent.mkdir(parents=True,exist_ok=True);f.write_text(enc(models))
for u in entries:
 if u['unit'] in reserve:u['base_rifle']='QBZ-191 (iron sights)';u['latest_user_rifle_override']='Sam2026-11-11: reservists/non-combat plain191; old sheet95 baseline superseded, current ammo quantities/performance retained'
 if u['unit'] in reserve:u['ability_rule']='No sprint or smoke; SF exception retained'
 if u['unit'] in plain_existing:u['base_rifle']='QBZ-191 (iron sights)'
designer['weapon_sources'][str(plain191)]=2003998;designer['weapon_sources'][str(plainreserve)]=2012205;designer['reference_card_revision']='User-directed reference and conscript ability overlay; live source-sheet cells have not been edited';(src/'UserData/FreedomArrow/pla-infantry-designer.json').write_text(enc(designer))
f=src/'UserData/FreedomArrow/pla-weapon-hud.json';hud=json.loads(f.read_text())
for e in hud['entries']:
 if e['weapon']==2003998:e.update(basis='Sam-supplied optic-equipped QBZ191 CAD image, measured source edges',profile='QBZ191')
 if e['weapon']==2013087:e.update(address='FA_PLA_WP_QBZ192',profile='QBZ192',basis='Sam-supplied suppressed QBZ192 image, measured source edges')
 if e['weapon']==2013349:e.update(address='FA_PLA_WP_QCW05',profile='QCW05',mode='custom',basis='Sam-supplied suppressed QCW05 bullpup image, measured source edges')
for wid,donor in [(plain191,2003998),(plainreserve,2012205)]:hud['entries'].append({'weapon':wid,'name':'QBZ-191','scope':'INFANTRY','mode':'custom','profile':'QBZ191_PLAIN','address':'FA_PLA_WP_QBZ191_PLAIN','native_weapon':donor,'basis':'Sam-supplied iron-sight reference; donor stats/model/audio and ammunition stocks retained'})
hud['profiles']=sorted({x['profile'] for x in hud['entries'] if x['mode']=='custom'});hud['resources']=[a for key in hud['profiles'] for a in ['FA_PLA_WP_'+key,'FA_PLA_WP_'+key+'_OUTLINE']];hud['infantry_weapons']=46;hud['native_icon_entries']=sum(e['mode']=='native' for e in hud['entries']);hud['custom_icon_entries']=sum(e['mode']=='custom' for e in hud['entries']);hud['raster_export_width']=1160;hud['reference_revision']='Measured source boundaries and internal lines replace rejected hand approximations';f.write_text(enc(hud))
receipt={'build':29,'basis':'Sam reference images and no-sprint/no-smoke conscript instruction','plain_qbz191_units':sorted(plain_existing|reserve),'reservists':sorted(reserve),'plain_noncombat_units':sorted(plain_existing),'sf_units_retained':sorted(sf),'plain_aliases':{'2014500':2003998,'2014501':2012205},'weapon_reference_edits':changes,'conscript_ability_edits':ability_edits,'model_binding_alias_edits':3,'all_alignment_values_preserved':True,'ammo_quantities_and_stats_preserved':True,'weapon_numeric_stats_preserved':True,'new_image_profiles':['QBZ191_PLAIN','QBZ191','QBZ192','QCW05'],'rejected_hand_drawn_pass_superseded':True,'native_verified':False,'source_sheet_updated':False};(src/'UserData/FreedomArrow/pla-qbz-reference-art.json').write_text(enc(receipt));(root/'tools/pla-specs/reference-revision-checks.json').write_text(enc(receipt));print('Applied13conscript restrictions,16plain rifle assignments,three model-binding aliases;all numeric weapon/ammo/unit stats preserved.')

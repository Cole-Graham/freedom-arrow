"""Verify the complete, integer-numbered PLA package without launching the game."""
from pathlib import Path
import hashlib,json,struct,sys,zipfile
R=Path(__file__).resolve().parent
p=Path(sys.argv[1]) if len(sys.argv)>1 else R/'out/PLA-TEST-Build-20.bamod'
with zipfile.ZipFile(p) as z:
 names=set(z.namelist());assert len(names)==len(z.namelist())
 assert all(not Path(n).is_absolute() and '..' not in Path(n).parts and '\\' not in n for n in names)
 mod=json.loads(z.read('mod.json'));assert mod['name']=='PLA TEST Build 20' and mod['version']=='20' and mod['type']=='modpack'
 assert z.read('README.md').startswith(b'# PLA TEST Build 20\n')
 m=json.loads(z.read('UserData/FreedomArrow/pla-package-manifest.json'));assert m['build']==20 and m['label']=='PLA TEST Build 20'
 assert names-{'mod.json','README.md','UserData/FreedomArrow/pla-package-manifest.json'}==set(m['sha256'])
 for n,h in m['sha256'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 core=json.loads(z.read('UserData/FreedomArrow/payload-manifest.json'));assert core['version']=='20'
 for n,h in core['sha256'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 def table(n):return json.loads(z.read('UserData/FreedomArrow/constants/'+n+'.json'))
 units=table('units');roster=json.loads((R/'pla-test-contract.json').read_text())['cards'];assert len(roster)==79
 for c in roster:assert units[str(c['unit'])]['Name']==(c['name'] if c.get('russia') or c.get('us') else 'PLA '+c['name'])
 assert units['983']['Name']=='XM30' and units['984']['Name']=='ZIL Karatel Punisher'
 assert mod['repo']=='Cole-Graham/freedom-arrow'
 assert table('countries')['4']['Name']=='China' and not table('countries')['4']['Hidden']
 specs=table('specializations');assert len([x for x in specs.values() if x and x.get('CountryId')==4])==6
 assert not table('countries')['1']['Hidden'] and not table('countries')['2']['Hidden']
 assert all(not r['DisplayInArmory'] for r in units.values() if r and r.get('CountryId')!=4 and 'DisplayInArmory' in r)
 draft=json.loads(z.read('UserData/FreedomArrow/pla-specializations.json'));assert draft['pla_only'] and len(draft['new_units'])==18
 assert not draft['hidden_fixture_units'] and draft['test_spec']==22
 assert all(units[str(uid)]['DisplayInArmory'] for uid in draft['test_fixture_units'])
 assert all(r['CountryId']==4 for r in units.values() if r and r.get('Name','').startswith('PLA '))
 assert sum(bool(r and r.get('UnitId') in range(985,1010)) for r in table('squad_members').values())==175
 binding=json.loads(z.read('UserData/FreedomArrow/pla-infantry-prototype.json'));assert binding['unit']==901
 members=[r for k,r in sorted(table('squad_members').items(),key=lambda x:int(x[0])) if r and r.get('UnitId')==901];assert len(members)==7
 for row,want in zip(members,binding['members']):assert row['PrimaryWeaponId']==want['primary'] and row['SpecialWeaponId']==want['special']
 weapon_rules=json.loads(z.read('UserData/FAModels/infantry-weapons.json'));body_rules=json.loads(z.read('UserData/FAModels/infantry-bodies.json'));assert body_rules[0]['offset']==[0,-0.05,0]
 for label,offset in [('QLU11',[0,-0.17,0.22]),('QTS11',[0,-0.17,0.196]),('QTS11_GL',[0,-0.17,0.196]),('QBU191',[0,-0.17,0.12]),('QBZ191',[0,-0.22,0.196])]:
  wid=binding['weapons'][label]['weaponId'];rule=next(r for r in weapon_rules if r['weaponId']==wid);assert rule['offset']==offset
  assert all('UserData/FAModels/'+rule[k] in names for k in ['file','battle'])
  assert any(r and r.get('UnitId')==901 and r['WeaponId']==wid and r['AmmunitionId']==binding['weapons'][label]['ammoId'] for r in table('weapon_ammunitions').values())
 modelmap=json.loads(z.read('UserData/FAModels/models.json'))
 for rule in modelmap.values():
  for k in ['file','battle']:
   if rule.get(k):assert 'UserData/FAModels/'+rule[k] in names
 assert all('green' in modelmap[n]['file'] for n in ['PLA ZTZ-99A','PLA ZBD-04A','PLA ZTZ-96B']) and 'black' in modelmap['PLA Z-10']['file']
 repair=json.loads(z.read('UserData/FreedomArrow/infantry-arm-repair.json'));assert sum(n.endswith('.fas') for n in repair['sha256'])==75 and len(repair['repacked_atlases'])==8
 for n,h in repair['sha256'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h
 catalogue=json.loads(z.read('UserData/FreedomArrow/pla-model-catalogue.json'));assert catalogue['entry_count']==157 and len(catalogue['new_units'])==102
 assert len(body_rules)==136 and len({r['unitId'] for r in body_rules})==136
 assert {r['unitId'] for r in body_rules}=={901,*range(985,1028),*catalogue['new_body_units'],*range(1136,1226)}
 excluded=json.loads(z.read('UserData/FreedomArrow/pla-spec-assignments.json'))['excluded_units']+list(range(1010,1028))
 for e in catalogue['entries']:assert units[str(e['unit'])]['CountryId']==4 and units[str(e['unit'])]['DisplayInArmory']==(e['unit'] not in excluded)
 assert specs['17']['UIName']=='Airforce / Airborne' and specs['20']['UIName']=='Marines / SF'
 options=table('options');assert all(0<int(k)<=32767 and struct.unpack('<h',struct.pack('<h',int(k)))[0]==int(k) for k,v in options.items() if v)
 migration=json.loads(z.read('UserData/FreedomArrow/option-id-migration.json'));assert len(migration)>=837
 retired_options=set(json.loads(z.read('UserData/FreedomArrow/pla-vehicle-armament.json'))['retired_option_ids'])
 assert all((str(v) in options and options[str(v)] is not None) or v in retired_options for v in migration.values())
 assert b'FAMODELS' in z.read('Mods/FAModels.dll') or 'FAMODELS'.encode('utf-16-le') in z.read('Mods/FAModels.dll')
 assignment=json.loads(z.read('UserData/FreedomArrow/pla-spec-assignments.json'));assert len(assignment['recon_variants'])==6
 assert all(22 not in specs for uid,specs in assignment['assignments'].items() if units.get(uid,{}).get('Type')!=2)
 result={'label':mod['name'],'verified_payload_hashes':len(m['sha256']),'verified_core_hashes':len(core['sha256']),'roster_cards':len(roster),'mapped_models':len(modelmap),'functional_infantry':True,'approved_offsets_preserved':True,'native_option_ids_fit_signed_short':True,'new_infantry_roles':90,'pla_only':True,'runtime_verified':False}
 print(json.dumps(result,indent=2))

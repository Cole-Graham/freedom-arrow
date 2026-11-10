"""Verify the complete, integer-numbered PLA package without launching the game."""
from pathlib import Path
import hashlib,json,struct,sys,zipfile
R=Path(__file__).resolve().parent
p=Path(sys.argv[1]) if len(sys.argv)>1 else R/'out/PLA-Build-1.bamod'
with zipfile.ZipFile(p) as z:
 names=set(z.namelist());assert len(names)==len(z.namelist())
 assert all(not Path(n).is_absolute() and '..' not in Path(n).parts and '\\' not in n for n in names)
 mod=json.loads(z.read('mod.json'));assert mod['name']=='PLA Build 1' and mod['version']=='1' and mod['type']=='modpack'
 assert z.read('README.md').startswith(b'# PLA Build 1\n')
 m=json.loads(z.read('UserData/FreedomArrow/pla-package-manifest.json'));assert m['build']==1 and m['label']=='PLA Build 1'
 assert names-{'mod.json','README.md','UserData/FreedomArrow/pla-package-manifest.json'}==set(m['sha256'])
 for n,h in m['sha256'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 core=json.loads(z.read('UserData/FreedomArrow/payload-manifest.json'));assert core['version']=='1'
 for n,h in core['sha256'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 def table(n):return json.loads(z.read('UserData/FreedomArrow/constants/'+n+'.json'))
 units=table('units');roster=json.loads((R/'pla-test-contract.json').read_text())['cards'];assert len(roster)==79
 for c in roster:assert units[str(c['unit'])]['Name']==(c['name'] if c.get('russia') or c.get('us') else 'PLA '+c['name'])
 assert units['983']['Name']=='XM30' and units['984']['Name']=='ZIL Karatel Punisher'
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
 for n,h in {'m_f14_cg.fam':'f0d3e5ed35b95e7ad160ff92dcf2a7f70ddbfa4b392951e44176e9e54bd79a4c','m_abramsx_lo.fam':'399f2fe9bb664e1ec911552a214ecc97624992cbd4b616a0175092f7eeff2ea4'}.items():assert hashlib.sha256(z.read('UserData/FAModels/'+n)).hexdigest()==h
 for i in (3,4,5,7):
  for suffix in ('.png','_n.png','_mask.png'):
   b=z.read(f'UserData/FAModels/m_f14_cg_tex{i}{suffix}');size=3072 if i in (3,4,5) and suffix=='.png' else 2048;assert struct.unpack('>2I',b[16:24])==(size,size)
 options=table('options');assert all(0<int(k)<=32767 and struct.unpack('<h',struct.pack('<h',int(k)))[0]==int(k) for k,v in options.items() if v)
 migration=json.loads(z.read('UserData/FreedomArrow/option-id-migration.json'));assert len(migration)>=837
 assert all(str(v) in options and options[str(v)] is not None for v in migration.values())
 assert b'FAMODELS' in z.read('Mods/FAModels.dll') or 'FAMODELS'.encode('utf-16-le') in z.read('Mods/FAModels.dll')
 result={'label':mod['name'],'verified_payload_hashes':len(m['sha256']),'verified_core_hashes':len(core['sha256']),'roster_cards':len(roster),'mapped_models':len(modelmap),'functional_infantry':True,'approved_offsets_preserved':True,'native_option_ids_fit_signed_short':True,'runtime_verified':False}
 print(json.dumps(result,indent=2))

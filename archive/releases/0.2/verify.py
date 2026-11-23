"""Verify exactly the development candidate we intend to ship to a later test."""
from pathlib import Path
import hashlib,json,sys,zipfile
R=Path(__file__).resolve().parent
p=Path(sys.argv[1]) if len(sys.argv)>1 else R/'out/FreedomArrow-0.2.0-dev.21.bamod'
with zipfile.ZipFile(p) as z:
    names=z.namelist();assert len(names)==len(set(names))
    assert all(not n.startswith('/') and '..' not in Path(n).parts and '\\' not in n for n in names)
    manifest=json.loads(z.read('UserData/FreedomArrow/payload-manifest.json'))
    assert manifest['version']=='0.2.0-dev.21'
    assert set(names)-{'mod.json','README.md','UserData/FreedomArrow/payload-manifest.json'}==set(manifest['sha256'])
    for n,h in manifest['sha256'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
    mod=json.loads(z.read('mod.json'));assert mod['type']=='modpack' and mod['version']==manifest['version']
    channel=json.loads(z.read('UserData/FreedomArrow/channel.json'));assert channel['package_version']==mod['version'] and channel['channel']=='testing'
    assert channel['deployment_status']=='built_offline_execution_held'
    assert z.read('UserData/FreedomArrow/release-notes.md').decode().splitlines()[0]=='# Freedom Arrow 0.2.0-dev.21 — development candidate'
    assert {n for n in names if n.startswith('Mods/')}=={'Mods/BALocalSkirmish.dll','Mods/FreedomArrow.Runtime.dll','Mods/FreedomArrow.ConquestBatch.dll'}
    for dll in ['FreedomArrow.Runtime.dll','FreedomArrow.ConquestBatch.dll']:assert mod['version'].encode() in z.read('Mods/'+dll)
    def table(n):return json.loads(z.read('UserData/FreedomArrow/constants/'+n+'.json'))
    def live(n):return {k:v for k,v in table(n).items() if v is not None}
    for n in ['weapons','turret_weapons']:
        assert table(n)=={},'Held table must remain empty: '+n
    contract=json.loads((R/'vehicle-contract.json').read_text())
    det=json.loads((R/'detection-contract.json').read_text())
    for k,v in contract['base_costs'].items():assert table('units')[k]['Cost']==v,k
    allowed_stealth={*det['stealth'].values(),*det['stealth_unit_values'].values()}
    st=json.loads((R/'structural-contract.json').read_text())
    added={str(x['unit']) for x in st['splits']}
    for k,row in live('units').items():
        if k in added:continue
        assert set(row)<={'Cost','Stealth','CurrentStealth','IsUnitModification','HUDName'},k
        assert ('Cost' in row)==(k in contract['base_costs']),k
        if 'Stealth' in row:assert row['Stealth']==row['CurrentStealth'] and row['Stealth'] in allowed_stealth,k
    for k,row in live('sensors').items():
        assert set(row)=={'OpticsGround'} and row['OpticsGround'] in [*det['optics_ground_tiers'].values(),*det['optics_ground_drones'].values()] and int(k) not in det['optics_held_sensors'],k
    assert len(table('sensors'))==36-len(det['optics_held_sensors'])
    for k,v in det['optics_ground_drones'].items():assert table('sensors')[k]['OpticsGround']==v,k
    assert json.loads(z.read('UserData/FreedomArrow/detection-config.json'))==json.loads((R/'source/UserData/FreedomArrow/detection-config.json').read_text())
    for oid,cost in contract['option_costs'].items():assert table('options')[oid]['Cost']==cost,(oid,cost)
    # Versioned audit and positive operator targets; source equality alone is not an independent full policy proof.
    audit=json.loads((R/'constant-audit.json').read_text())
    assert audit['version']==manifest['version'] and audit['source_table_pins_matched']==24
    for k,row in live('options').items():assert int(k)>=2_000_000 or not {'MainSensorId','ExtraSensorId'} & set(row)
    assert {k:r['StealthOverride'] for k,r in live('options').items() if 'StealthOverride' in r and int(k)<2_000_000}==det['stealth_override_options']
    opt=table('options');arm=table('armors');mob=table('mobility')
    for oid,hp,front,side in [(551,14,None,None),(2089,10,80,30),(2090,10,400,400),(1986,14,400,400)]:
        a=arm[str(opt[str(oid)]['ArmorId'])];assert a['MaxHealthPoints']==hp
        if front is not None:assert (a['HeatArmorFront'],a['HeatArmorSides'])==(front,side)
    a=mob[str(opt['1986']['MobilityId'])];assert (a['MaxSpeedRoad'],a['MaxCrossCountrySpeed'])==(60,55)
    assert opt['2082']['Ability2Id']==82
    assert table('unit_abilities')['1029']['AbilityId']==82
    # Retain old rows except the explicit US/Baltic field changes.
    us=json.loads((R/'us-baltic-contract.json').read_text())
    for f in ['abilities','ammunitions','armors']:
        before=json.loads((R.parent/'0.1/source/UserData/FreedomArrow/constants'/(f+'.json')).read_text())
        for k,row in before.items():
            want=dict(row);want.update((us['ammo_fields'] if f=='ammunitions' else us['armor_fields'] if f=='armors' else {}).get(k,{}));assert table(f)[k]==want,(f,k)
    for uid,oids in [(1,[504,505]),(425,[1881,1882])]:
        for oid in oids:assert arm[str(opt[str(oid)]['ArmorId'])]['MaxHealthPoints']==10
    b15=arm[str(opt['643']['ArmorId'])];assert (b15['HeatArmorFront'],b15['HeatArmorSides'])==(400,400)
    assert any(r.get('UnitId')==254 and r['ArmorId']==opt['643']['ArmorId'] for r in live('unit_armors').values())
    for oid in [3067,3070,3071,3072]:assert arm[str(opt[str(oid)]['ArmorId'])]['MaxHealthPoints']==8
    for oid in [564]:assert arm[str(opt[str(oid)]['ArmorId'])]['HeatArmorSides']==200
    assert arm['2000048']['HeatArmorSides']==400
    for f in ['units','options','armors','unit_armors','unit_propulsions','unit_abilities','mobility','sensors']:
        assert table(f)==json.loads((R/'source/UserData/FreedomArrow/constants'/(f+'.json')).read_text()),f
    # Explicit configured totals for held splits and the Reserve-only reduction.
    units=table('units')
    for uid,oid,cost in [(158,563,100),(716,564,190),(716,566,230),(717,3033,80),(718,1905,80),(719,381,85),(720,1949,110),(714,2049,90),(714,2050,90),(715,480,35),(214,2101,35),(214,491,55),(214,492,60),(214,493,75),(141,245,35),(216,499,35),(9,625,100),(209,478,50),(209,479,90),(209,1708,105),(467,2047,30),(467,2048,30),(455,1959,25),(455,1960,30),(455,1961,35),(21,50,60)]:
        base=units[str(uid)]['Cost'];surcharge=opt.get(str(oid),{}).get('Cost',0)
        assert base+surcharge==cost,(uid,oid,cost)
    files=json.loads((R/'row-tests/table-files.json').read_text())
    locks=json.loads((R/'clone-locks.json').read_text())
    for t,rows in locks['tables'].items():
        patch=table(files[t].removesuffix('.json'))
        allowed=us['armor_fields'] if t=='ArmorsJson' else us['ammo_fields'] if t=='AmmunitionsJson' else {}
        for key,lock in rows.items():
            row={'Id':int(key),**patch[key]}
            for field,want in allowed.get(key,{}).items():
                assert row[field]==want,(t,key,field);row[field]=lock['permitted_before'][field]
            assert hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':')).encode()).hexdigest()==lock['sha256'],(t,key)
    for aid,fields in us['ammo_fields'].items():
        assert table('ammunitions')[aid]['Damage']==fields['Damage']
    for aid,fields in us['armor_fields'].items():
        for field,want in fields.items():assert arm[aid][field]==want,(aid,field)
    for uid,oids in [(22,[8,1894]),(24,[25]),(33,[42])]:
        for oid in oids:
            row=arm[str(opt[str(oid)]['ArmorId'])];assert (row['MaxHealthPoints'],row['HeatArmorFront'],row['HeatArmorSides'])==(12,600,600)
            assert opt[str(oid)]['Cost']==(40 if oid==1894 else 25)
    for aid in ['2000017','2000018']:assert (arm[aid]['MaxHealthPoints'],arm[aid]['HeatArmorFront'],arm[aid]['HeatArmorSides'])==(12,250,200)
    # M6 Linebacker edits are front HEAT and uparmor HP. Its base stays 14.
    assert arm['47']=={'HeatArmorFront':400,'MaxHealthPoints':14} and arm['288']=={'HeatArmorFront':700,'MaxHealthPoints':14}
    assert arm['60']=={'MaxHealthPoints':14} and arm['322']=={'MaxHealthPoints':14}
    assert '15' not in arm and '120' not in arm,'Linebacker and Sprut default armor unchanged'
    assert arm['2000104']['MaxHealthPoints']==12 and arm['326']['MaxHealthPoints']==12 and arm['336']['MaxHealthPoints']==12
    assert arm['2000020']['MaxHealthPoints']==10 and arm['2000021']['MaxHealthPoints']==10
    assert arm['2000022']['MaxHealthPoints']==10 and arm['2000023']['MaxHealthPoints']==10
    assert opt['1759']['Cost']==25,'M2A3 ESV BUSK3 option 1759 is +25'
    amm=table('ammunitions');assert amm['2000177']['Damage']==10.5 and amm['2000173']['Damage']==12.0
    assert arm[str(table('unit_armors')['983']['ArmorId'])]['MaxHealthPoints']==8
    for uid,oid,total in [(14,1904,90),(180,1958,40),(185,388,30),(41,60,40),(41,2082,70)]:
        base=units.get(str(uid),{}).get('Cost',80)
        assert base+opt.get(str(oid),{}).get('Cost',0)==total,(uid,oid,total)
    assert units['421']['Cost']+30==50
    # Structural changes.
    pools=table('specialization_availabilities')
    for x in st['splits']:
        assert units[str(x['unit'])]['Cost']==x['cost'] and [r['MaxAvailabilityXp0'] for r in pools.values() if r.get('UnitId')==x['unit']]==[x['pool']['new']],x['name']
    for oid in st['retire_options']:assert opt[str(oid)] is None,oid
    for mid in st['retire_mods']:assert table('modifications')[str(mid)] is None,mid
    for rid in st['retire_members']:assert table('squad_members')[str(rid)] is None,rid
    for rid in st['retire_squad_weapons']:assert table('squad_weapons')[str(rid)] is None,rid
    for rid in st['retire_ammo']:assert table('weapon_ammunitions')[str(rid)] is None,rid
    assert units['701']['IsUnitModification'] is False and units['408']['IsUnitModification'] is False
    # Check all archive constants against generated source; golden locks are separate.
    for f in files.values():assert table(f.removesuffix('.json'))==json.loads((R/'source/UserData/FreedomArrow/constants'/f).read_text()),f
    src=(R/'source/offline-mod/LocalSkirmish.cs').read_text()
    for need in ['if (type != LobbyType.Scenario) return Refuse','if (types[i] == LobbyType.Scenario) return false','class JoinFromListPatch','class JoinByInvitePatch','class QuickSearchPatch','NetworkScenarioStorage.IsNetwork && NetworkScenarioStorage.ScenarioMode']:
        assert need in src,'Online lobby rule missing: '+need
    settings=json.loads(z.read('UserData/FAConquestPrototype/settings.json'))
    assert settings['FixedIncomePerMinute']==200 and not settings['ShowOverlay'] and not settings['EnableDeveloperFixtures']
    assert settings['TestDurationSeconds']==0 and settings['ScoreLimit']==0 and settings['Ending']=='time_limit'
    pins=json.loads(z.read('UserData/FAConquestPrototype/compatibility.json'))
    for n in ['Mods/BALocalSkirmish.dll','UserData/FAConquestPrototype/settings.json']:
        assert hashlib.sha256(z.read(n)).hexdigest()==pins[n]
    assert not any(k in n.lower() for n in names for k in ['probe.dll','armory-suite','behavior-tests','engine.json'])
    print(f'PASS: {len(manifest["sha256"])} payload hashes; metadata and held tables; requested vehicle and detection data; 200-income setting. No native/runtime result.')
    print(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name)

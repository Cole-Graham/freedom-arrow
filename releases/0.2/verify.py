"""Verify exactly the development candidate we intend to ship to a later test."""
from pathlib import Path
import hashlib,json,sys,zipfile
R=Path(__file__).resolve().parent
p=Path(sys.argv[1]) if len(sys.argv)>1 else R/'out/FreedomArrow-0.2.0-dev.2.bamod'
with zipfile.ZipFile(p) as z:
    names=z.namelist();assert len(names)==len(set(names))
    assert all(not n.startswith('/') and '..' not in Path(n).parts and '\\' not in n for n in names)
    manifest=json.loads(z.read('UserData/FreedomArrow/payload-manifest.json'))
    assert manifest['version']=='0.2.0-dev.2'
    assert set(names)-{'mod.json','README.md','UserData/FreedomArrow/payload-manifest.json'}==set(manifest['sha256'])
    for n,h in manifest['sha256'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
    mod=json.loads(z.read('mod.json'));assert mod['type']=='modpack' and mod['version']==manifest['version']
    channel=json.loads(z.read('UserData/FreedomArrow/channel.json'));assert channel['package_version']==mod['version'] and channel['channel']=='testing'
    assert channel['deployment_status']=='built_offline_execution_held'
    assert z.read('UserData/FreedomArrow/release-notes.md').decode().splitlines()[0]=='# Freedom Arrow 0.2.0-dev.2 — development candidate'
    assert {n for n in names if n.startswith('Mods/')}=={'Mods/BALocalSkirmish.dll','Mods/FreedomArrow.Runtime.dll','Mods/FreedomArrow.ConquestBatch.dll'}
    for dll in ['FreedomArrow.Runtime.dll','FreedomArrow.ConquestBatch.dll']:assert mod['version'].encode() in z.read('Mods/'+dll)
    def table(n):return json.loads(z.read('UserData/FreedomArrow/constants/'+n+'.json'))
    for n in ['weapons','sensors','sensor_units','squad_members','squad_weapons','modifications','specialization_availabilities','turret_weapons']:
        assert table(n)=={},'Held table must remain empty: '+n
    contract=json.loads((R/'vehicle-contract.json').read_text())
    assert table('units')=={k:{'Cost':v} for k,v in contract['base_costs'].items()}
    for oid,cost in contract['option_costs'].items():assert table('options')[oid]['Cost']==cost,(oid,cost)
    # Exact frozen dev1 output plus the audited dev2 changes, never extra archive rows.
    audit=json.loads((R/'constant-audit.json').read_text())
    assert audit['version']==manifest['version'] and audit['source_table_pins_matched']==24
    for row in table('options').values():assert not {'StealthOverride','MainSensorId','ExtraSensorId'} & set(row)
    opt=table('options');arm=table('armors');mob=table('mobility')
    for oid,hp,front,side in [(551,14,None,None),(2089,10,80,30),(2090,10,400,400),(1986,10,400,400)]:
        a=arm[str(opt[str(oid)]['ArmorId'])];assert a['MaxHealthPoints']==hp
        if front is not None:assert (a['HeatArmorFront'],a['HeatArmorSides'])==(front,side)
    a=mob[str(opt['1986']['MobilityId'])];assert (a['MaxSpeedRoad'],a['MaxCrossCountrySpeed'])==(60,55)
    assert opt['2082']['Ability2Id']==82
    assert table('unit_abilities')['1029']['AbilityId']==82
    # Retain every old cloned row exactly. The AMPV uses original pinned ability82.
    for f in ['abilities','ammunitions','armors']:
        before=json.loads((R.parent/'0.1/source/UserData/FreedomArrow/constants'/(f+'.json')).read_text())
        for k,row in before.items():assert table(f)[k]==row,(f,k)
    for uid,oids in [(1,[504,505]),(425,[1881,1882])]:
        for oid in oids:assert arm[str(opt[str(oid)]['ArmorId'])]['MaxHealthPoints']==10
    b15=arm[str(opt['643']['ArmorId'])];assert (b15['HeatArmorFront'],b15['HeatArmorSides'])==(400,400)
    assert any(r.get('UnitId')==254 and r['ArmorId']==opt['643']['ArmorId'] for r in table('unit_armors').values())
    for oid in [3067,3070,3071,3072]:assert arm[str(opt[str(oid)]['ArmorId'])]['MaxHealthPoints']==8
    for oid in [564,565]:assert arm[str(opt[str(oid)]['ArmorId'])]['HeatArmorSides']==200
    assert arm['2000048']['HeatArmorSides']==400
    for f in ['units','options','armors','unit_armors','unit_propulsions','unit_abilities','mobility']:
        assert table(f)==json.loads((R/'source/UserData/FreedomArrow/constants'/(f+'.json')).read_text()),f
    # Explicit configured totals for held splits and the Reserve-only reduction.
    units=table('units')
    for uid,oid,cost in [(158,563,100),(158,564,190),(158,565,200),(158,566,230),(615,3033,80),(214,2101,35),(214,491,55),(214,492,60),(214,493,75),(141,245,35),(216,499,35),(9,625,100)]:
        base=units[str(uid)]['Cost'];surcharge=opt.get(str(oid),{}).get('Cost',0)
        assert base+surcharge==cost,(uid,oid,cost)
    settings=json.loads(z.read('UserData/FAConquestPrototype/settings.json'))
    assert settings['FixedIncomePerMinute']==200 and not settings['ShowOverlay'] and not settings['EnableDeveloperFixtures']
    assert settings['TestDurationSeconds']==0 and settings['ScoreLimit']==0 and settings['Ending']=='time_limit'
    pins=json.loads(z.read('UserData/FAConquestPrototype/compatibility.json'))
    for n in ['Mods/BALocalSkirmish.dll','UserData/FAConquestPrototype/settings.json']:
        assert hashlib.sha256(z.read(n)).hexdigest()==pins[n]
    assert not any(k in n.lower() for n in names for k in ['probe.dll','armory-suite','behavior-tests','engine.json'])
    print(f'PASS: {len(manifest["sha256"])} payload hashes; metadata and held tables; requested vehicle data; 200-income setting. No native/runtime result.')
    print(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name)

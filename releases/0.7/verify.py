"""Verify exactly the development candidate we intend to ship to a later test."""
from pathlib import Path
import hashlib,io,json,math,sys,zipfile
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R/'scenarios'));import common as ms;import dead_center_2v2 as dc2;import airport_5v5,baltiisk_3v3,dam_3v3
p=Path(sys.argv[1]) if len(sys.argv)>1 else R/'out/FreedomArrow-0.7.0-dev.56.bamod'
with zipfile.ZipFile(p) as z:
    names=z.namelist();assert len(names)==len(set(names))
    assert all(not n.startswith('/') and '..' not in Path(n).parts and '\\' not in n for n in names)
    manifest=json.loads(z.read('UserData/FreedomArrow/payload-manifest.json'))
    assert manifest['version']=='0.7.0-dev.56'
    assert set(names)-{'mod.json','README.md','UserData/FreedomArrow/payload-manifest.json'}==set(manifest['sha256'])
    for n,h in manifest['sha256'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
    mod=json.loads(z.read('mod.json'));assert mod['type']=='modpack' and mod['version']==manifest['version']
    channel=json.loads(z.read('UserData/FreedomArrow/channel.json'));assert channel['package_version']==mod['version'] and channel['channel']=='testing'
    assert channel['deployment_status']=='built_offline_execution_held'
    assert z.read('UserData/FreedomArrow/release-notes.md').decode().splitlines()[0]=='# Freedom Arrow 0.7.0-dev.56 — development candidate'
    third={'HudQuick.dll':'71b81b88330288cac2a486f003564002b6a856728fbac1b74d6fbbc599555117','TeamVoice.dll':'e1f80c77fd18858e82f8b9517c48208d51c87b99a3b4d0aedb4bcd6be05181ed','ArrowQueue.dll':'0ab2455b16a3481d19625adada5df8b39de84bcb19cb6b58df2536db0293526a','FlatIncomeMod.dll':'9b71a1eb0776564c9884d59cf591853eb1b1fdcefd40291a2c59b74ca05dc4d3'}
    assert {n for n in names if n.startswith('Mods/')}=={'Mods/BALocalSkirmish.dll','Mods/FreedomArrow.Runtime.dll',*('Mods/'+n for n in third)}
    assert all(hashlib.sha256(z.read('Mods/'+n)).hexdigest()==h for n,h in third.items()),'0.6 ActualArrow mods unchanged'
    assert mod['version'].encode() in z.read('Mods/FreedomArrow.Runtime.dll')
    # Batch (Lateralus, 8 November 2026): the conquest mode is built into FreedomArrow.Runtime.dll.
    assert 'Freedom Arrow Conquest'.encode('utf-16-le') in z.read('Mods/FreedomArrow.Runtime.dll'),'conquest mode built into Runtime'
    option_map=json.loads(z.read('UserData/FreedomArrow/option-id-migration.json'))
    wire_option_ids=set(option_map.values())
    mc=json.loads((R/'f22-mako-mig31bsm-contract.json').read_text())
    wire_option_ids|={x['option'] for x in mc['f22']['bays']+mc['mig31bsm']['empty_bomber_slots']}
    wire_option_ids|={load['id'] for slot in json.loads((R/'f21-contract.json').read_text())['slots'] for load in slot['loads']}
    class OptionRows(dict):
        def __getitem__(self,key):return super().__getitem__(str(option_map.get(str(key),key)))
    def table(n):
        rows=json.loads(z.read('UserData/FreedomArrow/constants/'+n+'.json'))
        return OptionRows(rows) if n=='options' else rows
    assert all(0<int(k)<=32767 for k,v in table('options').items() if v is not None)

    for aid in ('60','62','213','231','262','454','534','561'):
        assert table('ammunitions')[aid]['MuzzleVelocity']==1610.0
    for field in ('DispersionHorizontalRadius','DispersionVerticalRadius'):
        assert table('ammunitions')['262'].get(field,1.6)==1.6
    for name in ('cram_prediction_installed','cram_prediction_applied','aa_cooldown_installed'):
        assert name.encode('utf-16le') in z.read('Mods/FreedomArrow.Runtime.dll')
    assert table('squad_members')['660']['SpecialWeaponId']==59 and table('squad_members')['661']['SpecialWeaponId']==59
    assert table('weapon_ammunitions')['2906'].get('Quantity',1)==1
    def live(n):return {k:v for k,v in table(n).items() if v is not None}
    assert table('armors')['2000467']['IsDefault'] is True
    assert table('armors')['2000465']['IsDefault'] is False
    ax_t={x['TurretId'] for x in live('turret_units').values() if x.get('UnitId')==964}
    ax_main=[(k,t) for k,t in live('turrets').items() if int(k) in ax_t and t.get('ParentTurretId') is None]
    assert len(ax_main)==1 and ax_main[0][1]['IsDefault']
    ax_gun_links=[w for w in live('turret_weapons').values() if w.get('TurretId')==int(ax_main[0][0]) and w.get('Order')==0]
    assert len(ax_gun_links)==1
    ax_gun=table('weapons')[str(ax_gun_links[0]['WeaponId'])]
    assert ax_gun['AutoLoaded'] and ax_gun['MagazineReloadTimeMin']==5 and ax_gun['MagazineReloadTimeMax']==6

    tgc=json.loads((R/'tigr-contract.json').read_text())
    # 0.6 arrw-contract.json: the AGM-183A ARRW is one new weapon row and one new turret-weapon row (a copy of the Kinzhal HE).
    arrw=json.loads((R/'arrw-contract.json').read_text())
    arrw_ws={k for k,r in table('weapons').items() if str(r.get('Name','')).startswith('Cruise AGM183A ARRW')}
    assert len(arrw_ws)==len(arrw['loads']) and all(table('weapons')[k]['HUDName']==arrw['name'] and int(k)>=2000000 for k in arrw_ws)
    arrw_tw={k for k,r in table('turret_weapons').items() if str(r.get('WeaponId')) in arrw_ws and table('turrets')[str(r['TurretId'])]['Name'].startswith('PylonTurret B52H')};assert len(arrw_tw)==len(arrw['loads'])
    mako_ws={k for k,r in table('weapons').items() if r and r.get('Name')=='Cruise MAKO'}
    mako_tw={k for k,r in table('turret_weapons').items() if r and str(r.get('WeaponId')) in mako_ws}
    assert len(mako_ws)==len(mako_tw)==1
    # b21-loadout-contract.json: the B-21 options, each on its own bay turret with the stated launchers and price.
    # abramsx-contract.json: the Abrams X turret rows (main turret and two cupolas) and its one option.
    ax=json.loads((R/'abramsx-contract.json').read_text())
    ax_t={str(r['TurretId']) for r in table('turret_units').values() if r and r.get('UnitId')==ax['unit'] and int(r['TurretId'])>=2000000};assert len(ax_t)==1+len(ax['cupolas'])
    ax_tw={k for k,r in table('turret_weapons').items() if r and str(r.get('TurretId')) in ax_t}
    assert table('units')[str(ax['unit'])]['Cost']==ax['cost']
    b21=json.loads((R/'b21-loadout-contract.json').read_text());b21_tw=set()
    b21_w={k for k,r in table('weapons').items() if r and str(r.get('Name','')).endswith('B21 bay')};b21_a={k for k,r in table('ammunitions').items() if r and r.get('Name')=='Missile A2A JATM Plane'}
    assert len(b21_w)==len(b21_a)==sum('ammo' in ld for ld in b21['loads'])
    for ld in b21['loads']:
        (o,)=[o for o in table('options').values() if o and o.get('Name')==ld['option_name']];assert o['Cost']==ld['cost'] and not o['IsDefault']
        tws=[r for r in table('turret_weapons').values() if r and r.get('TurretId')==o['Turret0Id']];assert len(tws)==ld['launchers'] and len({r['WeaponId'] for r in tws})==1
        b21_tw|={k for k,r in table('turret_weapons').items() if r and r.get('TurretId')==o['Turret0Id']}
    # 0.6 (Lateralus, 8 Nov): helicopter ATGM pylons are vanilla. No dev.46 'both racks' or dev.61 'rack' rows remain,
    # and no pylon option of dev30-heli-contract.json (or the Mi-28N Ataka option 653) is patched.
    assert not any(str(r.get('Name','')).endswith((' both racks',' rack (no rounds)',' rack (no weapon)')) for t in ('weapons','turrets') for r in table(t).values() if r)
    heli=json.loads((R/'dev30-heli-contract.json').read_text())
    assert not set(table('options'))&{str(x) for x in heli['pod_options']+[653]}
    xm_t={str(r['TurretId']) for r in live('turret_units').values() if r.get('UnitId')==983}
    xm_tw={k for k,r in live('turret_weapons').items() if str(r.get('TurretId')) in xm_t}
    losat_t={str(r['TurretId']) for r in live('turret_units').values() if r.get('UnitId')==984}
    losat_tw={k for k,r in live('turret_weapons').items() if str(r.get('TurretId')) in losat_t}
    losat_ws={k for k,r in live('weapons').items() if r.get('Name')=='LOSAT KEM launcher'}
    be_t={str(r['TurretId']) for r in live('turret_units').values() if r.get('UnitId')==985}
    be_tw={k for k,r in live('turret_weapons').items() if str(r.get('TurretId')) in be_t}
    assert len(be_t)==2 and len(be_tw)==3
    assert table('units')['985']['ThumbnailFileName']==json.loads((R/'black-eagle-contract.json').read_text())['thumbnail']=='FA_BLACK_EAGLE_WHITE-Label'
    assert (R/'source/runtime-qa/icons/FA_BLACK_EAGLE-Label.png').read_bytes() in z.read('Mods/FreedomArrow.Runtime.dll'),'white card resource embedded'
    assert table('units')['985']['PortraitFileName']=='FA_BLACK_EAGLE_USER-Portrait'
    user_png=(R/'source/runtime-qa/icons/FA_BLACK_EAGLE-Portrait.png').read_bytes()
    assert user_png in z.read('Mods/FreedomArrow.Runtime.dll'),'user portrait embedded'
    assert hashlib.sha256(user_png).hexdigest()==json.loads((R/'black-eagle-contract.json').read_text())['portrait_source_sha256'],'Sam supplied PNG unchanged'
    assert len(losat_t)==len(losat_tw)==len(losat_ws)==1
    f21_ws={k for k,r in live('weapons').items() if str(r.get('Name','')).endswith(' F21 pylon')}
    assert len(f21_ws)==3
    f21_tw={k for k,r in live('turret_weapons').items() if str(r.get('WeaponId')) in f21_ws}
    assert len(f21_tw)==3
    assert set(table('turret_weapons'))=={str(x) for x in tgc['turret_weapons']}|arrw_tw|b21_tw|ax_tw|xm_tw|f21_tw|losat_tw|mako_tw|be_tw,'turret_weapons: approved custom unit graphs only'
    # dev.14: weapons hold only infantry launcher reload times.
    jav=json.loads((R/'dev30-contract.json').read_text())['weapon_fields']
    assert all(table('weapons')[k]==f for k,f in jav.items()),'dev.30 Javelin aim'
    rip=json.loads((R/'dev37-contract.json').read_text())['weapon_fields']
    assert all(all(table('weapons')[k][n]==x for n,x in f.items()) for k,f in rip.items()),'dev.37 one missile per target'
    h37=json.loads((R/'dev37-contract.json').read_text())['helicopter_vanilla']  # helicopter ATGMs keep vanilla bursts
    assert not any({'ShotsPerBurstMin','ShotsPerBurstMax','SimultaneousTracking'}&set(table('weapons').get(str(w)) or {}) for w in h37)
    gap49=json.loads((R/'dev49-contract.json').read_text())['weapon_fields']
    assert all(all(table('weapons')[k][n]==x for n,x in f.items()) for k,f in gap49.items()),'dev.49 vehicle ATGM gap'
    srof=json.loads((R/'sniper-rof-contract.json').read_text())['weapon_fields']
    assert all(table('weapons')[k]==f for k,f in srof.items()),'dev.16 sniper rate of fire'
    assert all(set(table('weapons')[k])<=set(rip.get(k,{}))|set(gap49.get(k,{})) for k in set(rip)|set(gap49)),'dev.37/49 weapon fields only'
    rip2=str(table('turret_weapons')['505']['WeaponId']);assert all(table('turret_weapons')[str(x)]['WeaponId']==int(rip2) for x in tgc['turret_weapons'])
    w2=table('weapons')[rip2];assert w2['Name']=='ATGM Kornet x4' and all(w2[k]==v for k,v in tgc['weapon_fields'].items()) and w2['TimeBetweenBurstsMin']==5.0,'dev.19 Tigr ripple weapon'
    # 0.6: display renames (rename-contract.json) add only HUDName to a weapon row.
    ren=json.loads((R/'rename-contract.json').read_text())['WeaponsJson']
    assert all(table('weapons')[k]['HUDName']==f['HUDName'] for k,f in ren.items()),'0.6 weapon display names'
    # 0.6 dev.50 (air-gen-contract.json): plane air-to-air missiles aim in 0 s, long-range SAMs in 0.5 s (0.2 in dev.50); aim time is the only field.
    # Lateralus batch (infantry-rl-contract.json): the RPG-22 is a full copy of the RPG-18 weapon row.
    rlc=json.loads((R/'infantry-rl-contract.json').read_text())
    rpg22w={k for k,r in table('weapons').items() if r and r.get('HUDName')==rlc['rpg22']['weapon_fields']['HUDName']}
    assert len(rpg22w)==1 and int(next(iter(rpg22w)))>=2_000_000 and all(table('weapons')[k][f]==v for k in rpg22w for f,v in rlc['rpg22']['weapon_fields'].items()) and all(table('weapons')[k]['Type']==63 and table('weapons')[k]['MagazineSize']==1 for k in rpg22w),'RPG-22 weapon'
    agc=json.loads((R/'air-gen-contract.json').read_text());aimw={k for k,r in table('weapons').items() if set(r)=={'AimTimeMin','AimTimeMax'} and r['AimTimeMin'] in (0.0,0.5)}
    assert {k for k in aimw if table('weapons')[k]['AimTimeMin']==0.5}=={str(w) for w in agc['big_sam']['weapons']} and all(table('weapons')[k]['AimTimeMax']==table('weapons')[k]['AimTimeMin'] in (0.0,0.5) for k in aimw) and len(aimw)==31,'0.6 dev.50 aim times'
    xm_w={k for k,r in live('weapons').items() if r.get('Name') in ['XM30 2x TOW-2B','XM30 2x Javelin']}
    assert len(xm_w)==2 and all(live('weapons')[k]['MagazineSize']==2 for k in xm_w)
    m25_ws={k for k,r in live('weapons').items() if r.get('Name')=='MGL 25 M-25 CDTE'}
    assert table('weapons') and all(set(r)=={'MagazineReloadTimeMin','MagazineReloadTimeMax'} and (r['MagazineReloadTimeMin'],r['MagazineReloadTimeMax']) in [(6.0,6.0),(7.0,7.0),(8.0,8.0)] for k,r in ((k,{n:v for n,v in r.items() if not (k in ren and n=='HUDName')}) for k,r in table('weapons').items()) if k not in aimw and k not in jav and k not in rip and k not in gap49 and k not in srof and k!=rip2 and k not in arrw_ws and k not in mako_ws and k not in rpg22w and k not in b21_w and k not in xm_w and k not in f21_ws and k not in losat_ws and k not in m25_ws and k!=str(ax_gun_links[0]['WeaponId'])),'weapons: launcher reload only outside the verified Abrams X gun'
    m25w=[k for k,r in live('weapons').items() if r.get('Name')=='MGL 25 M-25 CDTE'];assert len(m25w)==1
    m25a=[r for r in live('ammunitions').values() if r.get('Name')=='InfGrenade 25x40 M-25 CDTE'];assert len(m25a)==1 and m25a[0]['Damage']==0.75 and m25a[0]['IgnoreCover']==0.75
    contract=json.loads((R/'vehicle-contract.json').read_text())
    det=json.loads((R/'detection-contract.json').read_text())
    for k,v in contract['base_costs'].items():assert table('units')[k]['Cost']==v+(5 if k in {'62','413'} else 0),k
    ad=json.loads((R/'air-detect-contract.json').read_text())
    allowed_stealth={*det['stealth'].values(),*det['stealth_unit_values'].values(),*ad['plane_stealth'].values(),*ad.get('unit_stealth',{}).values()}
    assert all(table('units')[k]['Stealth']==v for k,v in ad.get('unit_stealth',{}).items()),'unit stealth'
    st=json.loads((R/'structural-contract.json').read_text())
    added={str(x['unit']) for x in st['splits']}|{str(json.loads((R/'dev38-contract.json').read_text())['kornet']['unit'])}|{str(json.loads((R/'sprut-contract.json').read_text())['unit'])}|{str(tgc['unit'])}|{str(json.loads((R/'tgb-contract.json').read_text())['unit'])}|{str(c['unit']) for c in json.loads((R/'scouts-contract.json').read_text())['cards']}|{str(c['unit']) for c in json.loads((R/'recon-heli-contract.json').read_text())['cards']}|{str(c['unit']) for c in json.loads((R/'recon-heli-us-contract.json').read_text())['cards']}|{str(c['unit']) for c in json.loads((R/'logistics-contract.json').read_text())['copies']}|{str(c['unit']) for c in json.loads((R/'f16-asf-contract.json').read_text())['cards']}|{str(c['unit']) for c in json.loads((R/'navy-air-contract.json').read_text())['cards']}|{str(c['unit']) for c in json.loads((R/'mig31bsm-contract.json').read_text())['cards']}
    added|={str(c['unit']) for c in json.loads((R/'paladin-split-contract.json').read_text())['cards']}  # 0.6 dev.74 M1299 Iron Thunder
    added|={str(c['unit']) for c in json.loads((R/'new-cards-contract.json').read_text())['cards']}  # new US cards (Abrams X, B-21)
    added|={str(c['unit']) for c in json.loads((R/'target-dummy-contract.json').read_text())['cards']}  # Lateralus test targets (F-22, MiG-29K dummies)
    added.add(str(json.loads((R/'su75-contract.json').read_text())['unit']))
    added.add(str(json.loads((R/'karatel-contract.json').read_text())['unit']))
    added.update({'983','984','985'})
    added|={str(c['unit']) for c in json.loads((R/'new-cards-contract.json').read_text()).get('late_cards',[])}  # Su-47, F-14, YF-23 (dev.13)
    for k,row in live('units').items():
        if k in added:continue
        assert set(row)<={'Cost','Stealth','CurrentStealth','IsUnitModification','HUDName','ThumbnailFileName'},k
        assert ('Cost' in row)==(k in contract['base_costs']),k
        if 'Stealth' in row:assert row['Stealth']==row['CurrentStealth'] and row['Stealth'] in allowed_stealth,k
    # 0.6 dev.58 (air-detect-contract.json): high-altitude optics on four rows; one copy per SHORAD sensor (ids from 2,000,000).
    copies={k:r for k,r in live('sensors').items() if int(k)>=2_000_000}
    assert len(copies)==len(ad['shorad']['sensors']) and all(r['OpticsHighAltitude']==ad['shorad']['high_optics'] for r in copies.values())
    for k,row in live('sensors').items():
        if k in copies:continue
        if k in ad['high_optics']:assert row['OpticsHighAltitude']==ad['high_optics'][k],k;row={n:v for n,v in row.items() if n!='OpticsHighAltitude'}
        if not row:assert int(k) in det['optics_held_sensors'],k;continue
        assert set(row)=={'OpticsGround'} and row['OpticsGround'] in [*det['optics_ground_tiers'].values(),*det['optics_ground_drones'].values()] and int(k) not in det['optics_held_sensors'],k
    assert len(table('sensors'))==36-len(det['optics_held_sensors'])+sum(int(k) in det['optics_held_sensors'] for k in ad['high_optics'])+len(copies)
    for k,v in det['optics_ground_drones'].items():assert table('sensors')[k]['OpticsGround']==v,k
    assert json.loads(z.read('UserData/FreedomArrow/detection-config.json'))==json.loads((R/'source/UserData/FreedomArrow/detection-config.json').read_text())
    # Spotting cap: one vanilla cap for every modded ground optics value; names cover each optics channel from 0 upward.
    caps=json.loads(z.read('UserData/FreedomArrow/spotting-caps.json'))['OpticsGroundCaps']
    for k,row in live('sensors').items():assert 'OpticsGround' not in row or f"{row['OpticsGround']:g}" in caps,k
    assert caps['2300']==1000 and caps['6400']==2750 and all(float(k)>=v for k,v in caps.items())
    assert 'UserData/FreedomArrow/optics-names.json' not in z.namelist()  # card shows metres again (Lateralus batch)
    for oid,cost in contract['option_costs'].items():assert table('options')[oid]['Cost']==cost,(oid,cost)
    # Versioned audit and positive operator targets; source equality alone is not an independent full policy proof.
    audit=json.loads((R/'constant-audit.json').read_text())
    assert audit['version']==manifest['version'] and audit['source_table_pins_matched']==24
    brm_opts={str(o) for o in json.loads((R/'brm3k-contract.json').read_text())['options']}
    for k,row in live('options').items():assert int(k) in wire_option_ids or int(k)>=2_000_000 or k in brm_opts or not {'MainSensorId','ExtraSensorId'} & set(row) or (set(row)=={'MainSensorId'} and str(row['MainSensorId']) in copies),k
    assert {k:r['StealthOverride'] for k,r in live('options').items() if 'StealthOverride' in r and int(k)<2_000_000 and int(k) not in wire_option_ids}==det['stealth_override_options']
    opt=table('options');arm=table('armors');mob=table('mobility')
    for oid,hp,front,side in [(551,14,None,None),(2089,10,80,30),(2090,10,400,400),(1986,12,400,400)]:
        a=arm[str(opt[str(oid)]['ArmorId'])];assert a['MaxHealthPoints']==hp
        if front is not None:assert (a['HeatArmorFront'],a['HeatArmorSides'])==(front,side)
    a=mob[str(opt['1986']['MobilityId'])];assert (a['MaxSpeedRoad'],a['MaxCrossCountrySpeed'])==(60,55)
    assert opt['2082']['Ability2Id']==82
    assert table('unit_abilities')['1029']['AbilityId']==82
    # Retain old rows except the explicit US/Baltic field changes.
    us=json.loads((R/'us-baltic-contract.json').read_text())
    pinned=set(json.loads((R/'sabot-pin-contract.json').read_text())['pinned_ammo'])
    # 0.4 dev.12: ground ATGM damage and Kornet penetration.
    d11=json.loads((R/'dev12-contract.json').read_text())
    atgm={str(a):{'Damage':d11['atgm_damage'],**({'PenetrationAtMinRange':d11['atgm_penetration'][str(a)],'PenetrationAtGroundRange':d11['atgm_penetration'][str(a)]} if str(a) in d11['atgm_penetration'] else {})} for a in d11['atgm_rows']}
    for aid,pen in json.loads((R/'dev13-contract.json').read_text())['atgm_penetration'].items():atgm.setdefault(aid,{}).update(PenetrationAtMinRange=pen,PenetrationAtGroundRange=pen)
    for aid,f in json.loads((R/'dev35-contract.json').read_text())['ammo_fields'].items():atgm.setdefault(aid,{}).update(f)
    for aid,f in json.loads((R/'accuracy-contract.json').read_text())['ammo_fields'].items():atgm.setdefault(aid,{}).update(f)
    for aid,f in json.loads((R/'accuracy-contract.json').read_text())['atgm_fields'].items():atgm.setdefault(aid,{}).update(f)
    cov=json.loads((R/'cover-contract.json').read_text())
    for k in ('tank_he','autocannon_he'):
        for aid in cov[k]['ids']:atgm.setdefault(str(aid),{})['IgnoreCover']=cov[k]['ignore_cover']
    # 0.6 dev.23 doubles artillery supply cost (logistics-contract.json), so a dev.21 row is its value or twice it.
    supply21={aid:f['SupplyCost'] for aid,f in json.loads((R/'supply-contract.json').read_text())['ammo'].items()}
    d24=json.loads((R/'dev24-contract.json').read_text())
    ammo01=json.loads((R.parent/'0.1/source/UserData/FreedomArrow/constants/ammunitions.json').read_text())
    soft01=json.loads((R/'soft-atgm-contract.json').read_text())['rows']
    topc=json.loads((R/'top-armor-contract.json').read_text())
    for f in ['abilities','ammunitions','armors']:
        before=json.loads((R.parent/'0.1/source/UserData/FreedomArrow/constants'/(f+'.json')).read_text())
        for k,row in before.items():
            want=dict(row);want.update((us['ammo_fields'] if f=='ammunitions' else us['armor_fields'] if f=='armors' else us['ability_fields'] if f=='abilities' else {}).get(k,{}))
            if f=='ammunitions':want.update(atgm.get(k,{}))
            if f=='armors' and int(k) in d24['hp']['armors']:want['MaxHealthPoints']=d24['hp']['value']
            if f=='armors' and k in topc['armors']:want.update(HeatArmorTop=topc['top'],KinArmorTop=topc['top'])  # top-armor-contract.json
            if f=='ammunitions' and int(k) in pinned:want['PenetrationAtMinRange']=table(f)[k]['PenetrationAtMinRange']
            if f=='ammunitions' and k in soft01:want['Damage']=soft01[k]['damage']  # soft-atgm-contract.json (Lateralus batch)
            assert table(f)[k]==want,(f,k)
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
    for uid,oid,cost in [(158,563,85),(716,564,170),(716,566,190),(717,3033,80),(718,1905,70),(719,381,85),(720,1949,110),(714,2049,90),(714,2050,90),(715,480,35),(214,2101,30),(214,491,40),(214,492,45),(214,493,60),(141,245,35),(216,499,35),(9,625,115),(209,478,50),(209,479,65),(209,1708,80),(467,2047,30),(467,2048,30),(455,1959,25),(455,1960,25),(455,1961,35),(21,50,60)]:
        base=units[str(uid)]['Cost'];surcharge=opt.get(str(oid),{}).get('Cost',0)
        assert base+surcharge==cost,(uid,oid,cost)
    files=json.loads((R/'row-tests/table-files.json').read_text())
    locks=json.loads((R/'clone-locks.json').read_text())
    soft=json.loads((R/'soft-atgm-contract.json').read_text())['rows']
    for t,rows in locks['tables'].items():
        patch=table(files[t].removesuffix('.json'))
        allowed=us['armor_fields'] if t=='ArmorsJson' else us['ammo_fields'] if t=='AmmunitionsJson' else us['ability_fields'] if t=='AbilitiesJson' else {}
        for key,lock in rows.items():
            row={'Id':int(key),**patch[key]}
            for field,want in allowed.get(key,{}).items():
                assert row[field]==want,(t,key,field);row[field]=lock['permitted_before'][field]
            if t=='ArmorsJson' and int(key) in d24['hp']['armors']:
                assert row['MaxHealthPoints']==d24['hp']['value'],key;row['MaxHealthPoints']=json.loads((R.parent/'0.1/source/UserData/FreedomArrow/constants/armors.json').read_text())[key]['MaxHealthPoints']
            if t=='ArmorsJson' and key in topc['armors']:
                a01=json.loads((R.parent/'0.1/source/UserData/FreedomArrow/constants/armors.json').read_text())[key]
                for field in ('HeatArmorTop','KinArmorTop'):assert row[field]==topc['top'],(t,key,field);row[field]=a01[field]
            if t=='AmmunitionsJson':
                for field,want in atgm.get(key,{}).items():
                    assert row[field]==want,(t,key,field);row[field]=ammo01[key][field]
                if key in soft:assert row['Damage']==soft[key]['damage'],(t,key);row['Damage']=ammo01[key]['Damage']  # soft-atgm-contract.json
            assert hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':')).encode()).hexdigest()==lock['sha256'],(t,key)
    # 0.4: sabot close range is the long-range value plus the contract bonus. The row tests check the value against vanilla.
    for aid in pinned:
        row=table('ammunitions').get(str(aid),{});assert row.get('PenetrationAtMinRange') is not None,aid
    # 0.6 cover-wargame-contract.json: MLRS ignore cover 1.0, bombs 0.5, unguided bombs no overpressure, penetration under one MBT kill.
    rp=json.loads((R/'rocketpod-contract.json').read_text())
    assert all(table('ammunitions')[k]['Damage']==v['Damage'] and table('ammunitions')[k]['PenetrationAtMinRange']==table('ammunitions')[k]['PenetrationAtGroundRange']==v['Penetration'] and table('ammunitions')[k]['IgnoreCover']==v['IgnoreCover'] for k,v in rp['rounds'].items()),'0.6 dev.77 rocket pods'
    cw=json.loads((R/'cover-wargame-contract.json').read_text());am=table('ammunitions')
    floor=json.loads((R/'arty-floor-contract.json').read_text())
    assert all(am[k]['PenetrationAtMinRange']==am[k]['PenetrationAtGroundRange']==floor['minimum'] for k in floor['changed_before']),'final artillery penetration floor'
    def hitcap(aid,armor):
        r=am[str(aid)];d=r.get('Damage',cw['damage_unchanged'][str(aid)]);assert d==cw['damage_unchanged'][str(aid)],aid;p=r.get('PenetrationAtMinRange',cw['penetration_final'][str(aid)]);assert p==max(cw['penetration_final'][str(aid)],floor['minimum'] if str(aid) in floor['changed_before'] else 0),aid;return d*p*p/(p*p+armor*armor)<=cw['max_hit']+1e-6
    for aid in cw['mlrs']:assert am[str(aid)]['IgnoreCover']==cw['mlrs_fields'][str(aid)]['IC'] and hitcap(aid,cw['mlrs_armor']),aid
    for aid in cw['bombs']:assert am[str(aid)]['IgnoreCover']==cw['bomb_ignore_cover'],aid
    fb=am[str(cw['fab9000']['ammo'])];assert fb['IgnoreCover']==1.0 and fb['OverpressureRadius']==0 and fb['PenetrationAtMinRange']==fb['PenetrationAtGroundRange']==cw['fab9000']['penetration'],'FAB-9000'
    assert all(am[str(x)]['IgnoreCover']==1.0 for x in cw['ballistic']['ammo']),'ballistic cover'
    assert all([am[k]['DispersionHorizontalRadius'],am[k]['DispersionVerticalRadius']]==v and am[k]['IgnoreCover']==cw['tos']['ignore_cover'] and am[k].get('Damage',30)==cw['tos'].get('damage',30) and am[k].get('DamageOverTimeDuration',0)==cw['tos'].get('fire_seconds',0) for k,v in cw['tos']['ammo'].items()),'TOS'
    ac=json.loads((R/'arty-cover-contract.json').read_text());assert all(am[k]['IgnoreCover']==v['IgnoreCover'] for k,v in ac['ammo'].items()),'0.6 dev.85 artillery cover'
    mk=json.loads((R/'malka-contract.json').read_text());assert all(am[k]['Damage']==f['Damage'] for k,f in mk['ammo'].items()),'0.6 dev.89 Malka damage'
    assert am[str(cw['mop']['ammo'])]['IgnoreCover']==cw['mop']['ignore_cover'] and opt[str(cw['mop']['option'])]['Cost']==cw['mop']['option_cost'],'B-2 MOP'
    bk=json.loads((R/'brm3k-contract.json').read_text())
    assert all(opt[str(o)]['MainSensorId']==bk['sensor'] for o in bk['options']) and arm[str(bk['armor'])]['HeatArmorFront']==arm[str(bk['armor'])]['HeatArmorSides']==bk['heat'],'BRM-3K'
    for aid in cw['no_overpressure']:assert am[str(aid)]['OverpressureRadius']==0 and hitcap(aid,cw['bomb_armor']),aid
    # 0.6 arty-pen-contract.json: artillery penetration the 0.1 caps lowered is x1.5, not above vanilla.
    ap=json.loads((R/'arty-pen-contract.json').read_text())
    def arty_pen(aid,f,x):
        v=table('ammunitions')[aid][f]
        return f.startswith('Penetration') and ((aid=='426' and v==75.0) or (int(aid) in ap['ammo'] and x<v<=x*ap['factor']) or (aid in floor['changed_before'] and v==floor['minimum']))
    mlrs_owned=set(json.loads((R/'cover-wargame-contract.json').read_text())['mlrs_fields'])
    for aid,fields in us['ammo_fields'].items():
        assert all(table('ammunitions')[aid][f]==x or arty_pen(aid,f,x) or (aid in mlrs_owned and f in ('Damage','PenetrationAtMinRange','PenetrationAtGroundRange')) for f,x in fields.items()),aid
    for aid,fields in us['armor_fields'].items():
        for field,want in fields.items():assert arm[aid][field]==want,(aid,field)
    for uid,oids in [(22,[8,1894]),(24,[25]),(33,[42])]:
        for oid in oids:
            row=arm[str(opt[str(oid)]['ArmorId'])];assert (row['MaxHealthPoints'],row['HeatArmorFront'],row['HeatArmorSides'])==(12,700,700)
            assert opt[str(oid)]['Cost']==(65 if oid==1894 else 25)
    for aid in ['2000017','2000018']:assert (arm[aid]['MaxHealthPoints'],arm[aid]['HeatArmorFront'],arm[aid]['HeatArmorSides'])==(12,250,200)
    # M6 Linebacker edits are front HEAT and uparmor HP. Its base stays 14.
    assert arm['47']=={'HeatArmorFront':400,'MaxHealthPoints':14} and arm['288']=={'HeatArmorFront':700,'MaxHealthPoints':14}
    assert arm['60']=={'MaxHealthPoints':14} and arm['322']=={'MaxHealthPoints':14}
    assert '15' not in arm and '120' not in arm,'Linebacker and Sprut default armor unchanged'
    assert arm['2000104']['MaxHealthPoints']==12 and arm['326']['MaxHealthPoints']==12 and arm['336']['MaxHealthPoints']==12
    assert arm['2000020']['MaxHealthPoints']==10 and arm['2000021']['MaxHealthPoints']==10
    assert arm['2000022']['MaxHealthPoints']==10 and arm['2000023']['MaxHealthPoints']==10
    assert opt['1759']['Cost']==25,'M2A3 ESV BUSK3 option 1759 is +25'
    amm=table('ammunitions');assert amm['2000177']['Damage']==10.5 and amm['2000173']['Damage']==10.5
    assert arm[str(table('unit_armors')['983']['ArmorId'])]['MaxHealthPoints']==8
    for aid,fields in atgm.items():assert all(amm[aid][f]==x for f,x in fields.items()),aid
    if json.loads((R/'supply-contract.json').read_text()).get('retired'):
        sc=json.loads((R/'supply-contract.json').read_text())['ammo']  # FA-made rows (2000xxx) carry every field: back to their value before dev.21
        assert all(amm[aid]['SupplyCost']==sc[aid]['was'] if int(aid)>=2000000 else 'SupplyCost' not in amm.get(aid,{}) for aid in supply21),'0.6 dev.87 artillery supply cost vanilla'
    else:
        for aid,x in supply21.items():assert amm[aid]['SupplyCost'] in (x,x*json.loads((R/'logistics-contract.json').read_text())['supply_factor']),aid
    d13=json.loads((R/'dev13-contract.json').read_text())
    for aid,pen in d13['atgm_penetration'].items():assert amm[aid]['PenetrationAtGroundRange']==pen==amm[aid]['PenetrationAtMinRange'],aid
    assert amm['63']['PenetrationAtGroundRange']==700 and amm['2000160']['PenetrationAtGroundRange']==950
    for k,f in d13['member_fields'].items():assert table('squad_members')[k]['SpecialWeaponId']==0,k
    d14=json.loads((R/'dev14-contract.json').read_text())
    for k,q in d14['ammo_quantity'].items():assert table('weapon_ammunitions')[k]['Quantity']==q,k
    for k,f in d14['member_fields'].items():assert all(table('squad_members')[k][x]==v for x,v in f.items()),k
    for rid in d14['retire_members']:assert table('squad_members')[str(rid)] is None,rid
    for c in d14['cards']:assert units[str(c['unit'])]['IsUnitModification'] is False and [r['MaxAvailabilityXp0'] for r in table('specialization_availabilities').values() if r and r.get('UnitId')==c['unit']]==[c['xp0']],c['unit']
    assert opt['1623'] is None and opt['3030'] is None and units['613']['HUDName']=='BARS Igla'
    assert opt['1856'] is None and table('unit_armors')['832']['ArmorId']==81
    # The AH-1W keeps a copy of TOW-2A at 12. Front HEAT spread values are checked against vanilla in the row tests.
    tow=[k for k,r in amm.items() if r and r.get('Name')=='Missile AT TOW2A' and int(k)>=2_000_000]
    assert len(tow)==1 and amm[tow[0]]['Damage']==12.0 and [r for r in live('weapon_ammunitions').values() if r.get('AmmunitionId')==int(tow[0])]
    for uid,oid,total in [(14,1904,70),(180,1958,45),(185,388,30),(41,60,40),(41,2082,80)]:
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
    assert settings['TimeWinMarginPercent']==10,'time-up margin win (Lateralus, 12 November 2026)'
    assert settings['FixedIncomePerMinute']==200 and settings['ShowOverlay'] and not settings['EnableDeveloperFixtures']
    assert settings['TestDurationSeconds']==0 and settings['ScoreLimit']==300 and settings['Ending']=='score_or_time'
    pins=json.loads(z.read('UserData/FAConquestPrototype/compatibility.json'))
    for n in ['Mods/BALocalSkirmish.dll','UserData/FAConquestPrototype/settings.json']:
        assert hashlib.sha256(z.read(n)).hexdigest()==pins[n]
    assert not any(k in n.lower() for n in names for k in ['probe.dll','armory-suite','behavior-tests','engine.json'])
    def scenario_meta(name):return json.loads(z.read(f'UserData/FreedomArrow/scenarios/{name}/meta.json'))
    def scenario_part(name,part):
        raw=zipfile.ZipFile(io.BytesIO(z.read(f'UserData/FreedomArrow/scenarios/{name}/{name}.bascr'))).read(part)
        return ms.load(ms.dec(raw))
    def scenario_objects(name):return scenario_part(name,'objects.bam')
    pairs=[('[FA] [2v2] Dead Center 0.1','[FA] [2v2] Dead Center Skirmish 0.1','crop'),('[FA] [1v1] Dead Center 0.1','[FA] [1v1] Dead Center Skirmish 0.1',(4250,9000)),('[FA] [2v2] Chkalovsk Airbase 0.1','[FA] [2v2] Chkalovsk Airbase Skirmish 0.1',(9000,4850.01636)),('[FA] [2v2] Highway of Death 0.1','[FA] [2v2] Highway of Death Skirmish 0.1',(6000,9000))]
    for net_name,sk_name,crop in pairs:
        for name,kind in [(net_name,2),(sk_name,3)]:
            assert f'UserData/FreedomArrow/scenarios/{name}/{name}.bascr' in names
            # Every machine must write identical .bascr bytes: the lobby compares their hash.
            assert all(i.create_system==3 and i.external_attr==0o600<<16 for i in zipfile.ZipFile(io.BytesIO(z.read(f'UserData/FreedomArrow/scenarios/{name}/{name}.bascr'))).infolist()),name
            meta=scenario_meta(name);assert meta['gameVersion']=='1.2.2' and meta['type']==kind,name
            assert [o['defV'] for o in meta['pblOpt'] if o.get('desc')=='ui_lobby_Timer_desc']==[45],name
        net,sk=scenario_objects(net_name),scenario_objects(sk_name)
        nl,sl=ms.extract_layout(net),ms.extract_layout(sk)
        assert set(nl)==set(sl),net_name
        for r,src in nl.items():
            skip=ms.PLAYER_KEEP if r[0]=='player' else ms.KEEP
            for k,v in src.items():
                if k not in skip:assert sl[r][k]==v,(net_name,r,k)
        for o in [o for o in sk if o.get('_type')==7]:
            src=nl[('playable',)]
            for k,v in src.items():
                if k not in ms.KEEP:assert o[k]==v,(net_name,k)
        fight={o['_uid'] for o in sk if o.get('_type')==3 and o['_dname'] in ('Alpha team','Bravo team')}
        assert any(o.get('isBot') for o in sk if o.get('_type')==13 and o.get('ownTeam',{}).get('id') in fight),sk_name
        assert {o.get('teamSide') for o in net if o.get('_type')==3}=={0,1},net_name
        cams=[o for o in net if o.get('_type')==18]
        assert len(cams)==2 and all(o.get('actOnStart') for o in cams) and {o['team']['id'] for o in cams}==fight,net_name
        # Each camera looks at a tag on its own side, toward the zone centre.
        tags={o['_uid']:o['pos'] for o in net if o.get('_type')==6};zc=[o['pos'] for o in net if o.get('_type')==15]
        centre={k:sum(p[k] for p in zc)/len(zc) for k in 'XZ'}
        for cam in cams:
            look=tags[cam['aimTag']['id']];d=lambda p:((p['X']-centre['X'])**2+(p['Z']-centre['Z'])**2)**0.5
            assert d(look)<d(cam['pos']) and (look['X']-cam['pos']['X'])*(centre['X']-cam['pos']['X'])+(look['Z']-cam['pos']['Z'])*(centre['Z']-cam['pos']['Z'])>0,(net_name,cam['_dname'])
        assert any(n.get('nnKey')=='pauseGame' for n in scenario_part(net_name,'nodes.bam')['b']),net_name
        assert not any(n.get('nnKey')=='pauseGame' for n in scenario_part(sk_name,'nodes.bam')['b']),sk_name
        if crop=='crop':
            west=min(o['pos']['X']-ms.world_x_half(o) for o in net if o.get('_type')==15);east=max(o['pos']['X']+ms.world_x_half(o) for o in net if o.get('_type')==15);box=nl[('playable',)]
            assert abs(box['scale']['Z']-dc2.MAP_LENGTH)<1e-3 and abs(box['pos']['Z']-dc2.MAP_LENGTH/2)<1e-3
            assert abs((box['pos']['X']-box['scale']['X']/2)-(west-dc2.FLANK_MARGIN))<1e-2 and abs((box['pos']['X']+box['scale']['X']/2)-(east+dc2.FLANK_MARGIN))<1e-2
        else:
            box=nl[('playable',)];assert abs(box['scale']['X']-crop[0])<1e-3 and abs(box['scale']['Z']-crop[1])<1e-3,net_name
    dc=scenario_meta('[FA] [1v1] Dead Center 0.1');dcsk=scenario_meta('[FA] [1v1] Dead Center Skirmish 0.1')
    dc_zones={'38':2,'39':2,'40':2,'41':3,'42':3}
    assert dc['type']==2 and dcsk['type']==3 and settings['MapZoneWeights'][dc['scenario']]==dc_zones==settings['MapZoneWeights'][dcsk['scenario']]
    assert {t['teamSide'] for t in dc['teams']}=={0,1}=={t['teamSide'] for t in dcsk['teams']}
    assert {o['desc']:o['defV'] for o in dc['pblOpt']}=={'ui_lobby_StartMoney_desc':1500,'ui_lobby_Income_desc':300,'ui_lobby_Timer_desc':45}
    ck=scenario_meta('[FA] [2v2] Chkalovsk Airbase 0.1');cksk=scenario_meta('[FA] [2v2] Chkalovsk Airbase Skirmish 0.1')
    ck_zones={'31':2,'32':2,'33':2,'34':3,'35':3,'36':4,'37':4}
    assert ck['type']==2 and cksk['type']==3 and ck['sceneName']=='Airbase' and settings['MapZoneWeights'][ck['scenario']]==ck_zones==settings['MapZoneWeights'][cksk['scenario']]
    assert {o['_uid']:o['hudText'] for o in scenario_objects(ck['scenario']) if o.get('_type')==15}=={31:'Charlie',32:'Alpha',33:'Bravo',34:'Delta',35:'Echo',36:'Golf',37:'Foxtrot'}
    # Every Chkalovsk spawn faces within 60 degrees of the zone centre (dev.24 turned Bravo's Spawn point 5 from north).
    ckobj=scenario_objects(ck['scenario']);zc=[o['pos'] for o in ckobj if o.get('_type')==15];cx=sum(p['X'] for p in zc)/len(zc);cz=sum(p['Z'] for p in zc)/len(zc)
    for o in [o for o in ckobj if o.get('_type')==10]:
        yaw=math.degrees(2*math.atan2(o['rotate']['Y'],o['rotate']['W']));to=math.degrees(math.atan2(cx-o['pos']['X'],cz-o['pos']['Z']))
        assert abs((yaw-to+180)%360-180)<60,(o['_dname'],yaw,to)
    for net_name,sk_name,_ in pairs:
        for name in (net_name,sk_name):
            objs=scenario_objects(name);head=scenario_part(name,'head.bam')
            play=next(o for o in objs if o.get('_type')==7)
            assert head['spz']==play['_uid'],(name,'inactive playable zone')
    ckbox=next(o for o in ckobj if o.get('_type')==7)
    assert abs(ckbox['pos']['X']-ckbox['scale']['X']/2)<.001 and abs(ckbox['pos']['Z']-ckbox['scale']['Z']/2)<.001
    alpha=next(o for o in ckobj if o.get('_type')==15 and o['hudText']=='Alpha')
    assert abs(ckbox['pos']['Z']+ckbox['scale']['Z']/2-alpha['pos']['Z']-1500)<.001
    for name in ('[FA] [1v1] Dead Center 0.1','[FA] [1v1] Dead Center Skirmish 0.1','[FA] [2v2] Highway of Death 0.1','[FA] [2v2] Highway of Death Skirmish 0.1'):
        objs=scenario_objects(name);zones=[o for o in objs if o.get('_type')==15]
        cx=sum(o['pos']['X'] for o in zones)/len(zones);cz=sum(o['pos']['Z'] for o in zones)/len(zones)
        red=next(o['_uid'] for o in objs if o.get('_type')==3 and o['teamSide']==1)
        for o in objs:
            if o.get('_type')!=10 or ('Dead Center' in name and o['team']['id']!=red):continue
            yaw=2*math.atan2(o['rotate']['Y'],o['rotate']['W']);to=math.atan2(cx-o['pos']['X'],cz-o['pos']['Z'])
            assert abs((yaw-to+math.pi)%(2*math.pi)-math.pi)<1e-5,(name,o['_dname'])
        if 'Highway' in name:
            values=dict(Alpha=2,Bravo=2,Charlie=2,Delta=6,Echo=6,Foxtrot=3,Golf=2)
            assert {o['hudText'] for o in zones}==set(values)
            assert {str(o['_uid']):values[o['hudText']] for o in zones}==settings['MapZoneWeights'][name]
            assert all(o['ZoneIcon']==ord(o['hudText'][0])-ord('A')+1 for o in zones)
            assert all(len(t['slots'])==2 for t in scenario_meta(name)['teams'])
            assert len([o for o in objs if o.get('_type')==13])==4
            assert all(o['_uid']>=10000 for o in zones)
    for name in ('playable_borders_installed','playable_borders_bounds','playable_borders_material','lobby_deck_refresh_installed','lobby_deck_refresh'):
        assert name.encode('utf-16le') in z.read('Mods/FreedomArrow.Runtime.dll')
    # Lateralus's authored maps keep his script. Online pauses for deployment; Skirmish has none and bots in every slot.
    # Airport 5v5 always plays on Play Zone Large; its size logic and lobby Size option are gone.
    for mod,scene,slots in ((airport_5v5,'Airport',5),(baltiisk_3v3,'Baltiisk',5),(dam_3v3,'Dam',5)):
        for flavor in mod.FLAVORS:
            name,kind=flavor['name'],flavor['kind']
            meta=scenario_meta(name);objs=scenario_objects(name);nodes=scenario_part(name,'nodes.bam');head=scenario_part(name,'head.bam')
            assert meta['type']==kind and meta['sceneName']==scene and meta['guid']==flavor['guid'] and [len(t['slots']) for t in meta['teams']]==[slots,slots],name
            assert [o['defV'] for o in meta['pblOpt'] if o.get('desc')=='ui_lobby_Timer_desc']==[45],name
            plays=[o for o in objs if o.get('_type')==7];assert len(plays)==1 and head['spz']==plays[0]['_uid'],name
            ids={n['id'] for n in nodes['b']};assert all(c['a'] in ids and c['b'] in ids for c in nodes['c']),name
            zones=[o for o in objs if o.get('_type')==15]
            assert {str(o['_uid']):mod.VALUES[o['hudText']] for o in zones}==settings['MapZoneWeights'][name] and all(o['hudText']==o['_dname'] for o in zones),name
            assert all(o['ZoneIcon']==ord(o['hudText'][0])-ord('A')+1 and len(o['capturableBy'])==2 for o in zones),name
            assert any(n['nnKey']=='pauseGame' for n in nodes['b'])==(kind==2) and all(o.get('isBot',False)==(kind==3) for o in objs if o.get('_type')==13),name
            if mod is airport_5v5:
                assert (plays[0]['_uid'],plays[0]['scale']['X'],plays[0]['scale']['Z'])==(10,9000.0,9000.0),name
                assert not [o for o in meta['pblOpt'] if 'Size' in o['desc']] and not {n['nnKey'] for n in nodes['b']}&{'objVisible2','act_pz','Network Players'},name
    # Lateralus 2026-11-12: every FA map uses the vanilla 15 s zone capture time.
    for name in sorted({n.split('/')[3] for n in names if n.startswith('UserData/FreedomArrow/scenarios/') and n.endswith('.bascr')}):
        assert {o['capTime'] for o in scenario_objects(name) if o.get('_type')==15}=={15.0},name
    assert settings['SetupSeconds']==180 and settings['OpeningDelaySeconds']==300
    assert settings['Crits'] and settings['CritDamage']==9.3 and settings['AtgmCritDamage']==8.9 and settings['RearCritMinPenetration']==250 and settings['FrontArcDegrees']==60
    assert json.loads(z.read('UserData/FreedomArrow/game-config.json'))=={'DefaultPlayerMoney':1500,'ForestDamageTaken':0.7,'BuildingDamageFloor':0.18,'BuildingDamagePerSoldier':0,'MinorMobilityMultiplier':0.4,'ShockedMoveSpeed':0.7,'PanickedMoveSpeed':0.4,'FlareRerollCap':4,'AaCooldownEnabled':True,'AaCooldownShadowOnly':False}
    assert [o['defV'] for o in json.loads(z.read('UserData/FreedomArrow/scenarios/[FA] [2v2] Dead Center 0.1/meta.json'))['pblOpt'] if o.get('desc')=='ui_lobby_StartMoney_desc']==[1500]
    for aid,fields in us['ability_fields'].items():assert table('abilities')[aid]['APSCooldown']==fields['APSCooldown'],aid
    print(f'PASS: {len(manifest["sha256"])} payload hashes; metadata and held tables; requested vehicle and detection data; 200-income setting. No native/runtime result.')
    print(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name)

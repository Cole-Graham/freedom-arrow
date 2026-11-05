"""Generate the versioned 0.2 overlay on frozen 0.1.1 constants.

Includes reviewed dev.1/dev.2 and the US/Baltic data batch.
Card splits, squad resizing and option retirement are listed in structural-contract.json.
"""
from pathlib import Path
import argparse, copy, hashlib, json, sys
R=Path(__file__).resolve().parent
# Saved decks hold this option ID. A failure here means a clone moved above it.
XM913_APS_OPTION=2000379
sys.path.insert(0,str(R.parents[1]))
from pipeline.crypto import aes_decrypt
from pipeline.tables import FIELD_TO_FILE

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--vanilla-dir',required=True,type=Path)
    args=ap.parse_args()
    base=R.parent/'0.1/source/UserData/FreedomArrow'
    out=R/'source/UserData/FreedomArrow/constants'
    pins=json.loads((base/'compatibility.json').read_text())
    original, effective, patches, frozen = {}, {}, {}, {}
    for table,digest in pins['source_plaintext_sha256'].items():
        raw=aes_decrypt((args.vanilla_dir/(table+'.b64')).read_text())
        assert hashlib.sha256(raw).hexdigest()==digest,f'{table} does not match its pin. Delete this snapshot and run pipeline decrypt again; see TESTING.md.'
        original[table]={r['Id']:r for r in json.loads(raw)}
        patches[table]=json.loads((base/'constants'/FIELD_TO_FILE[table]).read_text())
        effective[table]=copy.deepcopy(original[table])
        for key,fields in patches[table].items():
            effective[table].setdefault(int(key),{'Id':int(key)}).update(fields)
        frozen[table]=copy.deepcopy(effective[table])
    next_id=max(i for rows in effective.values() for i in rows if i>=2_000_000)+1
    audit=[]
    def put(table,rid,fields,why):
        before=copy.deepcopy(effective[table].get(rid))
        effective[table].setdefault(rid,{'Id':rid}).update(fields)
        patches[table].setdefault(str(rid),{}).update(fields)
        audit.append(dict(table=table,id=rid,before=before,after=copy.deepcopy(effective[table][rid]),reason=why))
    def clone(table,rid,fields,why):
        nonlocal next_id
        new=next_id;next_id+=1
        row=copy.deepcopy(effective[table][rid]);row.pop('Id');row.update(fields)
        put(table,new,row,why)
        return new
    def options(uid):
        mods={r['Id'] for r in effective['ModificationsJson'].values() if r['UnitId']==uid}
        return [r for r in effective['OptionsJson'].values() if r['ModificationId'] in mods]
    def armor(uid,option,changes,why):
        selected=effective['OptionsJson'][option];old=selected['ArmorId']
        assert option in {r['Id'] for r in options(uid)}
        new=clone('ArmorsJson',old,changes,why)
        hits=0
        for link in list(effective['UnitArmorsJson'].values()):
            if link['UnitId']==uid and link['ArmorId']==old:
                put('UnitArmorsJson',link['Id'],{'ArmorId':new},why);hits+=1
        for opt in options(uid):
            if opt['ArmorId']==old:put('OptionsJson',opt['Id'],{'ArmorId':new},why)
        assert hits>0
    armor(235,551,{'MaxHealthPoints':14},'BMO-T base 12 to14 HP; ERA already14 retained')
    armor(151,2089,{'MaxHealthPoints':10},'Kornet-D1 base14 to10 HP; base protection retained')
    armor(151,2090,{'HeatArmorFront':400,'HeatArmorSides':400},'Kornet-D1 armored10 HP, front/side HEAT400')
    armor(144,1986,{'MaxHealthPoints':14,'HeatArmorFront':400,'HeatArmorSides':400},'Sprut cage14 HP, front/side HEAT400')
    old=effective['OptionsJson'][1986]['MobilityId']
    new=clone('MobilityJson',old,{'MaxSpeedRoad':60.0},'Sprut cage road70 to60 km/h; other mobility retained')
    for link in list(effective['UnitPropulsionsJson'].values()):
        if link['UnitId']==144 and link['MobilityId']==old:
            put('UnitPropulsionsJson',link['Id'],{'MobilityId':new},'Sprut cage mobility association')
    put('OptionsJson',1986,{'MobilityId':new},'Sprut cage selected mobility')
    # Vanilla ability82 already has the two-charge APS desired by the0.1 policy.
    # Reuse it; do not turn on the shared disabled clone used by other vehicles.
    aps=effective['AbilitiesJson'][82]
    assert aps['IsAPS'] and aps['APSQuantity']==2
    opt=effective['OptionsJson'][2082]
    assert opt['Ability2Id']==2000203 and not effective['AbilitiesJson'][2000203]['IsAPS']
    put('OptionsJson',2082,{'Ability2Id':82},'M1283 AMPV BRAT APS retained; two original ready charges')
    put('UnitAbilitiesJson',1029,{'AbilityId':82},'M1283 AMPV APS inventory matches option2082')
    unit_abilities={(r['UnitId'],r['AbilityId']) for r in effective['UnitAbilitiesJson'].values()}
    mods={r['Id']:r['UnitId'] for r in effective['ModificationsJson'].values()}
    for option in effective['OptionsJson'].values():
        for field in ['Ability1Id','Ability2Id','Ability3Id']:
            aid=option[field]
            if not aid or (option['Id']==279 and aid==4):continue
            assert (mods[option['ModificationId']],aid) in unit_abilities,('option ability missing from unit',option['Id'],aid)
    contract=json.loads((R/'vehicle-contract.json').read_text())
    for key,cost in contract['base_costs'].items():
        put('Units',int(key),{'Cost':cost},'Requested base cost; inspect configured surcharges separately')
    for key,cost in contract['option_costs'].items():
        put('OptionsJson',int(key),{'Cost':cost},'Requested surcharge or documented held-split/Reserve fallback')
    for uid,oids in [(1,[504,505]),(425,[1881,1882])]:
        for oid in oids:armor(uid,oid,{'MaxHealthPoints':10},'BTR82A/BTR80 all armor choices10 HP; shared BRDM3 unchanged')
    # B15 is a turret option with no selected armor. Add only its own association.
    old=effective['UnitArmorsJson'][415]['ArmorId']
    assert effective['OptionsJson'][643]['ArmorId']==0
    new=clone('ArmorsJson',old,{'HeatArmorFront':400,'HeatArmorSides':400,'IsDefault':False},'B15 only400/400 HEAT; B10/B11 retain120/100')
    link=next_id;next_id+=1
    put('UnitArmorsJson',link,{'UnitId':254,'ArmorId':new},'B15 new armor association')
    put('OptionsJson',643,{'ArmorId':new},'B15 selected armor without changing B10/B11 default')
    for oid in [3067,3070,3071,3072]:armor(628,oid,{'MaxHealthPoints':8},'Uran9 all four top-slot profiles8 HP; price held')
    for oid in [564,565]:armor(158,oid,{'HeatArmorSides':200},'T80BVM2017/held2018 side HEAT200;2018+ stays400')
    us=json.loads((R/'us-baltic-contract.json').read_text())
    for key,fields in us['armor_fields'].items():put('ArmorsJson',int(key),fields,'Explicit US/Baltic armor/HP target or M6 Linebacker front HEAT; shared consumers audited')
    for key,fields in us['ammo_fields'].items():put('AmmunitionsJson',int(key),fields,'Tank-gun sabot10 or all live Javelin and Spike LR10.5')
    # Cluster is the dedicated anti-armor round and keeps vanilla penetration. Other unguided artillery is capped. Laser-guided HE sits halfway from vanilla to the unguided value.
    for aid,row in effective['AmmunitionsJson'].items():
        if row['TrajectoryType'] in (20,30,40) and not row['LaserGuided'] and not row['GenerateSmoke'] and row['Damage']>1 and not row['TopArmorAttack']:
            assert row['PenetrationAtGroundRange']<=30 and row['PenetrationAtMinRange']==row['PenetrationAtGroundRange'],('artillery penetration',aid)
    for uid in us['stryker_scope']:
        for old in [2000017,2000018]:
            oid=next(o['Id'] for o in options(uid) if o['ArmorId']==old)
            armor(uid,oid,{'MaxHealthPoints':12,'HeatArmorFront':700,'HeatArmorSides':700},'Named Stryker SRAT scope, 700; RV/ATGM unchanged; legacy APS option has no APS')
    # TypeX has no armor slot; repoint its unit association, preserving the original row.
    old=effective['UnitArmorsJson'][983]['ArmorId'];assert old==341
    new=clone('ArmorsJson',old,{'MaxHealthPoints':8},'Playable Baltic TypeX8 HP')
    put('UnitArmorsJson',983,{'ArmorId':new},'TypeX unit-specific armor')
    # Uparmor never changes HP. Only the listed exceptions may differ.
    for uid,row in effective['Units'].items():
        hp={effective['ArmorsJson'][l['ArmorId']]['MaxHealthPoints'] for l in effective['UnitArmorsJson'].values() if l['UnitId']==uid}
        assert row['Type']!=4 or len(hp)<2 or uid in us['uparmor_hp_exceptions'],('uparmor changes HP',uid,hp)
    # Lateralus's detection proposal: table part. Config part is in detection-config.json.
    det=json.loads((R/'detection-contract.json').read_text())
    held=set(det['optics_held_sensors'])
    def new_optics(sid,row):return det['optics_ground_drones'].get(str(sid)) or det['optics_ground_tiers'][str(int(row['OpticsGround']))]
    for sid,row in list(effective['SensorsJson'].items()):
        if sid not in held:
            put('SensorsJson',sid,{'OpticsGround':new_optics(sid,row)},'Ground optics tier; shared with any unit on this sensor')
    def stealth_class(u):
        if u['Type']==4 and u['CategoryType'] in (0,2,3):return 'vehicle'
        if u['Type']!=2 or u['CategoryType']==4:return None
        if u['Stealth']==det['stealth']['sniper']:return 'sniper'  # Any unit at 3 in vanilla stays at 3.
        if u['CategoryType']==0:return 'recon_infantry'
        return 'infantry'
    def stealth_value(u):
        if str(u['Id']) in det['stealth_unit_values']:return det['stealth_unit_values'][str(u['Id'])]
        cls=stealth_class(u)
        return det['stealth'][cls] if cls else None
    for uid,row in list(effective['Units'].items()):
        v=stealth_value(row)
        if v is not None and row['Stealth']!=v:put('Units',uid,{'Stealth':v,'CurrentStealth':v},'Detection proposal stealth')
    for key,v in det['stealth_override_options'].items():put('OptionsJson',int(key),{'StealthOverride':v},'Recon option at UI 1.5 in vanilla goes to UI 1.25')
    for o in effective['OptionsJson'].values():
        unit=effective['Units'][mods[o['ModificationId']]]
        assert not o['StealthOverride'] or stealth_class(unit)!='vehicle' or o['StealthOverride'] in (1.0,0.8),('vehicle override',o['Id'])
    # Booker keeps its vanilla ready APS on both cards. The split copies these rows to the XM913.
    assert effective['AbilitiesJson'][88]['IsAPS'] and effective['AbilitiesJson'][88]['APSQuantity']==2
    put('OptionsJson',1951,{'Ability2Id':88},'M10 Booker APS option restored')
    put('UnitAbilitiesJson',868,{'AbilityId':88},'M10 Booker APS inventory matches option 1951')
    # Structural changes: added cards, deleted rows and squad edits.
    st=json.loads((R/'structural-contract.json').read_text())
    def links(table,uid):return [r['Id'] for r in effective[table].values() if r['UnitId']==uid]
    def add_unit(uid,template,fields,why):
        row=copy.deepcopy(effective['Units'][template]);row.pop('Id');row.update(fields);put('Units',uid,row,why)
    def drop(table,rid):
        del effective[table][rid];patches[table][str(rid)]=None
    for s in st['splits']:
        why='Card split '+s['name']
        add_unit(s['unit'],s['parent'],dict(HUDName=s['name'],Name=s['name'],Cost=s['cost']),why)
        for rid in s['move_turrets']:put('TurretUnitsJson',rid,{'UnitId':s['unit']},why)
        for rid in s['clone_turrets']:clone('TurretUnitsJson',rid,{'UnitId':s['unit']},why)
        for rid in s['move_ammo']:put('WeaponAmmunitionsJson',rid,{'UnitId':s['unit']},why)
        for table in ['WeaponAmmunitionsJson','SensorUnitsJson','UnitPropulsionsJson','UnitArmorsJson','UnitAbilitiesJson']:
            for rid in links(table,s['parent']):clone(table,rid,{'UnitId':s['unit']},why)
        new_mods={}
        for key in sorted({*map(int,s['copied']),*s['moved'].values()}):
            new_mods[key]=clone('ModificationsJson',key,{'UnitId':s['unit']},why)
        for key,ids in s['copied'].items():
            for oid in ids:clone('OptionsJson',oid,{'ModificationId':new_mods[int(key)]},why)
        for order,(key,old) in enumerate(s['moved'].items()):
            f={'ModificationId':new_mods[old],'Order':order,'Cost':s.get('keep_cost',{}).get(key,0)}
            if s.get('concat',{}).get(key) is not None or effective['OptionsJson'][int(key)]['ConcatenateWithUnitName']==' Javelin':f['ConcatenateWithUnitName']=s.get('concat',{}).get(key,'')
            put('OptionsJson',int(key),f,why)
        row=next(r for r in effective['SpecializationAvailabilitiesJson'].values() if r['UnitId']==s['parent'])
        clone('SpecializationAvailabilitiesJson',row['Id'],{'UnitId':s['unit'],'MaxAvailabilityXp0':s['pool']['new']},why)
        put('SpecializationAvailabilitiesJson',row['Id'],{'MaxAvailabilityXp0':s['pool']['parent']},why)
    for mid in st['retire_mods']:
        for oid in [r['Id'] for r in effective['OptionsJson'].values() if r['ModificationId']==mid]:drop('OptionsJson',oid)
        drop('ModificationsJson',mid)
    for oid in st['retire_options']:drop('OptionsJson',oid)
    for rid in st['retire_members']:drop('SquadMembersJson',rid)
    for rid in st['retire_squad_weapons']:drop('SquadWeaponsJson',rid)
    for rid in st['retire_ammo']:drop('WeaponAmmunitionsJson',rid)
    audit[:]=[a for a in audit if a['id'] in effective[a['table']]]
    # Saved decks can still hold options that moved to a new card.
    (R/'source/UserData/FreedomArrow/deck-migration.json').write_text(json.dumps({key:s['parent'] for s in st['splits'] for key in s['moved']},indent=2,sort_keys=True)+'\n')
    why='One-launcher and team-size policy'
    for key,f in st['member_fields'].items():put('SquadMembersJson',int(key),f,why)
    for key,aid in st['armor_links'].items():put('UnitArmorsJson',int(key),{'ArmorId':aid},'Five-man team health')
    for key,f in st['unit_fields'].items():put('Units',int(key),f,'Separate card')
    pools={}
    for p in st['new_pools']:pools[p['unit']]=clone('SpecializationAvailabilitiesJson',p['like'],{'UnitId':p['unit'],'MaxAvailabilityXp0':p['xp0']},'Separate card availability')
    for key,n in st['set_pools'].items():put('SpecializationAvailabilitiesJson',int(key),{'MaxAvailabilityXp0':n},'Requested availability')
    # Saved decks store option IDs. Clone new rows only below this line, so existing IDs stay stable.
    template=next(iter(effective['TransportAvailabilitiesJson']))
    for p in st['new_pools']:
        for t in p['transports']:clone('TransportAvailabilitiesJson',template,{'SpecializationAvailabilityId':pools[p['unit']],'UnitId':t},'Separate card transport')
    xm913_mod=next(r['Id'] for r in effective['ModificationsJson'].values() if r['UnitId']==720 and r['Name']==effective['ModificationsJson'][549]['Name'])
    xm913_aps=clone('OptionsJson',1951,{'ModificationId':xm913_mod},'M10 Booker XM913 APS option')
    assert xm913_aps==XM913_APS_OPTION,xm913_aps
    # All Stryker SRAT packages are 700 front and side.
    for uid,oid in [(21,50),(25,44),(20,70),(20,1934),(5,1943),(5,1944),(452,1946),(452,1947)]:
        armor(uid,oid,{'HeatArmorFront':700,'HeatArmorSides':700},'All Stryker SRAT 700 HEAT front and side')
    # Every TUSK 2 package is 700 side. TUSK 1 side is already 400.
    for uid,oid in [(191,415),(191,416),(243,590),(243,593),(244,596),(245,599)]:
        armor(uid,oid,{'HeatArmorSides':700},'TUSK 2 side HEAT 700')
    armor(78,1834,{'HeatArmorFront':400,'HeatArmorSides':400},'AAVP SU kit 400 HEAT')
    armor(240,574,{'HeatArmorSides':200},'BMPT baseline side HEAT 200')
    armor(9,624,{'HeatArmorSides':200},'T-72B1 side HEAT 200')
    # Every active APS ability uses the longer cooldown.
    assert {i for i,a in effective['AbilitiesJson'].items() if a['IsAPS']}==set(map(int,us['ability_fields'])),'APS list changed'
    for key,fields in us['ability_fields'].items():put('AbilitiesJson',int(key),fields,'APS cooldown 30 seconds')
    # Javelin breakpoints. Top 100 is a 3-hit kill with a sliver left; the T-72 family at top 80 is a 2-hit kill.
    why='Top HEAT for the Javelin breakpoint'
    for uid,top in [(u,100) for u in [2,53,54,191,243,244,245,158,239,716,236,237,238,13]]+[(u,80) for u in [9,157,615,703,717,240,255,235]]:
        for link in [r for r in effective['UnitArmorsJson'].values() if r['UnitId']==uid]:
            old=link['ArmorId']
            if effective['ArmorsJson'][old]['HeatArmorTop']==top:continue
            # The plain T-80BV hull stays at top 80. The clone keeps the later row IDs stable.
            new=clone('ArmorsJson',old,{'HeatArmorTop':80 if effective['ArmorsJson'][old]['Name']=='Armor T80BV' else top},why)
            put('UnitArmorsJson',link['Id'],{'ArmorId':new},why)
            for opt in options(uid):
                if opt['ArmorId']==old:put('OptionsJson',opt['Id'],{'ArmorId':new},why)
    # Freeze every pre-dev3 added row except explicitly permitted fields/values.
    locks=json.loads((R/'clone-locks.json').read_text())
    def permitted(table,rid):
        return (us['armor_fields'] if table=='ArmorsJson' else us['ammo_fields'] if table=='AmmunitionsJson' else us['ability_fields'] if table=='AbilitiesJson' else {}).get(str(rid),{})
    for table,rows in locks['tables'].items():
        for key,lock in rows.items():
            row=copy.deepcopy(effective[table][int(key)])
            for field,value in permitted(table,int(key)).items():
                assert row[field]==value,(table,key,field)
                row[field]=lock['permitted_before'][field]
            assert hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':')).encode()).hexdigest()==lock['sha256'],('locked clone drift',table,key)
    # Unit costs and old profile mutations are explicit field allow-lists.

    for table,rows in frozen.items():
        for rid,row in rows.items():
            if rid>=2_000_000:
                want=copy.deepcopy(row);want.update(permitted(table,rid));assert effective[table][rid]==want,(table,rid)
    for uid,row in frozen['Units'].items():
        want=copy.deepcopy(row)
        if str(uid) in contract['base_costs']:want['Cost']=contract['base_costs'][str(uid)]
        want.update(st['unit_fields'].get(str(uid),{}))
        v=stealth_value(row)
        if v is not None:want['Stealth']=want['CurrentStealth']=v
        assert effective['Units'][uid]==want,('unexpected unit change',uid)
    assert set(effective['Units'])==set(frozen['Units'])|{s['unit'] for s in st['splits']}
    for mid,row in frozen['ModificationsJson'].items():
        if mid in st['retire_mods']:continue
        want=copy.deepcopy(row)
        assert effective['ModificationsJson'][mid]==want,('unexpected modification change',mid)
    for aid,row in frozen['AmmunitionsJson'].items():
        want=copy.deepcopy(row);want.update(us['ammo_fields'].get(str(aid),{}));assert effective['AmmunitionsJson'][aid]==want,('unexpected ammo change',aid)
    for rid,row in frozen['SquadMembersJson'].items():
        if rid in st['retire_members']:continue
        want=copy.deepcopy(row);want.update(st['member_fields'].get(str(rid),{}))
        assert effective['SquadMembersJson'][rid]==want,('unexpected squad change',rid)
    for sid,row in frozen['SensorsJson'].items():
        want=copy.deepcopy(row)
        if sid not in held:want['OpticsGround']=new_optics(sid,row)
        assert effective['SensorsJson'][sid]==want,('unexpected sensor change',sid)
    for table in ['WeaponsJson','TurretWeaponsJson']:
        assert effective[table]==frozen[table]
    # Validate every changed foreign key against the complete effective graph.
    schema=json.loads((R/'source/UserData/FreedomArrow/reference-schema.json').read_text())
    for a in audit:
        for field,(target,nullable) in schema.get(a['table'],{}).items():
            v=a['after'][field]
            assert (v==0 and nullable) or v in effective[target],(a['table'],a['id'],field,v)
    # A deleted row must leave no reference behind, in any row.
    for table,rules in schema.items():
        if table not in effective:continue
        for row in effective[table].values():
            for field,(target,nullable) in rules.items():
                v=row.get(field,0)
                assert (v==0 and nullable) or v in effective.get(target,{v:1}),('dangling',table,row['Id'],field,v)
    # The game's squad loader needs these for every unit.
    for uid in effective['Units']:
        weapons=[r['WeaponId'] for r in effective['SquadWeaponsJson'].values() if r['UnitId']==uid]
        assert len(weapons)==len(set(weapons)),('duplicate squad weapon',uid)
        for m in effective['SquadMembersJson'].values():
            if m['UnitId']==uid:assert {m['PrimaryWeaponId'],m['SpecialWeaponId']}-{0}<=set(weapons),('member weapon not listed',uid,m['Id'])
    out.mkdir(parents=True,exist_ok=True)
    for table,rows in patches.items():(out/FIELD_TO_FILE[table]).write_text(json.dumps(rows,indent=2)+'\n')
    # Resolve consumers from the final effective graph, including shared Javelin rounds.
    affected=set()
    for change in audit:
        table=change['table'];rid=change['id'];row=change['after']
        if table=='Units':affected.add(rid)
        if 'UnitId' in row:affected.add(row['UnitId'])
        if table=='OptionsJson':affected.add(effective['ModificationsJson'][row['ModificationId']]['UnitId'])
        if table=='AmmunitionsJson':affected.update(x['UnitId'] for x in effective['WeaponAmmunitionsJson'].values() if x['AmmunitionId']==rid)
        if table=='ArmorsJson':affected.update(x['UnitId'] for x in effective['UnitArmorsJson'].values() if x['ArmorId']==rid)
        if table=='MobilityJson':affected.update(x['UnitId'] for x in effective['UnitPropulsionsJson'].values() if x['MobilityId']==rid)
    record={'version':contract['version'],'source_build':pins['source_build_id'],
            'baseline_commit':'72783a51acfd0fac53fc1f40ea881f0f009fe6e0',
            'affected_units':sorted(affected),'new_profile_ids':list(range(2000218,next_id)),
            'baseline_rows_locked':locks['counts'],'allowed_clone_fields':{t:{k:list(permitted(t,int(k))) for k in rows if permitted(t,int(k))} for t,rows in locks['tables'].items()},'source_table_pins_matched':24,
            'rows':{k:len(v) for k,v in patches.items()},'changes':audit,
            'scope':'data generation only; no runtime, armory or behavior result'}
    (R/'constant-audit.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:record[k] for k in ['affected_units','new_profile_ids','baseline_rows_locked','source_table_pins_matched']}))
if __name__=='__main__':main()

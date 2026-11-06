"""Generate the versioned 0.5 overlay (0.4 history plus 0.5 accuracy) on frozen 0.1.1 constants.

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
import dev_version

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--vanilla-dir',required=True,type=Path)
    args=ap.parse_args()
    dev_version.ensure()
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
    # 0.4: tank-gun sabot close range is the long-range value plus a fixed bonus.
    sabot=json.loads((R/'sabot-pin-contract.json').read_text())
    pin={i:effective['AmmunitionsJson'][i]['PenetrationAtGroundRange']+sabot['close_range_bonus'] for i in sabot['pinned_ammo']}
    for aid,pen in pin.items():
        assert effective['AmmunitionsJson'][aid]['ArmorTargeted']==1,('pin needs a KE row',aid)
        put('AmmunitionsJson',aid,{'PenetrationAtMinRange':pen},'Sabot close range = long-range penetration + bonus')
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
    def new_optics(sid,row):return det['optics_ground_overrides'].get(str(sid)) or det['optics_ground_drones'].get(str(sid)) or det['optics_ground_tiers'][str(int(row['OpticsGround']))]
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
    for key,fields in us['ability_fields'].items():put('AbilitiesJson',int(key),fields,'APS cooldown 10 seconds')
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
    # 0.4 dev.5: smoke by price, unit HP and Bumerang uparmor HEAT. New rows are cloned here, below the saved-deck rows.
    d5=json.loads((R/'dev5-contract.json').read_text())
    sm=d5['smoke']
    smoke={i for i,a in effective['AbilitiesJson'].items() if a['IsSmoke']}
    def no_smoke(u):
        if u['Id'] in sm.get('keep_units',[]):return False
        return (u.get('Role')==sm['tank_role'] and u['Cost']<sm['tank_min_cost']) or (u.get('Role')==sm['ifv_role'] and u['Cost']<=sm['ifv_max_cost_without_smoke'])
    why='Smoke only on tanks at 100 points and up and IFVs above 30 points'
    for uid,u in list(effective['Units'].items()):
        if not no_smoke(u):continue
        for link in [r for r in effective['UnitAbilitiesJson'].values() if r['UnitId']==uid and r['AbilityId'] in smoke]:
            assert not effective['AbilitiesJson'][link['AbilityId']]['IsAPS'],('smoke row also carries APS',uid)
            # A row the mod added has no vanilla row to delete: remove it from the patch instead.
            if link['Id'] in original['UnitAbilitiesJson']:drop('UnitAbilitiesJson',link['Id'])
            else:
                del effective['UnitAbilitiesJson'][link['Id']];patches['UnitAbilitiesJson'].pop(str(link['Id']),None)
        for opt in options(uid):
            f={k:0 for k in ('Ability1Id','Ability2Id','Ability3Id') if opt[k] in smoke}
            if f:put('OptionsJson',opt['Id'],f,why)
    for key,hp in d5['unit_hp'].items():
        uid=int(key);made={};why=f'Unit HP {hp}'
        for link in [r for r in effective['UnitArmorsJson'].values() if r['UnitId']==uid]:
            old=link['ArmorId']
            if old not in made:made[old]=clone('ArmorsJson',old,{'MaxHealthPoints':hp},why)
            put('UnitArmorsJson',link['Id'],{'ArmorId':made[old]},why)
        for opt in options(uid):
            if opt['ArmorId'] in made:put('OptionsJson',opt['Id'],{'ArmorId':made[opt['ArmorId']]},why)
        assert made,('unit has no armor',uid)
    for key,fields in d5['option_armor'].items():armor(253,int(key),fields,'K16 Bumerang uparmor HEAT 400')
    # A per-unit copy of a shared round: only the listed units get the new values.
    for edit in d5.get('unit_ammo',[]):
        new=clone('AmmunitionsJson',edit['ammo'],edit['fields'],edit['why'])
        links=[r for r in effective['WeaponAmmunitionsJson'].values() if r['UnitId'] in edit['units'] and r['AmmunitionId']==edit['ammo']]
        assert {r['UnitId'] for r in links}==set(edit['units']),('unit without that round',edit['units'])
        for r in links:put('WeaponAmmunitionsJson',r['Id'],{'AmmunitionId':new},edit['why'])
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
        want=copy.deepcopy(row);want.update(us['ammo_fields'].get(str(aid),{}))
        if aid in pin:want['PenetrationAtMinRange']=pin[aid]
        assert effective['AmmunitionsJson'][aid]==want,('unexpected ammo change',aid)
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
    # 0.4 dev.12: ATGM damage and Kornet penetration, and the mid-tank front HEAT spread. After the freeze checks above.
    d11=json.loads((R/'dev12-contract.json').read_text())
    air={uid for uid,u in effective['Units'].items() if u['Type'] not in (2,4)}
    rows={aid for aid,a in effective['AmmunitionsJson'].items() if a['Name'].startswith(('Missile AT ','Missile GLAT ')) and a['ArmorTargeted']==2
          and a['Damage']>d11['atgm_damage'] and any(r['AmmunitionId']==aid and r['UnitId'] not in air for r in effective['WeaponAmmunitionsJson'].values())}
    assert rows==set(d11['atgm_rows']),('ground ATGM rows changed',sorted(rows^set(d11['atgm_rows'])))
    for aid in sorted(rows):
        why='Air units keep the vanilla missile; ground ATGMs change'
        links=[r for r in effective['WeaponAmmunitionsJson'].values() if r['AmmunitionId']==aid and r['UnitId'] in air]
        if links:
            keep=clone('AmmunitionsJson',aid,{},why)
            for r in links:put('WeaponAmmunitionsJson',r['Id'],{'AmmunitionId':keep},why)
        f={'Damage':d11['atgm_damage']}
        pen=d11['atgm_penetration'].get(str(aid))
        if pen:f.update(PenetrationAtMinRange=pen,PenetrationAtGroundRange=pen)
        put('AmmunitionsJson',aid,f,'Ground ATGM damage 10.5; base Kornet 650, Kornet-M 950')
    assert all(str(a) in map(str,rows) for a in d11['atgm_penetration'])
    for key,spread in d11['front_heat'].items():
        uid=int(key);made={};why='Mid-tank front HEAT spread'
        for link in [r for r in effective['UnitArmorsJson'].values() if r['UnitId']==uid]:
            old=link['ArmorId'];front=effective['ArmorsJson'][old]['HeatArmorFront']
            if str(int(front)) not in spread:continue
            if old not in made:made[old]=clone('ArmorsJson',old,{'HeatArmorFront':spread[str(int(front))]},why)
            put('UnitArmorsJson',link['Id'],{'ArmorId':made[old]},why)
        for opt in options(uid):
            if opt['ArmorId'] in made:put('OptionsJson',opt['Id'],{'ArmorId':made[opt['ArmorId']]},why)
        fronts={int(effective['ArmorsJson'][r['ArmorId']]['HeatArmorFront']) for r in effective['UnitArmorsJson'].values() if r['UnitId']==uid}
        assert {int(v) for v in spread.values()}<=fronts and not {int(k) for k in spread}&fronts-{int(v) for v in spread.values()},('front spread incomplete',uid,fronts)
    # 0.4 dev.13: ATGM penetration ladder and one reusable AT launcher per squad. Ammo rows keep their quantity.
    d13=json.loads((R/'dev13-contract.json').read_text())
    for key,pen in d13['atgm_penetration'].items():
        row=effective['AmmunitionsJson'][int(key)]
        assert row['Name'].startswith(('Missile AT ','Missile GLAT ')) and not row['TopArmorAttack'],('ladder row',key)
        put('AmmunitionsJson',int(key),{'PenetrationAtMinRange':pen,'PenetrationAtGroundRange':pen},'ATGM ladder 450-700, Kornet-M 950')
    for key,f in d13['member_fields'].items():
        assert effective['SquadMembersJson'][int(key)]['SpecialWeaponId'],('member has no launcher',key)
        put('SquadMembersJson',int(key),f,'One AT launcher per squad: '+d13['member_why'][key])
    # 0.4 dev.14: ammo, one AT launcher per squad, launcher reload, RPG-29 Vampyr 5 men and two card splits.
    d14=json.loads((R/'dev14-contract.json').read_text())
    for key,q in d14['ammo_quantity'].items():put('WeaponAmmunitionsJson',int(key),{'Quantity':q},d14['ammo_why'][key])
    for key,f in d14['member_fields'].items():put('SquadMembersJson',int(key),f,'One AT launcher per squad: '+d14['member_why'][key])
    for rid in d14['retire_members']:drop('SquadMembersJson',rid)
    for rid in d14['retire_squad_weapons']:drop('SquadWeaponsJson',rid)
    for rid in d14['retire_ammo']:drop('WeaponAmmunitionsJson',rid)
    for key,aid in d14['armor_links'].items():put('UnitArmorsJson',int(key),{'ArmorId':aid},'RPG-29 Vampyr 5 men, 25 HP')
    moved14={}
    for c in d14['cards']:
        why=f"Separate card {effective['Units'][c['unit']]['Name']}"
        put('Units',c['unit'],{'IsUnitModification':False},why)
        pool=clone('SpecializationAvailabilitiesJson',c['like_pool'],{'UnitId':c['unit'],'MaxAvailabilityXp0':c['xp0']},why)
        for t in c['transports']:clone('TransportAvailabilitiesJson',template,{'SpecializationAvailabilityId':pool,'UnitId':t},why)
        for oid in c.get('retire_parent_options',[]):drop('OptionsJson',oid);moved14[str(oid)]=c['parent']
        if c.get('move_options'):
            mod=clone('ModificationsJson',c['modification_like'],{'UnitId':c['unit']},why)
            for key,order in c['move_options'].items():
                put('OptionsJson',int(key),{'ModificationId':mod,'Order':order},why);moved14[key]=c['parent']
    mig=R/'source/UserData/FreedomArrow/deck-migration.json'
    mig.write_text(json.dumps({**json.loads(mig.read_text()),**moved14},indent=2,sort_keys=True)+'\n')
    rl=d14['reload'];sm_users={}
    for m in effective['SquadMembersJson'].values():
        for f in ('PrimaryWeaponId','SpecialWeaponId'):
            if m[f]:sm_users.setdefault(m[f],set()).add(effective['Units'][m['UnitId']]['Type'])
    turret={r['WeaponId'] for r in effective['TurretWeaponsJson'].values()}
    for wid,w in list(effective['WeaponsJson'].items()):
        if not w['Name'].startswith('RocketLauncher') or wid in rl['skip_weapons']:continue
        assert wid not in turret and sm_users.get(wid,{2})=={2},('launcher not infantry-only',wid)
        lo,hi=rl['disposable'] if 'Disposable' in w['Name'] else rl['reusable']
        if (w['MagazineReloadTimeMin'],w['MagazineReloadTimeMax'])!=(lo,hi):
            put('WeaponsJson',wid,{'MagazineReloadTimeMin':lo,'MagazineReloadTimeMax':hi},'Infantry launcher reload 6-7 s, disposable 7 s')
    # 0.4 dev.18: cheap fire-support tanks have availability of at least 6.
    d18=json.loads((R/'dev18-contract.json').read_text())
    for uid in d18['units']:
        rows=[r for r in effective['SpecializationAvailabilitiesJson'].values() if r['UnitId']==uid]
        assert rows and effective['Units'][uid]['Role']==11,('availability',uid)
        for r in rows:
            if r['MaxAvailabilityXp0']<d18['min_availability']:put('SpecializationAvailabilitiesJson',r['Id'],{'MaxAvailabilityXp0':d18['min_availability']},'Cheap fire-support tank availability 6')
    # 0.4 dev.21: Chernye Berety RShG and BARS Igla become separate cards.
    # dev.22 adds PTRK Konkurs-M with the same mechanism.
    moved21={}
    for c in [c for f in ('dev21-contract.json','dev22-contract.json') for c in json.loads((R/f).read_text())['cards']]:
        why=f"Separate card {c['fields']['HUDName']}"
        assert effective['Units'][c['unit']]['IsUnitModification'],c['unit']
        put('Units',c['unit'],{'IsUnitModification':False,**c['fields']},why)
        if c.get('parent_fields'):put('Units',c['parent'],c['parent_fields'],why)
        pool=clone('SpecializationAvailabilitiesJson',c['like_pool'],{'UnitId':c['unit'],'MaxAvailabilityXp0':c['xp0']},why)
        for t in c['transports']:clone('TransportAvailabilitiesJson',template,{'SpecializationAvailabilityId':pool,'UnitId':t},why)
        for oid in c['retire_parent_options']:
            assert effective['OptionsJson'][oid]['ReplaceUnitId']==c['unit'],oid
            drop('OptionsJson',oid);moved21[str(oid)]=c['parent']
        if c.get('parent_default_option'):put('OptionsJson',c['parent_default_option'],{'IsDefault':True},why)
    mig=R/'source/UserData/FreedomArrow/deck-migration.json'
    mig.write_text(json.dumps({**json.loads(mig.read_text()),**moved21},indent=2,sort_keys=True)+'\n')
    # 0.4 dev.30: Javelin aim time and a fourth AT-4 on Troopers AT.
    d30=json.loads((R/'dev30-contract.json').read_text())
    for key,f in d30['weapon_fields'].items():
        assert 'Javelin' in effective['WeaponsJson'][int(key)]['Name'],key
        put('WeaponsJson',int(key),f,'Javelin aim 3-4 s')
    for key,f in d30['member_fields'].items():
        m=effective['SquadMembersJson'][int(key)];assert not m['SpecialWeaponId'],key
        assert f['SpecialWeaponId'] in {r['WeaponId'] for r in effective['SquadWeaponsJson'].values() if r['UnitId']==m['UnitId']},key
        put('SquadMembersJson',int(key),f,d30['member_why'][key])
    # 0.4 dev.31: mortar range +50% and smoke on every mortar loadout.
    d31=json.loads((R/'dev31-contract.json').read_text());mw=set(d31['mortar_weapons'])
    for w in mw:assert w in effective['WeaponsJson'],w
    mammo={r['AmmunitionId'] for r in effective['WeaponAmmunitionsJson'].values() if r['WeaponId'] in mw and effective['AmmunitionsJson'][r['AmmunitionId']]['TrajectoryType'] in (20,30)}
    for aid in mammo:
        assert all(r['WeaponId'] in mw for r in effective['WeaponAmmunitionsJson'].values() if r['AmmunitionId']==aid),('mortar round shared',aid)
        put('AmmunitionsJson',aid,{'GroundRange':effective['AmmunitionsJson'][aid]['GroundRange']*d31['range_factor']},'Mortar range +50%')
    cl=d31['clone240'];smoke240=clone('AmmunitionsJson',cl['from'],{'Name':cl['name'],'GroundRange':effective['AmmunitionsJson'][cl['range_like']]['GroundRange']},'240 mm mortar smoke round')
    for key,sa in d31['smoke_add'].items():
        w=int(key);sa=smoke240 if sa=='clone240' else sa
        assert effective['AmmunitionsJson'][sa]['GenerateSmoke'],sa
        links=[r for r in effective['WeaponAmmunitionsJson'].values() if r['WeaponId']==w]
        assert links and not any(effective['AmmunitionsJson'][r['AmmunitionId']]['GenerateSmoke'] for r in links),('weapon already has smoke',w)
        for uid in sorted({r['UnitId'] for r in links}):
            mine=[r for r in links if r['UnitId']==uid]
            q=max(5,int(5*round(sum(r['Quantity'] for r in mine)*0.25/5)))
            clone('WeaponAmmunitionsJson',mine[0]['Id'],{'AmmunitionId':sa,'Quantity':q,'Order':max(r['Order'] for r in mine)+1},'Mortar smoke rounds')
    for w in mw:
        if any(r['WeaponId']==w for r in effective['WeaponAmmunitionsJson'].values()):
            assert any(effective['AmmunitionsJson'][r['AmmunitionId']]['GenerateSmoke'] for r in effective['WeaponAmmunitionsJson'].values() if r['WeaponId']==w),('mortar without smoke',w)
    # 0.4 dev.34: M8 Thunderbolt ERA 700 and Applique 400 HEAT all around.
    d34=json.loads((R/'dev34-contract.json').read_text())
    for key,f in d34['option_armor'].items():armor(d34['unit'],int(key),f,'M8 Thunderbolt kit HEAT all around')
    # 0.4 dev.35: TOW-2B penetration and damage equal the Javelin.
    d35=json.loads((R/'dev35-contract.json').read_text());jav=effective['AmmunitionsJson'][int(d35['match'])]
    for key,f in d35['ammo_fields'].items():
        row=effective['AmmunitionsJson'][int(key)];assert 'TOW2B' in row['Name'] and row['TopArmorAttack'],key
        assert all(jav[k]==v for k,v in f.items()),('not the Javelin values',f)
        put('AmmunitionsJson',int(key),f,'TOW-2B equals Javelin penetration and damage')
    assert not [i for i,a in effective['AmmunitionsJson'].items() if 'TOW2B' in a['Name'] and str(i) not in d35['ammo_fields'] and any(r['AmmunitionId']==i for r in effective['WeaponAmmunitionsJson'].values())],'another TOW-2B row in use'
    # 0.4 dev.37: no missile ripple fire, 1 missile per target.
    d37=json.loads((R/'dev37-contract.json').read_text())
    for key,f in d37['weapon_fields'].items():
        assert effective['WeaponsJson'][int(key)]['Type'] in d37['types'],key
        put('WeaponsJson',int(key),f,'One missile per target, no ripple fire')
    left=[i for i,w in effective['WeaponsJson'].items() if w['Type'] in d37['types'] and (w['ShotsPerBurstMax']>1 or w['SimultaneousTracking']>w['MultiTargetTracking'])]
    assert not left,('missile weapon still ripples',left)
    # 0.4 dev.38: BARS, BARS FS and BARS Kornet are separate cards.
    d38=json.loads((R/'dev38-contract.json').read_text());why='BARS card split'
    def gone(table,rid):
        if rid in original[table]:drop(table,rid)
        else:del effective[table][rid];patches[table].pop(str(rid),None)
    def swap(uid,old,new,ammo=None):
        for m in [r for r in effective['SquadMembersJson'].values() if r['UnitId']==uid]:
            for f in ('PrimaryWeaponId','SpecialWeaponId'):
                if m[f]==old:put('SquadMembersJson',m['Id'],{f:new},why)
        have={r['WeaponId'] for r in effective['SquadWeaponsJson'].values() if r['UnitId']==uid}
        for r in [r for r in effective['SquadWeaponsJson'].values() if r['UnitId']==uid and r['WeaponId']==old]:
            if new in have:gone('SquadWeaponsJson',r['Id'])
            else:put('SquadWeaponsJson',r['Id'],{'WeaponId':new},why)
        rows=[r for r in effective['WeaponAmmunitionsJson'].values() if r['UnitId']==uid and r['WeaponId']==old]
        assert rows and (ammo is None)==any(r['WeaponId']==new for r in effective['WeaponAmmunitionsJson'].values() if r['UnitId']==uid),(uid,old,new)
        for r in rows[1 if ammo else 0:]:gone('WeaponAmmunitionsJson',r['Id'])
        if ammo:put('WeaponAmmunitionsJson',rows[0]['Id'],{'WeaponId':new,'AmmunitionId':ammo['id'],'Quantity':ammo['qty']},why)
    def card(uid):
        pool=clone('SpecializationAvailabilitiesJson',d38['pool_like'],{'UnitId':uid,'MaxAvailabilityXp0':d38['xp0']},why)
        for t in [r for r in effective['TransportAvailabilitiesJson'].values() if r['SpecializationAvailabilityId']==d38['pool_like']]:
            clone('TransportAvailabilitiesJson',t['Id'],{'SpecializationAvailabilityId':pool},why)
    fs,rpg,kor=d38['fs'],d38['rpg'],d38['kornet']
    assert effective['Units'][rpg['unit']]['IsUnitModification'] and kor['unit'] not in effective['Units']
    for oid in d38['retire_options']:
        assert effective['OptionsJson'][oid]['ModificationId']==d38['retire_mod'],oid
        drop('OptionsJson',oid);moved21[str(oid)]=fs['unit']
    assert not options(fs['unit']);drop('ModificationsJson',d38['retire_mod'])
    # BARS Kornet copies the fire-support squad before its Kornet becomes an AGS-40.
    add_unit(kor['unit'],fs['unit'],kor['fields'],why)
    for table in ['SquadMembersJson','SquadWeaponsJson','WeaponAmmunitionsJson','UnitAbilitiesJson','UnitArmorsJson','UnitPropulsionsJson','SensorUnitsJson']:
        for rid in [r['Id'] for r in list(effective[table].values()) if r['UnitId']==fs['unit']]:clone(table,rid,{'UnitId':kor['unit']},why)
    swap(kor['unit'],*kor['swap'],kor['ammo']);card(kor['unit'])
    put('Units',fs['unit'],fs['fields'],why);swap(fs['unit'],*fs['swap'],fs['ammo'])
    put('Units',rpg['unit'],rpg['fields'],why);swap(rpg['unit'],*rpg['swap']);card(rpg['unit'])
    for key,w in rpg['add_special'].items():
        assert not effective['SquadMembersJson'][int(key)]['SpecialWeaponId'] and effective['SquadMembersJson'][int(key)]['UnitId']==rpg['unit'],key
        put('SquadMembersJson',int(key),{'SpecialWeaponId':w},why)
    mig.write_text(json.dumps({**json.loads(mig.read_text()),**moved21},indent=2,sort_keys=True)+'\n')
    audit[:]=[a for a in audit if a['id'] in effective[a['table']]]
    # 0.4 dev.39: S-300PM, S-400, S-350, Uragan-1M and TOS-2 change specialization.
    for key,p in json.loads((R/'dev39-contract.json').read_text())['pools'].items():
        row=effective['SpecializationAvailabilitiesJson'][int(key)]
        assert (row['UnitId'],row['SpecializationId'])==(p['unit'],p['from']),key
        assert not any(r['UnitId']==p['unit'] and r['SpecializationId']==p['to'] for r in effective['SpecializationAvailabilitiesJson'].values()),key
        put('SpecializationAvailabilitiesJson',int(key),{'SpecializationId':p['to']},'Card moves specialization')
    # 0.4 dev.40: Spetsnaz Alpha CQC 12 men; standoff loses one AEK-999, one RG-6 and two RPG-30.
    d40=json.loads((R/'dev40-contract.json').read_text())
    for rid in d40['retire_members']:
        assert effective['SquadMembersJson'][rid]['UnitId']==131 and not effective['SquadMembersJson'][rid]['SpecialWeaponId'],rid
        drop('SquadMembersJson',rid)
    for key,aid in d40['armor_links'].items():put('UnitArmorsJson',int(key),{'ArmorId':aid},'Spetsnaz Alpha CQC 12 men, 60 HP')
    for key,f in d40['member_fields'].items():
        assert effective['SquadMembersJson'][int(key)]['UnitId']==354,key
        put('SquadMembersJson',int(key),f,d40['member_why'][key])
    alpha=[m for m in effective['SquadMembersJson'].values() if m['UnitId']==131]
    assert len(alpha)*5==effective['ArmorsJson'][effective['UnitArmorsJson'][222]['ArmorId']]['MaxHealthPoints']==60
    # 0.4 dev.42: T-62M 12 HP; T-72A front armor +100.
    d42=json.loads((R/'dev42-contract.json').read_text())
    for oid in d42['t62']['options']:armor(d42['t62']['unit'],oid,{'MaxHealthPoints':d42['t62']['hp']},'T-62M 12 HP')
    for oid in d42['t72a']['options']:
        a=effective['ArmorsJson'][effective['OptionsJson'][oid]['ArmorId']];n=d42['t72a']['front_add']
        armor(d42['t72a']['unit'],oid,{'KinArmorFront':a['KinArmorFront']+n,'HeatArmorFront':a['HeatArmorFront']+n},'T-72A front armor +100')
    # 0.4 dev.43: Troopers AT carry the AT4 CS HP.
    d43=json.loads((R/'dev43-contract.json').read_text());why='Troopers AT AT4 CS HP'
    swap(d43['unit'],*d43['swap'],d43['ammo'])
    assert not any(m['UnitId']==d43['unit'] and d43['swap'][0] in (m['PrimaryWeaponId'],m['SpecialWeaponId']) for m in effective['SquadMembersJson'].values())
    # 0.4 dev.49: ground-vehicle ATGM launchers wait 5 s between missiles.
    d49=json.loads((R/'dev49-contract.json').read_text())
    for key,f in d49['weapon_fields'].items():
        w=effective['WeaponsJson'][int(key)]
        assert w['Type']==80 and w['MagazineSize']>1 and not any(x in w['Name'] for x in ('Heli','UAV','Plane','Infantry')),key
        put('WeaponsJson',int(key),f,'Vehicle ATGM 5 s between missiles')
    # 0.5 dev.1: accuracy. Unguided tank-gun and rocket rounds scatter twice as far; guided missiles unchanged.
    acc=json.loads((R/'accuracy-contract.json').read_text())
    for key,f in acc['ammo_fields'].items():
        a=effective['AmmunitionsJson'][int(key)];old=acc['was'][key]
        assert [a['DispersionHorizontalRadius'],a['DispersionVerticalRadius']]==old and not a['Name'].startswith('Missile'),key
        assert {effective['WeaponsJson'][r['WeaponId']]['Type'] for r in effective['WeaponAmmunitionsJson'].values() if r['AmmunitionId']==int(key)}<=set(acc['weapon_types']),key
        launcher=key in acc['launcher_dev2']
        assert launcher==('DispersionMinimal' in f) and (not launcher or effective['AmmunitionsJson'][int(key)]['DispersionMinimal']==0),key
        put('AmmunitionsJson',int(key),f,'0.5 dev.2 accuracy: launcher 2.14 with 80% close cap' if launcher else '0.5 accuracy: dispersion x'+str(acc['factor']))
    # 0.5 dev.3: smoke with the BMP-2G, BMP-2M and T-72B1 packages.
    smc=json.loads((R/'smoke-contract.json').read_text())
    for key,ab in smc['option_ability'].items():
        o=effective['OptionsJson'][int(key)];a=effective['AbilitiesJson'][ab]
        assert a['IsSmoke'] and not a['IsAPS'] and not any(o[k] for k in ('Ability1Id','Ability2Id','Ability3Id')),key
        put('OptionsJson',int(key),{'Ability1Id':ab},'Smoke with this package')
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
    # Spotting cap (SpottingCap.cs): each observer's ground range stops at the vanilla value of its sensor tier.
    caps={}
    for sid,row in effective['SensorsJson'].items():
        if str(sid) in det['optics_ground_overrides']:continue  # moved to a tier: takes that tier's cap
        mod,van=row['OpticsGround'],original['SensorsJson'][sid]['OpticsGround']
        assert caps.setdefault(mod,van)==van,('one modded optics value maps to two vanilla values',sid,mod)
    (R/'source/UserData/FreedomArrow/spotting-caps.json').write_text(json.dumps({'OpticsGroundCaps':{f'{k:g}':v for k,v in sorted(caps.items())}},indent=2)+'\n')
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

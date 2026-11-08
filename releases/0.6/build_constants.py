"""Generate the versioned 0.5 overlay (0.4 history plus 0.5 accuracy) on frozen 0.1.1 constants.

Includes reviewed dev.1/dev.2 and the US/Baltic data batch.
Card splits, squad resizing and option retirement are listed in structural-contract.json.
"""
from pathlib import Path
import argparse, copy, hashlib, json, math, re, sys
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
            if opt['Id'] in sm.get('keep_options',[]):continue
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
    for w in mw|set(d31['hawkeye_smoke_only']):
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
    # 0.5 dev.16/dev.18: long-range sniper rifles fire 8 and anti-materiel rifles 6 rounds per minute on the unit card.
    srof=json.loads((R/'sniper-rof-contract.json').read_text())
    def card_rof(w):  # WeaponHelper.RateOfFire(weapon, 1), read from the game code
        m=w['MagazineSize'];lo=(m/w['ShotsPerBurstMax']-1)*w['TimeBetweenBurstsMin']+(m-m/w['ShotsPerBurstMax'])*w['TimeBetweenShotsInBurst']+w['MagazineReloadTimeMin']
        hi=(m/w['ShotsPerBurstMin']-1)*w['TimeBetweenBurstsMax']+(m-m/w['ShotsPerBurstMin'])*w['TimeBetweenShotsInBurst']+w['MagazineReloadTimeMax']
        return 60*m/abs((lo+hi)/2)
    def long_range(wid):
        return max([effective['AmmunitionsJson'][r['AmmunitionId']]['GroundRange']*2 for r in effective['WeaponAmmunitionsJson'].values() if r['WeaponId']==wid] or [0])>=srof['min_range_m']
    scope={str(i) for i,w in effective['WeaponsJson'].items() if w['Type'] in srof['types'] and long_range(i)}
    assert scope==set(srof['weapon_fields']),('sniper RoF scope',sorted(scope^set(srof['weapon_fields'])))
    for key,f in srof['weapon_fields'].items():
        put('WeaponsJson',int(key),f,'Long-range sniper rifles 8 and anti-materiel rifles 6 rounds per minute')
        w=effective['WeaponsJson'][int(key)]
        assert abs(card_rof(w)-srof['rate_of_fire_per_minute_by_type'][str(w['Type'])])<1e-6,key
    # 0.5 dev.1: accuracy. Unguided tank-gun and rocket rounds scatter twice as far; guided missiles unchanged.
    acc=json.loads((R/'accuracy-contract.json').read_text())
    for key,f in acc['ammo_fields'].items():
        a=effective['AmmunitionsJson'][int(key)];old=acc['was'][key]
        assert [a['DispersionHorizontalRadius'],a['DispersionVerticalRadius']]==old and not a['Name'].startswith('Missile'),key
        assert {effective['WeaponsJson'][r['WeaponId']]['Type'] for r in effective['WeaponAmmunitionsJson'].values() if r['AmmunitionId']==int(key)}<=set(acc['weapon_types']),key
        assert key in acc['launcher_dev2'] and 'DispersionMinimal' not in f,key
        put('AmmunitionsJson',int(key),f,'0.5 accuracy: launcher radius 1.96')
    # 0.5 dev.3: smoke with the BMP-2G, BMP-2M and T-72B1 packages.
    smc=json.loads((R/'smoke-contract.json').read_text())
    for key,ab in smc['option_ability'].items():
        o=effective['OptionsJson'][int(key)];a=effective['AbilitiesJson'][ab]
        assert a['IsSmoke'] and not a['IsAPS'] and not any(o[k] for k in ('Ability1Id','Ability2Id','Ability3Id')),key
        put('OptionsJson',int(key),{'Ability1Id':ab},'Smoke with this package')
    # 0.5 dev.4: Sprut-SDM is its own card; Sprut-SD 60, Sprut-SDM 75, both 12 HP with smoke.
    sp=json.loads((R/'sprut-contract.json').read_text());why='Sprut-SDM card split';par,new=sp['parent'],sp['unit']
    assert new not in effective['Units'] and effective['OptionsJson'][sp['move_option']]['ModificationId']==sp['variant_mod']
    made={}
    for link in [r for r in effective['UnitArmorsJson'].values() if r['UnitId']==par]:
        made.setdefault(link['ArmorId'],clone('ArmorsJson',link['ArmorId'],{'MaxHealthPoints':sp['hp']},'Sprut 12 HP'))
        put('UnitArmorsJson',link['Id'],{'ArmorId':made[link['ArmorId']]},'Sprut 12 HP')
    for opt in options(par):
        if opt['ArmorId'] in made:put('OptionsJson',opt['Id'],{'ArmorId':made[opt['ArmorId']]},'Sprut 12 HP')
    add_unit(new,par,sp['fields'],why)
    for table in ['TurretUnitsJson','WeaponAmmunitionsJson','UnitAbilitiesJson','UnitArmorsJson','UnitPropulsionsJson','SensorUnitsJson']:
        for rid in [r['Id'] for r in list(effective[table].values()) if r['UnitId']==par]:clone(table,rid,{'UnitId':new},why)
    vm=clone('ModificationsJson',sp['variant_mod'],{'UnitId':new},why)
    put('OptionsJson',sp['move_option'],{'ModificationId':vm,'Order':0,'Cost':0,'ConcatenateWithUnitName':''},why)
    am=clone('ModificationsJson',sp['armor_mod'],{'UnitId':new},why)
    for oid in sp['armor_options']:
        clone('OptionsJson',oid,{'ModificationId':am},why)
    clone('SpecializationAvailabilitiesJson',sp['pool'],{'UnitId':new},why)
    mig.write_text(json.dumps({**json.loads(mig.read_text()),str(sp['move_option']):par},indent=2,sort_keys=True)+'\n')
    for uid in (par,new):
        arm={effective['ArmorsJson'][r['ArmorId']]['MaxHealthPoints'] for r in effective['UnitArmorsJson'].values() if r['UnitId']==uid}
        assert arm=={12} and any(effective['AbilitiesJson'][r['AbilityId']]['IsSmoke'] for r in effective['UnitAbilitiesJson'].values() if r['UnitId']==uid),(uid,arm)
    # 0.5 dev.7: ground ATGMs hit 75% (missile accuracy 0.75); air missiles unchanged.
    ground={2,4}
    for key,f in acc['atgm_fields'].items():
        a=effective['AmmunitionsJson'][int(key)]
        kinds={effective['Units'][r['UnitId']]['Type'] for r in effective['WeaponAmmunitionsJson'].values() if r['AmmunitionId']==int(key) and r['UnitId'] in effective['Units']}
        assert a['Name'].startswith(('Missile AT','Missile GLAT')) and a['DispersionHorizontalRadius']==1.0 and kinds and kinds<=ground,(key,kinds)
        put('AmmunitionsJson',int(key),f,'0.5 accuracy: ground ATGM hit chance 75%')
    # 0.5 dev.8: APS options. Tanks pay +70 over the armor kit; the FEP and T-72B3AM get a kit + APS option.
    apsc=json.loads((R/'aps-contract.json').read_text());why='APS option at kit +70'
    for n in apsc['new_options']:
        like=effective['OptionsJson'][n['like']];ab=effective['AbilitiesJson'][n['ability']]
        assert ab['IsAPS'] and ab['APSQuantity']>0 and like['ModificationId'] in {m['Id'] for m in effective['ModificationsJson'].values() if m['UnitId']==n['unit']}
        assert not any(like[k] for k in ('Ability1Id','Ability2Id','Ability3Id')) and n['fields']['Cost']==like['Cost']+70,n
        clone('OptionsJson',n['like'],{**n['fields'],'Ability1Id':n['ability']},why)
        assert effective['UnitAbilitiesJson'][n['ua_like']]['UnitId']==n['unit']
        clone('UnitAbilitiesJson',n['ua_like'],{'AbilityId':n['ability']},'APS inventory matches the new option')
    # 0.5 dev.17: cover. 120/125 mm tank HE ignores 25% of cover; ground-vehicle autocannon HE ignores 12.5%.
    cov=json.loads((R/'cover-contract.json').read_text())
    def users(aid):
        ws={r['WeaponId'] for r in effective['WeaponAmmunitionsJson'].values() if r['AmmunitionId']==aid}
        ts={r['TurretId'] for r in effective['TurretWeaponsJson'].values() if r['WeaponId'] in ws}
        us={r['UnitId'] for r in effective['TurretUnitsJson'].values() if r['TurretId'] in ts}
        return ws,{effective['Units'][u]['Type'] for u in us if u in effective['Units']}
    tank=re.compile(r'Round 12[05] .*HE');auto=re.compile(r'Round (\d+) ')
    def scope(row):
        a=row;m=auto.match(a['Name'])
        if not m or a['Damage']<=0:return None
        if tank.match(a['Name']) and 'HEAT' not in a['Name'] and a['IgnoreCover']==cov['tank_he']['was']:return 'tank_he'
        ws,kinds=users(a['Id'])
        if 20<=int(m.group(1))<=57 and re.search('HE',a['Name']) and a['IgnoreCover']==0 and ws and kinds=={4} and all(effective['WeaponsJson'][w]['Name'].startswith('Autocannon') for w in ws):return 'autocannon_he'
    found={}
    for a in effective['AmmunitionsJson'].values():
        k=scope(a)
        if k:found.setdefault(k,set()).add(a['Id'])
    for k in ('tank_he','autocannon_he'):
        assert found.get(k,set())==set(cov[k]['ids']),(k,sorted(found.get(k,set())^set(cov[k]['ids'])))
        for aid in cov[k]['ids']:
            put('AmmunitionsJson',aid,{'IgnoreCover':cov[k]['ignore_cover']},'0.5 cover: '+k.replace('_',' ')+' ignore cover')
    # 0.5 dev.19: Tigr Kornet 2x4 is its own card at 120 in Motorized Infantry; its launchers ripple fire 2 missiles.
    tg=json.loads((R/'tigr-contract.json').read_text());why='Tigr Kornet 2x4 card split';par,new=tg['parent'],tg['unit']
    assert new not in effective['Units'] and effective['OptionsJson'][tg['move_option']]['ModificationId']==tg['variant_mod']
    add_unit(new,par,tg['fields'],why)
    for table in ['TurretUnitsJson','WeaponAmmunitionsJson','UnitAbilitiesJson','UnitArmorsJson','UnitPropulsionsJson','SensorUnitsJson']:
        for rid in [r['Id'] for r in list(effective[table].values()) if r['UnitId']==par]:clone(table,rid,{'UnitId':new},why)
    vm=clone('ModificationsJson',tg['variant_mod'],{'UnitId':new},why)
    put('OptionsJson',tg['move_option'],{'ModificationId':vm,'Order':0,'Cost':0},why)
    for mod,oids in tg['copy_mods'].items():
        m=clone('ModificationsJson',int(mod),{'UnitId':new},why)
        assert {o['Id'] for o in effective['OptionsJson'].values() if o['ModificationId']==int(mod)}==set(oids),mod
        for oid in oids:clone('OptionsJson',oid,{'ModificationId':m},why)
    assert [r['SpecializationId'] for r in effective['SpecializationAvailabilitiesJson'].values() if r['UnitId']==par]==[effective['SpecializationAvailabilitiesJson'][tg['pool']]['SpecializationId']]
    clone('SpecializationAvailabilitiesJson',tg['pool'],{'UnitId':new,'SpecializationId':tg['specialization']},why)
    mig.write_text(json.dumps({**json.loads(mig.read_text()),str(tg['move_option']):par},indent=2,sort_keys=True)+'\n')
    rip2=clone('WeaponsJson',tg['weapon'],tg['weapon_fields'],'Tigr Kornet 2x4 ripple fire: 2 missiles per target')
    for rid in tg['turret_weapons']:
        assert effective['TurretWeaponsJson'][rid]['WeaponId']==tg['weapon'];put('TurretWeaponsJson',rid,{'WeaponId':rip2},why)
    for r in list(effective['WeaponAmmunitionsJson'].values()):
        if r['UnitId'] in (par,new) and r['WeaponId']==tg['weapon']:put('WeaponAmmunitionsJson',r['Id'],{'WeaponId':rip2},why)
    turrets={effective['TurretWeaponsJson'][rid]['TurretId'] for rid in tg['turret_weapons']}
    assert all(o['ModificationId']==vm for o in effective['OptionsJson'].values() if any(o.get(f'Turret{i}Id') in turrets for i in range(21)))
    # 0.5 dev.20: T-72B3AM obr. 16 is the T-72B3A base; the no-ERA base option is retired; obr. 16 + Arena is +70.
    tb=json.loads((R/'t72b3a-contract.json').read_text());why='T-72B3AM obr. 16 is the base';u=tb['unit']
    base=effective['OptionsJson'][tb['base_option']];mod=base['ModificationId']
    assert effective['OptionsJson'][tb['retire_option']]['ModificationId']==mod and base['Cost']==0 and base['ArmorId']==tb['new_armor']
    drop('OptionsJson',tb['retire_option']);mig.write_text(json.dumps({**json.loads(mig.read_text()),str(tb['retire_option']):u},indent=2,sort_keys=True)+'\n')
    rest=sorted((o for o in effective['OptionsJson'].values() if o['ModificationId']==mod),key=lambda o:(o['Id']!=tb['base_option'],o['Order']))
    for order,o in enumerate(rest):put('OptionsJson',o['Id'],{'Order':order},why)
    assert [o['Cost'] for o in rest]==[0,70],[(o['Id'],o['Cost']) for o in rest]
    hits=[r['Id'] for r in effective['UnitArmorsJson'].values() if r['UnitId']==u and r['ArmorId']==tb['old_armor']];assert hits
    for rid in hits:put('UnitArmorsJson',rid,{'ArmorId':tb['new_armor']},why)
    put('Units',u,{'HUDName':tb['hud']},why);assert effective['Units'][u]['Cost']==165
    # 0.5 dev.21: artillery uses more supply to refill (ActualArrow 1.1.20 values).
    sup=json.loads((R/'supply-contract.json').read_text())
    for key,f in sup['ammo'].items():
        a=effective['AmmunitionsJson'][int(key)]
        assert a['Name'].strip()==f['name'] and a['SupplyCost']==f['was'] and f['SupplyCost']>f['was'],key
        assert a['Name'].startswith(('Shell','Obus','MLRS','Missile Ballistic','Missile Cruise IskanderK','Round 152 2A33','Round 122 2A31')),key
        put('AmmunitionsJson',int(key),{'SupplyCost':f['SupplyCost']},'Artillery supply cost (ActualArrow values)')
    # 0.5 dev.22: helicopter anti-tank missiles do 12 damage, except LMUR; ground copies of shared rounds stay.
    hm=json.loads((R/'heli-missile-contract.json').read_text());why='Helicopter ATGM 12 damage'
    heli={u for u,r in effective['Units'].items() if r['Type']==8}
    found={r['AmmunitionId'] for r in effective['WeaponAmmunitionsJson'].values() if r['UnitId'] in heli and effective['AmmunitionsJson'][r['AmmunitionId']]['Name'].startswith('Missile AT')}
    assert found==set(hm['ammo'])|{int(k) for k in hm['excluded']},sorted(found^(set(hm['ammo'])|{int(k) for k in hm['excluded']}))
    for aid in hm['ammo']:
        rows=[r for r in effective['WeaponAmmunitionsJson'].values() if r['AmmunitionId']==aid]
        if all(r['UnitId'] in heli for r in rows):put('AmmunitionsJson',aid,{'Damage':hm['damage']},why);continue
        new=clone('AmmunitionsJson',aid,{'Damage':hm['damage']},why+' (helicopter copy)')
        for r in rows:
            if r['UnitId'] in heli:put('WeaponAmmunitionsJson',r['Id'],{'AmmunitionId':new},why)
    # 0.5 dev.24: M-ATV 10 HP, Silent Hawk 90, Booker and Mech. Riflemen availability, recon infantry laser designators.
    d24=json.loads((R/'dev24-contract.json').read_text());why='0.5 dev.24'
    hp=d24['hp'];assert {r['UnitId'] for r in effective['UnitArmorsJson'].values() if r['ArmorId'] in hp['armors']}==set(hp['units'])
    assert all(effective['ModificationsJson'][o['ModificationId']]['UnitId'] in hp['units'] for o in effective['OptionsJson'].values() if o.get('ArmorId') in hp['armors'])
    for aid in hp['armors']:put('ArmorsJson',aid,{'MaxHealthPoints':hp['value']},'M-ATV 10 HP')
    lz=d24['laser'];like=effective['AbilitiesJson'][lz['like']];assert like['IsLaserDesignator']
    sf=[u for u,r in effective['Units'].items() if r['Type']==2 and r['DisplayInArmory'] and r['CategoryType']==lz['category'] and not any(x in r['HUDName'] for x in lz['exclude_names'])]
    has=lambda u:any(effective['AbilitiesJson'][r['AbilityId']]['IsLaserDesignator'] for r in effective['UnitAbilitiesJson'].values() if r['UnitId']==u)
    assert sorted(u for u in sf if not has(u))==sorted(lz['units']) and sorted(u for u in sf if has(u))==sorted(lz['already']),sf
    made={}
    for r in [r for r in effective['UnitAbilitiesJson'].values() if r['UnitId'] in lz['units']]:
        a=effective['AbilitiesJson'][r['AbilityId']];assert a['IsInfantrySprint'] or a['IsSmoke'],r
        if r['AbilityId'] not in made:made[r['AbilityId']]=clone('AbilitiesJson',r['AbilityId'],{**{f:like[f] for f in lz['fields']},'Name':a['Name']+' Laser'},'Recon infantry laser designator')
        put('UnitAbilitiesJson',r['Id'],{'AbilityId':made[r['AbilityId']]},'Recon infantry laser designator')
    assert all(has(u) for u in sf)
    # 0.5 dev.27: TGB-1111 RBS is its own card at 50; TGB-1111 with the Pvpj 1110 is 30.
    tgb=json.loads((R/'tgb-contract.json').read_text());why='TGB-1111 RBS card split';par,new=tgb['parent'],tgb['unit']
    assert new not in effective['Units'] and effective['OptionsJson'][tgb['move_option']]['ModificationId']==tgb['variant_mod']
    assert {m['Id'] for m in effective['ModificationsJson'].values() if m['UnitId']==par}=={tgb['variant_mod']}
    add_unit(new,par,tgb['fields'],why)
    for table in ['TurretUnitsJson','WeaponAmmunitionsJson','UnitAbilitiesJson','UnitArmorsJson','UnitPropulsionsJson','SensorUnitsJson']:
        for rid in [r['Id'] for r in list(effective[table].values()) if r['UnitId']==par]:clone(table,rid,{'UnitId':new},why)
    vm=clone('ModificationsJson',tgb['variant_mod'],{'UnitId':new},why)
    put('OptionsJson',tgb['move_option'],{'ModificationId':vm,'Order':0,'Cost':0},why)
    clone('SpecializationAvailabilitiesJson',tgb['pool'],{'UnitId':new},why)
    mig.write_text(json.dumps({**json.loads(mig.read_text()),str(tgb['move_option']):par},indent=2,sort_keys=True)+'\n')
    assert effective['Units'][par]['Cost']==30 and [o['Id'] for o in options(par)]==[2207]
    # 0.5 dev.28: Mi-28N outer Ataka pylon has one launcher, so it fires one missile at a time.
    d28=json.loads((R/'dev28-contract.json').read_text());o=effective['OptionsJson'][d28['option']]
    assert o[d28['clear']]==d28['turret'] and o[d28['keep']]==d28['turret']
    put('OptionsJson',d28['option'],{d28['clear']:0},'Mi-28N one Ataka launcher on the outer pylon')
    # 0.5 dev.30: helicopter ATGM pylons carry one launcher; AH-64E, Comanche, Mi-28N and Mi-28NM can laser-designate.
    h30=json.loads((R/'dev30-heli-contract.json').read_text());why='Helicopter ATGM pylon: one launcher'
    atw={w for w in effective['WeaponsJson'] if any(effective['AmmunitionsJson'][r['AmmunitionId']]['Name'].startswith('Missile AT') for r in effective['WeaponAmmunitionsJson'].values() if r['WeaponId']==w)}
    tur_at={r['TurretId'] for r in effective['TurretWeaponsJson'].values() if r['WeaponId'] in atw}
    slot=lambda k:int(k[6:-2])
    found={}
    for o in effective['OptionsJson'].values():
        m=effective['ModificationsJson'].get(o['ModificationId'])
        if not m or effective['Units'][m['UnitId']]['Type']!=8:continue
        keys=sorted([k for k in o if k.startswith('Turret') and k.endswith('Id') and o[k]],key=slot)
        for t in {o[k] for k in keys}:
            dup=[k for k in keys if o[k]==t]
            if t in tur_at and len(dup)>1 and t not in h30['skip_single_round_turrets']:found.setdefault(o['Id'],[]).extend(dup[1:])
    assert sorted(found)==sorted(h30['pod_options']),sorted(set(found)^set(h30['pod_options']))
    # 0.6 dev.46 (Osama): an empty mount shows the unit's default turret (the Hydra pod on the Longbow and AH-64E). The freed
    # mount now carries a copy of the launcher turret with no weapon (the rack model only), and the one launcher left carries
    # both racks' rounds, so a pylon still holds its vanilla count and fires one missile at a time.
    rack={};load2={};units_of=lambda oid:effective['ModificationsJson'][effective['OptionsJson'][oid]['ModificationId']]['UnitId']
    why46='Helicopter ATGM pylon: one launcher with both racks, second rack is the model only'
    def unit_turret(u,t,new):
        if not any(r['UnitId']==u and r['TurretId']==new for r in effective['TurretUnitsJson'].values()):
            (tul,)=[r['Id'] for r in effective['TurretUnitsJson'].values() if r['UnitId']==u and r['TurretId']==t]
            clone('TurretUnitsJson',tul,{'TurretId':new},why46)
    for oid,keys in sorted(found.items()):
        u=units_of(oid);o=effective['OptionsJson'][oid]
        (dup,)=keys;t=o[dup]
        (first,)=[k for k in o if k.startswith('Turret') and k.endswith('Id') and o[k]==t and k!=dup]
        if t not in rack:
            rack[t]=clone('TurretsJson',t,{'Name':effective['TurretsJson'][t]['Name']+' rack (no weapon)'},why46)
            # A copy of the launcher whose weapon(s) are copies too, so its round count is its own (other options keep t).
            t2=clone('TurretsJson',t,{'Name':effective['TurretsJson'][t]['Name']+' both racks'},why46);wmap={}
            for r in [r for r in effective['TurretWeaponsJson'].values() if r['TurretId']==t]:
                w=r['WeaponId'];wmap[w]=clone('WeaponsJson',w,{'Name':effective['WeaponsJson'][w]['Name']+' both racks'},why46)
                clone('TurretWeaponsJson',r['Id'],{'TurretId':t2,'WeaponId':wmap[w]},why46)
            load2[t]=(t2,wmap)
        t2,wmap=load2[t]
        unit_turret(u,t,rack[t]);unit_turret(u,t,t2)
        for w,w2 in wmap.items():
            if not any(r['UnitId']==u and r['WeaponId']==w2 for r in effective['WeaponAmmunitionsJson'].values()):
                for r in [r for r in effective['WeaponAmmunitionsJson'].values() if r['UnitId']==u and r['WeaponId']==w]:
                    clone('WeaponAmmunitionsJson',r['Id'],{'WeaponId':w2,'Quantity':r['Quantity']*2},why46)
        put('OptionsJson',oid,{first:t2,dup:rack[t]},why46)
    like=effective['AbilitiesJson'][h30['laser_like']];why='Helicopter laser designator';made={}
    def lased(aid):
        a=effective['AbilitiesJson'][aid];assert a['Name'].startswith('ECM Heli') and not a['IsLaserDesignator'],aid
        if aid not in made:made[aid]=clone('AbilitiesJson',aid,{**{f:like[f] for f in h30['laser_fields']},'Name':a['Name']+' + Laser'},why)
        return made[aid]
    for u in h30['laser_units']:
        for r in [r for r in effective['UnitAbilitiesJson'].values() if r['UnitId']==u]:put('UnitAbilitiesJson',r['Id'],{'AbilityId':lased(r['AbilityId'])},why)
        for o in options(u):
            for i in (1,2,3):
                if o.get(f'Ability{i}Id'):put('OptionsJson',o['Id'],{f'Ability{i}Id':lased(o[f'Ability{i}Id'])},why)
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
    # 0.5 dev.44: BARS 7 men 35 HP, 3 PKM and 4 AK-74M (bars-contract.json). Before dev.35, which counts launcher carriers.
    bars=json.loads((R/'bars-contract.json').read_text());why='BARS 7 men, 3 PKM'
    for rid in bars['retire_members']:
        assert effective['SquadMembersJson'][rid]['UnitId']==bars['unit'],rid
        drop('SquadMembersJson',rid)
    for key,aid in bars['armor_links'].items():
        assert effective['UnitArmorsJson'][int(key)]['UnitId']==bars['unit'],key
        put('UnitArmorsJson',int(key),{'ArmorId':aid},'BARS 7 men, 35 HP')
    for key,f in bars['member_fields'].items():
        assert effective['SquadMembersJson'][int(key)]['UnitId']==bars['unit'] and effective['SquadMembersJson'][int(key)]['PrimaryWeaponId']==bars['ak'],key
        put('SquadMembersJson',int(key),f,why)
    men=[m for m in effective['SquadMembersJson'].values() if m['UnitId']==bars['unit']]
    assert len(men)==bars['men'] and sum(m['PrimaryWeaponId']==bars['pkm'] for m in men)==bars['pkm_men'] and sum(m['PrimaryWeaponId']==bars['ak'] for m in men)==bars['ak_men']
    assert len(men)*5==effective['ArmorsJson'][effective['UnitArmorsJson'][1309]['ArmorId']]['MaxHealthPoints']
    assert sum(m['SpecialWeaponId']==bars['rpg26'] for m in men)==bars['rpg26_men'] and sum(m['SpecialWeaponId']==bars['gp25'] for m in men)==bars['gp25_men']
    # 0.6: Spetsnaz Alpha close-quarters 10 men at 85, stand-off back to 2 AEK-999 and 2 RG-6, Delta Force stand-off laser (alpha-delta-contract.json).
    ad=json.loads((R/'alpha-delta-contract.json').read_text())
    cq=ad['alpha_cqc'];why='Spetsnaz Alpha close-quarters 10 men'
    for rid in cq['retire_members']:
        m=effective['SquadMembersJson'][rid]
        assert m['UnitId']==cq['unit'] and m['PrimaryWeaponId']==cq['rifle'] and not m['SpecialWeaponId'],rid
        drop('SquadMembersJson',rid)
    link=effective['UnitArmorsJson'][cq['armor_link']];assert (link['UnitId'],link['ArmorId'])==(cq['unit'],cq['armor_like'])
    like=effective['ArmorsJson'][cq['armor_like']];assert like['Name'].strip()=='Armor Infantry Elite 12Men' and like['MaxHealthPoints']==60
    put('UnitArmorsJson',cq['armor_link'],{'ArmorId':clone('ArmorsJson',cq['armor_like'],{'Name':'Armor Infantry Elite 10Men','MaxHealthPoints':5*cq['men']},why)},why)
    men=[m for m in effective['SquadMembersJson'].values() if m['UnitId']==cq['unit']]
    assert len(men)==cq['men'] and sum(m['PrimaryWeaponId']==cq['rifle'] for m in men)==cq['rifle_men']
    assert len(men)*5==effective['ArmorsJson'][effective['UnitArmorsJson'][cq['armor_link']]['ArmorId']]['MaxHealthPoints']
    so=ad['alpha_standoff'];why='Spetsnaz Alpha stand-off 2 AEK-999 and 2 RG-6'
    for key,f in so['member_fields'].items():
        assert effective['SquadMembersJson'][int(key)]['UnitId']==so['unit'],key
        put('SquadMembersJson',int(key),f,why)
    men=[m for m in effective['SquadMembersJson'].values() if m['UnitId']==so['unit']]
    assert len(men)==so['men'] and all(sum(m['PrimaryWeaponId']==int(w) for m in men)==n for w,n in so['counts'].items()),so
    dl=ad['delta_laser'];link=effective['UnitAbilitiesJson'][dl['link']]
    assert (link['UnitId'],link['AbilityId'])==(dl['unit'],dl['from']) and effective['AbilitiesJson'][dl['to']]['IsLaserDesignator']
    a,b={k:v for k,v in effective['AbilitiesJson'][dl['from']].items() if k not in ('Id','Name')},{k:v for k,v in effective['AbilitiesJson'][dl['to']].items() if k not in ('Id','Name')}
    assert {k for k in a if a[k]!=b.get(k)}=={'IsLaserDesignator','LaserMaxRange'},'the laser ability must be the same ability plus the laser'
    put('UnitAbilitiesJson',dl['link'],{'AbilityId':dl['to']},'Delta Force stand-off laser designator')
    # 0.6: 30-point 3-man recon card in every deck, 8 per deck; old Razvedka and Scouts renamed (scouts-contract.json).
    def rows_of(table,uid):return [r['Id'] for r in effective[table].values() if r['UnitId']==uid]
    sc=json.loads((R/'scouts-contract.json').read_text())
    for key,f in sc['rename'].items():put('Units',int(key),f,'Recon card renamed for the new 3-man card')
    for c in sc['cards']:
        why='3-man recon card '+c['fields']['HUDName'];par,new=c['parent'],c['unit']
        assert new not in effective['Units'] and effective['Units'][par]['CountryId']==c['country']
        add_unit(new,par,c['fields'],why)
        for table in ['UnitAbilitiesJson','SensorUnitsJson','UnitPropulsionsJson']:
            for rid in rows_of(table,par):clone(table,rid,{'UnitId':new},why)
        arm=effective['ArmorsJson'][c['armor']];assert re.search(r'\b3Men\b',arm['Name']) and arm['MaxHealthPoints']==15,arm['Name']
        (link,)=rows_of('UnitArmorsJson',par);clone('UnitArmorsJson',link,{'UnitId':new,'ArmorId':c['armor']},why)
        for like,prio in c['members']:
            assert effective['SquadMembersJson'][like]['UnitId']==par,like
            clone('SquadMembersJson',like,{'UnitId':new,'PrimaryWeaponId':c['rifle'],'SpecialWeaponId':c['launcher'],'DeathPriority':prio},why)
        sw=rows_of('SquadWeaponsJson',par)[0];wa=rows_of('WeaponAmmunitionsJson',par)[0]
        for order,(wid,(aid,qty)) in enumerate(c['ammo'].items()):
            assert any(r['WeaponId']==int(wid) and r['AmmunitionId']==aid for r in effective['WeaponAmmunitionsJson'].values()),wid
            clone('SquadWeaponsJson',sw,{'UnitId':new,'WeaponId':int(wid),'Order':order},why)
            clone('WeaponAmmunitionsJson',wa,{'UnitId':new,'WeaponId':int(wid),'AmmunitionId':aid,'Order':0,'Quantity':qty},why)
        decks={s for s,r in effective['SpecializationsJson'].items() if r['ShowInHangar'] and r['CountryId']==c['country']}
        assert decks=={int(s) for s in c['transports_from']},(c['unit'],sorted(decks))
        for s,like in c['transports_from'].items():
            assert effective['Units'][effective['SpecializationAvailabilitiesJson'][like]['UnitId']]['CountryId']==c['country'] and effective['SpecializationAvailabilitiesJson'][like]['SpecializationId']==int(s),like
            pool=clone('SpecializationAvailabilitiesJson',like,{'UnitId':new,'SpecializationId':int(s),'MaxAvailabilityXp0':sc['availability']},why)
            for t in [r for r in effective['TransportAvailabilitiesJson'].values() if r['SpecializationAvailabilityId']==like]:
                clone('TransportAvailabilitiesJson',t['Id'],{'SpecializationAvailabilityId':pool},why)
        men=[m for m in effective['SquadMembersJson'].values() if m['UnitId']==new]
        assert len(men)==3 and all((m['PrimaryWeaponId'],m['SpecialWeaponId'])==(c['rifle'],c['launcher']) for m in men)
    # 0.6: recon helicopters, own cards in the recon tab, availability 4 (recon-heli-contract.json).
    # 0.6: F-16C Block 50 ASF, an F-16C copy with its air-to-air loadout built in (f16-asf-contract.json).
    # 0.6: F-35C and EA-18G Growler, with option edits, an ECM ability swap and extra pylon rows (navy-air-contract.json).
    def slots(o):return {o[k] for k in o if k.startswith('Turret') and k.endswith('Id') and o[k]}
    def copy_card(rh,c):
        why=('Recon helicopter ' if rh.get('type',8)==8 else 'Card copy ')+c['fields']['HUDName'];par,new=c['parent'],c['unit']
        country=rh.get('country',1)
        assert new not in effective['Units'] and effective['Units'][par]['Type']==rh.get('type',8) and effective['Units'][par]['CountryId']==country
        add_unit(new,par,{**c['fields'],'CategoryType':rh['category']},why)
        popts=options(par);keep=set(c['keep_options'])
        assert keep<={o['Id'] for o in popts},(new,keep-{o['Id'] for o in popts})
        used=set().union(*map(slots,popts)) if popts else set()
        used|={t for t,(t2,_) in load2.items() if t2 in used}  # dev.46: a launcher replaced by its both-racks copy is still an option turret
        turrets={r['TurretId'] for r in effective['TurretUnitsJson'].values() if r['UnitId']==par}
        kept_t=({t for t in turrets if t not in used}|set().union(*(slots(o) for o in popts if o['Id'] in keep))|set(c.get('keep_turrets',[])))-set(c.get('drop_turrets',[]))
        assert set(c.get('keep_turrets',[]))<=turrets
        weapons={r['WeaponId'] for r in effective['TurretWeaponsJson'].values() if r['TurretId'] in kept_t}
        for r in [r for r in list(effective['TurretUnitsJson'].values()) if r['UnitId']==par and r['TurretId'] in kept_t]:clone('TurretUnitsJson',r['Id'],{'UnitId':new},why)
        for r in [r for r in list(effective['WeaponAmmunitionsJson'].values()) if r['UnitId']==par and r['WeaponId'] in weapons]:clone('WeaponAmmunitionsJson',r['Id'],{'UnitId':new},why)
        for table in ['UnitAbilitiesJson','UnitArmorsJson','UnitPropulsionsJson']:
            for rid in rows_of(table,par):
                if table=='UnitAbilitiesJson' and effective[table][rid]['AbilityId'] in c.get('drop_abilities',[]):continue
                sw=c.get('ability_swap',{}).get(str(effective[table][rid].get('AbilityId')))
                clone(table,rid,{'UnitId':new,**({'AbilityId':sw} if table=='UnitAbilitiesJson' and sw else {})},why)
        for table,rids in c.get('add_rows',{}).items():
            for rid in rids:
                assert rid not in rows_of(table,par);clone(table,rid,{'UnitId':new},why)
        if 'optics' in c:
            # One optics row for the card; no kept option may pick another sensor.
            sl=rows_of('SensorUnitsJson',par)[0];clone('SensorUnitsJson',sl,{'UnitId':new,'SensorId':rh['sensors'][c['optics']]},why)
            assert all(not o['MainSensorId'] and not o['ExtraSensorId'] for o in popts if o['Id'] in keep)
        else:
            for rid in rows_of('SensorUnitsJson',par):clone('SensorUnitsJson',rid,{'UnitId':new},why)
        newmod={}
        for mod in sorted({o['ModificationId'] for o in popts if o['Id'] in keep}):
            m=newmod[mod]=clone('ModificationsJson',mod,{'UnitId':new},why)
            mine=sorted((o for o in popts if o['ModificationId']==mod and o['Id'] in keep),key=lambda o:(o['Order'],o['Id']))
            default=any(o['IsDefault'] for o in mine) or not any(o['IsDefault'] for o in popts if o['ModificationId']==mod)
            for order,o in enumerate(mine):
                clone('OptionsJson',o['Id'],{'ModificationId':m,'Order':order,'Cost':c['option_costs'].get(str(o['Id']),o['Cost']),'IsDefault':o['IsDefault'] or (not default and order==0),**c.get('option_fields',{}).get(str(o['Id']),{})},why)
        # A new choice in an existing slot: a copy of a kept option, placed last in the same slot.
        for x in c.get('extra_options',[]):
            assert x['like'] in keep;m=newmod[effective['OptionsJson'][x['like']]['ModificationId']]
            clone('OptionsJson',x['like'],{'ModificationId':m,'Order':1+max(o['Order'] for o in effective['OptionsJson'].values() if o['ModificationId']==m),**x['fields']},why)
        like=next((r['Id'] for r in effective['SpecializationAvailabilitiesJson'].values() if r['UnitId']==par),c.get('pool_like'))
        for s in c['decks']:
            assert effective['SpecializationsJson'][s]['CountryId']==country
            clone('SpecializationAvailabilitiesJson',like,{'UnitId':new,'SpecializationId':s,'MaxAvailabilityXp0':c.get('availability',rh['availability'])},why)
        assert not any(r['UnitId']==new for r in effective['TransportAvailabilitiesJson'].values())
        # Every pylon an option names is on the card, and every weapon on the card has its rounds.
        mine={r['TurretId'] for r in effective['TurretUnitsJson'].values() if r['UnitId']==new}
        assert all(slots(o)<=mine for o in options(new)),(new,'option turret missing')
        armed={r['WeaponId'] for r in effective['TurretWeaponsJson'].values() if r['TurretId'] in mine}
        assert armed<={r['WeaponId'] for r in effective['WeaponAmmunitionsJson'].values() if r['UnitId']==new},(new,'weapon without rounds')
    for rh,c in [(rh,c) for f in ('recon-heli-contract.json','recon-heli-us-contract.json','f16-asf-contract.json','navy-air-contract.json','mig31bsm-contract.json') for rh in [json.loads((R/f).read_text())] for c in rh['cards']]:copy_card(rh,c)
    # 0.6: the Airborne TOW-2A team also in Stryker, riding a Stryker ICV (tow-stryker-contract.json).
    tw=json.loads((R/'tow-stryker-contract.json').read_text());why='TOW-2A team in Stryker'
    pool=effective['SpecializationAvailabilitiesJson'][tw['like']];assert pool['UnitId']==tw['unit'],tw
    assert not any(r['UnitId']==tw['unit'] and r['SpecializationId']==tw['spec'] for r in effective['SpecializationAvailabilitiesJson'].values())
    ride=effective['TransportAvailabilitiesJson'][tw['transport_like']];assert effective['SpecializationAvailabilitiesJson'][ride['SpecializationAvailabilityId']]['SpecializationId']==tw['spec']
    new=clone('SpecializationAvailabilitiesJson',tw['like'],{'SpecializationId':tw['spec']},why)
    clone('TransportAvailabilitiesJson',tw['transport_like'],{'SpecializationAvailabilityId':new},why)
    # 0.6: long-range SAM cards availability 3; S-400 stays 2 (sam-avail-contract.json).
    sa=json.loads((R/'sam-avail-contract.json').read_text())
    for pid,uid in sa['pools'].items():
        r=effective['SpecializationAvailabilitiesJson'][int(pid)];assert r['UnitId']==uid and r['MaxAvailabilityXp0']==sa['was'],(pid,r)
        put('SpecializationAvailabilitiesJson',int(pid),{'MaxAvailabilityXp0':sa['availability']},'Long-range SAM availability 3')
    for pid,uid in sa['held'].items():
        r=effective['SpecializationAvailabilitiesJson'][int(pid)];assert r['UnitId']==uid and r['MaxAvailabilityXp0']==sa['was'],(pid,r)
    # 0.6: Airborne infantry shows as Air Naval (spec-contract.json). Only the shown name.
    sc=json.loads((R/'spec-contract.json').read_text())
    for sid,x in sc['specs'].items():
        row=effective['SpecializationsJson'][int(sid)];assert all(row[k]==v for k,v in x['was'].items()),('spec changed upstream',sid)
        put('SpecializationsJson',int(sid),x['fields'],'Specialization shown name')
    # 0.6: B-52H AGM-183A ARRW, 2x in the bomb bay and 2x on the wings, +200 each; a renamed copy of the Kinzhal HE on the Kinzhal model (arrw-contract.json).
    aw=json.loads((R/'arrw-contract.json').read_text());why='AGM-183A ARRW on the B-52H'
    assert effective['AmmunitionsJson'][aw['ammo']]['HUDName']=='Kh-47M2 Kinzhal' and effective['WeaponsJson'][aw['weapon']]['Name']=='Cruise Kh47M2 HE'
    am=clone('AmmunitionsJson',aw['ammo'],{'HUDName':aw['name'],'Name':'Missile Cruise AGM183A ARRW',**aw.get('ammo_fields',{})},why)
    (tw,)=[r['Id'] for r in effective['TurretWeaponsJson'].values() if r['TurretId']==aw['turret'] and r['WeaponId']==aw['weapon']]
    b52mods={m['Id'] for m in effective['ModificationsJson'].values() if m['UnitId']==aw['unit']}
    assert effective['TurretUnitsJson'][aw['like_turret_link']]['UnitId']==aw['unit'] and effective['WeaponAmmunitionsJson'][aw['like_ammo_link']]['UnitId']==aw['unit']
    for ld in aw['loads']:
        # Each load has its own weapon and pylon rows, because the round count is per weapon per mount.
        wp=clone('WeaponsJson',aw['weapon'],{'HUDName':aw['name'],'Name':'Cruise AGM183A ARRW '+ld['slot'],'MagazineSize':ld['per_mount']},why)
        model={'ModelFileName':effective['TurretsJson'][ld['model_like']]['ModelFileName']} if 'model_like' in ld else {}
        tu=clone('TurretsJson',aw['turret'],{'Name':'PylonTurret B52H AGM183A ARRW '+ld['slot'],**model},why)
        ch=effective['TurretWeaponsJson'][aw['channel_like']];assert effective['TurretUnitsJson'][aw['like_turret_link']]['UnitId']==aw['unit'] and ch['WeaponId']==430
        clone('TurretWeaponsJson',tw,{'TurretId':tu,'WeaponId':wp,'WeaponChannel':ch['WeaponChannel'],'WeaponPriority':ch['WeaponPriority']},why)
        like=effective['OptionsJson'][ld['like_option']];assert like['ModificationId'] in b52mods
        mounts={k:tu for k in like if k.startswith('Turret') and k.endswith('Id') and like[k]}
        assert len(mounts)*ld['per_mount']==2,ld
        clone('OptionsJson',ld['like_option'],{'Name':ld['option_name'],'UIName':'2x '+aw['name'],'Cost':ld['cost'],'IsDefault':False,'OptionPicture':'MOD_KINZHAL_HE','Order':1+max(o['Order'] for o in effective['OptionsJson'].values() if o['ModificationId']==like['ModificationId']),**mounts},why)
        clone('TurretUnitsJson',aw['like_turret_link'],{'TurretId':tu},why)
        clone('WeaponAmmunitionsJson',aw['like_ammo_link'],{'WeaponId':wp,'AmmunitionId':am,'Quantity':ld['per_mount']},why)
    # 0.6: supply trucks in more decks; artillery uses twice the supply (logistics-contract.json). Truck prices are in vehicle-contract.json.
    lg=json.loads((R/'logistics-contract.json').read_text());why='Supply truck card in another deck'
    for p in lg['pools']:
        like=effective['SpecializationAvailabilitiesJson'][p['like']];assert like['UnitId']==p['unit'],p
        for s in p['specs']:
            assert effective['SpecializationsJson'][s]['CountryId']==effective['Units'][p['unit']]['CountryId']
            assert not any(r['UnitId']==p['unit'] and r['SpecializationId']==s for r in effective['SpecializationAvailabilitiesJson'].values()),p
            clone('SpecializationAvailabilitiesJson',p['like'],{'SpecializationId':s},why)
    for c in lg['copies']:
        why='Truck card copy '+c['fields']['HUDName'];par,new=c['parent'],c['unit']
        assert new not in effective['Units'] and effective['SpecializationAvailabilitiesJson'][c['like']]['UnitId']==par
        add_unit(new,par,c['fields'],why)
        for table in ['TurretUnitsJson','WeaponAmmunitionsJson','UnitAbilitiesJson','UnitArmorsJson','UnitPropulsionsJson','SensorUnitsJson']:
            for rid in rows_of(table,par):clone(table,rid,{'UnitId':new},why)
        keep=[o for o in options(par) if o['Id'] in c['keep_options']];assert len(keep)==len(c['keep_options'])
        assert all(not any(o.get(f'Turret{i}Id') for i in range(21)) for o in options(par))
        for mod in sorted({o['ModificationId'] for o in keep}):
            m=clone('ModificationsJson',mod,{'UnitId':new},why)
            for order,o in enumerate(sorted((o for o in keep if o['ModificationId']==mod),key=lambda o:o['Order'])):clone('OptionsJson',o['Id'],{'ModificationId':m,'Order':order},why)
        for s in c['specs']:clone('SpecializationAvailabilitiesJson',c['like'],{'UnitId':new,'SpecializationId':s},why)
    for aid,a in effective['AmmunitionsJson'].items():
        if a['TrajectoryType'] not in lg['artillery_trajectories'] or a['SupplyCost']<=0:continue
        kinds={effective['Units'][r['UnitId']]['Type'] for r in effective['WeaponAmmunitionsJson'].values() if r['AmmunitionId']==aid and r['UnitId'] in effective['Units']}
        if kinds-{4}:continue  # plane and ship rounds
        put('AmmunitionsJson',aid,{'SupplyCost':a['SupplyCost']*lg['supply_factor']},'Artillery uses twice the supply')
    # 0.6 (Osama): artillery penetration FA lowered (0.1 caps above) x1.5, never above vanilla (arty-pen-contract.json).
    arty=json.loads((R/'arty-pen-contract.json').read_text());n=0
    for aid,row in list(effective['AmmunitionsJson'].items()):
        van=original['AmmunitionsJson'].get(aid)
        if row['TrajectoryType'] not in arty['trajectories'] or van is None:continue
        cur=(row['PenetrationAtMinRange'],row['PenetrationAtGroundRange'])
        if cur==(van['PenetrationAtMinRange'],van['PenetrationAtGroundRange']):continue
        assert all(c<v for c,v in zip(cur,(van['PenetrationAtMinRange'],van['PenetrationAtGroundRange']))),('artillery above vanilla',aid)
        assert aid in arty['ammo'],('artillery row not in contract',aid)
        put('AmmunitionsJson',aid,{'PenetrationAtMinRange':min(cur[0]*arty['factor'],van['PenetrationAtMinRange']),'PenetrationAtGroundRange':min(cur[1]*arty['factor'],van['PenetrationAtGroundRange'])},'Artillery penetration x1.5, not above vanilla');n+=1
    assert n==len(arty['ammo']),('artillery rows',n)
    # 0.6: SEAD missiles move as in ActualArrow 1.1.20: speed, acceleration, turn rate (sead-contract.json).
    sd=json.loads((R/'sead-contract.json').read_text())
    for aid,fields in sd['fields'].items():
        row=effective['AmmunitionsJson'][int(aid)];assert row['Seeker']==200 and all(row[k]==v for k,v in sd['was'][aid].items()),('SEAD row changed upstream',aid)
        put('AmmunitionsJson',int(aid),fields,'SEAD missile movement as ActualArrow 1.1.20')
    # 0.6: 12ga SLUG T2 (M1014, Benelli M4) damage 7.0, penetration at max range 8 (slug-contract.json).
    sl=json.loads((R/'slug-contract.json').read_text());row=effective['AmmunitionsJson'][sl['ammo']]
    assert all(row[k]==v for k,v in sl['was'].items()),('slug changed upstream',{k:row[k] for k in sl['was']})
    put('AmmunitionsJson',sl['ammo'],sl['fields'],'12ga SLUG T2 damage 7.0, max-range penetration 8')
    # 0.6: infantry in buildings at Wargame level; unguided bombs lose overpressure; penetration cap (cover-wargame-contract.json).
    cw=json.loads((R/'cover-wargame-contract.json').read_text());cap=lambda d,a:math.floor(a*math.sqrt(cw['max_hit']/(d-cw['max_hit']))) if d>cw['max_hit'] else math.inf
    for aid in cw['mlrs']:
        row=effective['AmmunitionsJson'][aid];assert row['Name'].startswith('MLRS') and row['Damage']>=10 and not row['GenerateSmoke'],aid
        mf=cw['mlrs_fields'][str(aid)]  # dev.73-75: about 90% of Wargame per rocket counting misses; MBT roof hit about 1.5 HP at most
        put('AmmunitionsJson',aid,{'IgnoreCover':cw['mlrs_ignore_cover'],'Damage':mf['Damage'],'PenetrationAtMinRange':mf['Pen'],'PenetrationAtGroundRange':mf['Pen']},'MLRS at about 90% of Wargame per rocket, low penetration')
    for aid in cw['bombs']:
        row=effective['AmmunitionsJson'][aid];assert row['Name'].startswith('Bomb') and row['Damage']>=15 and row['IgnoreCover']==0,aid
        assert not re.search('Cluster|Napalm|Nuke',row['Name']),aid
        f={'IgnoreCover':cw['bomb_ignore_cover']}
        if aid in cw['no_overpressure']:
            assert not re.search('GBU|KAB',row['Name']) and row['OverpressureRadius']>0,aid
            f['OverpressureRadius']=0.0
            if row['PenetrationAtMinRange']>cap(row['Damage'],cw['bomb_armor']):f.update(PenetrationAtMinRange=float(cap(row['Damage'],cw['bomb_armor'])),PenetrationAtGroundRange=float(cap(row['Damage'],cw['bomb_armor'])))
        put('AmmunitionsJson',aid,f,'Bomb ignore cover 0.5; unguided: no overpressure, penetration under one MBT kill')
    fb=cw['fab9000'];row=effective['AmmunitionsJson'][fb['ammo']];assert row['Name']=='Bomb 9000kg FAB9000' and row['IgnoreCover']==0 and row['OverpressureRadius']>0,row['Name']
    put('AmmunitionsJson',fb['ammo'],{'IgnoreCover':fb['ignore_cover'],'OverpressureRadius':0.0,'PenetrationAtMinRange':fb['penetration'],'PenetrationAtGroundRange':fb['penetration']},'FAB-9000 ignores cover 1.0, penetration 150, no overpressure')
    bl=cw['ballistic']
    assert {a['Id'] for a in effective['AmmunitionsJson'].values() if a['Name'].startswith('Missile Ballistic')}==set(bl['ammo']),'ballistic rows changed'
    for aid in bl['ammo']:put('AmmunitionsJson',aid,{'IgnoreCover':bl['ignore_cover']},'Ballistic missiles ignore cover 1.0')
    mop=cw['mop'];row=effective['AmmunitionsJson'][mop['ammo']];assert row['Name']=='Bomb 13600kg GBU57' and row['IgnoreCover']==0,row['Name']
    put('AmmunitionsJson',mop['ammo'],{'IgnoreCover':mop['ignore_cover']},'B-2 GBU-57 MOP ignores cover 1.0')
    o=effective['OptionsJson'][mop['option']];assert o['Name']=='Loadout B2 2xGBU57' and o['Cost']==mop['option_cost_was'],(o['Name'],o['Cost'])
    put('OptionsJson',mop['option'],{'Cost':mop['option_cost']},'B-2 2x GBU-57 MOP loadout +250')
    # 0.6 dev.63: BRM-3K Very Good optics on every turret, Kaktus ERA HEAT front and side 700 (brm3k-contract.json).
    bk=json.loads((R/'brm3k-contract.json').read_text());why='BRM-3K Very Good optics, Kaktus HEAT 700'
    assert any(r['UnitId']==bk['unit'] and r['SensorId']==bk['sensor'] for r in effective['SensorUnitsJson'].values())
    for oid in bk['options']:
        o=effective['OptionsJson'][oid];assert effective['ModificationsJson'][o['ModificationId']]['UnitId']==bk['unit'] and o['MainSensorId']==bk['sensor_was'],oid
        put('OptionsJson',oid,{'MainSensorId':bk['sensor']},why)
    ar=effective['ArmorsJson'][bk['armor']];assert ar['HeatArmorFront']==ar['HeatArmorSides']==bk['heat_was'],ar
    assert [o['Id'] for o in effective['OptionsJson'].values() if o['ArmorId']==bk['armor']]==[bk['armor_option']]
    assert {r['UnitId'] for r in effective['UnitArmorsJson'].values() if r['ArmorId']==bk['armor']}=={bk['unit']}
    put('ArmorsJson',bk['armor'],{'HeatArmorFront':bk['heat'],'HeatArmorSides':bk['heat']},why)
    # 0.6 dev.64: MiG-31BM air-to-air only (ground-strike options go to the MiG-31BSM card); wheeled cargo trucks availability 4 (mig31bsm-contract.json).
    mb=json.loads((R/'mig31bsm-contract.json').read_text());par=mb['cards'][0]['parent']
    for oid in mb['retire_parent_options']:
        o=effective['OptionsJson'][oid];assert effective['ModificationsJson'][o['ModificationId']]['UnitId']==par and not o['IsDefault'],oid
        assert any(x['Name'].split()[-1]==o['Name'].split()[-1] for x in options(mb['cards'][0]['unit'])),oid
        drop('OptionsJson',oid)
    for uid,spec in mb['truck_pools_unit_spec']:
        (r,)=[r for r in effective['SpecializationAvailabilitiesJson'].values() if (r['UnitId'],r['SpecializationId'])==(uid,spec)];u=effective['Units'][uid]
        assert r['MaxAvailabilityXp0']==mb['truck_was'] and u['Role']==14 and u['Type']==4,(uid,u['HUDName'])
        put('SpecializationAvailabilitiesJson',r['Id'],{'MaxAvailabilityXp0':mb['truck_availability']},'Cargo truck availability 4')
    left={a['Id'] for a in effective['AmmunitionsJson'].values() if a['Name'].startswith(('Bomb','MLRS')) and a['Damage']>=10 and a['IgnoreCover'] not in (cw['bomb_ignore_cover'],cw['mlrs_ignore_cover'],1.0) and not re.search('Cluster|Napalm|Nuke|Incendiary|SMK',a['Name'])}
    assert not left,('bomb or MLRS row not in contract',sorted(left))
    # 0.6: 15 smoke rounds on Nona-S, Nona-SVK, Magnolia and LAV-M loadouts; Hawkeye MWS in Special Operations (smoke15-contract.json).
    sm=json.loads((R/'smoke15-contract.json').read_text());why='Mortar loadout 15 smoke rounds'
    for r in sm['smoke']:
        a=effective['AmmunitionsJson'][r['ammo']];assert a['GenerateSmoke'],r
        rows=[w for w in effective['WeaponAmmunitionsJson'].values() if (w['UnitId'],w['WeaponId'],w['AmmunitionId'])==(r['unit'],r['weapon'],r['ammo'])]
        if rows:
            (w,)=rows;assert 'like' not in r and w['Quantity']<r['quantity'],r
            put('WeaponAmmunitionsJson',w['Id'],{'Quantity':r['quantity']},why)
        else:
            like=effective['WeaponAmmunitionsJson'][r['like']];assert like['UnitId']==r['unit'],r
            assert any(t['WeaponId']==r['weapon'] for t in effective['TurretWeaponsJson'].values()),r
            clone('WeaponAmmunitionsJson',r['like'],{'WeaponId':r['weapon'],'AmmunitionId':r['ammo'],'Quantity':r['quantity'],'Order':1+max(w['Order'] for w in effective['WeaponAmmunitionsJson'].values() if (w['UnitId'],w['WeaponId'])==(r['unit'],r['weapon']))},why)
    for p in sm['pools']:
        assert effective['SpecializationAvailabilitiesJson'][p['like']]['UnitId']==p['unit']
        for s in p['specs']:
            assert not any(r['UnitId']==p['unit'] and r['SpecializationId']==s for r in effective['SpecializationAvailabilitiesJson'].values())
            clone('SpecializationAvailabilitiesJson',p['like'],{'SpecializationId':s},'Hawkeye MWS in Special Operations')
    # 0.6: display-name changes only (rename-contract.json).
    rn=json.loads((R/'rename-contract.json').read_text())
    for table in ('WeaponsJson',):
        for key,f in rn[table].items():
            assert effective[table][int(key)]['HUDName']==f['was'],(table,key)
            put(table,int(key),{'HUDName':f['HUDName']},'Display name '+f['HUDName'])
    # 0.6: MiG-31 agility, moderate nerf (mig31-contract.json). Only the MiG-31 mobility row uses this preset.
    mg=json.loads((R/'mig31-contract.json').read_text());fp=effective['FlyPresetsJson'][mg['preset']]
    assert fp['Name']==mg['name'] and all(fp[k]==v for k,v in mg['was'].items()),('MiG-31 preset changed upstream',mg['preset'])
    assert {m['Name'] for m in effective['MobilityJson'].values() if m.get('FlyPresetId')==mg['preset']}=={'Plane MIG31'},'MiG-31 preset is shared'
    put('FlyPresetsJson',mg['preset'],mg['fields'],'MiG-31 turn 14/30/30, pitch 45, roll 75')
    # 0.6 dev.50: air combat by generation: ECM per jet, flares x0.9, instant air-to-air aim, F-22/Su-57 agility (air-gen-contract.json).
    ag=json.loads((R/'air-gen-contract.json').read_text());why='Air combat by generation'
    ecm_ab={i for i,a in effective['AbilitiesJson'].items() if a['IsDecoy'] and a['ECMAccuracyMultiplier']>0}
    made={}
    for key,tier in ag['tiers'].items():
        uid=int(key);assert effective['Units'][uid]['Type']==16,uid
        links=[r for r in effective['UnitAbilitiesJson'].values() if r['UnitId']==uid and r['AbilityId'] in ecm_ab]
        olds=sorted({r['AbilityId'] for r in links},key=lambda a:-effective['AbilitiesJson'][a]['ECMAccuracyMultiplier'])
        vals=sorted({effective['AbilitiesJson'][a]['ECMAccuracyMultiplier'] for a in olds},reverse=True)
        assert olds and all(effective['AbilitiesJson'][a]['DecoyAccuracyMultiplier']==ag['flare_was'] for a in olds),(uid,olds)
        swap={}
        for a in olds:
            new=round(max(ag['ecm_floor'],tier-ag['pod_step']*vals.index(effective['AbilitiesJson'][a]['ECMAccuracyMultiplier'])),2)
            if (a,new) not in made:made[(a,new)]=clone('AbilitiesJson',a,{'Name':effective['AbilitiesJson'][a]['Name']+f' FA {new:g}','ECMAccuracyMultiplier':new,'DecoyAccuracyMultiplier':ag['flare']},why)
            swap[a]=made[(a,new)]
        for r in links:put('UnitAbilitiesJson',r['Id'],{'AbilityId':swap[r['AbilityId']]},why)
        for o in options(uid):
            f={k:swap[o[k]] for k in ('Ability1Id','Ability2Id','Ability3Id') if o[k] in swap}
            if f:put('OptionsJson',o['Id'],f,why)
        left={r['AbilityId'] for r in effective['UnitAbilitiesJson'].values() if r['UnitId']==uid}|{o[k] for o in options(uid) for k in ('Ability1Id','Ability2Id','Ability3Id')}
        assert not left&set(olds),(uid,left&set(olds))
    for key,f in ag['unit_fields'].items():put('Units',int(key),f,'Super Hornet name')
    planes={u for u,r in effective['Units'].items() if r['Type']==16}
    aam=set()
    for r in effective['WeaponAmmunitionsJson'].values():
        a=effective['AmmunitionsJson'].get(r['AmmunitionId'])
        if r['UnitId'] in planes and a and a['TargetType']&24 and a['HighAltRange']>0 and a['Seeker']:aam.add(r['WeaponId'])
    shared={r['WeaponId'] for r in effective['WeaponAmmunitionsJson'].values() if r['WeaponId'] in aam and r['UnitId'] not in planes}
    for wid in sorted(aam-shared):put('WeaponsJson',wid,ag['aim'],'Air-to-air missile aims instantly')
    for wid in ag['big_sam']['weapons']:
        w=effective['WeaponsJson'][wid];assert w['Name'].startswith('SAM ') and w['AimTimeMin']==1.0 and wid not in aam,wid
        put('WeaponsJson',wid,ag['big_sam']['aim'],'Long-range SAM aims in 0.5 s')
    agl=ag['agile'];base=effective['FlyPresetsJson'][agl['preset']];assert base['Name']=='Fighter-Top' and base['CornerSpeedYaw']==50.8
    fp=clone('FlyPresetsJson',agl['preset'],{'Name':'FA Fighter-Supermaneuver',**{k:round(base[k]*agl['factor'],2) for k in agl['fields']}},'F-22 and Su-57 supermaneuverability')
    for uid in agl['units']:
        (link,)=[p for p in effective['UnitPropulsionsJson'].values() if p['UnitId']==uid]
        mob=link['MobilityId'];assert sum(p['MobilityId']==mob for p in effective['UnitPropulsionsJson'].values())==1 and effective['MobilityJson'][mob]['FlyPresetId']==agl['preset'],uid
        put('MobilityJson',mob,{'FlyPresetId':fp},'F-22 and Su-57 supermaneuverability')
    # 0.6 dev.51: S-300V4, S-300PM and PAC-2 missiles take the S-400 missile stats except range (sam-match-contract.json).
    smc=json.loads((R/'sam-match-contract.json').read_text())
    for key,src in smc['copies'].items():
        row=effective['AmmunitionsJson'][int(key)];tpl=effective['AmmunitionsJson'][src]
        assert row['Name'].startswith('Missile AA') and tpl['Name'].startswith('Missile AA S') and 'S400' in tpl['Name'],key
        f={k:v for k,v in tpl.items() if k not in smc['keep'] and row.get(k)!=v}
        if f:put('AmmunitionsJson',int(key),f,'Long-range SAM missile as the S-400, own range')
    # 0.6 dev.52: air-to-air missile ranges, R-37 accuracy, F-35 wingtip AIM-9 test slot (air-range-contract.json).
    ar=json.loads((R/'air-range-contract.json').read_text());planes={u for u,r in effective['Units'].items() if r['Type']==16}
    def plane_only(aid):return {r['UnitId'] in planes for r in effective['WeaponAmmunitionsJson'].values() if r['AmmunitionId']==aid}=={True}
    for aid in ar['plus_1km']:
        a=effective['AmmunitionsJson'][aid];assert plane_only(aid) and a['TargetType']&24 and 1000<a['HighAltRange']<=3500,aid
        put('AmmunitionsJson',aid,{'LowAltRange':a['LowAltRange']+ar['plus'],'HighAltRange':a['HighAltRange']+ar['plus']},'Medium air-to-air missile +1 km on the card (+500 data)')
    for aid in ar['long']:
        a=effective['AmmunitionsJson'][aid];assert plane_only(aid) and a['HighAltRange']==4500,aid
        put('AmmunitionsJson',aid,{'LowAltRange':ar['long_range'],'HighAltRange':ar['long_range']},'Long-range air-to-air missile 11 km on the card (5500 data)')
    for key,acc in ar['accuracy'].items():
        a=effective['AmmunitionsJson'][int(key)];assert a['HUDName']=='R-37' and a['DispersionHorizontalRadius']==1.0,key
        put('AmmunitionsJson',int(key),{'DispersionHorizontalRadius':acc},'R-37 accuracy 0.9')
    wt=ar['wingtips'];why='F-35 wingtip AIM-9 test slot'
    (tl,)=[r['Id'] for r in effective['TurretUnitsJson'].values() if r['UnitId']==wt['like_turret_link_unit'] and r['TurretId']==wt['turret']]
    (wl,)=[r['Id'] for r in effective['WeaponAmmunitionsJson'].values() if r['UnitId']==wt['like_turret_link_unit'] and r['WeaponId']==wt['weapon'] and r['AmmunitionId']==wt['ammo']]
    for uid in wt['units']:
        mods=[m for m in effective['ModificationsJson'].values() if m['UnitId']==uid]
        assert not any(o[f'Turret{i}Id'] for o in options(uid) for i in wt['mounts']),uid
        m=clone('ModificationsJson',wt['mod_like'],{'UnitId':uid,'Name':effective['Units'][uid]['Name']+' Wingtips','Order':1+max(x['Order'] for x in mods)},why)
        mounts=lambda t:{f'Turret{i}Id':t for i in wt['mounts']}
        clone('OptionsJson',wt['empty_like'],{'ModificationId':m,'Name':'Wingtips F35 Empty','IsDefault':True,'Order':0,'Cost':0,**mounts(0)},why)
        clone('OptionsJson',wt['aim9_like'],{'ModificationId':m,'Name':'Wingtips F35 2xAIM9','IsDefault':False,'Order':1,'Cost':wt['cost'],**mounts(wt['turret'])},why)
        if not any(r['UnitId']==uid and r['TurretId']==wt['turret'] for r in effective['TurretUnitsJson'].values()):clone('TurretUnitsJson',tl,{'UnitId':uid},why)
        if not any(r['UnitId']==uid and r['WeaponId']==wt['weapon'] for r in effective['WeaponAmmunitionsJson'].values()):clone('WeaponAmmunitionsJson',wl,{'UnitId':uid},why)
    # 0.6 dev.58 (Lateralus): air detection. Fighter and Patriot-tier high-altitude optics, plane stealth +0.25 UI,
    # six SHORADs on their own sensor copy (air-detect-contract.json). Displayed m = 2 x optics x radar x stealth.
    ad=json.loads((R/'air-detect-contract.json').read_text())
    for key,v in ad['high_optics'].items():
        assert effective['SensorsJson'][int(key)]['OpticsHighAltitude'] in (2000.0,6000.0),key
        put('SensorsJson',int(key),{'OpticsHighAltitude':v},'High-altitude optics (air detection)')
    for uid,u in list(effective['Units'].items()):
        if u['Type']==16 and f"{u['Stealth']:g}" in ad['plane_stealth']:
            v=ad['plane_stealth'][f"{u['Stealth']:g}"];put('Units',uid,{'Stealth':v,'CurrentStealth':v},'Plane stealth +0.25 UI')
    for uid,v in ad.get('unit_stealth',{}).items():
        u=effective['Units'][int(uid)];assert u['Type']==16,uid
        put('Units',int(uid),{'Stealth':v,'CurrentStealth':v},'Unit stealth (air-detect-contract.json unit_stealth)')
    sh=ad['shorad'];why='SHORAD high-altitude optics 1500 (6 km with radar on)';copies={}
    for uid in sh['units']:
        links=[r for r in effective['SensorUnitsJson'].values() if r['UnitId']==uid];assert links,uid
        for r in links:
            sid=r['SensorId'];assert sid in sh['sensors'],(uid,sid)
            if sid not in copies:copies[sid]=clone('SensorsJson',sid,{'OpticsHighAltitude':sh['high_optics']},why)
            put('SensorUnitsJson',r['Id'],{'SensorId':copies[sid]},why)
        for o in options(uid):
            if o['MainSensorId'] in copies:put('OptionsJson',o['Id'],{'MainSensorId':copies[o['MainSensorId']]},why)
            assert o['MainSensorId'] in (0,*copies.values()) and not o['ExtraSensorId'],(uid,o['Id'])
    # 0.6 dev.61 (Osama, in-game report): the dev.46 rack turret had no weapon, and the game builds a pylon model from its
    # weapons, so the second pod was not drawn. Each rack now holds a copy of the launcher weapon with no rounds on any
    # unit (no WeaponAmmunitions row, as vanilla does for unused loadout weapons): drawn, never fired. The both-racks
    # weapon's magazine now holds both racks' rounds, so it does not stop to reload halfway (the dev.59 ARRW fault).
    why61='Helicopter ATGM pylon: second rack drawn (weapon with no rounds); both-racks magazine holds all rounds'
    for t,(t2,wmap) in sorted(load2.items()):
        for w,w2 in wmap.items():put('WeaponsJson',w2,{'MagazineSize':effective['WeaponsJson'][w]['MagazineSize']*2},why61)
        assert not any(r['TurretId']==rack[t] for r in effective['TurretWeaponsJson'].values()),t
        for r in [r for r in effective['TurretWeaponsJson'].values() if r['TurretId']==t]:
            w=r['WeaponId'];wr=clone('WeaponsJson',w,{'Name':effective['WeaponsJson'][w]['Name']+' rack (no rounds)'},why61)
            clone('TurretWeaponsJson',r['Id'],{'TurretId':rack[t],'WeaponId':wr},why61)
            assert not any(a['WeaponId']==wr for a in effective['WeaponAmmunitionsJson'].values())
    # 0.6 (Osama): rocket pods at Wargame infantry damage per salvo (Wargame misses counted), open and in buildings; S-24 the tank killer (rocketpod-contract.json).
    rp=json.loads((R/'rocketpod-contract.json').read_text());why='Rocket pod: Wargame infantry damage, open and in buildings'
    hit=lambda d,p,a:d*p*p/(p*p+a*a)
    for key,v in rp['rounds'].items():
        a=effective['AmmunitionsJson'][int(key)];assert a['Name'].startswith('Rocket ') and a['IgnoreCover']==0.0 and a['PenetrationAtMinRange']==a['PenetrationAtGroundRange'],key
        assert all(effective['Units'][r['UnitId']]['Type'] in (8,16) for r in effective['WeaponAmmunitionsJson'].values() if r['AmmunitionId']==int(key)),key
        assert key in rp['tank_killer'] or hit(v['Damage'],v['Penetration'],rp['mbt_armor'])<=rp['mbt_max_hit']+1e-9,key
        put('AmmunitionsJson',int(key),{'Damage':v['Damage'],'PenetrationAtMinRange':v['Penetration'],'PenetrationAtGroundRange':v['Penetration'],'IgnoreCover':rp['ignore_cover']},why)
    # 0.6 dev.71/73 (Osama): Russian Mechanized Tulpan availability 4, Malka 6 (mech-arty-avail-contract.json).
    ma=json.loads((R/'mech-arty-avail-contract.json').read_text())
    for pool,uid in ma['pools'].items():
        r=effective['SpecializationAvailabilitiesJson'][int(pool)];assert r['UnitId']==uid and r['SpecializationId']==15,pool
        put('SpecializationAvailabilitiesJson',int(pool),{'MaxAvailabilityXp0':ma['availability'][pool]},'Mechanized Tulpan 4 and Malka 6 availability')
    ad=ma['add'];like=effective['SpecializationAvailabilitiesJson'][ad['like_pool']];assert like['UnitId']==ad['unit']
    assert not any(r['UnitId']==ad['unit'] and r['SpecializationId']==ad['specialization'] for r in effective['SpecializationAvailabilitiesJson'].values())
    clone('SpecializationAvailabilitiesJson',ad['like_pool'],{'SpecializationId':ad['specialization'],'MaxAvailabilityXp0':ad['availability']},'Msta-S in Mechanized Infantry, availability 4')
    # 0.6 dev.74 (Osama): M1299 Iron Thunder its own Armored Brigade card, M109A7 Paladin keeps only its own turret;
    # M109A6 Paladin in USMC (paladin-split-contract.json). Added last so no earlier clone ID moves.
    pz=json.loads((R/'paladin-split-contract.json').read_text())
    for c in pz['cards']:copy_card(pz,c)
    for c in pz['cards']:
        for oid in c['retire_parent_options']:
            o=effective['OptionsJson'][oid];assert effective['ModificationsJson'][o['ModificationId']]['UnitId']==c['parent'] and not o['IsDefault'],oid
            drop('OptionsJson',oid)
    ad=pz['add_pool'];like=effective['SpecializationAvailabilitiesJson'][ad['like_pool']];assert like['UnitId']==ad['unit']
    assert not any(r['UnitId']==ad['unit'] and r['SpecializationId']==ad['specialization'] for r in effective['SpecializationAvailabilitiesJson'].values())
    clone('SpecializationAvailabilitiesJson',ad['like_pool'],{'SpecializationId':ad['specialization'],'MaxAvailabilityXp0':ad['availability']},'M109A6 Paladin in USMC, availability 2')
    # 0.5 dev.35: infantry launcher rate of fire per squad (squad-rof-contract.json).
    sr=json.loads((R/'squad-rof-contract.json').read_text());why='Reusable launcher on 2-launcher squads 15 per minute'
    def carriers(uid,wid):return sum(1 for m in effective['SquadMembersJson'].values() if m['UnitId']==uid and wid in (m['PrimaryWeaponId'],m['SpecialWeaponId']))
    two=set()
    for r in effective['SquadWeaponsJson'].values():
        w=effective['WeaponsJson'][r['WeaponId']]
        if w['Type']==62 and w['MagazineSize']==1 and carriers(r['UnitId'],r['WeaponId'])>=2:two.add(r['WeaponId'])
    assert two==set(sr['two_launcher_rows']),sorted(two)
    for wid in sr['two_launcher_rows']:
        assert all(carriers(r['UnitId'],wid) in (0,2) for r in effective['SquadWeaponsJson'].values() if r['WeaponId']==wid),wid
        put('WeaponsJson',wid,{'MagazineReloadTimeMin':sr['two_launcher_reload'],'MagazineReloadTimeMax':sr['two_launcher_reload']},why)
    table={}
    for r in sorted(effective['SquadWeaponsJson'].values(),key=lambda r:r['Id']):
        w=effective['WeaponsJson'][r['WeaponId']]
        if w['Type']!=sr['disposable_type'] or w['MagazineSize']!=1:continue
        n=carriers(r['UnitId'],r['WeaponId'])
        if n<1:continue
        rate=sr['k']*n**sr['exponent'];table[f"{r['UnitId']}:{r['WeaponId']}"]={'carriers':n,'rate':round(rate,3),'reload':round(60*n/rate,3)}
    (R/'source/UserData/FreedomArrow/squad-reload.json').write_text(json.dumps({'k':sr['k'],'exponent':sr['exponent'],'disposableType':sr['disposable_type'],'squads':table},indent=1,sort_keys=True)+'\n')
    # Spotting cap (SpottingCap.cs): each observer's ground range stops at the vanilla value of its sensor tier.
    caps={}
    for sid,row in effective['SensorsJson'].items():
        if str(sid) in det['optics_ground_overrides']:continue  # moved to a tier: takes that tier's cap
        if sid not in original['SensorsJson']:continue  # a copy keeps its source's ground optics and cap
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

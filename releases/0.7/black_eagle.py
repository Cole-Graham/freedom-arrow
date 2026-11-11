"""One Coastal card using T-80BVM obr.2018+ with explicit requested overrides.

Build last to preserve every existing saved ID. The selected modernization is
intrinsic, so an empty saved option list has the same armor, engine and weapons.
"""
def apply(t, clone, add_unit, rows_of, c):
    uid, parent = c['unit'], c['parent']
    why = 'Osama: Black Eagle in Coastal, T80BVM obr2018 baseline'
    assert uid not in t['Units']
    option = t['OptionsJson'][c['baseline_option']]
    assert t['ModificationsJson'][option['ModificationId']]['UnitId'] == parent
    assert option['Name'] == 'Variant T80BVM Obr.2018+'
    add_unit(uid, parent, dict(Name=c['name'], HUDName=c['name'],
        Cost=c['cost'],
        PortraitFileName=c['portrait'], ThumbnailFileName=c['thumbnail']), why)

    def link(table, key, old, new):
        matches = [r for r in rows_of(table, parent) if t[table][r][key] == old]
        assert len(matches) == 1, (table, old)
        clone(table, matches[0], {'UnitId': uid, key: new}, why)

    armor = clone('ArmorsJson', option['ArmorId'],
        dict(Name='Armor Black Eagle obr2018 baseline', IsDefault=True, ModelFileName=None, **c['armor_fields']), why)
    link('UnitArmorsJson', 'ArmorId', option['ArmorId'], armor)
    mobility = clone('MobilityJson', option['MobilityId'],
        dict(Name='Tracks Black Eagle obr2018 baseline', IsDefault=True, ModelFileName=None, **c['mobility_fields']), why)
    link('UnitPropulsionsJson', 'MobilityId', option['MobilityId'], mobility)
    assert not option['ExtraSensorId'] and not option['StealthOverride']
    link('SensorUnitsJson', 'SensorId', option['MainSensorId'], option['MainSensorId'])
    assert not any(option[f'Ability{i}Id'] for i in (1, 2, 3))
    for rid in list(rows_of('UnitAbilitiesJson', parent)):
        aid = t['UnitAbilitiesJson'][rid]['AbilityId']
        fields = dict(Name='Black Eagle smoke x1', SmokeAmmunitionQuantity=c['smoke_quantity']) if t['AbilitiesJson'][aid]['IsSmoke'] else {}
        own = clone('AbilitiesJson', aid, fields, why)
        clone('UnitAbilitiesJson', rid, {'UnitId': uid, 'AbilityId': own}, why)

    # Preserve the native turret names and parent relationship. Making the
    # selected main turret intrinsic also covers a fresh or empty saved loadout.
    main = option['Turret0Id']
    assert main and all(not option[f'Turret{i}Id'] for i in range(1, 21))
    children = [t['TurretUnitsJson'][r]['TurretId'] for r in rows_of('TurretUnitsJson', parent)
                if t['TurretsJson'][t['TurretUnitsJson'][r]['TurretId']]['ParentTurretId'] == main]
    turrets = {main: clone('TurretsJson', main, {'IsDefault': True}, why)}
    for tid in children:
        turrets[tid] = clone('TurretsJson', tid, {'ParentTurretId': turrets[main]}, why)
    weapons = set()
    for old, own in turrets.items():
        link('TurretUnitsJson', 'TurretId', old, own)
        for row in list(t['TurretWeaponsJson'].values()):
            if row['TurretId'] == old:
                clone('TurretWeaponsJson', row['Id'], {'TurretId': own}, why)
                weapons.add(row['WeaponId'])
    for rid in list(rows_of('WeaponAmmunitionsJson', parent)):
        if t['WeaponAmmunitionsJson'][rid]['WeaponId'] in weapons:
            clone('WeaponAmmunitionsJson', rid, {'UnitId': uid}, why)
    availability = [r for r in rows_of('SpecializationAvailabilitiesJson', parent)
                    if t['SpecializationAvailabilitiesJson'][r]['SpecializationId'] == c['specialization']]
    assert len(availability) == 1
    clone('SpecializationAvailabilitiesJson', availability[0], {'UnitId': uid}, why)


def fix_t80_defaults(t, patches, clone, put, audit):
    """Discard inherited BV fallbacks on the BVM card without changing BV."""
    uid = 716
    options = [t['OptionsJson'][oid] for oid in (564, 566)]
    def unlink_except(table, key, allowed):
        removed = {r['Id'] for r in t[table].values() if r['UnitId'] == uid and r[key] not in allowed}
        for rid in removed:
            assert rid >= 2_000_000
            del t[table][rid]
            patches[table].pop(str(rid), None)
        audit[:] = [r for r in audit if not (r['table'] == table and r['id'] in removed)]
    unlink_except('UnitArmorsJson', 'ArmorId', {o['ArmorId'] for o in options})
    put('ArmorsJson', options[0]['ArmorId'], {'IsDefault': True}, 'T80BVM2017 is the intrinsic armor, not inherited BV')
    put('OptionsJson', 564, {'IsDefault': True}, 'T80BVM2017 fresh loadout default')
    source = options[0]['MobilityId']
    own = clone('MobilityJson', source, {'Name': 'Tracks T80BVM default', 'IsDefault': True}, 'BVM own default mobility; BV unchanged')
    unlink_except('UnitPropulsionsJson', 'MobilityId', {source})
    for row in list(t['UnitPropulsionsJson'].values()):
        if row['UnitId'] == uid:
            put('UnitPropulsionsJson', row['Id'], {'MobilityId': own}, 'BVM sole intrinsic mobility')
    for o in options:
        put('OptionsJson', o['Id'], {'MobilityId': own}, 'BVM both variants retain same selected mobility')
    unlink_except('SensorUnitsJson', 'SensorId', {options[0]['MainSensorId']})
    turret = options[0]['Turret0Id']
    assert {r['UnitId'] for r in t['TurretUnitsJson'].values() if r['TurretId'] == turret} == {uid}
    put('TurretsJson', turret, {'IsDefault': True}, 'BVM intrinsic main turret covers empty saved loadout')

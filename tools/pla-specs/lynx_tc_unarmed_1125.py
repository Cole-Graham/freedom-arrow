"""Lynx Troop Carrier entirely unarmed; Lynx ATV retired (Osama 25 Nov 2026 01:1x PST, thread 1567745029781454889: "LYNX troop carrier model
about 10% smaller, we can now replace the Lynx ATV and retire it. this should be entirely unarmed").
- Troop Carrier (1431, 'PLA Lynx CS/VP16B'): its QJZ-89 12.7 mm (31416) and QLZ-87 35 mm AGL (31417) options go, with their own turret, weapon
  and ammo rows, so the card lists no weapon. The Unarmed option (31415, empty turret) stays as the only choice. Model 10% smaller and no armed
  model swap: work/model-rework-096/stage.py.
- Lynx ATV (1448, lynx_ifv_atv_1125.py): hidden in the Armory and its 10 transport links removed. The Troop Carrier is offered to the same
  10 airborne squads (checked), so it takes the ATV's place. Its rows stay, so nothing that points to them breaks."""
TC, ATV, ARMED = 1431, 1448, (31416, 31417)


def apply(t, g, ok, rec):
    U, O, TU, TW, WA, TA, SA = (t[k] for k in ('Units', 'OptionsJson', 'TurretUnitsJson', 'TurretWeaponsJson', 'WeaponAmmunitionsJson',
                                              'TransportAvailabilitiesJson', 'SpecializationAvailabilitiesJson'))
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok(U[TC]['HUDName'] == 'Lynx Troop Carrier' and U[ATV]['HUDName'] == 'Lynx ATV', 'Troop Carrier 1431, Lynx ATV 1448')
    ok([O[o]['UIName'] for o in ARMED] == ['QJZ-89 12.7 mm', 'QLZ-87 35 mm AGL'] and O[31415]['UIName'] == 'Unarmed' and O[31415]['IsDefault'], 'TC options')
    turrets = [O[o]['Turret0Id'] for o in ARMED]
    ok(all(len(rows('TurretUnitsJson', TurretId=x)) == 1 and rows('TurretUnitsJson', TurretId=x)[0]['UnitId'] == TC for x in turrets)
       and not any(r and r['Id'] not in ARMED and r.get('Turret0Id') in turrets for r in O.values()), ('armed turrets are the TC own', turrets))
    weapons = sorted({w['WeaponId'] for x in turrets for w in rows('TurretWeaponsJson', TurretId=x)})
    removed = {'options': list(ARMED), 'turret_units': [], 'turret_weapons': [], 'weapon_ammunitions': []}
    for o in ARMED: g.remove('OptionsJson', o)
    for x in turrets:
        for r in rows('TurretUnitsJson', TurretId=x): g.remove('TurretUnitsJson', r['Id']); removed['turret_units'].append(r['Id'])
        for r in rows('TurretWeaponsJson', TurretId=x): g.remove('TurretWeaponsJson', r['Id']); removed['turret_weapons'].append(r['Id'])
    for r in rows('WeaponAmmunitionsJson', UnitId=TC): g.remove('WeaponAmmunitionsJson', r['Id']); removed['weapon_ammunitions'].append(r['Id'])
    mods = rows('ModificationsJson', UnitId=TC)
    ok(not rows('WeaponAmmunitionsJson', UnitId=TC) and len(mods) == 1 and [o['Id'] for o in rows('OptionsJson', ModificationId=mods[0]['Id'])] == [31415]
       and all(not rows('TurretWeaponsJson', TurretId=r['TurretId']) for r in rows('TurretUnitsJson', UnitId=TC)), ('Troop Carrier unarmed', removed, weapons))
    tc_squads = sorted(SA[r['SpecializationAvailabilityId']]['UnitId'] for r in rows('TransportAvailabilitiesJson', UnitId=TC))
    atv_links = rows('TransportAvailabilitiesJson', UnitId=ATV)
    ok(len(atv_links) == 10 and sorted(SA[r['SpecializationAvailabilityId']]['UnitId'] for r in atv_links) == tc_squads, ('ATV squads = Troop Carrier squads', len(atv_links)))
    for r in atv_links: g.remove('TransportAvailabilitiesJson', r['Id'])
    g.put('Units', ATV, {'DisplayInArmory': False})
    ok(not rows('TransportAvailabilitiesJson', UnitId=ATV) and not rows('SpecializationAvailabilitiesJson', UnitId=ATV) and len(tc_squads) == 10, 'ATV retired; TC on 10 squads')
    rec['lynx_tc_unarmed_1125'] = {**removed, 'weapons_off_tc': weapons, 'atv_transport_links_removed': [r['Id'] for r in atv_links], 'tc_squads': tc_squads}
    print('LYNX TC UNARMED', rec['lynx_tc_unarmed_1125'])

"""Lynx Troop Carrier entirely unarmed; Lynx ATV retired (Osama 25 Nov 2026 01:1x PST, thread 1567745029781454889: "LYNX troop carrier model
about 10% smaller, we can now replace the Lynx ATV and retire it. this should be entirely unarmed").
- Troop Carrier (1431, 'PLA Lynx CS/VP16B'): its QJZ-89 12.7 mm (31416) and QLZ-87 35 mm AGL (31417) options go, with their own turret, weapon
  and ammo rows, so the card lists no weapon. The Unarmed option (31415, empty turret) stays as the only choice. Model 10% smaller and no armed
  model swap: work/model-rework-096/stage.py.
- Lynx ATV (1448, lynx_ifv_atv_1125.py): hidden in the Armory and its 10 transport links removed. The Troop Carrier is offered to the same
  10 airborne squads (checked), so it takes the ATV's place. Its rows stay, so nothing that points to them breaks.
- Osama 25 Nov 2026 01:5x (thread blue dragons): "The Lynx Troop Carrier should have HMG and AGL options for +5 that change the model to the
  model we had with a gun on it". So the QJZ-89 12.7 mm and QLZ-87 35 mm AGL options stay (with their turret, weapon and ammo rows), each +5 pts;
  Unarmed stays the default. The armed model swap (old Lynx Cargo model m_315224) is in work/model-rework-096/stage.py."""
TC, ATV, ARMED = 1431, 1448, (31416, 31417)


def apply(t, g, ok, rec):
    U, O, TU, TW, WA, TA, SA = (t[k] for k in ('Units', 'OptionsJson', 'TurretUnitsJson', 'TurretWeaponsJson', 'WeaponAmmunitionsJson',
                                              'TransportAvailabilitiesJson', 'SpecializationAvailabilitiesJson'))
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok(U[TC]['HUDName'] == 'Lynx Troop Carrier' and U[ATV]['HUDName'] == 'Lynx ATV', 'Troop Carrier 1431, Lynx ATV 1448')
    ok([O[o]['UIName'] for o in ARMED] == ['QJZ-89 12.7 mm', 'QLZ-87 35 mm AGL'] and O[31415]['UIName'] == 'Unarmed' and O[31415]['IsDefault'], 'TC options')
    turrets = [O[o]['Turret0Id'] for o in ARMED]
    ok(all(len(rows('TurretUnitsJson', TurretId=x)) == 1 and rows('TurretUnitsJson', TurretId=x)[0]['UnitId'] == TC for x in turrets)
       and all(rows('TurretWeaponsJson', TurretId=x) for x in turrets), ('armed turrets are the TC own, with weapons', turrets))
    weapons = sorted({w['WeaponId'] for x in turrets for w in rows('TurretWeaponsJson', TurretId=x)})
    before = {o: O[o]['Cost'] for o in ARMED}
    for o in ARMED: g.put('OptionsJson', o, {'Cost': 5})
    ok(all(O[o]['Cost'] == 5 and not O[o]['IsDefault'] for o in ARMED) and O[31415]['IsDefault'] and rows('WeaponAmmunitionsJson', UnitId=TC),
       ('TC: Unarmed default, HMG / AGL +5 with ammo', before))
    removed = {'armed_option_cost_before': before, 'armed_options_kept': list(ARMED)}
    tc_squads = sorted(SA[r['SpecializationAvailabilityId']]['UnitId'] for r in rows('TransportAvailabilitiesJson', UnitId=TC))
    atv_links = rows('TransportAvailabilitiesJson', UnitId=ATV)
    ok(len(atv_links) == 10 and sorted(SA[r['SpecializationAvailabilityId']]['UnitId'] for r in atv_links) == tc_squads, ('ATV squads = Troop Carrier squads', len(atv_links)))
    for r in atv_links: g.remove('TransportAvailabilitiesJson', r['Id'])
    g.put('Units', ATV, {'DisplayInArmory': False})
    ok(not rows('TransportAvailabilitiesJson', UnitId=ATV) and not rows('SpecializationAvailabilitiesJson', UnitId=ATV) and len(tc_squads) == 10, 'ATV retired; TC on 10 squads')
    rec['lynx_tc_unarmed_1125'] = {**removed, 'tc_armed_weapons': weapons, 'atv_transport_links_removed': [r['Id'] for r in atv_links], 'tc_squads': tc_squads}
    print('LYNX TC UNARMED', rec['lynx_tc_unarmed_1125'])

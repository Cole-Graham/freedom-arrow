"""MD-22: no stray 2x PL-12 (Osama 23 Nov 2026 13:0x PST, thread 1567745029781454889: "MD-22 still has a bug where it retains 2x PL-12 throughout all
loadouts"). The MD-22 (976) uses the US_F35A body, whose gun slot 0 holds the default MainTurret F35A on the F-35A. The MD-22 has no default mount, so
the game puts its first TurretUnits mount, 'PLA air pylon PL-12 x2', in slot 0 for every loadout (the 0.8.0-dev.8 aircraft stray-weapon rule). Its
loadouts also set only bay slots 1 and 2, while the F-35A body has bay slots 1-4. Fix as for the J-35/J-20 (0.8.0-dev.8): link the 'PLA empty default
mount' (2018554, IsDefault, no weapon) and set slots 3 and 4 to 'Turret Empty' (160, already linked) on every MD-22 loadout."""

MD22, EMPTY_DEFAULT, EMPTY, BODY = 976, 2018554, 160, 'US_F35A'


def apply(t, g, ok, rec):
    U, TU, T, TW, O, M = (t[k] for k in ('Units', 'TurretUnitsJson', 'TurretsJson', 'TurretWeaponsJson', 'OptionsJson', 'ModificationsJson'))
    links = lambda: sorted([r for r in TU.values() if r and r.get('UnitId') == MD22], key=lambda r: r['Id'])
    slots = lambda o: {i: o[f'Turret{i}Id'] for i in range(21) if o.get(f'Turret{i}Id')}
    opts = sorted([o for o in O.values() if o and M.get(o['ModificationId'], {}).get('UnitId') == MD22], key=lambda o: o['Order'])
    ok(U[MD22]['HUDName'] == 'MD-22' and U[MD22]['ModelFileName'] == BODY, 'MD-22 on the F-35A body')
    ok(T[EMPTY_DEFAULT]['Name'] == 'PLA empty default mount' and T[EMPTY_DEFAULT]['IsDefault'] and not any(r and r['TurretId'] == EMPTY_DEFAULT for r in TW.values()),
       'empty default mount: default, no weapon')
    ok(not any(T[r['TurretId']]['IsDefault'] for r in links()) and T[links()[0]['TurretId']]['Name'] == 'PLA air pylon PL-12 x2', 'no default mount; first mount = PL-12 x2')
    ok(any(r['TurretId'] == EMPTY for r in links()) and len(opts) == 6 and all(set(slots(o)) == {1, 2} for o in opts), ('MD-22 loadouts set only slots 1 and 2', [slots(o) for o in opts]))
    g.add('TurretUnitsJson', links()[0], {'UnitId': MD22, 'TurretId': EMPTY_DEFAULT, 'Order': 0})
    for o in opts: g.put('OptionsJson', o['Id'], {'Turret3Id': EMPTY, 'Turret4Id': EMPTY})
    ok([T[r['TurretId']]['Name'] for r in links() if T[r['TurretId']]['IsDefault']] == ['PLA empty default mount'], 'one default mount, the empty one')
    ok(all(set(slots(O[o['Id']])) == {1, 2, 3, 4} and O[o['Id']]['Turret3Id'] == O[o['Id']]['Turret4Id'] == EMPTY for o in opts), 'every loadout fills bay slots 1-4')
    rec['md22_slots'] = {'unit': MD22, 'default_mount': EMPTY_DEFAULT, 'options': [o['Id'] for o in opts], 'slots_3_4': EMPTY}
    print('MD-22 slots', rec['md22_slots'])

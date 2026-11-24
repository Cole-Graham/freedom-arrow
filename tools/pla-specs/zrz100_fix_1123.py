"""ZRZ-100 weapons, price and speed (Osama 24 Nov 2026 00:5x PST, thread 1567745029781454889: "zrz-100 has no weapons, it should have 2xabz-13 and
2xHJ-16 (non fnf) and a QJY-201 for 45 points and 90 forward speed and 20 reverse"). MODEL BUILD ONLY. After zrz100_1123.py.
- Why no weapons: the Uran-9 body spawns its turret only through a loadout option (its turrets are not default; vanilla 'Weapons Uran9 Main'
  slot 725). zrz100_1123.py linked the turret but made no option, so nothing was mounted. Now: a copy of that slot with one default +0 option
  '2x HJ-16, 2x ABZ-13, QJY-201' (a copy of the Uran-9 4x Ataka option) pointing at the ZRZ-100 turret.
- Turret slots: order 0 QJC-88 12.7 mm -> QJY-201 7.62 mm (the VP4's vehicle QJY-201, 200 rounds); order 1 ABZ-13 x2; order 2 HJ-16 x2, the
  ZBD-251 round (Seeker 100 = command-guided like the TOW / Ataka, not fire-and-forget).
- Cost 25 -> 45. Speed: road 50 -> 90, reverse 15 -> 20 (its own mobility row); cross-country stays 45."""
QJC, QJY, QJY_AMMO, ABZ, HJ16, URAN_MOD, URAN_OPT = 2014643, 2011045, 2011049, 2014659, 2014655, 725, 3068


def apply(t, g, ok, rec):
    U, TU, TW, WA, W, A, M, O, UP, MB = (t[k] for k in ('Units', 'TurretUnitsJson', 'TurretWeaponsJson', 'WeaponAmmunitionsJson', 'WeaponsJson',
                                                        'AmmunitionsJson', 'ModificationsJson', 'OptionsJson', 'UnitPropulsionsJson', 'MobilityJson'))

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    (u,) = [i for i, x in U.items() if x and x.get('Name') == 'PLA ZRZ-100']
    (tu,) = rows('TurretUnitsJson', UnitId=u); tid = tu['TurretId']
    tw = rows('TurretWeaponsJson', TurretId=tid)
    ok([(x['WeaponId'], x['Order']) for x in tw] == [(QJC, 0), (ABZ, 1), (HJ16, 2)] and not rows('ModificationsJson', UnitId=u), 'ZRZ-100 turret as built; no options yet')
    ok(W[QJY]['HUDName'] == 'QJY-201 7.62 mm' and A[QJY_AMMO]['Seeker'] == 0 and all(A[r['AmmunitionId']]['Seeker'] == 100 for r in rows('WeaponAmmunitionsJson', WeaponId=HJ16)),
       'vehicle QJY-201; HJ-16 2014655 command-guided (not fire-and-forget)')
    g.put('TurretWeaponsJson', tw[0]['Id'], {'WeaponId': QJY})
    (hmg,) = [r for r in rows('WeaponAmmunitionsJson', UnitId=u) if r['WeaponId'] == QJC]
    vp4 = next(r for r in rows('WeaponAmmunitionsJson', WeaponId=QJY) if r['AmmunitionId'] == QJY_AMMO)
    g.remove('WeaponAmmunitionsJson', hmg['Id']); g.add('WeaponAmmunitionsJson', vp4, {'UnitId': u, 'Order': 0})
    ok(M[URAN_MOD]['UnitId'] == 628 and O[URAN_OPT]['ModificationId'] == URAN_MOD and O[URAN_OPT]['Turret0Id'] == 1222, 'Uran-9 main slot 725 / Ataka option 3068')
    nm = g.add('ModificationsJson', M[URAN_MOD], {'UnitId': u, 'Name': 'Weapons ZRZ-100 Main'})
    g.add('OptionsJson', O[URAN_OPT], {'ModificationId': nm, 'Name': 'MainTurret ZRZ-100', 'UIName': '2x HJ-16, 2x ABZ-13, QJY-201', 'Cost': 0, 'IsDefault': True,
                                        'Turret0Id': tid, 'Order': 0})
    g.put('Units', u, {'Cost': 45})
    (mob,) = rows('UnitPropulsionsJson', UnitId=u)
    ok(MB[mob['MobilityId']]['Name'].endswith('PLA ZRZ-100') and [r['UnitId'] for r in rows('UnitPropulsionsJson', MobilityId=mob['MobilityId'])] == [u], 'own mobility row')
    g.put('MobilityJson', mob['MobilityId'], {'MaxSpeedRoad': 90.0, 'MaxSpeedReverse': 20.0})
    got = sorted((W[r['WeaponId']]['HUDName'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=u))
    ok(got == sorted([('QJY-201 7.62 mm', vp4['Quantity']), ('ABZ-13 anti-personnel', 2), ('HJ-16', 2)]) and U[u]['Cost'] == 45
       and [o['Turret0Id'] for m in rows('ModificationsJson', UnitId=u) for o in rows('OptionsJson', ModificationId=m['Id'])] == [tid], ('ZRZ-100 loadout', got))
    rec['zrz100_fix'] = {'unit': u, 'cost': [25, 45], 'loadout': got, 'option_slot': nm, 'speed': {'road': [50, 90], 'reverse': [15, 20]}}
    print('ZRZ-100 FIX', rec['zrz100_fix'])

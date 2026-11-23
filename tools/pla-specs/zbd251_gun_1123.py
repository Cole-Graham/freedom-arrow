"""ZBD-251 gets the Type 100 CSV's 40 mm telescoped gun and costs 90 (Osama 23 Nov 2026 00:0x PST, thread 1572407822849810463: "zbd-251 gets the
same gun but goes up to 90 points"). Its 30 mm autocannon (weapon 2010735, rounds 2010739 AP / 2010741 HE, used by no other unit) is replaced on
the same mount and ammo rows by the Type 100's gun and rounds (zbd100.py: 40 mm CT, APFSDS 180/100, HE 1200 m ground and low altitude), with the
Type 100's round counts (100 APFSDS, 234 HE). HJ-16, ABZ-13, the Type 86 MG and the GL-5 APS slot are unchanged."""

ZBD251, OLD_GUN, MOUNT = 1056, 2010735, 2010736


def apply(t, g, ok, rec):
    U, W, TW, WA = t['Units'], t['WeaponsJson'], t['TurretWeaponsJson'], t['WeaponAmmunitionsJson']
    z = rec['zbd100']
    gun, ke, he = z['gun'], z['ke'], z['he']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok(U[ZBD251]['HUDName'] == 'ZBD-251' and U[ZBD251]['Cost'] == 75 and W[gun]['HUDName'] == '40 mm CT', 'ZBD-251 75 pts; Type 100 40 mm CT gun')
    tw = rows('TurretWeaponsJson', TurretId=MOUNT, WeaponId=OLD_GUN)
    wa = rows('WeaponAmmunitionsJson', UnitId=ZBD251, WeaponId=OLD_GUN)
    ok(len(tw) == 1 and len(wa) == 2 and {r['UnitId'] for r in rows('WeaponAmmunitionsJson', WeaponId=OLD_GUN)} == {ZBD251}
       and {r['UnitId'] for r in rows('TurretUnitsJson', TurretId=MOUNT)} == {ZBD251}, 'ZBD-251 30 mm on its own mount, used by no other unit')
    qty = {r['AmmunitionId']: r['Quantity'] for r in rows('WeaponAmmunitionsJson', UnitId=z['unit'], WeaponId=gun)}
    g.put('TurretWeaponsJson', tw[0]['Id'], {'WeaponId': gun})
    g.put('WeaponAmmunitionsJson', wa[0]['Id'], {'WeaponId': gun, 'AmmunitionId': ke, 'Quantity': qty[ke]})
    g.put('WeaponAmmunitionsJson', wa[1]['Id'], {'WeaponId': gun, 'AmmunitionId': he, 'Quantity': qty[he]})
    g.put('Units', ZBD251, {'Cost': 90})
    ok(U[ZBD251]['Cost'] == 90 and [(r['AmmunitionId'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=ZBD251, WeaponId=gun)] == [(ke, qty[ke]), (he, qty[he])]
       and not rows('WeaponAmmunitionsJson', WeaponId=OLD_GUN) and rows('TurretWeaponsJson', TurretId=MOUNT)[0]['WeaponId'] == gun, 'ZBD-251: 90 pts, Type 100 40 mm CT gun and rounds')
    ok(not any(o.get('ReplaceUnitId') for m in rows('ModificationsJson', UnitId=ZBD251) for o in rows('OptionsJson', ModificationId=m['Id'])), 'ZBD-251 has no swap rows to reprice')
    rec['zbd251_gun'] = {'unit': ZBD251, 'gun': gun, 'rounds': qty, 'cost': [75, 90]}
    print('ZBD251', rec['zbd251_gun'])

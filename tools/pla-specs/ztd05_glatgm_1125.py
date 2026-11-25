"""ZTD-05 gets the ZTL-11's gun-launched missile (Osama 25 Nov 2026 00:5x PST, thread 1567745029781454889: "for the ZTD-05, please add the GLATGM
from the ZTL-11?"). One new ammo row on the ZTD-05's 105 mm gun: the ZTL-11's own round 2019038 ('105 mm gun-launched missile': 10.5 damage,
600 penetration, 100-750 m, interceptable), 8 rounds like the ZTL-11, Order 2 like the ZTL-11's missile row. The round is shared, not copied, so
one edit changes both. Cost (100 pts) and the gun's other rounds are not changed. Adds one row: after every other row-creating section."""
ZTD05, ZTL11, MISSILE = 1411, 938, 2019038


def apply(t, g, ok, rec):
    U, A, WA, TU, TW = t['Units'], t['AmmunitionsJson'], t['WeaponAmmunitionsJson'], t['TurretUnitsJson'], t['TurretWeaponsJson']
    ok(U[ZTD05]['Name'] == 'PLA ZTD-05' and U[ZTL11]['Name'] == 'PLA ZTL-11', 'ZTD-05 1411, ZTL-11 938')
    src = [r for r in WA.values() if r and r['UnitId'] == ZTL11 and r['AmmunitionId'] == MISSILE]
    ok(len(src) == 1 and A[MISSILE]['HUDName'] == '105 mm gun-launched missile', ('ZTL-11 missile row', src))
    gun = [r for r in WA.values() if r and r['UnitId'] == ZTD05 and A[r['AmmunitionId']]['HUDName'] in ('105 mm APFSDS', '105 mm HESH')]
    ok(len(gun) == 2 and len({r['WeaponId'] for r in gun}) == 1, ('ZTD-05 105 mm gun: APFSDS + HESH rows', gun))
    w = gun[0]['WeaponId']
    mounts = {r['TurretId'] for r in TU.values() if r and r['UnitId'] == ZTD05}
    ok(any(r['TurretId'] in mounts and r['WeaponId'] == w for r in TW.values() if r), 'the 105 mm gun is on a ZTD-05 turret')
    ok(not any(r and r['UnitId'] == ZTD05 and r['AmmunitionId'] == MISSILE for r in WA.values()), 'no missile row yet')
    row = g.add('WeaponAmmunitionsJson', src[0], {'UnitId': ZTD05, 'WeaponId': w})
    ok(WA[row]['Quantity'] == 8 and WA[row]['Order'] == 2 and WA[row]['AmmunitionId'] == MISSILE, ('new row', WA[row]))
    rec['ztd05_glatgm_1125'] = {'unit': ZTD05, 'weapon': w, 'row': row, 'round': MISSILE, 'quantity': 8}
    print('ZTD-05 GLATGM', rec['ztd05_glatgm_1125'])

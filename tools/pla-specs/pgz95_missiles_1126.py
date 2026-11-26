"""PGZ-95 missiles (Osama 26 Nov 2026 10:5x PST, bugs thread 1573561286803980289: "the pgz-95 doesn't get its missiles in the live build, for the
current devbuild can you please make sure this is fixed?").
Cause (data, 0.9.7): the PGZ-95 (unit 1052) uses the Shilka body (RU_ZSU-2-4). Its 25 mm guns sit on mount 0 (TurretUnits Order 0) and its QW-2 sits on
a second top-level turret, mount 1 (TurretUnits Order 1, model RU_ZSU_m4). The vanilla Shilka only ever uses body slot 0 (its three turret options
373/374/375 are all Order 0), so a weapon on slot 1 never comes alive; the same class as the ZTZ-59D1 MG (extra-body-slot weapons, 23 Nov).
Fix, the vanilla Shilka M4 pattern (turret 375: AAG Order 0 + Igla-S Order 1 on ONE turret, model RU_ZSU_m4):
- one new turret, a copy of mount 0 with the M4 turret model (it has the launcher rails), carrying the 25 mm guns at Order 0 and the QW-2 at Order 1;
- the unit's slot 0 points at it and its slot-1 row goes. Weapons, rounds and quantities are unchanged.
The PGZ-04 (1050) and PGZ-04A (932) are built the same way on the same body (guns slot 0, QW-2 slot 1), so they get the same fix."""
NAMES = ('PLA Catalogue PGZ-95', 'PLA Catalogue PGZ-04', 'PLA PGZ-04A')
M4_MODEL = 'RU_ZSU-2-4/RU_ZSU_m4'


def apply(t, g, ok, rec):
    rec['pgz95_missiles_1126'] = [one(t, g, ok, n) for n in NAMES]
    print('PGZ QW-2 ON SLOT 0', rec['pgz95_missiles_1126'])


def one(t, g, ok, name):
    U, T, TW, TU, WA, W = (t[k] for k in ('Units', 'TurretsJson', 'TurretWeaponsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson', 'WeaponsJson'))
    (u,) = [i for i, x in U.items() if x and x.get('Name') == name]
    ok(U[u]['ModelFileName'] == 'RU_ZSU-2-4', (name, 'on the Shilka body', U[u]['ModelFileName']))
    tu = sorted([r for r in TU.values() if r and r['UnitId'] == u], key=lambda r: r['Order'])
    ok([r['Order'] for r in tu] == [0, 1], (name, 'two top-level mounts', [(r['Order'], r['TurretId']) for r in tu]))
    m0, m1 = tu[0]['TurretId'], tu[1]['TurretId']
    guns = [r for r in TW.values() if r and r['TurretId'] == m0]
    msl = [r for r in TW.values() if r and r['TurretId'] == m1]
    ok(len(guns) == 1 and len(msl) == 1 and W[guns[0]['WeaponId']]['HUDName'] == 'Four 25 mm AA guns' and W[msl[0]['WeaponId']]['HUDName'] == 'QW-2',
       (name, 'guns on mount 0, QW-2 on mount 1'))
    others = {r['UnitId'] for r in TU.values() if r and r['TurretId'] in (m0, m1)} - {u}
    ok(not others, (name, 'mounts used by no other unit', others))
    tid = g.add('TurretsJson', T[m0], {'Name': name.replace('Catalogue ', '') + ' turret (guns + QW-2)', 'ModelFileName': M4_MODEL})
    g.add('TurretWeaponsJson', guns[0], {'TurretId': tid, 'Order': 0})
    g.add('TurretWeaponsJson', msl[0], {'TurretId': tid, 'Order': 1})
    g.put('TurretUnitsJson', tu[0]['Id'], {'TurretId': tid}); g.remove('TurretUnitsJson', tu[1]['Id'])
    now = [(r['Order'], r['TurretId']) for r in TU.values() if r and r['UnitId'] == u]
    lay = sorted((x['Order'], W[x['WeaponId']]['HUDName']) for x in TW.values() if x and x['TurretId'] == tid)
    ammo = sorted((W[r['WeaponId']]['HUDName'], r['Quantity']) for r in WA.values() if r and r['UnitId'] == u)
    ok(now == [(0, tid)] and lay == [(0, 'Four 25 mm AA guns'), (1, 'QW-2')] and T[tid]['ModelFileName'] == M4_MODEL,
       (name, 'one slot-0 turret, guns 0 + QW-2 1, M4 model', now, lay))
    ok([a for a, _ in ammo] == ['Four 25 mm AA guns', 'QW-2'], (name, 'ammo unchanged', ammo))
    return {'unit': u, 'name': name, 'turrets_before': [m0, m1], 'turret_after': tid, 'weapons': lay, 'ammo': ammo}

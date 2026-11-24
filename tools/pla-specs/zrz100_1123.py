"""PLA ZRZ-100 unmanned support vehicle for the MarkII_ model (Osama 23 Nov 2026 22:2x PST, thread "blue dragons": "zrz100 just came in, add to
PLAN SOF, I'll give you the stats but just copy what we have for the other russian combat vehicle", "it's got 2 each of the 2 missiles from the
ZBD-251 and a 50 cal machine gun").
Copy of DLC3 Uran-9 (628: body, armour, mobility, abilities, sensors, 25 pts, its card count, DLC3 gate as the Uran-9), CountryId 4, in PLAN Special
Forces (spec 20). No loadout options: one own turret, a copy of the Uran-9 3-weapon turret (1222, the Ataka layout), with existing rows linked:
order 0 QJC-88 12.7 mm (2014643, as the ZSL-92 MG, 100 rounds), order 1 ABZ-13 anti-personnel (2014659) x2, order 2 HJ-16 (2014655) x2 (the
ZBD-251's two missiles). Stats are placeholders until Osama gives them. FAModels draws the MarkII_ model (models.json key = Name, c5-cn-1123)."""
NAME, HUD, SPEC, URAN, TUR = 'PLA ZRZ-100', 'ZRZ-100', 20, 628, 1222
HMG, ABZ, HJ16 = 2014643, 2014659, 2014655


def apply(t, g, ok, rec):
    U, S, SA, W, A = t['Units'], t['SpecializationsJson'], t['SpecializationAvailabilitiesJson'], t['WeaponsJson'], t['AmmunitionsJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    ok(U[URAN]['Name'] == 'DLC3 Uran-9' and S[SPEC]['Name'] == 'PLA PLAN Special Forces', 'Uran-9 628, PLAN spec 20')
    ok(W[HMG]['HUDName'] == 'QJC-88 12.7 mm' and W[ABZ]['HUDName'] == 'ABZ-13 anti-personnel' and W[HJ16]['HUDName'] == 'HJ-16', 'QJC-88, ABZ-13, HJ-16 rows')
    tw = rows('TurretWeaponsJson', TurretId=TUR)
    ok([x['Order'] for x in tw] == [0, 1, 2], ('Uran-9 Ataka turret has weapon orders 0-2', [x['Order'] for x in tw]))
    ammo = {w: rows('WeaponAmmunitionsJson', WeaponId=w) for w in (HMG, ABZ, HJ16)}
    hmg_row = [r for r in ammo[HMG] if r['UnitId'] == 1232]
    ok(len(hmg_row) == 1 and all(ammo[w] for w in (ABZ, HJ16)), 'ammo rows for the three weapons')
    ok(not any(u and NAME in (u.get('Name'), u.get('HUDName')) for u in U.values()), NAME + ' name free')
    d = dict(U[URAN]); d.pop('Id')
    d.update({'Name': NAME, 'HUDName': HUD, 'OriginalCost': 0, 'CountryId': 4, 'DisplayInArmory': True, 'Description': None, 'OriginalName': None})
    uid = g.put('Units', max(U) + 1, d)
    for tab, field, target in (('UnitArmorsJson', 'ArmorId', 'ArmorsJson'), ('UnitPropulsionsJson', 'MobilityId', 'MobilityJson')):
        for r in rows(tab, UnitId=URAN):
            g.add(tab, r, {'UnitId': uid, field: g.add(target, t[target][r[field]], {'Name': f'{t[target][r[field]]["Name"]} {NAME}'})})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson'):
        for r in rows(tab, UnitId=URAN): g.add(tab, r, {'UnitId': uid})
    tid = g.add('TurretsJson', t['TurretsJson'][TUR], {'Name': 'PLA ZRZ-100 turret'})
    for x, w in zip(tw, (HMG, ABZ, HJ16)): g.add('TurretWeaponsJson', x, {'TurretId': tid, 'WeaponId': w})
    (tu,) = [r for r in rows('TurretUnitsJson', UnitId=URAN) if r['TurretId'] == 1221]   # the default main-turret slot
    g.add('TurretUnitsJson', tu, {'UnitId': uid, 'TurretId': tid})
    g.add('WeaponAmmunitionsJson', hmg_row[0], {'UnitId': uid, 'Order': 0})
    for w, src in ((ABZ, ammo[ABZ][0]), (HJ16, ammo[HJ16][0])): g.add('WeaponAmmunitionsJson', src, {'UnitId': uid, 'Quantity': 2, 'Order': 0})
    (sa,) = rows('SpecializationAvailabilitiesJson', UnitId=URAN)
    g.add('SpecializationAvailabilitiesJson', sa, {'UnitId': uid, 'SpecializationId': SPEC})
    ok(len(rows('TurretUnitsJson', UnitId=uid)) == 1 and not rows('ModificationsJson', UnitId=uid), 'one fixed turret, no options')
    got = sorted((W[r['WeaponId']]['HUDName'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=uid))
    ok(got == sorted([('QJC-88 12.7 mm', hmg_row[0]['Quantity']), ('ABZ-13 anti-personnel', 2), ('HJ-16', 2)]), ('ZRZ-100 loadout', got))
    rec['zrz100_1123'] = {'unit': uid, 'cost': U[uid]['Cost'], 'spec': SPEC, 'cards': sa['MaxAvailabilityXp0'], 'turret': tid, 'loadout': got,
                          'content': U[uid]['ContentMembership']}
    print('ZRZ-100', rec['zrz100_1123'])

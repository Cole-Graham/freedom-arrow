"""US LRHW 'Dark Eagle' (Osama 23 Nov 2026 01:2x PST, thread 1572407822849810463: "I added the US LRHW, can we add it to the US? It's basically a
double DF-17"). Full copy of PLA Catalogue DF-17 (1028) for the US: same missile and launcher stats, 2 missiles instead of 1 (own weapon/ammo
names). Osama 01:3x: "and make it 350", "and only 1 availability", "this should go to Stryker cav" (spec 6),
"Give it the same unit card as DF-21" (DF-21 1030 thumbnail + portrait), "call it LRHW Dark Eagle and the ammo CHGB".
Body = the DF-17's RU_Iskander stand-in; FAModels draws the LRHW model (models.json key = NAME)."""
NAME, HUD, COST, SPEC, CARDS, PARENT = 'US LRHW Dark Eagle', 'LRHW Dark Eagle', 350, 6, 1, 1028


def apply(t, g, ok, rec):
    U, S, SA, A, W, T = t['Units'], t['SpecializationsJson'], t['SpecializationAvailabilitiesJson'], t['AmmunitionsJson'], t['WeaponsJson'], t['TurretsJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    us = S[SPEC]['CountryId']
    ok(U[PARENT]['Name'] == 'PLA Catalogue DF-17' and S[SPEC]['Name'] == 'Stryker Cavalry regiment' and U[1030]['Name'] == 'PLA Catalogue DF-21', 'LRHW parent DF-17, spec Stryker Cavalry, card art DF-21')
    ok(not any(u and NAME in (u.get('Name'), u.get('HUDName')) for u in U.values()), 'LRHW name free')
    d = dict(U[PARENT]); d.pop('Id')
    d.update({'Name': NAME, 'HUDName': HUD, 'Cost': COST, 'OriginalCost': 0, 'CountryId': us, 'DisplayInArmory': True,
              'ThumbnailFileName': U[1030]['ThumbnailFileName'], 'PortraitFileName': U[1030]['PortraitFileName']})
    uid = g.put('Units', max(U) + 1, d)
    for tab, field, target in (('UnitArmorsJson', 'ArmorId', 'ArmorsJson'), ('UnitPropulsionsJson', 'MobilityId', 'MobilityJson')):
        for r in rows(tab, UnitId=PARENT):
            g.add(tab, r, {'UnitId': uid, field: g.add(target, t[target][r[field]], {'Name': f'{t[target][r[field]]["Name"]} LRHW'})})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson'):
        for r in rows(tab, UnitId=PARENT):g.add(tab, r, {'UnitId': uid})
    (tu,) = rows('TurretUnitsJson', UnitId=PARENT); (wa,) = rows('WeaponAmmunitionsJson', UnitId=PARENT); (tw,) = rows('TurretWeaponsJson', TurretId=tu['TurretId'])
    ok(wa['Quantity'] == 1 and wa['WeaponId'] == tw['WeaponId'], 'DF-17 carries 1 missile')
    w = g.add('WeaponsJson', W[tw['WeaponId']], {'Name': 'US LRHW Dark Eagle launcher', 'HUDName': 'LRHW Dark Eagle', 'MagazineSize': 2})
    a = g.add('AmmunitionsJson', A[wa['AmmunitionId']], {'Name': 'US LRHW Dark Eagle CHGB', 'HUDName': 'CHGB'})
    tr = g.add('TurretsJson', T[tu['TurretId']], {'Name': 'US LRHW Dark Eagle mount'})
    g.add('TurretWeaponsJson', tw, {'TurretId': tr, 'WeaponId': w})
    g.add('TurretUnitsJson', tu, {'UnitId': uid, 'TurretId': tr})
    g.add('WeaponAmmunitionsJson', wa, {'UnitId': uid, 'WeaponId': w, 'AmmunitionId': a, 'Quantity': 2})
    tpl = next(r for r in SA.values() if r and r['UnitId'] == PARENT)   # DF-17 row: Xp1-3 are 0, so 1 card at every veterancy
    g.add('SpecializationAvailabilitiesJson', tpl, {'UnitId': uid, 'SpecializationId': SPEC, 'MaxAvailabilityXp0': CARDS})
    ok(rows('WeaponAmmunitionsJson', UnitId=uid)[0]['Quantity'] == 2 and t['AmmunitionsJson'][a]['Damage'] == A[wa['AmmunitionId']]['Damage'], 'LRHW = DF-17 missile x2')
    ok(U[uid]['Cost'] == 350 and [(r['SpecializationId'], r['MaxAvailabilityXp0'], r['MaxAvailabilityXp1'], r['MaxAvailabilityXp2'], r['MaxAvailabilityXp3']) for r in rows('SpecializationAvailabilitiesJson', UnitId=uid)] == [(SPEC, 1, 0, 0, 0)], 'LRHW 350 points, 1 card')
    ok(len(rows('ModificationsJson', UnitId=PARENT)) == 0, 'DF-17 has no option slots to copy')
    rec['lrhw'] = {'unit': uid, 'name': NAME, 'cost': COST, 'spec': SPEC, 'cards': CARDS, 'weapon': w, 'ammo': a, 'turret': tr, 'missiles': 2}

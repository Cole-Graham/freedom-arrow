"""FK-3000 card and PCL-181 in the Medium CAB (Osama 24 Nov 2026 17:2x/18:0x PST, thread "China cosmetic work": "new model for SR-5, PCL-181
(add to medium cab), FK-3000 medium cab"; then "add it but the models don't look ready?").
- PLA FK-3000: a full copy of the PLA FK-2000 (935: 250 pts, AA tab, 2x 30 mm + 12 FK-2000 SAMs), with its own armour, mobility and turret rows
  (the turret's weapon links copied), the same abilities, sensor and ammunition. PLAGF Medium Combined Arms Brigade (spec 21), 4 cards like
  the FK-2000. Stats are the FK-2000's until Osama sets them. Model: models.json key 'PLA FK-3000' (stage.py; FK-2000 model until the new one).
- PCL-181 (1034 'PLA Catalogue PCL-181 / SH-15'): a spec 21 availability row with 2 cards, the SR-5's count; it stays in the hidden test spec 26.
Creates rows: keep after every other row-creating section so no earlier id moves (saved decks keep units by id)."""
SRC, NAME, HUD, SPEC, PCL = 935, 'PLA FK-3000', 'FK-3000', 21, 1034


def apply(t, g, ok, rec):
    U, S = t['Units'], t['SpecializationsJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    ok(U[SRC]['Name'] == 'PLA FK-2000' and U[SRC]['Cost'] == 250, 'FK-2000 935, 250 pts')
    ok(S[SPEC]['UIName'].startswith('PLAGF Medium Combined Arms Brigade'), 'spec 21 = Medium CAB')
    ok(not any(u and NAME in (u.get('Name'), u.get('HUDName')) for u in U.values()), NAME + ' name free')
    ok(not rows('ModificationsJson', UnitId=SRC), 'FK-2000 has no loadout slots')
    d = dict(U[SRC]); d.pop('Id'); d.update({'Name': NAME, 'HUDName': HUD, 'OriginalCost': 0, 'Description': None, 'OriginalName': None})
    uid = g.put('Units', max(U) + 1, d)
    for tab, field, target in (('UnitArmorsJson', 'ArmorId', 'ArmorsJson'), ('UnitPropulsionsJson', 'MobilityId', 'MobilityJson')):
        for r in rows(tab, UnitId=SRC):
            g.add(tab, r, {'UnitId': uid, field: g.add(target, t[target][r[field]], {'Name': f'{t[target][r[field]]["Name"]} FK-3000'})})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'WeaponAmmunitionsJson'):
        for r in rows(tab, UnitId=SRC): g.add(tab, r, {'UnitId': uid})
    for tu in rows('TurretUnitsJson', UnitId=SRC):
        tur = g.add('TurretsJson', t['TurretsJson'][tu['TurretId']], {'Name': t['TurretsJson'][tu['TurretId']]['Name'].replace('FK-2000', 'FK-3000')})
        for r in rows('TurretWeaponsJson', TurretId=tu['TurretId']): g.add('TurretWeaponsJson', r, {'TurretId': tur})
        g.add('TurretUnitsJson', tu, {'UnitId': uid, 'TurretId': tur})
    for r in rows('SpecializationAvailabilitiesJson', UnitId=SRC): g.add('SpecializationAvailabilitiesJson', r, {'UnitId': uid})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'WeaponAmmunitionsJson', 'UnitArmorsJson', 'UnitPropulsionsJson', 'TurretUnitsJson'):
        ok(len(rows(tab, UnitId=uid)) == len(rows(tab, UnitId=SRC)), ('FK-3000', tab, 'copied'))
    wsrc = [(r['Order'], r['WeaponId']) for tu in rows('TurretUnitsJson', UnitId=SRC) for r in rows('TurretWeaponsJson', TurretId=tu['TurretId'])]
    wnew = [(r['Order'], r['WeaponId']) for tu in rows('TurretUnitsJson', UnitId=uid) for r in rows('TurretWeaponsJson', TurretId=tu['TurretId'])]
    ok(wsrc == wnew, ('FK-3000 weapons = FK-2000', wnew))
    av = rows('SpecializationAvailabilitiesJson', UnitId=uid)
    ok([(r['SpecializationId'], r['MaxAvailabilityXp0']) for r in av] == [(SPEC, 4)], ('FK-3000: 4 cards in Medium CAB', av))
    # PCL-181 into the Medium CAB
    ok(U[PCL]['Name'] == 'PLA Catalogue PCL-181 / SH-15' and U[PCL]['DisplayInArmory'], 'PCL-181 1034')
    pav = rows('SpecializationAvailabilitiesJson', UnitId=PCL)
    ok(not any(r['SpecializationId'] == SPEC for r in pav), 'PCL-181 not yet in Medium CAB')
    g.add('SpecializationAvailabilitiesJson', pav[0], {'SpecializationId': SPEC, 'MaxAvailabilityXp0': 2, 'MaxAvailabilityXp1': 0, 'MaxAvailabilityXp2': 0,
                                                       'MaxAvailabilityXp3': 0})
    pav2 = sorted((r['SpecializationId'], r['MaxAvailabilityXp0']) for r in rows('SpecializationAvailabilitiesJson', UnitId=PCL))
    ok((SPEC, 2) in pav2, ('PCL-181 in Medium CAB, 2 cards', pav2))
    rec['fk3000_pcl181_1124'] = {'fk3000': uid, 'copy_of': SRC, 'cost': U[uid]['Cost'], 'weapons': wnew, 'pcl181_specs': pav2}
    print('FK-3000 / PCL-181', rec['fk3000_pcl181_1124'])

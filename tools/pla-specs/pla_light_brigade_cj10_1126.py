"""PLA Light Brigade build, CJ-10 for the Medium CAB (Osama 26 Nov 2026 19:1x PST, thread 1572407822849810463 "China cosmetic work": "add the
CJ-10 to medium CAB, iskander cruise missile clone (except 3 shots)"). Branch codex/batch/osama/pla-light-brigade only; the last plb section.
- Vanilla 9K720 Iskander (226) cruise loadouts: 'Iskander-K x2' (turret 383, weapon 317 magazine 2, round 219 9M728, +0) and 'x4' (turret 384,
  weapon 318 magazine 4, round 752, +50). New unit 'PLA CJ-10' = the Iskander with only the cruise launcher: a copy of the x2 tube turret (383),
  a copy of weapon 317 ('CJ-10', magazine 3) firing the existing CJ-10 round of the PHL-191 Cruise (2019099, a 9M728 copy: same flight, damage
  and range; no new round row, Lateralus 26 Nov rule), 3 missiles, no loadout choice.
- Price 250 = halfway between the 2-shot (225) and 4-shot (275) Iskander; cards as the Iskander (2). China country, Artillery/Regular voice.
- Model: no CJ-10 model yet; the game body is the Iskander (RU_Iskander, 2-tube cruise turret), like the DF-15's stand-in."""
ISK, ISK_K_TURRET, ISK_K_W, ISK_K_A, MEDIUM, CJ10_A = 226, 383, 317, 219, 21, 2019099
NAME, HUD, COST, MISSILES = 'PLA CJ-10', 'CJ-10', 250, 3


def apply(t, g, ok, rec):
    U, SA, W, A, T = t['Units'], t['SpecializationAvailabilitiesJson'], t['WeaponsJson'], t['AmmunitionsJson'], t['TurretsJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok(U[ISK]['HUDName'] == '9K720 Iskander' and W[ISK_K_W]['Name'] == 'Cruise IskanderK x2' and W[ISK_K_W]['MagazineSize'] == 2 and A[ISK_K_A]['HUDName'] == '9M728', 'Iskander-K x2 rows')
    ok([x['WeaponId'] for x in rows('TurretWeaponsJson', TurretId=ISK_K_TURRET)] == [ISK_K_W] and [(r['AmmunitionId'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=ISK, WeaponId=ISK_K_W)] == [(ISK_K_A, 2)], 'K turret fires 2 x 9M728')
    ok(not any(u and (u.get('Name') == NAME or u.get('HUDName') == HUD) for u in U.values()), 'name free')
    df15 = U[1029]; (card,) = rows('SpecializationAvailabilitiesJson', UnitId=ISK)
    uid = g.add('Units', U[ISK], {'Name': NAME, 'HUDName': HUD, 'Description': None, 'OriginalName': None, 'OriginalCost': 0, 'Cost': COST, 'CountryId': df15['CountryId'],
                                  'AudioPreset': df15['AudioPreset']})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitArmorsJson', 'UnitPropulsionsJson'):
        for r in rows(tab, UnitId=ISK): g.add(tab, r, {'UnitId': uid})
    a = CJ10_A
    ok(A[a]['HUDName'] == 'CJ-10' and {U[r['UnitId']]['HUDName'] for r in t['WeaponAmmunitionsJson'].values() if r and r['AmmunitionId'] == a} == {'PHL-191 Cruise'}, 'CJ-10 round of the PHL-191 Cruise')
    w = g.add('WeaponsJson', W[ISK_K_W], {'Name': 'Cruise CJ-10 x3', 'HUDName': HUD, 'MagazineSize': MISSILES})
    tur = g.add('TurretsJson', T[ISK_K_TURRET], {'Name': 'MainTurret CJ-10'})
    g.add('TurretWeaponsJson', rows('TurretWeaponsJson', TurretId=ISK_K_TURRET)[0], {'TurretId': tur, 'WeaponId': w, 'Order': 0})
    g.add('TurretUnitsJson', rows('TurretUnitsJson', UnitId=ISK, TurretId=ISK_K_TURRET)[0], {'UnitId': uid, 'TurretId': tur, 'Order': 0})
    g.add('WeaponAmmunitionsJson', rows('WeaponAmmunitionsJson', UnitId=ISK, WeaponId=ISK_K_W)[0], {'UnitId': uid, 'WeaponId': w, 'AmmunitionId': a, 'Quantity': MISSILES, 'Order': 0})
    nc = g.add('SpecializationAvailabilitiesJson', card, {'UnitId': uid, 'SpecializationId': MEDIUM})
    # checks after
    ok(not rows('ModificationsJson', UnitId=uid), 'CJ-10 has no loadout choice')
    ok([(r['WeaponId'], r['AmmunitionId'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=uid)] == [(w, a, MISSILES)]
       and [r['TurretId'] for r in rows('TurretUnitsJson', UnitId=uid)] == [tur] and [x['WeaponId'] for x in rows('TurretWeaponsJson', TurretId=tur)] == [w], 'CJ-10: one launcher, 3 missiles')
    same = ('GroundRange', 'Damage', 'Seeker', 'MaxSpeed', 'BurnTime')
    ok(all(A[a].get(k) == A[ISK_K_A].get(k) for k in same) and W[w]['MagazineSize'] == MISSILES and W[w]['Type'] == W[ISK_K_W]['Type'], 'CJ-10 round = 9M728 flight and damage')
    ok(SA[nc]['SpecializationId'] == MEDIUM and SA[card['Id']]['SpecializationId'] == 10 and U[uid]['CountryId'] == df15['CountryId'], 'Medium CAB card, China; Iskander card unchanged')
    rec['pla_light_brigade_cj10_1126'] = {'unit': uid, 'card': nc, 'cards': SA[nc]['MaxAvailabilityXp0'], 'cost': COST, 'weapon': w, 'round': a, 'turret': tur, 'missiles': MISSILES,
        'card_range_m': A[a]['GroundRange'] * 2, 'damage': A[a]['Damage'], 'body': U[uid]['ModelFileName']}
    print('PLA LIGHT BRIGADE CJ-10', rec['pla_light_brigade_cj10_1126'])

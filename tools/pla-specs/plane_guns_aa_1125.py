"""Plane guns: ActualArrow 1.2.2 values, China included (Lateralus 25 Nov 2026 08:5x, thread 1572962048705429598: "1. Copy 2. Copy 3. Copy
4. Copy 5. A, queue it" on work/aa-plane-guns-20261125/PROPOSAL.md).
Values read from ActualArrow-Full 1.2.2 (UserData/MLDatabaseMod/actual, 23 Nov 2026) and compared with vanilla 1.2.2.1 (REPORT.md). Existing rows
are edited in place: no new rows, no id shifts.
- Shared vanilla rows (every FA plane on them follows): fighter guns aim 0.1 s + IsLowAltDirectWeapon; M61 / GSh-6-23M rounds damage 1.25 -> 2.25;
  fighter rounds low/high-alt range 700/500 -> 1000/1000 world (1400/1000 -> 2000/2000 m), LaunchMarginAngle 0 -> 7.5, SupplyCost -> 0;
  GSh-6-23M bursts 2-5 -> 8; light-jet GSh-23L aim 0.2 s; Su-25 and light-jet rounds SupplyCost -> 0; bomber tail guns aim 0.1 s, damage 2.6 -> 1.75;
  AC-130 aim 1.5 s, 40 mm 4 -> 8, 30 mm HEI-T 3 -> 6 / API 1.5 -> 1.95 with no spread, 30-shot bursts 0.5714286 s apart without pauses.
- China rows by class: 30 mm cannons = GSh-30-1 (W241 / A90); "Type 23 cannon" = Yak-130 GSh-23L (W483 / A333); cannons that already fire A333
  get the W483 weapon values; H-6K tail gun = bomber tail gun (W486 / A292). The [TEST] M61 preview copy = M61 (W88 / A295).
- Option 5 A: IsLowAltDirectWeapon and LaunchMarginAngle are copied; their effect on guns is to be tested in Skirmish (not traced in code)."""
FIGHTER_W = {'AimTimeMin': 0.1, 'AimTimeMax': 0.1, 'IsLowAltDirectWeapon': True}
LIGHT_W = {'AimTimeMin': 0.2, 'AimTimeMax': 0.2, 'IsLowAltDirectWeapon': True}
TAIL_W = {'AimTimeMin': 0.1, 'AimTimeMax': 0.1}
AIR_A = {'LowAltRange': 1000.0, 'HighAltRange': 1000.0, 'LaunchMarginAngle': 7.5, 'SupplyCost': 0.0}
# id: (before, after) on the vanilla rows; before = vanilla 1.2.2.1, after = ActualArrow 1.2.2
WEAPONS = {
    88: ({'AimTimeMin': 0.5, 'AimTimeMax': 0.5, 'IsLowAltDirectWeapon': False}, FIGHTER_W),                # M61 20mm
    120: ({'AimTimeMin': 0.5, 'AimTimeMax': 0.5, 'IsLowAltDirectWeapon': False}, FIGHTER_W),               # GSh-30-1 Su-57
    241: ({'AimTimeMin': 0.5, 'AimTimeMax': 0.5, 'IsLowAltDirectWeapon': False}, FIGHTER_W),               # GSh-30-1
    418: ({'AimTimeMin': 0.5, 'AimTimeMax': 0.5, 'IsLowAltDirectWeapon': False}, FIGHTER_W),               # GAU-22
    480: ({'AimTimeMin': 0.5, 'AimTimeMax': 0.5, 'IsLowAltDirectWeapon': False, 'ShotsPerBurstMin': 2, 'ShotsPerBurstMax': 5},
          {**FIGHTER_W, 'ShotsPerBurstMin': 8, 'ShotsPerBurstMax': 8}),                                     # GSh-6-23M
    483: ({'AimTimeMin': 0.5, 'AimTimeMax': 0.5, 'IsLowAltDirectWeapon': False}, LIGHT_W),                 # GSh-23L Yak-130 / Yak-38M
    484: ({'AimTimeMin': 0.5, 'AimTimeMax': 0.5, 'IsLowAltDirectWeapon': True}, LIGHT_W),                  # GSh-23L AN-72P / L-39 / Yak-38M
    380: ({'AimTimeMin': 1.0, 'AimTimeMax': 1.0}, TAIL_W),                                                 # GSh-23L tail IL-76 / Tu-95 / Tu-142
    486: ({'AimTimeMin': 0.5, 'AimTimeMax': 0.5}, TAIL_W),                                                 # GSh-23L tail Tu-22M3
    80: ({'AimTimeMin': 1.0, 'AimTimeMax': 2.0}, {'AimTimeMin': 1.5, 'AimTimeMax': 1.5}),                  # AC-130 Bofors 40mm
    82: ({'AimTimeMin': 1.0, 'AimTimeMax': 2.0}, {'AimTimeMin': 1.5, 'AimTimeMax': 1.5}),                  # AC-130 GAU-12
    431: ({'AimTimeMin': 1.0, 'AimTimeMax': 2.0, 'ShotsPerBurstMin': 4, 'ShotsPerBurstMax': 8, 'TimeBetweenShotsInBurst': 0.3,
           'TimeBetweenBurstsMin': 1.0, 'TimeBetweenBurstsMax': 2.0, 'FlashPerShot': 0.3},
          {'AimTimeMin': 1.5, 'AimTimeMax': 1.5, 'ShotsPerBurstMin': 30, 'ShotsPerBurstMax': 30, 'TimeBetweenShotsInBurst': 0.5714286,
           'TimeBetweenBurstsMin': 0.0, 'TimeBetweenBurstsMax': 0.0, 'FlashPerShot': 0.75}),                # AC-130 Bushmaster II
}
AMMO = {
    295: ({'Damage': 1.25, 'LowAltRange': 700.0, 'HighAltRange': 500.0, 'LaunchMarginAngle': 0.0, 'SupplyCost': 1.0}, {**AIR_A, 'Damage': 2.25}),  # 20x102mm
    330: ({'Damage': 1.25, 'LowAltRange': 700.0, 'HighAltRange': 500.0, 'LaunchMarginAngle': 0.0, 'SupplyCost': 0.8}, {**AIR_A, 'Damage': 2.25}),  # 23x115mm GSh-6-23M
    90: ({'LowAltRange': 700.0, 'HighAltRange': 500.0, 'LaunchMarginAngle': 0.0, 'SupplyCost': 1.2}, AIR_A),                                      # 30x165mm GSh-30-1
    305: ({'LowAltRange': 700.0, 'HighAltRange': 500.0, 'LaunchMarginAngle': 0.0, 'SupplyCost': 0.8}, AIR_A),                                     # 25x137mm GAU-22
    332: ({'SupplyCost': 1.2}, {'SupplyCost': 0.0}),                                                       # 30x165mm Su-25
    333: ({'SupplyCost': 1.0}, {'SupplyCost': 0.0}),                                                       # 23x115mm light jets
    292: ({'Damage': 2.6}, {'Damage': 1.75}),                                                              # 23x115mm bomber tail guns
    55: ({'Damage': 4.0}, {'Damage': 8.0}),                                                                # AC-130 40x311mm HEDP
    74: ({'Damage': 3.0, 'DispersionHorizontalRadius': 2.25, 'DispersionVerticalRadius': 2.25},
         {'Damage': 6.0, 'DispersionHorizontalRadius': 0.0, 'DispersionVerticalRadius': 0.0}),            # AC-130 30x173mm HEI-T
    307: ({'Damage': 1.5, 'DispersionHorizontalRadius': 2.25, 'DispersionVerticalRadius': 2.25},
          {'Damage': 1.95, 'DispersionHorizontalRadius': 0.0, 'DispersionVerticalRadius': 0.0}),           # AC-130 30x173mm API
}
# China and preview rows: weapon -> reference weapon, round -> reference round (values copied from the reference's ActualArrow values)
COPY_W = {**{w: 241 for w in (2009279, 2009297, 2009315, 2009399, 2009417, 2009777, 2009997, 2011443)},   # 30 mm aircraft cannon / GSh-30-1
          **{w: 483 for w in (2011479, 2011509, 2011521, 2011539, 2018695, 2018699, 2018704, 2018708)},   # Type 23 cannon; A333 users
          2009351: 486}   # the [TEST] M61 weapon copy 2020855 is gone: preview uses 88 (26 Nov)                                                                       # H-6K tail gun; [TEST] M61
COPY_A = {**{m: 90 for m in (2009283, 2009301, 2009319, 2009403, 2009421, 2009781, 2010001, 2011447)},
          **{m: 333 for m in (2011483, 2011513, 2011525, 2011543)}, 2009355: 292}   # the [TEST] M61 round copy 2020909 is gone: preview uses 295 (26 Nov)
GUN_TYPES = {114, 115, 116, 28, 29}


def apply(t, g, ok, rec):
    U, W, A, WA = t['Units'], t['WeaponsJson'], t['AmmunitionsJson'], t['WeaponAmmunitionsJson']
    planes = {i for i, u in U.items() if u and u.get('Type') == 16}
    guns = {}
    for r in WA.values():
        if r and r['UnitId'] in planes and W.get(r['WeaponId'], {}).get('Type') in GUN_TYPES:guns.setdefault(r['WeaponId'], set()).add(r['AmmunitionId'])
    # every plane gun is covered, or one of the three ActualArrow left alone (GAU-8, AV-8B GAU-12, Su-25 GSh-2-30)
    untouched = {383, 225, 482}
    ok(set(guns) == set(WEAPONS) | set(COPY_W) | untouched, ('plane guns covered', sorted(set(guns) - set(WEAPONS) - set(COPY_W) - untouched),
                                                              sorted((set(WEAPONS) | set(COPY_W) | untouched) - set(guns))))
    rounds = set().union(*guns.values())
    ok(rounds <= set(AMMO) | set(COPY_A) | {56, 146, 293}, ('plane gun rounds covered', sorted(rounds - set(AMMO) - set(COPY_A) - {56, 146, 293})))
    # before: the vanilla values (FA had not changed any of them)
    for i, (before, _) in WEAPONS.items():ok(all(W[i].get(k) == v for k, v in before.items()), ('weapon before', i, W[i]['HUDName'], {k: W[i].get(k) for k in before}))
    for i, (before, _) in AMMO.items():ok(all(A[i].get(k) == v for k, v in before.items()), ('round before', i, A[i]['HUDName'], {k: A[i].get(k) for k in before}))
    for i, ref in COPY_W.items():ok(all(W[i].get(k) == W[ref].get(k) for k in WEAPONS[ref][0]), ('China/preview weapon matches its class before', i, W[i]['HUDName'], ref))
    for i, ref in COPY_A.items():ok(all(A[i].get(k) == A[ref].get(k) for k in AMMO[ref][0]), ('China/preview round matches its class before', i, A[i]['HUDName'], ref))
    for i, (_, after) in WEAPONS.items():g.put('WeaponsJson', i, dict(after))
    for i, (_, after) in AMMO.items():g.put('AmmunitionsJson', i, dict(after))
    for i, ref in COPY_W.items():g.put('WeaponsJson', i, dict(WEAPONS[ref][1]))
    for i, ref in COPY_A.items():g.put('AmmunitionsJson', i, dict(AMMO[ref][1]))
    # after
    for i, (_, after) in WEAPONS.items():ok(all(W[i].get(k) == v for k, v in after.items()), ('weapon after', i))
    for i, (_, after) in AMMO.items():ok(all(A[i].get(k) == v for k, v in after.items()), ('round after', i))
    for i, ref in COPY_W.items():ok(all(W[i].get(k) == W[ref].get(k) for k in WEAPONS[ref][1]), ('China/preview weapon = class after', i))
    for i, ref in COPY_A.items():ok(all(A[i].get(k) == A[ref].get(k) for k in AMMO[ref][1]), ('China/preview round = class after', i))
    china = sorted({U[r['UnitId']]['HUDName'] for r in WA.values() if r and r['UnitId'] in planes and U[r['UnitId']].get('CountryId') == 4 and r['WeaponId'] in COPY_W})
    rec['plane_guns_aa_1125'] = {'weapons': len(WEAPONS) + len(COPY_W), 'rounds': len(AMMO) + len(COPY_A), 'china_planes': china}
    print('PLANE GUNS (ActualArrow 1.2.2)', rec['plane_guns_aa_1125'])

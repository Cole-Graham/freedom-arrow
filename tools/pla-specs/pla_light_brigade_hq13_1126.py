"""PLA Light Brigade build, HQ-13 SHORAD for PLAN (Osama 26 Nov 2026 16:2x PST, thread 1572407822849810463 "China cosmetic work": "Add this to
PLAN, As HQ-13. it's a Fb-10 clone which I believe the FK-2000 has" / "HQ-13 SHORAD", on the ZSD-05 + FK-3000 turret render with two long
missile pods and no autocannon). Branch codex/batch/osama/pla-light-brigade only; the last plb section, so no earlier row id moves.
- The FB-10 in the data is the PGL-625's missile (weapon 2009371, round 2009373: 1,100 low / 900 high altitude world range, radar seeker 100,
  damage 14); the FK-2000 carries its own 'FK-2000 SAM' (2009605). New unit 'PLA HQ-13 SHORAD' = the PGL-625 (920) without its 25 mm gun:
  FB-10 only, 8 missiles (the two 4-tube pods of the model), its Radar SHORAD ability and optics, 4 cards in PLAN (spec 20).
- ZSD-05 chassis (1412): its default armour (2020686) and amphibious tracks (2020692) linked, its sound and dive offset; game body
  US_M6_Linebacker with a copy of the HJ-10's Linebacker launcher mount (2009620) carrying the FB-10 at Order 0, as the ZSD-05 HJ-10.
- Price 130 pts is a placeholder (PGL-625 170 with the gun); Osama to set. Not yet tested in a game. Model: work/zsd05-hj10-1126 build_fk.py."""
PGL, HJ10_MOUNT, ZSD05, PLAN = 920, 2009620, 1412, 20
FB10, FB10_ROUND, ZSD_ARMOR, ZSD_TRACKS = 2009371, 2009373, 2020686, 2020692
NAME, HUD, COST, MISSILES = 'PLA HQ-13 SHORAD', 'HQ-13 SHORAD', 130, 8


def apply(t, g, ok, rec):
    U, SA, W, A, T = t['Units'], t['SpecializationAvailabilitiesJson'], t['WeaponsJson'], t['AmmunitionsJson'], t['TurretsJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    ok(U[PGL]['HUDName'] == 'PGL-625' and W[FB10]['HUDName'] == 'FB-10' and A[FB10_ROUND]['HUDName'] == 'FB-10 ammunition', 'PGL-625 / FB-10 rows')
    ok([r['AmmunitionId'] for r in rows('WeaponAmmunitionsJson', UnitId=PGL, WeaponId=FB10)] == [FB10_ROUND], 'PGL-625 fires the FB-10 round')
    ok(T[HJ10_MOUNT]['ModelFileName'] == 'US_M6_Linebacker/US_M6_Linebacker_A4' and len(rows('TurretWeaponsJson', TurretId=HJ10_MOUNT)) == 1, 'HJ-10 Linebacker mount')
    ok(not any(u and (u.get('Name') == NAME or u.get('HUDName') == HUD) for u in U.values()), 'name free')
    (card,) = rows('SpecializationAvailabilitiesJson', UnitId=PGL)
    z = U[ZSD05]
    uid = g.add('Units', U[PGL], {'Name': NAME, 'HUDName': HUD, 'Description': None, 'OriginalName': None, 'OriginalCost': 0, 'Cost': COST,
                                  'ModelFileName': 'US_M6_Linebacker', 'PortraitFileName': U[936]['PortraitFileName'], 'ThumbnailFileName': z['ThumbnailFileName'],
                                  'AudioPreset': z['AudioPreset'], 'WaterDiveOffset': z['WaterDiveOffset'], 'ContentMembership': U[936]['ContentMembership'],
                                  'Length': U[936]['Length'], 'Width': U[936]['Width'], 'Height': U[936]['Height'], 'Weight': U[936]['Weight']})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson'):
        for r in rows(tab, UnitId=PGL): g.add(tab, r, {'UnitId': uid})
    mount = g.add('TurretsJson', T[HJ10_MOUNT], {'Name': 'PLA HQ-13 mount 0'})
    g.add('TurretWeaponsJson', rows('TurretWeaponsJson', TurretId=HJ10_MOUNT)[0], {'TurretId': mount, 'WeaponId': FB10, 'Order': 0})
    g.add('TurretUnitsJson', rows('TurretUnitsJson', UnitId=PGL)[0], {'UnitId': uid, 'TurretId': mount, 'Order': 0})
    g.add('WeaponAmmunitionsJson', rows('WeaponAmmunitionsJson', UnitId=PGL, WeaponId=FB10)[0], {'UnitId': uid, 'Quantity': MISSILES, 'Order': 0})
    g.add('UnitArmorsJson', rows('UnitArmorsJson', UnitId=PGL)[0], {'UnitId': uid, 'ArmorId': ZSD_ARMOR})
    g.add('UnitPropulsionsJson', rows('UnitPropulsionsJson', UnitId=PGL)[0], {'UnitId': uid, 'MobilityId': ZSD_TRACKS})
    nc = g.add('SpecializationAvailabilitiesJson', card, {'UnitId': uid, 'SpecializationId': PLAN})
    ok(not rows('ModificationsJson', UnitId=PGL), 'PGL-625 has no loadouts')
    ok([(r['WeaponId'], r['AmmunitionId'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=uid)] == [(FB10, FB10_ROUND, MISSILES)]
       and [r['WeaponId'] for r in rows('TurretWeaponsJson', TurretId=mount)] == [FB10] and [r['TurretId'] for r in rows('TurretUnitsJson', UnitId=uid)] == [mount],
       'HQ-13: one mount, FB-10 only, 8 rounds')
    ok(SA[card['Id']]['SpecializationId'] == 21 and SA[nc]['SpecializationId'] == PLAN, 'PGL-625 stays in the Medium CAB; HQ-13 card in PLAN')
    rec['pla_light_brigade_hq13_1126'] = {'unit': uid, 'card': nc, 'cards': SA[nc]['MaxAvailabilityXp0'], 'cost': COST, 'mount': mount, 'missiles': MISSILES,
        'abilities': [t['AbilitiesJson'][r['AbilityId']].get('Name') for r in rows('UnitAbilitiesJson', UnitId=uid)],
        'sensors': [r['SensorId'] for r in rows('SensorUnitsJson', UnitId=uid)], 'body': U[uid]['ModelFileName']}
    print('PLA LIGHT BRIGADE HQ-13', rec['pla_light_brigade_hq13_1126'])

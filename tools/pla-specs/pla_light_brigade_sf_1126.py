"""PLA Light Brigade build, Flying Tigers kit and Marine Scouts (Osama 26 Nov 2026 03:2x-03:3x PST, thread 1567745029781454889). Branch
codex/batch/osama/pla-light-brigade only; inside g.scope('plb'), after the names section.
- 03:2x "Flying Tigers get 3x SIG 516, cloned from HK416 D10RS, 3x SPAS-12 (clone from M1014), and 1x MP5SD they get a "ARWEN 37" that shoots a GL
  that doesn't really do damage but it panicks enemy infantry (30 meter min range to 300m), use the same icon as the arbalet, 6 man team", with the
  Hong Kong SDU patch for the card icon (tools/icons-src/make_flying_tigers.py -> FA_PLA_INF_FLYING_TIGERS).
  - New weapons (exact stat copies, new names): SIG 516 = HK 416 D10RS (210), SPAS-12 = M1014 (45); both fire the vanilla rounds (469, 359).
    MP5SD = the vanilla MP5SD6 (508, round 341).
  - ARWEN 37 = copy of the M320 Standalone (533: single shot, 6 s reload) with the Arbalet's icon INF_TKB_0249. Its round = copy of the M320's 40x46mm
    (470) as '37 mm less-lethal': Damage 2.0 -> 0.1, penetration 20 -> 0, health radius 6 -> 0; stress 20 -> 500 in a 6 -> 10 m radius (world;
    card 20 m), so one close hit shocks (500) and two panic (800 of 1000); range 15-150 world = 30-300 on the card (ranges show twice the world
    value, docs/engine/stress.md). Starting values to tune.
  - 04:4x "the gl on the flying tigers is a bit weak, not really panicking. It should full panick an infantry in 5 seconds": with one shot per
    6-8 s reload and falloff over a 10 m spread it averaged ~250 stress per 9-11 s. Now a 5-round revolver like the real ARWEN: magazine 5, one burst
    of 5 shots 1.0 s apart, aim 1.0-1.5 s (was 2-3), reload 8-10 s; each round 200 stress with no falloff inside the 10 m radius (NoDamageFalloff),
    so 4 hits = 800 = panicked, about 4.5-5 s after the order (aim + 3 s). 25 rounds per carrier (5 reloads). Calculated, not yet measured in game.
  - Kit (6 men, as before): leader SIG 516 + ARWEN 37; SIG 516 + SPAS-12 (shotgun as the special weapon, the vanilla M1014 pattern of Delta / Green
    Berets / Pararescue); SIG 516; 2 SPAS-12; MP5SD. The flashbang goes (not in the list). Ammo per carrier: SIG 160 (Rangers RRC HK 416), SPAS 96
    (M1014), MP5SD 160 (KNT), ARWEN 20. Armour, price (55), stealth, ability and cards unchanged. Card icon FA_PLA_INF_FLYING_TIGERS.
- 03:3x "PLAN gets Marine Scouts (their icon is a target crosshair instead of the binos in front of the marine icon). They are a 3 man unit. 1x QMK,
  1xQBU-191, QBU-203, 75 points": new unit = copy of Marine Recon (1224: PLAN Recon tab, stealth 0.4 = card 2.5, its card row: 4 cards and 5
  transports) with 3 men (QMK leader, QBU-202 (was QBU-191, 26 Nov 11:1x), QBU-203 (the QBU-201 row, shown as QBU-203)), armour 'Armor Infantry Shock 3Men' (279: 8, 15 HP),
  75 pts, card icon FA_PLA_INF_LINE_MARINE_SCOUT (tools/icons-src/make_marine_scouts.py). No sniper rifle (Type 4), so card stealth 2.5 by the
  China recon rule."""
FT, HK416, M1014, MP5SD, M320, M320_A = 1187, 210, 45, 508, 533, 470
HK_A, M1014_A, MP5_A, ARBALET_ICON = 469, 359, 341, 'INF_TKB_0249'
MRECON, SHOCK3, QMK, QMK_A, QBU191, QBU191_A, QBU203, QBU203_A = 1224, 279, 2019300, 2019301, 2004000, 2004001, 2020834, 2020835


def apply(t, g, ok, rec):
    U, W, A, SM, AR = (t[k] for k in ('Units', 'WeaponsJson', 'AmmunitionsJson', 'SquadMembersJson', 'ArmorsJson'))
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    wn = lambda i: W[i]['HUDName'] if i else ''
    ok([wn(w) for w in (HK416, M1014, MP5SD, M320)] == ['HK 416 D10RS', 'M1014', 'MP5SD6', 'M320'] and W[932]['HUDIcon'] == ARBALET_ICON, 'donor weapons, Arbalet icon')
    ok([A[a]['HUDName'] for a in (HK_A, M1014_A, MP5_A)] == ['5.56x45mm', '12ga SLUG', '9x19mm'] and A[M320_A]['Damage'] == 2.0 and A[M320_A]['StressDamage'] == 20.0, 'donor rounds')
    ok(not any(w and w.get('HUDName') in ('SIG 516', 'SPAS-12', 'ARWEN 37') for w in W.values()), 'new weapon names free')
    sig = g.add('WeaponsJson', W[HK416], {'Name': 'PLA infantry SIG 516', 'HUDName': 'SIG 516'})
    spas = g.add('WeaponsJson', W[M1014], {'Name': 'PLA infantry SPAS-12', 'HUDName': 'SPAS-12'})
    ARWEN_FIRE = {'MagazineSize': 5, 'ShotsPerBurstMin': 5, 'ShotsPerBurstMax': 5, 'TimeBetweenShotsInBurst': 1.0, 'AimTimeMin': 1.0, 'AimTimeMax': 1.5,
                  'MagazineReloadTimeMin': 8.0, 'MagazineReloadTimeMax': 10.0}
    arwen = g.add('WeaponsJson', W[M320], {'Name': 'PLA infantry ARWEN 37', 'HUDName': 'ARWEN 37', 'HUDIcon': ARBALET_ICON, **ARWEN_FIRE})
    arwen_a = g.add('AmmunitionsJson', A[M320_A], {'Name': 'PLA infantry ARWEN 37 less-lethal', 'HUDName': '37 mm less-lethal', 'Damage': 0.1,
                                                   'PenetrationAtGroundRange': 0.0, 'PenetrationAtMinRange': 0.0, 'HealthAOERadius': 0.0,
                                                   'StressDamage': 200.0, 'StressAOERadius': 10.0, 'NoDamageFalloff': True, 'MinimalRange': 15.0, 'GroundRange': 150.0})
    # Flying Tigers kit
    men = rows('SquadMembersJson', UnitId=FT)
    ok(U[FT]['HUDName'] == 'Flying Tigers' and len(men) == 6 and U[FT]['Cost'] == 55, 'Flying Tigers 1187: 6 men, 55 pts')
    kit = [(sig, arwen, 1), (sig, spas, 2), (sig, 0, 3), (spas, 0, 2), (spas, 0, 3), (MP5SD, 0, 3)]
    for r, (p, s, dp) in zip(men, kit): g.put('SquadMembersJson', r['Id'], {'PrimaryWeaponId': p, 'SpecialWeaponId': s, 'DeathPriority': dp})
    sw0, wa0 = rows('SquadWeaponsJson', UnitId=FT)[0], rows('WeaponAmmunitionsJson', UnitId=FT)[0]
    for tab in ('SquadWeaponsJson', 'WeaponAmmunitionsJson'):
        for r in rows(tab, UnitId=FT): g.remove(tab, r['Id'])
    for n, (w, a, q) in enumerate([(sig, HK_A, 160), (spas, M1014_A, 96), (MP5SD, MP5_A, 160), (arwen, arwen_a, 25)], 1):
        g.add('SquadWeaponsJson', sw0, {'UnitId': FT, 'WeaponId': w, 'Order': n})
        g.add('WeaponAmmunitionsJson', wa0, {'UnitId': FT, 'WeaponId': w, 'AmmunitionId': a, 'Quantity': q, 'Order': 0})
    g.put('Units', FT, {'ThumbnailFileName': 'FA_PLA_INF_FLYING_TIGERS'})
    # Marine Scouts
    ok(U[MRECON]['HUDName'] == 'Marine Recon' and U[MRECON]['Stealth'] == 0.4 and AR[SHOCK3]['Name'] == 'Armor Infantry Shock 3Men' and AR[SHOCK3]['MaxHealthPoints'] == 15, 'Marine Recon, Shock 3Men')
    ok([wn(w) for w in (QMK, QBU191, QBU203)] == ['QMK', 'QBU-191', 'QBU-203'] and not any(W[w]['Type'] == 4 for w in (QMK, QBU191, QBU203)), 'scout weapons (no sniper rifle)')
    ok(not any(u and 'Marine Scouts' in (u.get('Name', ''), u.get('HUDName', '')) for u in U.values()), 'Marine Scouts name free')
    ms = g.add('Units', U[MRECON], {'Name': 'PLA Marine Scouts', 'HUDName': 'Marine Scouts', 'Cost': 75, 'OriginalCost': 0, 'Description': None,
                                    'OriginalName': None, 'ThumbnailFileName': 'FA_PLA_INF_LINE_MARINE_SCOUT'})
    for tab in ('UnitPropulsionsJson', 'UnitAbilitiesJson', 'SensorUnitsJson'):
        for r in rows(tab, UnitId=MRECON): g.add(tab, r, {'UnitId': ms})
    g.add('UnitArmorsJson', rows('UnitArmorsJson', UnitId=MRECON)[0], {'UnitId': ms, 'ArmorId': SHOCK3})
    man = rows('SquadMembersJson', UnitId=MRECON)[0]
    for p, dp in ((QMK, 1), (QBU191, 2), (QBU203, 2)):
        g.add('SquadMembersJson', man, {'UnitId': ms, 'PrimaryWeaponId': p, 'SpecialWeaponId': 0, 'DeathPriority': dp})
    sw0, wa0 = rows('SquadWeaponsJson', UnitId=MRECON)[0], rows('WeaponAmmunitionsJson', UnitId=MRECON)[0]
    # 26 Nov 11:1x "we're going to give the qbu202 to the Marine Scouts it replaces the qbu 191": the back-pocket QBU-202 (Mk 22 ASR copy, Type 3
    # marksman like the Mk 22, round '8.6 mm precision ammunition') in place of the QBU-191; 40 rounds, the Green Berets' Mk 22 count.
    qb = rec['backpocket_weapons_1125']['QBU-202']; QBU202, QBU202_A = qb['weapon'], qb['ammo']
    ok(W[QBU202]['HUDName'] == 'QBU-202' and W[QBU202]['Type'] == 3, 'QBU-202 back-pocket row')
    for m in rows('SquadMembersJson', UnitId=ms):
        if m['PrimaryWeaponId'] == QBU191: g.put('SquadMembersJson', m['Id'], {'PrimaryWeaponId': QBU202})
    for n, (w, a, q) in enumerate([(QMK, QMK_A, 160), (QBU202, QBU202_A, 40), (QBU203, QBU203_A, 60)], 1):
        g.add('SquadWeaponsJson', sw0, {'UnitId': ms, 'WeaponId': w, 'Order': n})
        g.add('WeaponAmmunitionsJson', wa0, {'UnitId': ms, 'WeaponId': w, 'AmmunitionId': a, 'Quantity': q, 'Order': 0})
    (mc,) = rows('SpecializationAvailabilitiesJson', UnitId=MRECON)
    nc = g.add('SpecializationAvailabilitiesJson', mc, {'UnitId': ms})
    for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=mc['Id']): g.add('TransportAvailabilitiesJson', r, {'SpecializationAvailabilityId': nc})
    # checks after
    for u in (FT, ms):
        carried = {w for r in rows('SquadMembersJson', UnitId=u) for w in (r['PrimaryWeaponId'], r['SpecialWeaponId']) if w}
        ok({r['WeaponId'] for r in rows('SquadWeaponsJson', UnitId=u)} == carried == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=u)}, ('card + ammo = carried', u))
    same = lambda x, y, skip=(): all(x.get(k) == y[k] for k in y if k not in ('Id', 'Name', 'HUDName', 'HUDIcon', *skip))
    ok(same(W[sig], W[HK416]) and same(W[spas], W[M1014]) and same(W[arwen], W[M320], tuple(ARWEN_FIRE)), 'SIG 516 / SPAS-12 = donor stats; ARWEN 37 = M320 but fire rate')
    ok(4 * A[arwen_a]['StressDamage'] >= 800 and A[arwen_a]['NoDamageFalloff'] and W[arwen]['MagazineSize'] == 5, 'ARWEN: 4 hits panic (800 of 1000)')
    import os
    icons = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'mod', 'source', 'runtime-qa', 'icons')
    ok(all(os.path.isfile(os.path.join(icons, n + s + '.png')) for n in ('FA_PLA_INF_FLYING_TIGERS', 'FA_PLA_INF_LINE_MARINE_SCOUT') for s in ('', '_OUTLINE')), 'card icons in runtime-qa/icons')
    kit_of = lambda u: sorted((wn(r['PrimaryWeaponId']), wn(r['SpecialWeaponId']), r['DeathPriority']) for r in rows('SquadMembersJson', UnitId=u))
    ok(len(kit_of(ms)) == 3 and U[ms]['Cost'] == 75 and nc, ('Marine Scouts', kit_of(ms)))
    rec['pla_light_brigade_sf_1126'] = {'weapons': {'SIG 516': sig, 'SPAS-12': spas, 'ARWEN 37': arwen, 'ARWEN round': arwen_a}, 'flying_tigers': kit_of(FT),
                                        'marine_scouts': {'unit': ms, 'kit': kit_of(ms), 'cards': mc['MaxAvailabilityXp0'],
                                                          'transports': [U[r['UnitId']]['HUDName'] for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=nc)]}}
    print('PLA LIGHT BRIGADE SF', rec['pla_light_brigade_sf_1126'])

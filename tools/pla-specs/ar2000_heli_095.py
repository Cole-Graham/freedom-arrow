"""AR-2000 on a helicopter stand-in (Osama 22 Nov 2026 13:2x PST, thread 1573561286803980289: "You might need to use a different stand in for
the Drone then the AR 2000 let's try that out and make sure we Mount things like it's a real helicopter. Of course we keep this current stats").
- Why: QQ sheet FA-041 ("AKD-11 laser rounds fly wild"). 22 Nov player logs (0.9.4): AR-2000 AKD-11 "shots 161, hits 3", gaps down to 0.01 s,
  with 8 rounds on board = the launch is refused and retried every frame (other matches 4/0, 8/0, 75/10, 28/11). The same round on the Z-10
  hits 61-65%. The AKD-11 round 2019088 and launcher 2019087 are AGM-114K Hellfire copies; the stand-in was the MDP-01 Termit drone, whose
  fixed pylon only ever carries the Kornet in vanilla (no loft, 30 degree seeker, no laser).
- Change: body = vanilla OH-58D Kiowa Warrior (US_OH58Kiowa: recon helicopter, role 70 like the AR-2000, Hellfire pylons). The AKD-11 goes on the
  Kiowa's left and right pylon slots (Turret0Id / Turret1Id) through one default loadout option, the Kiowa / Z-10 / Wing Loong pattern, with the
  Hellfire x4 pylon model: 4 rounds per pylon = 8, as before. The pylon turret stops being a default hull turret (it would be loaded twice).
- Kept (Osama: "keep this current stats"): price 120, stealth, size, weight, mobility (Termit drive 308), sound, sensor, armour and every AKD-11
  round value. Helicopters merge identical pylons into one launcher (UnitBuilder.CombinePylonsOnAircraft: magazines summed, seeker-round
  TimeBetweenBursts divided by the pylon count; [[sead-pylon-merge]]), so the launcher row gets 48-64 s: 24-32 s between shots in battle, as now.
- FAModels hides every stand-in renderer and draws m_ar2000 by the unit Name ('PLA Catalogue AR-2000', unchanged): no asset change.
Called from apply_0_9_4_dev1.py."""
AR, LAUNCHER, ROUND, PYLON, AMMO_ROW, TU_ROW = 1084, 2019087, 2019088, 2019089, 2019096, 2019095
KIOWA, KIOWA_HELLFIRE_PYLON, WING_LOONG_LOADOUT = 267, 157, 2017049


def apply(t, g, ok, rec):
    U, W, T, WA, TU, M, O = (t[k] for k in ('Units', 'WeaponsJson', 'TurretsJson', 'WeaponAmmunitionsJson', 'TurretUnitsJson', 'ModificationsJson', 'OptionsJson'))
    rows = lambda tab, **kw: [r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())]
    u = U[AR]
    ok(u['Name'] == 'PLA Catalogue AR-2000' and u['ModelFileName'] == 'DLC3_MDP01_Termit' and u['Type'] == 8 and u['Cost'] == 120, ('AR-2000 before', u['ModelFileName'], u['Cost']))
    ok(U[KIOWA]['ModelFileName'] == 'US_OH58Kiowa' and U[KIOWA]['Type'] == 8 and U[KIOWA]['Role'] == u['Role'] == 70, 'Kiowa stand-in: recon helicopter')
    ok([(r['TurretId'], r['Order']) for r in rows('TurretUnitsJson', UnitId=AR)] == [(PYLON, 0)] and T[PYLON]['IsDefault'] is True, 'one default Termit pylon before')
    ok([(r['Id'], r['WeaponId']) for r in rows('TurretWeaponsJson', TurretId=PYLON)] and all(r['WeaponId'] == LAUNCHER for r in rows('TurretWeaponsJson', TurretId=PYLON)), 'pylon carries the AKD-11 launcher only')
    ok([(r['Id'], r['WeaponId'], r['AmmunitionId'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=AR)] == [(AMMO_ROW, LAUNCHER, ROUND, 8)], '8 AKD-11 before')
    w = W[LAUNCHER]
    ok((w['MagazineSize'], w['TimeBetweenBurstsMin'], w['TimeBetweenBurstsMax'], w['CanBeMerged']) == (4, 24.0, 32.0, True), ('AKD-11 launcher before', w['MagazineSize'], w['TimeBetweenBurstsMin']))
    ok(not rows('ModificationsJson', UnitId=AR), 'AR-2000 has no loadout slot before')
    ok(T[KIOWA_HELLFIRE_PYLON]['ModelFileName'] == 'Weapon/Hellfire/Hellfire_2' and {o['Turret0Id'] for o in O.values() if o and o.get('Name') == 'LeftPylon Kiowa HellfireR'} == {KIOWA_HELLFIRE_PYLON}, 'Kiowa Hellfire on pylon slots 0 / 1')

    g.put('Units', AR, {'ModelFileName': 'US_OH58Kiowa'})
    g.put('TurretsJson', PYLON, {'Name': 'PLA AR-2000 AKD-11 x4 pylon', 'ModelFileName': 'Weapon/Hellfire/Hellfire_4', 'IsDefault': False})
    g.put('WeaponAmmunitionsJson', AMMO_ROW, {'Quantity': 4})
    g.put('WeaponsJson', LAUNCHER, {'Name': 'PLA AR-2000 AKD-11 x4', 'TimeBetweenBurstsMin': 48.0, 'TimeBetweenBurstsMax': 64.0})
    tm = rows('ModificationsJson', Id=WING_LOONG_LOADOUT)[0]
    mod = g.add('ModificationsJson', tm, {'UnitId': AR, 'Name': 'PLA loadout AR-2000', 'Order': 0})
    to = rows('OptionsJson', ModificationId=WING_LOONG_LOADOUT, IsDefault=True)[0]
    # 0 = "no change" in every id / override field, as in vanilla options (None fails check_field_types; build 285 first try).
    slots = {f'Turret{i}Id': 0 for i in range(21)}
    slots.update(Turret0Id=PYLON, Turret1Id=PYLON)
    opt = g.add('OptionsJson', to, {'ModificationId': mod, 'Name': 'PLA loadout AR-2000 0', 'UIName': 'Anti-armor (AKD-11)', 'Order': 0, 'IsDefault': True,
                                    'Cost': 0, 'ReplaceUnitId': 0, 'ReplaceUnitName': None, 'MobilityId': 0, 'ArmorId': 0, 'MainSensorId': 0,
                                    'ExtraSensorId': 0, 'StealthOverride': 0.0, 'Ability1Id': 0, 'Ability2Id': 0, 'Ability3Id': 0, **slots})

    o = O[opt]
    ok(U[AR]['ModelFileName'] == 'US_OH58Kiowa' and U[AR]['Cost'] == 120 and U[AR]['Stealth'] == u['Stealth'], 'AR-2000 on the Kiowa body, price and stealth kept')
    ok(o['IsDefault'] is True and o['Cost'] == 0 and (o['Turret0Id'], o['Turret1Id']) == (PYLON, PYLON) and all(o.get(f'Turret{i}Id') == 0 for i in range(2, 21)), 'AKD-11 on both pylon slots')
    ok(T[PYLON]['IsDefault'] is False and [r['TurretId'] for r in rows('TurretUnitsJson', UnitId=AR)] == [PYLON], 'pylon linked, not a default hull turret')
    ok(WA[AMMO_ROW]['Quantity'] * 2 == 8 and (W[LAUNCHER]['TimeBetweenBurstsMin'] / 2, W[LAUNCHER]['TimeBetweenBurstsMax'] / 2) == (24.0, 32.0), '8 rounds, 24-32 s after the pylon merge')
    rec['ar2000_heli'] = {'unit': AR, 'stand_in': 'US_OH58Kiowa (was DLC3_MDP01_Termit)', 'pylon': PYLON, 'option': opt, 'modification': mod,
                          'rounds_per_pylon': 4, 'launcher_pause_s': [48.0, 64.0], 'pause_after_merge_s': [24.0, 32.0]}

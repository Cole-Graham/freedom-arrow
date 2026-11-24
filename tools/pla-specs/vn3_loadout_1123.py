"""VN-3 loadouts (Osama 23 Nov 2026 21:4x PST, thread 1567745029781454889): "VN-3, starts at the 2A72 Autocannon, no kord, should cost 30 pts and
start from there, remove Spitsa module, and the atgm option, it should have a +10 atgm option that adds the HJ-73D (4x)".
mk_china_1123.py made the VN-3 a copy of the BPM-97 with its four turret options (Kord +0, 2A72 +10, Spitsa AGS +15, Spitsa ATGM +20).
- Unit cost 20 -> 30; the 2A72 option (2A72 + PKT) +10 -> +0, so the VN-3 starts at 30 with the 2A72.
- Removed: the Kord, Spitsa AGS and Spitsa ATGM (Konkurs-M) options, their turret links and their ammunition rows (Kord, 2A42, AG-30, Konkurs-M).
- New "+10" option = the old Spitsa ATGM option row with its own turret: a copy of the vanilla Spitsa ATGM turret (1211, three weapon points)
  carrying 2A72 + PKT + HJ-73D in the same three slots and priorities, so the BPM-97 body spawns it as it spawns the Spitsa ATGM.
  HJ-73D = the vehicle launcher of the ZBD-03 / ZBL-08 (weapon 2011151, ammunition 2011153), 4 missiles as on those vehicles."""
KORD, A2A72, AGS, SPITSA_ATGM = 'Custom_Option_Kord', 'Custom_Option_2A72', 'dlc_3_Custom_Option_Spitsa_AGS_module', 'dlc_3_Custom_Option_Spitsa_ATGM_module'
T_KORD, T_2A72, T_AGS, T_ATGM = 368, 369, 370, 1211
W_2A72, W_2A42, W_PKT, W_KONKURS, W_HJ73D, A_HJ73D = 2, 306, 7, 518, 2011151, 2011153


def apply(t, g, ok, rec):
    U, O, M, T, TW, TU, WA, W = (t[k] for k in ('Units', 'OptionsJson', 'ModificationsJson', 'TurretsJson', 'TurretWeaponsJson', 'TurretUnitsJson',
                                                'WeaponAmmunitionsJson', 'WeaponsJson'))
    vn = [i for i, u in U.items() if u and u.get('Name') == 'PLA VN-3']
    ok(len(vn) == 1 and U[vn[0]]['Cost'] == 20, 'VN-3 card (20 pts)'); vn = vn[0]
    mods = [m for m, x in M.items() if x and x['UnitId'] == vn]
    opts = {o['UIName']: o for o in O.values() if o and o['ModificationId'] in mods}
    ok(len(mods) == 1 and {k: (v['Cost'], v['Turret0Id']) for k, v in opts.items()} == {KORD: (0, T_KORD), A2A72: (10, T_2A72), AGS: (15, T_AGS), SPITSA_ATGM: (20, T_ATGM)},
       ('VN-3 options as copied from the BPM-97', {k: v['Cost'] for k, v in opts.items()}))
    ok([(r['WeaponId'], r['Order']) for r in sorted((r for r in TW.values() if r and r['TurretId'] == T_ATGM), key=lambda r: r['Order'])] == [(W_2A42, 0), (W_PKT, 1), (W_KONKURS, 2)]
       and W[W_HJ73D]['HUDName'] == 'HJ-73D' and W[W_2A72]['HUDName'] == '2А72 30mm', 'Spitsa ATGM turret: 2A42, PKT, Konkurs-M; HJ-73D vehicle launcher')
    # new turret: Spitsa ATGM slots with 2A72 / PKT / HJ-73D
    tid = g.add('TurretsJson', T[T_ATGM], {'Name': 'MainTurret VN-3 2A72 HJ-73D'})
    for r in [r for r in TW.values() if r and r['TurretId'] == T_ATGM]:
        g.add('TurretWeaponsJson', r, {'TurretId': tid, 'WeaponId': {W_2A42: W_2A72, W_KONKURS: W_HJ73D}.get(r['WeaponId'], r['WeaponId'])})
    atgm = opts[SPITSA_ATGM]
    # Osama 24 Nov 01:2x 'vn-3 is bugged and doesn't show its weapon': removing the Kord option (Order 0, the BPM-97's default) left the VN-3
    # with options at Order 1 and 3 and none at 0. The 2A72 option becomes Order 0 + IsDefault (as ar2000_heli_095.py), the HJ-73D option Order 1.
    g.put('OptionsJson', atgm['Id'], {'Turret0Id': tid, 'Cost': 10, 'UIName': '2A72 + HJ-73D (4x)', 'Ability1Id': opts[A2A72]['Ability1Id'], 'Order': 1})
    g.put('OptionsJson', opts[A2A72]['Id'], {'Cost': 0, 'Order': 0, 'IsDefault': True})
    g.put('Units', vn, {'Cost': 30})
    for k in (KORD, AGS): g.remove('OptionsJson', opts[k]['Id'])
    for r in [r for r in TU.values() if r and r['UnitId'] == vn]:
        if r['TurretId'] in (T_KORD, T_AGS): g.remove('TurretUnitsJson', r['Id'])
        elif r['TurretId'] == T_ATGM: g.put('TurretUnitsJson', r['Id'], {'TurretId': tid})
    keep = {W_2A72, W_PKT}
    old = [r for r in WA.values() if r and r['UnitId'] == vn and r['WeaponId'] not in keep]
    tpl = next(r for r in WA.values() if r and r['WeaponId'] == W_HJ73D and r['AmmunitionId'] == A_HJ73D and r['Quantity'] == 4)
    for r in old: g.remove('WeaponAmmunitionsJson', r['Id'])
    g.add('WeaponAmmunitionsJson', tpl, {'UnitId': vn})
    opts2 = sorted(((o['UIName'], o['Cost'], o['Turret0Id']) for o in O.values() if o and o['ModificationId'] in mods), key=lambda x: x[1])
    ok(opts2 == [(A2A72, 0, T_2A72), ('2A72 + HJ-73D (4x)', 10, tid)] and U[vn]['Cost'] == 30, ('VN-3: 30 pts with 2A72, +10 HJ-73D', opts2))
    ok(sorted((o['Order'], o['IsDefault'], o['Cost']) for o in O.values() if o and o['ModificationId'] in mods) == [(0, True, 0), (1, False, 10)], 'VN-3 default option = 2A72 at Order 0')
    ok(sorted(r['TurretId'] for r in TU.values() if r and r['UnitId'] == vn) == sorted([T_2A72, tid]), 'VN-3 turret links = its two options')
    weapons = {w['WeaponId'] for x in (T_2A72, tid) for w in TW.values() if w and w['TurretId'] == x}
    has = {(r['WeaponId'], r['Quantity']) for r in WA.values() if r and r['UnitId'] == vn}
    ok({w for w, _ in has} == weapons and (W_HJ73D, 4) in has, ('VN-3 ammunition = its weapons, HJ-73D x4', sorted(has)))
    rec['vn3_loadout'] = {'unit': vn, 'cost': [20, 30], 'options': opts2, 'turret': tid, 'removed': [KORD, AGS, 'Spitsa ATGM (Konkurs-M)']}
    print('VN-3 LOADOUT', rec['vn3_loadout'])

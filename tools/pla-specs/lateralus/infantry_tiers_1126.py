"""Infantry weapons: one name, one set of stats (Lateralus 26 Nov 2026 13:1x PST, thread 1572962048705429598: "Make the following changes, and
then remove the variants that are not placed on any unit from the game"). Infantry weapons no longer get per-squad tier rounds.
- M240L: every squad on the T3 round 390; Weapons Squad's M240L 6.8 (weapon 1021) -> M240L 63 + round 390.
- PKP-M -> PKP-N (weapon 125): round 362 damage 2.4, no minimum range, Close quarter (Weapons.CQC).
- PKP (weapon 30): own round (new, copy of 75) damage 2.1, no minimum range, Close quarter. Round 75 stays the PKM's (shared before).
  Pulemetchiki PKP (399): PKP T3 -> PKP-N 125 + round 362.
- PKM (weapon 158): every squad on round 75, damage 1.8, no minimum range, Close quarter (Reservisty 118 had the T0 round 365, BARS 616 the
  7.62x51 round 153 that the Ksp 58B and MG3 also fire).
- M249 (weapon 364) removed: Reserve Marines (407) get the M249E3 (weapon 60, same round 51).
- M249 Para T2 round 360: damage 2.55 -> 2.4.
- R-20 Rahe: Eesti Scouts (468, 525) T2 round 357 -> T1 round 16.
- HK 416A5: Jegeris (526) weapon 767 + round 358 -> Zaliukai's weapon 754 + round 469.
Removed once no unit has them (soldier or turret): weapons 1021, 364, 767 and round 365, with every WeaponAmmunitions / SquadWeapons row that
still names them (vanilla also kept leftover rows for weapons nobody carries). Runs after every other row-making section, so no other row's ID
moves. The game's WeaponCoverage rule is checked again at the end."""
import weapon_coverage_check

M240L, M240L68, R_M240L_T3 = 63, 1021, 390
PKPN, R_PKPN = 125, 362
PKP, PKM, R_PK_T1, R_PKM_T0, R_762x51_T1 = 30, 158, 75, 365, 153
PULEM = 399
M249, M249E3 = 364, 60
R_PARA_T2 = 360
RAHE, R_556_T1, R_556_T2 = 693, 16, 357
HK_J, HK_Z, R_HK_Z = 767, 754, 469
REMOVE_W, REMOVE_A = (M240L68, M249, HK_J), (R_PKM_T0,)


def apply(t, g, ok, rec, patches):
    U, W, A, WA, SW, SM = (t[k] for k in ('Units', 'WeaponsJson', 'AmmunitionsJson', 'WeaponAmmunitionsJson', 'SquadWeaponsJson', 'SquadMembersJson'))
    live = lambda tab: [r for r in t[tab].values() if r]
    names = {M240L: 'M240L', M240L68: 'M240L 6.8', PKPN: 'PKP-M', PKP: 'PKP', PKM: 'PKM', M249: 'M249', M249E3: 'M249E3', 53: 'M249 Para',
             RAHE: 'R-20 Rahe', HK_J: 'HK 416A5', HK_Z: 'HK 416A5'}
    for w, n in names.items():
        ok(W[w]['HUDName'] == n, ('weapon', w, W[w]['HUDName'], n))
    for a, dmg in ((R_M240L_T3, 2.7), (R_PKPN, 2.25), (R_PK_T1, 1.8), (R_PKM_T0, 0.9), (R_PARA_T2, 2.55), (R_556_T1, 1.2), (R_556_T2, 1.5), (R_HK_Z, 3.1)):
        ok(A[a]['Damage'] == dmg, ('round before', a, A[a]['Name'], A[a]['Damage'], dmg))
    carried = lambda u, w: any(m.get('UnitId') == u and w in (m.get('PrimaryWeaponId'), m.get('SpecialWeaponId')) for m in live('SquadMembersJson'))
    log = []

    def swap(u, old_w, new_w, new_a):
        """Unit u: every soldier with old_w gets new_w; its ammo and list rows point at (new_w, new_a)."""
        ok(carried(u, old_w), ('carries', u, U[u]['HUDName'], old_w))
        for m in live('SquadMembersJson'):
            if m['UnitId'] == u:
                ch = {k: new_w for k in ('PrimaryWeaponId', 'SpecialWeaponId') if m.get(k) == old_w}
                if ch: g.put('SquadMembersJson', m['Id'], ch)
        have_wa = any(r['UnitId'] == u and r['WeaponId'] == new_w and r['AmmunitionId'] == new_a for r in live('WeaponAmmunitionsJson'))
        for r in [r for r in live('WeaponAmmunitionsJson') if r['UnitId'] == u and r['WeaponId'] == old_w]:
            if have_wa: g.remove('WeaponAmmunitionsJson', r['Id'])
            else: g.put('WeaponAmmunitionsJson', r['Id'], {'WeaponId': new_w, 'AmmunitionId': new_a}); have_wa = True
        have_sw = any(r['UnitId'] == u and r['WeaponId'] == new_w for r in live('SquadWeaponsJson'))
        for r in [r for r in live('SquadWeaponsJson') if r['UnitId'] == u and r['WeaponId'] == old_w]:
            if have_sw: g.remove('SquadWeaponsJson', r['Id'])
            else: g.put('SquadWeaponsJson', r['Id'], {'WeaponId': new_w}); have_sw = True
        log.append(f"{U[u]['HUDName'].strip()} [{u}]: {W[old_w]['HUDName']} [{old_w}] -> {W[new_w]['HUDName']} [{new_w}] + round {new_a}")

    def reround(w, old_a, new_a):
        """Every unit that carries w and fires old_a from it fires new_a."""
        for r in [r for r in live('WeaponAmmunitionsJson') if r['WeaponId'] == w and r['AmmunitionId'] == old_a and carried(r['UnitId'], w)]:
            g.put('WeaponAmmunitionsJson', r['Id'], {'AmmunitionId': new_a})
            log.append(f"{U[r['UnitId']]['HUDName'].strip()} [{r['UnitId']}]: {W[w]['HUDName']} round {old_a} -> {new_a}")

    # M240L
    reround(M240L, 76, R_M240L_T3)
    for u in sorted({r['UnitId'] for r in live('WeaponAmmunitionsJson') if r['WeaponId'] == M240L68 and carried(r['UnitId'], M240L68)}):
        swap(u, M240L68, M240L, R_M240L_T3)
    # PKP-N
    g.put('WeaponsJson', PKPN, {'HUDName': 'PKP-N', 'Name': 'MMG 7.62 PKPN', 'CQC': True})
    g.put('AmmunitionsJson', R_PKPN, {'Damage': 2.4, 'MinimalRange': 0.0})
    # PKP: own round
    r_pkp = g.add('AmmunitionsJson', A[R_PK_T1], {'Name': 'InfBullet 7.62x54 MG PKP', 'Damage': 2.1, 'MinimalRange': 0.0})
    g.put('WeaponsJson', PKP, {'CQC': True})
    reround(PKP, R_PK_T1, r_pkp)
    swap(PULEM, PKP, PKPN, R_PKPN)
    # PKM
    reround(PKM, R_PKM_T0, R_PK_T1)
    reround(PKM, R_762x51_T1, R_PK_T1)
    g.put('WeaponsJson', PKM, {'CQC': True})
    g.put('AmmunitionsJson', R_PK_T1, {'Damage': 1.8, 'MinimalRange': 0.0})
    # M249 -> M249E3
    for u in sorted({r['UnitId'] for r in live('WeaponAmmunitionsJson') if r['WeaponId'] == M249 and carried(r['UnitId'], M249)}):
        a = next(r['AmmunitionId'] for r in live('WeaponAmmunitionsJson') if r['UnitId'] == u and r['WeaponId'] == M249)
        swap(u, M249, M249E3, a)
    # M249 Para T2
    g.put('AmmunitionsJson', R_PARA_T2, {'Damage': 2.4})
    # R-20 Rahe
    reround(RAHE, R_556_T2, R_556_T1)
    # HK 416A5
    for u in sorted({r['UnitId'] for r in live('WeaponAmmunitionsJson') if r['WeaponId'] == HK_J and carried(r['UnitId'], HK_J)}):
        swap(u, HK_J, HK_Z, R_HK_Z)

    # remove what no unit has any more, with the leftover rows that still name it
    for w in REMOVE_W:
        ok(not any(w in (m.get('PrimaryWeaponId'), m.get('SpecialWeaponId')) for m in live('SquadMembersJson')), ('still carried', w))
        ok(not any(r['WeaponId'] == w for r in live('TurretWeaponsJson')), ('on a turret', w))
    for a in REMOVE_A:
        ok(not any(r['AmmunitionId'] == a and carried(r['UnitId'], r['WeaponId']) for r in live('WeaponAmmunitionsJson')), ('round still fired', a))
    gone = {'WeaponAmmunitionsJson': 0, 'SquadWeaponsJson': 0}
    for r in live('WeaponAmmunitionsJson'):
        if r['WeaponId'] in REMOVE_W or r['AmmunitionId'] in REMOVE_A: g.remove('WeaponAmmunitionsJson', r['Id']); gone['WeaponAmmunitionsJson'] += 1
    for r in live('SquadWeaponsJson'):
        if r['WeaponId'] in REMOVE_W: g.remove('SquadWeaponsJson', r['Id']); gone['SquadWeaponsJson'] += 1
    for w in REMOVE_W: g.remove('WeaponsJson', w)
    for a in REMOVE_A: g.remove('AmmunitionsJson', a)

    # after: every squad that carries these guns fires one round each, with the asked values
    def rounds(w):
        return {r['AmmunitionId'] for r in live('WeaponAmmunitionsJson') if r['WeaponId'] == w and carried(r['UnitId'], w)}
    ok(rounds(M240L) == {R_M240L_T3}, ('M240L rounds', rounds(M240L)))
    ok(rounds(PKPN) == {R_PKPN} and W[PKPN]['HUDName'] == 'PKP-N' and W[PKPN]['CQC'] and A[R_PKPN]['Damage'] == 2.4 and A[R_PKPN]['MinimalRange'] == 0, 'PKP-N')
    ok(rounds(PKP) == {r_pkp} and W[PKP]['CQC'] and A[r_pkp]['Damage'] == 2.1 and A[r_pkp]['MinimalRange'] == 0, ('PKP', rounds(PKP)))
    ok(not carried(PULEM, PKP) and carried(PULEM, PKPN), 'Pulemetchiki on PKP-N')
    ok(rounds(PKM) == {R_PK_T1} and W[PKM]['CQC'] and A[R_PK_T1]['Damage'] == 1.8 and A[R_PK_T1]['MinimalRange'] == 0, ('PKM', rounds(PKM)))
    ok({W[r['WeaponId']]['HUDName'] for r in live('WeaponAmmunitionsJson') if r['AmmunitionId'] == R_PK_T1 and carried(r['UnitId'], r['WeaponId'])} == {'PKM'}, 'round 75 only PKM')
    ok(A[R_762x51_T1]['MinimalRange'] == 5.0, 'Ksp 58B / MG3 round 153 unchanged')
    ok(rounds(RAHE) == {R_556_T1} and A[R_556_T2]['Damage'] == 1.5, ('R-20 Rahe', rounds(RAHE)))
    ok(A[R_PARA_T2]['Damage'] == 2.4, 'M249 Para T2 2.4')
    ok(all(w not in W or not W[w] for w in REMOVE_W) and all(a not in A or not A[a] for a in REMOVE_A), 'removed')
    rec['infantry_tiers_1126'] = {'swaps': log, 'pkp_round': r_pkp, 'removed_rows': gone, 'removed_weapons': list(REMOVE_W), 'removed_rounds': list(REMOVE_A)}
    print('INFANTRY TIERS', rec['infantry_tiers_1126'])
    rec['weapon_coverage_rows'] = weapon_coverage_check.check(t, patches, ok)

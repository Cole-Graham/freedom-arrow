"""Reserve Marines prices and Standard loadout kit; China Marines price (Lateralus 26 Nov 2026 17:3x PST, thread 1568104480459722894, "Queue it up").
- Reserve Marines (407): 65 -> 70 points.
- Its "Standard" loadout (option 1842, swaps the card to unit 59 'Marines', which has no card of its own): 75 -> 85 points. The deck editor shows
  base + option and the Arsenal overview shows the swap row's own Cost, so option 1842 Cost 10 -> 15 and unit 59 Cost 75 -> 85 (swap-row rule,
  audit_swap_prices.py).
- Standard kit: M27 IAR x13 -> x11 and 2 M240L. Two plain riflemen (members 181, 182: M27 IAR only) take the M240L (weapon 63, the one infantry
  M240L; round 390, 400 rounds each, as on Troopers AA, CAAT Dragon and Weapons Squad). Head count and HP unchanged (squad-swap rule).
  New rows: one SquadWeapons and one WeaponAmmunitions row for the M240L on unit 59, copied from unit 59's M27 IAR rows.
- "M240L soldiers die last": they get DeathPriority 1 and every other member of unit 59 moves up by one (1..4 -> 2..5), so nobody ties with them and
  the order of the others stays. Card list order: M27 IAR 1, M240L 2, M320 2 -> 3, AT4CS-RS 3 -> 4 (rifle, MG, grenade launcher, launcher).
- Marines 陆战队 (1192, China PLAN): 65 -> 60 points. No loadout option and no swap row.
"""

RESERVE, STD_OPT, STD_UNIT, CN_MARINES = 407, 1842, 59, 1192
M240L, M240L_ROUND, M240L_QTY = 63, 390, 400
MG_MEN = (181, 182)


def apply(t, g, ok, rec):
    U, O, W, SM, SW, WA = (t[k] for k in ('Units', 'OptionsJson', 'WeaponsJson', 'SquadMembersJson', 'SquadWeaponsJson', 'WeaponAmmunitionsJson'))
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok(U[RESERVE]['HUDName'].strip() == 'Reserve Marines' and U[RESERVE]['Cost'] == 65 and not U[RESERVE].get('OriginalCost'), ('Reserve Marines', U[RESERVE]['Cost']))
    ok(O[STD_OPT].get('ReplaceUnitId') == STD_UNIT and O[STD_OPT].get('Cost') == 10 and U[STD_UNIT]['HUDName'].strip() == 'Marines' and U[STD_UNIT]['Cost'] == 75,
       ('Standard loadout', O[STD_OPT].get('Cost'), U[STD_UNIT]['Cost']))
    ok(not [o for o in O.values() if o and o.get('ReplaceUnitId') == STD_UNIT and o['Id'] != STD_OPT], 'unit 59 is swapped in only by the Reserve Marines Standard loadout')
    ok(U[CN_MARINES]['HUDName'].strip() == 'Marines 陆战队' and U[CN_MARINES]['Cost'] == 65 and not U[CN_MARINES].get('OriginalCost')
       and not [o for o in O.values() if o and o.get('ReplaceUnitId') == CN_MARINES], ('China Marines', U[CN_MARINES]['Cost']))
    ok(W[M240L]['HUDName'] == 'M240L' and {r['AmmunitionId'] for r in rows('WeaponAmmunitionsJson', WeaponId=M240L)} == {M240L_ROUND}, 'M240L 63 fires round 390')
    men = rows('SquadMembersJson', UnitId=STD_UNIT)
    m27 = {r['PrimaryWeaponId'] for r in men}
    ok(len(men) == 13 and len(m27) == 1 and W[next(iter(m27))]['HUDName'] == 'M27 IAR', ('Standard kit: 13 M27 IAR', len(men), m27))
    m27 = next(iter(m27))
    ok(all(SM[i]['UnitId'] == STD_UNIT and SM[i]['PrimaryWeaponId'] == m27 and not SM[i].get('SpecialWeaponId') for i in MG_MEN), ('plain riflemen', MG_MEN))
    sw = {W[r['WeaponId']]['HUDName']: r for r in rows('SquadWeaponsJson', UnitId=STD_UNIT)}
    ok({k: r.get('Order') for k, r in sw.items()} == {'M27 IAR': 1, 'M320': 2, 'AT4CS-RS': 3}, ('Standard card order', {k: r.get('Order') for k, r in sw.items()}))
    m27_wa = rows('WeaponAmmunitionsJson', UnitId=STD_UNIT, WeaponId=m27)
    ok(len(m27_wa) == 1 and not rows('WeaponAmmunitionsJson', UnitId=STD_UNIT, WeaponId=M240L), 'unit 59: one M27 IAR ammo row, no M240L yet')

    g.put('Units', RESERVE, {'Cost': 70})
    g.put('OptionsJson', STD_OPT, {'Cost': 15})
    g.put('Units', STD_UNIT, {'Cost': 85})
    g.put('Units', CN_MARINES, {'Cost': 60})
    for r in men:
        g.put('SquadMembersJson', r['Id'], {'PrimaryWeaponId': M240L, 'DeathPriority': 1} if r['Id'] in MG_MEN else {'DeathPriority': r['DeathPriority'] + 1})
    g.put('SquadWeaponsJson', sw['M320']['Id'], {'Order': 3})
    g.put('SquadWeaponsJson', sw['AT4CS-RS']['Id'], {'Order': 4})
    nsw = g.add('SquadWeaponsJson', sw['M27 IAR'], {'WeaponId': M240L, 'Order': 2})
    nwa = g.add('WeaponAmmunitionsJson', m27_wa[0], {'WeaponId': M240L, 'AmmunitionId': M240L_ROUND, 'Quantity': M240L_QTY})

    men = rows('SquadMembersJson', UnitId=STD_UNIT)
    kit = sorted((W[r['PrimaryWeaponId']]['HUDName'], r['DeathPriority']) for r in men)
    ok(sum(r['PrimaryWeaponId'] == m27 for r in men) == 11 and sorted(r['Id'] for r in men if r['PrimaryWeaponId'] == M240L) == list(MG_MEN), 'Standard: 11 M27 IAR + 2 M240L')
    ok(all(r['DeathPriority'] == 1 for r in men if r['PrimaryWeaponId'] == M240L) and all(r['DeathPriority'] >= 2 for r in men if r['PrimaryWeaponId'] != M240L),
       'M240L men die last')
    ok(U[RESERVE]['Cost'] + O[STD_OPT]['Cost'] == U[STD_UNIT]['Cost'] == 85 and U[CN_MARINES]['Cost'] == 60, 'prices applied')
    rec['marines_prices_1126'] = {'Reserve Marines': '65 -> 70', 'Standard loadout': '75 -> 85 (option 10 -> 15, unit 59 75 -> 85)',
                                  'Standard kit': 'M27 IAR 13 -> 11, M240L 0 -> 2 (400 rounds each, die last)', 'Marines 陆战队': '65 -> 60',
                                  'new_rows': {'SquadWeaponsJson': nsw, 'WeaponAmmunitionsJson': nwa}, 'kit': kit}
    print('MARINES PRICES', rec['marines_prices_1126'])

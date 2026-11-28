"""PF-89B (Osama 28 Nov 2026 01:4x PST, thread 1567745029781454889: "PF-89B added as a new weapon for China, copy of the AT-4 found on AT riflemen
with 750mm penetration. this replaces the PF-89 on marines (china). This also replaces Airborne's PF-98.").
- New weapon 'PF-89B' = a copy of the vanilla AT4CS HP (631, Troopers AT / Airborne / Rangers RRC; disposable). It fires the AT4CS HP's own round
  '84mm Tandem' (2000139: 750 / 750 mm, damage 10, 200 world = 400 card m), reused rather than copied (no-redundant-ammo rule, Lateralus 26 Nov).
- Marines 陆战队 (1192): the 6 PF-89 carriers carry the PF-89B instead (1 per carrier, as the PF-89 and the AT4CS HP).
- Airborne 空降兵 (1136): the leader's PF-98 (6 rounds, reusable) -> PF-89B (disposable, 1 round, as every AT4CS HP carrier).
Only these two squads; every other PF-89 / PF-98 squad is unchanged. In the plb scope (adds a weapon row). Model: the copied AT4CS HP's game model
'AT-4' (the PF-89 has no PLA model either: it uses the game's RPG-26), so no FAModels rule is needed."""
AT4HP, TANDEM, MAR, ABN = 631, 2000139, 1192, 1136


def apply(t, g, ok, rec):
    U, W, A, SM, SW, WA = (t[k] for k in ('Units', 'WeaponsJson', 'AmmunitionsJson', 'SquadMembersJson', 'SquadWeaponsJson', 'WeaponAmmunitionsJson'))
    rows = lambda tab, **kw: sorted((r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())), key=lambda r: r['Id'])
    hud = lambda h: [i for i, w in W.items() if w and w.get('HUDName') == h]
    kit = lambda u: sorted(W[m['PrimaryWeaponId']]['HUDName'] + (' + ' + W[m['SpecialWeaponId']]['HUDName'] if m.get('SpecialWeaponId') else '') for m in rows('SquadMembersJson', UnitId=u))
    ammo = lambda u: sorted((W[r['WeaponId']]['HUDName'], A[r['AmmunitionId']]['HUDName'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=u))
    ok(W[AT4HP]['HUDName'] == 'AT4CS HP' and A[TANDEM]['HUDName'] == '84mm Tandem' and A[TANDEM]['PenetrationAtMinRange'] == A[TANDEM]['PenetrationAtGroundRange'] == 750.0, 'AT4CS HP 631, 84mm Tandem 750 mm')
    ok(sorted({r['AmmunitionId'] for r in WA.values() if r and r['WeaponId'] == AT4HP}) == [TANDEM], 'AT4CS HP fires only 84mm Tandem')
    ok(not hud('PF-89B'), 'PF-89B name free')
    ok(U[MAR]['HUDName'] == 'Marines 陆战队' and U[ABN]['HUDName'] == 'Airborne 空降兵', 'Marines 1192 / Airborne 1136')
    before = {'Marines': (kit(MAR), ammo(MAR)), 'Airborne': (kit(ABN), ammo(ABN))}
    (pf89,) = [i for i in hud('PF-89') if any(m.get('SpecialWeaponId') == i for m in rows('SquadMembersJson', UnitId=MAR))]
    (pf98,) = [i for i in hud('PF-98') if any(m.get('SpecialWeaponId') == i for m in rows('SquadMembersJson', UnitId=ABN))]
    ok(sum(m.get('SpecialWeaponId') == pf89 for m in rows('SquadMembersJson', UnitId=MAR)) == 6, 'Marines: 6 PF-89 carriers')
    ok(sum(m.get('SpecialWeaponId') == pf98 for m in rows('SquadMembersJson', UnitId=ABN)) == 1, 'Airborne: 1 PF-98 carrier')
    nw = g.add('WeaponsJson', W[AT4HP], {'Name': 'PLA infantry PF-89B (AT4CS HP copy)', 'HUDName': 'PF-89B'})
    for unit, old in ((MAR, pf89), (ABN, pf98)):
        for m in rows('SquadMembersJson', UnitId=unit):
            if m.get('SpecialWeaponId') == old: g.put('SquadMembersJson', m['Id'], {'SpecialWeaponId': nw})
        for r in rows('SquadWeaponsJson', UnitId=unit, WeaponId=old): g.put('SquadWeaponsJson', r['Id'], {'WeaponId': nw})
        wa = rows('WeaponAmmunitionsJson', UnitId=unit, WeaponId=old)
        g.put('WeaponAmmunitionsJson', wa[0]['Id'], {'WeaponId': nw, 'AmmunitionId': TANDEM, 'Quantity': 1})
        for r in wa[1:]: g.remove('WeaponAmmunitionsJson', r['Id'])
    after = {'Marines': (kit(MAR), ammo(MAR)), 'Airborne': (kit(ABN), ammo(ABN))}
    for unit, old in ((MAR, pf89), (ABN, pf98)):
        men = rows('SquadMembersJson', UnitId=unit); carried = {x for m in men for x in (m['PrimaryWeaponId'], m.get('SpecialWeaponId')) if x}
        ok(old not in carried and nw in carried, (unit, 'old launcher gone, PF-89B carried'))
        ok({r['WeaponId'] for r in rows('SquadWeaponsJson', UnitId=unit)} == carried == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=unit)}, (unit, 'card + ammo = carried'))
    ok(sum(k.endswith('+ PF-89B') for k in after['Marines'][0]) == 6 and sum(k.endswith('+ PF-89B') for k in after['Airborne'][0]) == 1, ('carriers after', after))
    ok([len(before[k][0]) for k in before] == [len(after[k][0]) for k in after], 'same men')
    rec['osama_pf89b_1128'] = {'weapon': nw, 'round': TANDEM, 'replaced': {'Marines': 'PF-89', 'Airborne': 'PF-98'}, 'before': before, 'after': after}
    print('PF-89B', rec['osama_pf89b_1128'])

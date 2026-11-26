"""Type 100 CSV: CH-901 loadout rows in the same tab as their base, and new CH-901 prices (Osama 24 Nov 2026 23:4x PST, bugs thread 1573561286803980289:
"right that makes sense, also make the CH-901 +60 and CH w/ APS +100").
SteelPlate (24 Nov 22:5x, Coal Mountain): could not bring more Type 100 transports. In 0.9.6 the base rows ('PLA ZBD-100', '... transport') and their
APS swaps are CategoryType 0 (Recon) but the CH-901 swaps are CategoryType 2 (Vehicles): they were copied from the old Vehicle-tab CH-901 unit. Every
vanilla swap row keeps its base's CategoryType (about 150 swaps, vanilla tables). Suspected cause of the in-match count, not proven in game.
- CH-901 swap rows (both families) -> the base's CategoryType.
- Options: '9x CH-901' 40 -> 60, '9x CH-901 + GL-5 APS' 80 -> 100; swap row Cost = base Cost + option (swap-row-prices rule).
- Front KE armour -> 500 (Osama 23:4x "and make the frontal KE armor 500") on the Type 100's own armour row (zbd100.py; no other unit uses it)."""
FAMILIES = ('PLA ZBD-100', 'PLA ZBD-100 transport')
FRONT_KE = 500
PRICE = {'9x CH-901': 60, '9x CH-901 + GL-5 APS': 100}


def apply(t, g, ok, rec):
    U, M, O = t['Units'], t['ModificationsJson'], t['OptionsJson']
    out = {}
    for name in FAMILIES:
        (b,) = [i for i, u in U.items() if u and u.get('Name') == name and not u.get('IsUnitModification')]
        (mod,) = [m for m in M.values() if m and m['UnitId'] == b and m['Type'] == 3]
        opts = sorted((o for o in O.values() if o and o['ModificationId'] == mod['Id']), key=lambda o: o['Order'])
        ok([o['UIName'] for o in opts] == ['40 mm CT', '40 mm CT + GL-5 APS', '9x CH-901', '9x CH-901 + GL-5 APS'], (name, 'four-way loadout'))
        cat, base_cost = U[b]['CategoryType'], U[b]['Cost']
        before = [(o['UIName'], o['Cost'], U[o['ReplaceUnitId']]['CategoryType'], U[o['ReplaceUnitId']]['Cost']) for o in opts]
        for o in opts:
            r = o['ReplaceUnitId']
            if o['UIName'] in PRICE:
                g.put('OptionsJson', o['Id'], {'Cost': PRICE[o['UIName']]})
                g.put('Units', r, {'CategoryType': cat, 'Cost': base_cost + PRICE[o['UIName']]})
        after = [(o['UIName'], O[o['Id']]['Cost'], U[o['ReplaceUnitId']]['CategoryType'], U[o['ReplaceUnitId']]['Cost']) for o in opts]
        ok(all(c == cat for _, _, c, _ in after), (name, 'every loadout row in the base tab', after))
        ok(all(uc == base_cost + oc for _, oc, _, uc in after), (name, 'swap row Cost = base + option', after))
        ok([a[1] for a in after] == [0, 40, 60, 100], (name, 'option prices 0 / 40 / 60 / 100', after))
        out[name] = {'before': before, 'after': after}
    fam = {i for i, u in U.items() if u and (u.get('Name') or '').startswith('PLA ZBD-100')}
    arms = {r['ArmorId'] for r in t['UnitArmorsJson'].values() if r and r['UnitId'] in fam}
    ok(len(fam) == 8 and len(arms) == 1, ('Type 100: 8 rows, one armour row', sorted(fam), arms))
    (arm,) = arms
    others = {r['UnitId'] for r in t['UnitArmorsJson'].values() if r and r['ArmorId'] == arm} - fam
    ok(not others, ('Type 100 armour row used by no other unit', others))
    A = t['ArmorsJson']; ke_before = A[arm]['KinArmorFront']
    g.put('ArmorsJson', arm, {'KinArmorFront': FRONT_KE})
    ok(A[arm]['KinArmorFront'] == FRONT_KE, 'Type 100 front KE 500')
    out['armour'] = {'row': arm, 'KinArmorFront': [ke_before, FRONT_KE], 'row_now': {k: v for k, v in A[arm].items() if 'Armor' in k or k == 'MaxHealthPoints'}}
    # Type100ShopFix.cs (focolate's fix, Osama 26 Nov "Definitely port it") hard-codes transport 1416 and options 31361/31362/31363 ->
    # units 1417/1418/1419. Fail the build if the data drifts from those IDs.
    (tb,) = [i for i, u in U.items() if u and u.get('Name') == 'PLA ZBD-100 transport' and not u.get('IsUnitModification')]
    (tm,) = [m for m in M.values() if m and m['UnitId'] == tb and m['Type'] == 3]
    swaps = {o['Id']: o['ReplaceUnitId'] for o in O.values() if o and o['ModificationId'] == tm['Id'] and o['Order']}
    ok(tb == 1416 and swaps == {31361: 1417, 31362: 1418, 31363: 1419}, ('Type100ShopFix IDs match the data', tb, swaps))
    rec['type100_cat_price_1124'] = out
    print('TYPE100 CAT+PRICE', out)

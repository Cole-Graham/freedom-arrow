"""Lynx Howitzer and Lynx 120 mm Mortar (Osama 25 Nov 2026 03:1x PST, thread 1567745029781454889).
- "Lynx Howitzer should be 80 points but have 3600 max range and v:200/h:150 dispersion (same as hawkeye). Supply weight is 40kg per shell":
  1436, 60 -> 80 pts. Its two rounds were shared with the PLL-05 (2009463 HE, 2018957 smoke), so it gets its own copies: GroundRange 1575 ->
  1800 (the card shows 2x: 3600 m), dispersion H 60 -> 75, V 60 -> 100 (the Hawkeye's 105 mm rounds; card H 150 / V 200), SupplyCost 20 -> 40
  (the card's supply weight in kg). The PLL-05 keeps the old rounds.
- "Lynx 120mm mortar, 8 smoke rounds, 65 points": 1435, smoke row 5 -> 8 rounds, 70 -> 65 pts."""
HOW, MOR, HAWK_HE = 1436, 1435, 37


def apply(t, g, ok, rec):
    U, WA, A = t['Units'], t['WeaponAmmunitionsJson'], t['AmmunitionsJson']
    rows = lambda uid: sorted([r for r in WA.values() if r and r['UnitId'] == uid], key=lambda r: r['Id'])
    ok(U[HOW]['HUDName'] == 'Lynx Howitzer' and U[HOW]['Cost'] == 60 and U[MOR]['HUDName'] == 'Lynx 120mm Mortar' and U[MOR]['Cost'] == 70, 'Lynx Howitzer 60 / Mortar 70')
    ok(A[HAWK_HE]['Name'] == 'Shell 105 M20 HE' and (A[HAWK_HE]['DispersionHorizontalRadius'], A[HAWK_HE]['DispersionVerticalRadius']) == (75.0, 100.0), 'Hawkeye 105 HE dispersion 75 / 100')
    hw = rows(HOW)
    ok([A[r['AmmunitionId']]['HUDName'] for r in hw] == ['120 mm gun-mortar ammunition', '120 mm smoke'] and all(A[r['AmmunitionId']]['GroundRange'] == 1575 for r in hw), ('Howitzer rounds', hw))
    new = {}
    for r in hw:
        a = A[r['AmmunitionId']]
        n = g.add('AmmunitionsJson', a, {'Name': 'PLA Lynx Howitzer ' + a['HUDName'], 'GroundRange': 1800.0, 'DispersionHorizontalRadius': 75.0,
                                         'DispersionVerticalRadius': 100.0, 'SupplyCost': 40.0})
        g.put('WeaponAmmunitionsJson', r['Id'], {'AmmunitionId': n}); new[a['Id']] = n
    ok(all(any(x and x['UnitId'] != HOW and x['AmmunitionId'] == old for x in WA.values()) for old in new), 'PLL-05 keeps the old rounds')
    g.put('Units', HOW, {'Cost': 80})
    mw = rows(MOR); smoke = [r for r in mw if A[r['AmmunitionId']]['HUDName'] == '120mm smoke']
    ok(len(mw) == 2 and len(smoke) == 1 and smoke[0]['Quantity'] == 5, ('Mortar smoke row', mw))
    g.put('WeaponAmmunitionsJson', smoke[0]['Id'], {'Quantity': 8})
    g.put('Units', MOR, {'Cost': 65})
    rec['lynx_arty_1125'] = {'howitzer': {'cost': [60, 80], 'rounds': new}, 'mortar': {'cost': [70, 65], 'smoke_row': smoke[0]['Id'], 'smoke': [5, 8]}}
    print('LYNX ARTY', rec['lynx_arty_1125'])

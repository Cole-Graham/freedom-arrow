"""Lynx 81 mm Mortar: the Hawkeye MWS's range and dispersion, 60 pts (Osama 25 Nov 2026 03:2x PST, thread 1567745029781454889: "Lynx 81mm
mortar. Give it Hawkeye MWS range and dispersion. make this 60 pts").
1434 'Lynx 81mm Mortar', 50 -> 60 pts. Its indirect rounds were vanilla rows shared with other units (410 82mm HE, 136 82mm smoke), so it gets
its own copies with the Hawkeye 105 mm HE values: GroundRange 1125 / 1350 -> 1850 (card 3700 m), dispersion H 40 -> 75, V 40 -> 100 (card
150 / 200). The direct-fire 82mm HEAT round (600 m) is not artillery fire and stays. Creates rows: after every other row-creating section."""
M81, HAWK_HE = 1434, 37


def apply(t, g, ok, rec):
    U, WA, A = t['Units'], t['WeaponAmmunitionsJson'], t['AmmunitionsJson']
    ok(U[M81]['HUDName'] == 'Lynx 81mm Mortar' and U[M81]['Cost'] == 50 and U[50]['HUDName'] == 'Hawkeye MWS', 'Lynx 81mm Mortar 50 pts; Hawkeye MWS')
    h = A[HAWK_HE]
    ok(h['Name'] == 'Shell 105 M20 HE' and (h['GroundRange'], h['DispersionHorizontalRadius'], h['DispersionVerticalRadius']) == (1850.0, 75.0, 100.0), 'Hawkeye 105 HE 1850 / 75 / 100')
    rows = sorted([r for r in WA.values() if r and r['UnitId'] == M81], key=lambda r: r['Id'])
    ind = [r for r in rows if A[r['AmmunitionId']]['HUDName'] in ('82mm HE', '82mm smoke')]
    ok(len(rows) == 3 and len(ind) == 2, ('81 mm rows', [(A[r['AmmunitionId']]['HUDName'], r['Quantity']) for r in rows]))
    new = {}
    for r in ind:
        a = A[r['AmmunitionId']]
        n = g.add('AmmunitionsJson', a, {'Name': 'PLA Lynx 81mm Mortar ' + a['HUDName'], 'GroundRange': h['GroundRange'],
                                         'DispersionHorizontalRadius': h['DispersionHorizontalRadius'], 'DispersionVerticalRadius': h['DispersionVerticalRadius']})
        g.put('WeaponAmmunitionsJson', r['Id'], {'AmmunitionId': n}); new[a['Id']] = n
    ok(all(any(x and x['UnitId'] != M81 and x['AmmunitionId'] == old for x in WA.values()) for old in new), 'other users keep the vanilla rounds')
    g.put('Units', M81, {'Cost': 60})
    rec['lynx_m81_1125'] = {'unit': M81, 'cost': [50, 60], 'rounds': new}
    print('LYNX 81', rec['lynx_m81_1125'])

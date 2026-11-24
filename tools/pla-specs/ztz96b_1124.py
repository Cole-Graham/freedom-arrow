"""ZTZ-96B front armour and price (Osama 24 Nov 2026 01:25 PST, thread "blue dragons"; he wrote "ztz-99B" and confirmed 01:3x "96B not 99B"):
same front armour as the ZTZ-96A and lowered to 195 points. The ZTZ-99A (904) and its 99B APS loadouts are not changed.
- ZTZ-96B armour row 2009091 (905 only): front KE 650 -> 600, HEAT 850 -> 600 = ZTZ-96A (1082, row 2011345). Sides, rear, top unchanged.
- ZTZ-96B 220 -> 195 pts."""
UID, ROW, REF, REFROW, COST = 905, 2009091, 1082, 2011345, 195


def apply(t, g, ok, rec):
    U, A = t['Units'], t['ArmorsJson']
    ok(U[UID]['Name'] == 'PLA ZTZ-96B' and U[UID]['Cost'] == 220 and U[REF]['HUDName'] == 'ZTZ-96A', 'ZTZ-96B 905 (220 pts), ZTZ-96A 1082')
    ok([r['ArmorId'] for r in t['UnitArmorsJson'].values() if r and r['UnitId'] == UID] == [ROW]
       and [r['UnitId'] for r in t['UnitArmorsJson'].values() if r and r['ArmorId'] == ROW] == [UID], 'ZTZ-96B armour row 2009091, 905 only')
    ok([r['ArmorId'] for r in t['UnitArmorsJson'].values() if r and r['UnitId'] == REF] == [REFROW], 'ZTZ-96A armour row 2011345')
    before = {k: A[ROW][k] for k in ('KinArmorFront', 'HeatArmorFront')}
    ok(before == {'KinArmorFront': 650, 'HeatArmorFront': 850}, ('ZTZ-96B front before', before))
    g.put('ArmorsJson', ROW, {k: A[REFROW][k] for k in before})
    g.put('Units', UID, {'Cost': COST})
    after = {k: A[ROW][k] for k in before}
    ok(after == {k: A[REFROW][k] for k in before} == {'KinArmorFront': 600, 'HeatArmorFront': 600} and U[UID]['Cost'] == COST, ('ZTZ-96B front = ZTZ-96A, 195', after))
    rec['ztz96b_1124'] = {'unit': UID, 'front_before': before, 'front_after': after, 'cost': [220, COST]}
    print('ZTZ-96B', rec['ztz96b_1124'])

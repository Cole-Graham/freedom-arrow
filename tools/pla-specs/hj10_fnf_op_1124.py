"""HJ-10 FNF round overpressure 0 -> 0.5 (Osama 24 Nov 2026 21:3x PST, bugs thread 1573561286803980289: "can you give the HJ-10 a 0.5m overpressure
range too"). The HJ-10 NLOS round 2009623 is already 0.5 (qq_sheet_fixes_1123.py, 23 Nov); this matches the FNF option's round to it."""
ROUND = 2019706


def apply(t, g, ok, rec):
    A, WA, U = t['AmmunitionsJson'], t['WeaponAmmunitionsJson'], t['Units']
    a = A[ROUND]
    users = sorted({U[r['UnitId']]['HUDName'] for r in WA.values() if r and r['AmmunitionId'] == ROUND and r['UnitId'] in U})
    ok(a['HUDName'] == 'HJ-10 FNF' and a.get('OverpressureRadius') == 0.0 and users == ['HJ-10'], ('HJ-10 FNF round, HJ-10 only, OP 0', users))
    ok(A[2009623].get('OverpressureRadius') == 0.5, 'HJ-10 NLOS round already 0.5')
    rest = {k: v for k, v in a.items() if k != 'OverpressureRadius'}
    g.put('AmmunitionsJson', ROUND, {'OverpressureRadius': 0.5})
    ok(A[ROUND]['OverpressureRadius'] == 0.5 and {k: v for k, v in A[ROUND].items() if k != 'OverpressureRadius'} == rest, 'HJ-10 FNF OP 0.5, nothing else')
    rec['hj10_fnf_op_1124'] = {'round': ROUND, 'overpressure': [0.0, 0.5]}

"""Hand-held QLZ-87 range 800 -> 700 card m (Osama 27 Nov 2026 17:4x PST, thread 1567745029781454889: "handheld QLZ-87 is 700m range" / "the one
on falcons"). The squad QLZ-87 (weapon 3000005: Falcons 1185, Tiger Brigade 6002) shares round 2012158 with the tripod 'QLZ-87 (tripod)'
(2012157: QLZ-87 Team, Airborne QLZ-87 Team), which keeps 800 m. So the hand-held one gets its own copy of that round, GroundRange 400 -> 350,
everything else equal (a different stat, so not a redundant row). In the plb scope (adds a row)."""
SQUAD_W, ROUND, TRIPOD_W = 3000005, 2012158, 2012157


def apply(t, g, ok, rec):
    U, W, A, WA = t['Units'], t['WeaponsJson'], t['AmmunitionsJson'], t['WeaponAmmunitionsJson']
    rows = [r for r in WA.values() if r and r['WeaponId'] == SQUAD_W]
    ok(W[SQUAD_W]['HUDName'] == 'QLZ-87' and W[TRIPOD_W]['HUDName'] in ('QLZ-87', 'QLZ-87 (tripod)') and A[ROUND]['GroundRange'] == 400.0, 'QLZ-87 rows as read')
    ok(rows and all(r['AmmunitionId'] == ROUND for r in rows), ('hand-held QLZ-87 fires 2012158', [r['AmmunitionId'] for r in rows]))
    a = g.add('AmmunitionsJson', A[ROUND], {'Name': 'PLA infantry QLZ-87 hand-held 35 mm HE-fragmentation', 'GroundRange': 350.0})
    for r in rows: g.put('WeaponAmmunitionsJson', r['Id'], {'AmmunitionId': a})
    ok(A[ROUND]['GroundRange'] == 400.0 and {r['UnitId'] for r in WA.values() if r and r['AmmunitionId'] == ROUND} >= {1171, 1148}, 'tripod keeps 800 m')
    rec['pla_light_brigade_qlz87_range_1127'] = {'round': a, 'range_m': [800, 700], 'units': sorted({r['UnitId'] for r in rows})}
    print('QLZ-87 HAND-HELD', rec['pla_light_brigade_qlz87_range_1127'])

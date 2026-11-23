"""Lateralus 23 Nov 2026 14:4x PST, thread 1568104480459722894: "Thermobaric Assault infantry PF-97 ammo needs to be corrected from 3 -> 6".
Called from batch_0_9_5b.py.
Thermobaric Assault 温压突击 (unit 1209) has 3 PF-97 carriers and its own ammo row (WeaponAmmunitions 2015630, PF-97 round 2012516,
Quantity 1, HUDMultiplier 1). The squad's PF-97 pool is Quantity x carriers (docs/engine/infantry-ammo.md), so 1 -> 2 per carrier gives
3 -> 6. The row belongs to this unit only; the other thermobaric squads (1162 Breachers 5 x 1, 1195 Marine Engineers 2 x 1) are unchanged."""


def apply(t, g, ok, rec):
    U, SM, WA, A = t['Units'], t['SquadMembersJson'], t['WeaponAmmunitionsJson'], t['AmmunitionsJson']
    ok(U[1209]['HUDName'].strip().startswith('Thermobaric Assault'), ('unit 1209 is Thermobaric Assault', U[1209]['HUDName']))
    carriers = sum(1 for m in SM.values() if m and m.get('UnitId') == 1209 and 2012515 in (m.get('PrimaryWeaponId'), m.get('SpecialWeaponId')))
    rows = [r for r in WA.values() if r and r.get('UnitId') == 1209 and r.get('WeaponId') == 2012515]
    ok(carriers == 3 and [r['Id'] for r in rows] == [2015630] and rows[0]['Quantity'] == 1, ('Thermobaric Assault PF-97: 3 carriers x 1', carriers, rows))
    ok(A[rows[0]['AmmunitionId']].get('HUDMultiplier', 1) in (1, None), ('PF-97 round HUD multiplier 1', A[rows[0]['AmmunitionId']].get('HUDMultiplier')))
    g.put('WeaponAmmunitionsJson', 2015630, {'Quantity': 2})
    ok(WA[2015630]['Quantity'] * carriers == 6, 'Thermobaric Assault PF-97 pool 6')
    rec['thermobaric_pf97_1123'] = {'unit': 1209, 'weapon_ammo_row': 2015630, 'quantity': [1, 2], 'pool': [3, 6]}

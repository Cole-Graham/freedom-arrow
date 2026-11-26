"""KS-23 slug and GM-94 thermobaric grenade base damage (Lateralus 25 Nov 2026 19:0x PST, thread 1572962048705429598:
"lower ks-23 base damage from 4.99 -> 3.5", "lower GM-94 base damage from 5 -> 3"). Existing vanilla rows only, no new rows.
Every weapon that fires these rounds follows. Round 914 = KS-23 4ga SLUG, round 911 = GM-94 43x30 thermobaric."""
ROUNDS = {914: ('InfBullet 4Gauge SLUG KS23 T2', 4.99, 3.5), 911: ('InfGrenade 43x30 GM94 (Thermobaric)', 5.0, 3.0)}


def apply(t, g, ok, rec):
    A, W, WA, U = t['AmmunitionsJson'], t['WeaponsJson'], t['WeaponAmmunitionsJson'], t['Units']
    for i, (name, before, after) in ROUNDS.items():
        ok(A[i]['Name'].strip() == name and A[i]['Damage'] == before, ('round before', i, A[i]['Name'], A[i]['Damage']))
        g.put('AmmunitionsJson', i, {'Damage': after})
        ok(A[i]['Damage'] == after, ('round after', i))
    users = {i: sorted({(U[r['UnitId']]['HUDName'].strip(), W[r['WeaponId']]['HUDName'].strip()) for r in WA.values()
                        if r and r.get('AmmunitionId') == i and r.get('UnitId') in U and r.get('WeaponId') in W}) for i in ROUNDS}
    rec['ks23_gm94_damage_1125'] = {str(i): {'damage': ROUNDS[i][1:], 'users': users[i]} for i in ROUNDS}
    print('KS-23 / GM-94 DAMAGE', rec['ks23_gm94_damage_1125'])

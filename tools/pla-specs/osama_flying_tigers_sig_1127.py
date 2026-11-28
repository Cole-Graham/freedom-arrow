"""Osama 27 Nov 2026 22:0x PST, thread 1567745029781454889: "flying tigers remove 1 shotgun, add 1 more sig516". Flying Tigers (1187) keep 6 men,
55 pts, armour and cards; one of the two plain SPAS-12 men now carries the SIG 516 (squad-swap-keeps-headcount rule). Kit after: leader SIG 516 +
ARWEN 37; SIG 516 + SPAS-12; SIG 516 + ARWEN 37 Smoke; SIG 516; SPAS-12; MP5SD6. Ammunition per man unchanged (SIG 516 160, SPAS-12 96), so
the squad pool follows the carriers. Death priority unchanged (2). Put-only: after the plb scope."""
FT = 1187


def apply(t, g, ok, rec):
    U, W, SM = t['Units'], t['WeaponsJson'], t['SquadMembersJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    hud = lambda h: [i for i, w in W.items() if w and w.get('HUDName') == h]
    (sig,), (spas,) = hud('SIG 516'), hud('SPAS-12')
    kit = lambda: sorted(W[m['PrimaryWeaponId']]['HUDName'] + (' + ' + W[m['SpecialWeaponId']]['HUDName'] if m.get('SpecialWeaponId') else '') for m in rows('SquadMembersJson', UnitId=FT))
    before = kit()
    plain = [m for m in rows('SquadMembersJson', UnitId=FT) if m['PrimaryWeaponId'] == spas and not m.get('SpecialWeaponId')]
    ok(U[FT]['HUDName'] == 'Flying Tigers' and len(rows('SquadMembersJson', UnitId=FT)) == 6 and len(plain) == 2, ('Flying Tigers: 6 men, two plain SPAS-12', before))
    g.put('SquadMembersJson', plain[-1]['Id'], {'PrimaryWeaponId': sig})
    after = kit()
    ok(sum(k.startswith('SIG 516') for k in after) == 4 and after.count('SPAS-12') == 1 and len(after) == 6 and U[FT]['Cost'] == 55, ('kit after', after))
    carried = {x for m in rows('SquadMembersJson', UnitId=FT) for x in (m['PrimaryWeaponId'], m.get('SpecialWeaponId')) if x}
    ok({r['WeaponId'] for r in rows('SquadWeaponsJson', UnitId=FT)} == carried == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=FT)}, 'card + ammo = carried')
    rec['osama_flying_tigers_sig_1127'] = {'member': plain[-1]['Id'], 'before': before, 'after': after}
    print('FLYING TIGERS SIG', rec['osama_flying_tigers_sig_1127'])

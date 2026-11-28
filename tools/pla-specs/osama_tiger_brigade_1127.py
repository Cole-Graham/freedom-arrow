"""Osama 27 Nov 2026 22:4x PST, thread 1567745029781454889: "new tiger brigade for marines" (his DPM-visualizer custom unit 'tiger test': 1 QBU-203,
3 QBZ-192, 3 QJY-201, 1 QLZ-87, 8 men, 80 pts, 40 HP, armour 8). Tiger Brigade 猛虎旅 (6002, PLAN & PLAGF Amphibious CAB) keeps 8 men, 80 pts,
armour and cards: the leader keeps his PF-98 (Osama 28 Nov 01:2x "you removed the AT weapons
and launchers of the infantry I reworked"; dev.9 had removed it); one plain QBZ-192 rifleman becomes a QJY-201 gunner (400 rounds per man as
the other two; death priority 4 -> 2, the vanilla MG rule). Put-only: after the plb scope."""
TB = 6002


def apply(t, g, ok, rec):
    U, W = t['Units'], t['WeaponsJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    hud = lambda h: [i for i, w in W.items() if w and w.get('HUDName') == h]
    kit = lambda: sorted(W[m['PrimaryWeaponId']]['HUDName'] + (' + ' + W[m['SpecialWeaponId']]['HUDName'] if m.get('SpecialWeaponId') else '') for m in rows('SquadMembersJson', UnitId=TB))
    before = kit()
    ok(U[TB]['HUDName'] == 'Tiger Brigade 猛虎旅' and U[TB]['Cost'] == 80 and before == ['QBU-203', 'QBZ-192', 'QBZ-192', 'QBZ-192', 'QBZ-192 + PF-98', 'QJY-201', 'QJY-201', 'QLZ-87'], ('Tiger Brigade kit before', before))
    (qjy,) = [w for w in hud('QJY-201') if any(m['PrimaryWeaponId'] == w for m in rows('SquadMembersJson', UnitId=TB))]
    (lead,) = [m for m in rows('SquadMembersJson', UnitId=TB) if m.get('SpecialWeaponId')]
    pf = lead['SpecialWeaponId']
    plain = [m for m in rows('SquadMembersJson', UnitId=TB) if W[m['PrimaryWeaponId']]['HUDName'] == 'QBZ-192' and m['Id'] != lead['Id']]
    g.put('SquadMembersJson', plain[-1]['Id'], {'PrimaryWeaponId': qjy, 'DeathPriority': 2})
    for i, r in enumerate(sorted(rows('SquadWeaponsJson', UnitId=TB), key=lambda r: r['Order']), 1):
        if r['Order'] != i: g.put('SquadWeaponsJson', r['Id'], {'Order': i})
    after = kit(); men = rows('SquadMembersJson', UnitId=TB)
    carried = {x for m in men for x in (m['PrimaryWeaponId'], m.get('SpecialWeaponId')) if x}
    ok(after == ['QBU-203', 'QBZ-192', 'QBZ-192', 'QBZ-192 + PF-98', 'QJY-201', 'QJY-201', 'QJY-201', 'QLZ-87'] and U[TB]['Cost'] == 80, ('kit after', after))
    ok({r['WeaponId'] for r in rows('SquadWeaponsJson', UnitId=TB)} == carried == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=TB)}, 'card + ammo = carried')
    rec['osama_tiger_brigade_1127'] = {'before': before, 'after': after, 'ammo_per_man': [(W[r['WeaponId']]['HUDName'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=TB)]}
    print('TIGER BRIGADE', rec['osama_tiger_brigade_1127'])

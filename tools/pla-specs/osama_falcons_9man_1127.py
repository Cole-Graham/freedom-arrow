"""Osama 27 Nov 2026 22:3x PST, thread 1567745029781454889: "change flacons to this configuration" then "sorry this one but lets make them 9 man"
(his DPM-visualizer custom unit 'falcons test': 5 QBZ-192, 2 QLU-11, 2 QLZ-87, 75 pts, armour 8). Falcons 猎鹰 (1185): 8 -> 9 men; the leader's
PF-98 is removed (weapon and ammo rows); a second QLZ-87 man is added (copy of the QLZ-87 man, 190 rounds per man as before); 85 -> 75 pts.
Health stays 5 per man: armour link -> an existing row equal to the current one but 45 HP (vanilla 277 'Armor Infantry Shock 9Men', 8 / 45; the
ability-row-reuse rule). Adds a squad member, so it runs in the plb scope, after the Falcons kit sections."""
FAL = 1185


def apply(t, g, ok, rec):
    U, W, AR, UA = t['Units'], t['WeaponsJson'], t['ArmorsJson'], t['UnitArmorsJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    hud = lambda h: [i for i, w in W.items() if w and w.get('HUDName') == h]
    kit = lambda: sorted(W[m['PrimaryWeaponId']]['HUDName'] + (' + ' + W[m['SpecialWeaponId']]['HUDName'] if m.get('SpecialWeaponId') else '') for m in rows('SquadMembersJson', UnitId=FAL))
    before = kit()
    ok(U[FAL]['HUDName'] == 'Falcons 猎鹰' and U[FAL]['Cost'] == 85 and len(before) == 8, ('Falcons 85 pts, 8 men', before))
    pf98 = [m for m in rows('SquadMembersJson', UnitId=FAL) if m.get('SpecialWeaponId') and W[m['SpecialWeaponId']]['HUDName'] == 'PF-98']
    ok(len(pf98) == 1, 'one PF-98 carrier'); pfw = pf98[0]['SpecialWeaponId']
    g.put('SquadMembersJson', pf98[0]['Id'], {'SpecialWeaponId': 0})
    for r in rows('SquadWeaponsJson', UnitId=FAL, WeaponId=pfw): g.remove('SquadWeaponsJson', r['Id'])
    for r in rows('WeaponAmmunitionsJson', UnitId=FAL, WeaponId=pfw): g.remove('WeaponAmmunitionsJson', r['Id'])
    qlz = [m for m in rows('SquadMembersJson', UnitId=FAL) if W[m['PrimaryWeaponId']]['HUDName'] == 'QLZ-87']
    ok(len(qlz) == 1, 'one QLZ-87 man'); g.add('SquadMembersJson', qlz[0], {})
    # squad weapon order stays 1..n
    sw = rows('SquadWeaponsJson', UnitId=FAL)
    for i, r in enumerate(sorted(sw, key=lambda r: r['Order']), 1):
        if r['Order'] != i: g.put('SquadWeaponsJson', r['Id'], {'Order': i})
    (link,) = rows('UnitArmorsJson', UnitId=FAL); old_row = link['ArmorId']; cur = AR[old_row]
    ok(cur['ArmorValue'] == 8 and cur['MaxHealthPoints'] == 40, ('armour 8 / 40 before', cur['ArmorValue'], cur['MaxHealthPoints']))
    ign = {'Id', 'Name', 'MaxHealthPoints'}
    hit = sorted(k for k, a in AR.items() if a and a.get('MaxHealthPoints') == 45 and all(a.get(f) == cur.get(f) for f in set(a) | set(cur) if f not in ign))
    ok(bool(hit), 'an existing 8 / 45 row'); g.put('UnitArmorsJson', link['Id'], {'ArmorId': hit[0]})
    g.put('Units', FAL, {'Cost': 75})
    after = kit()
    men = rows('SquadMembersJson', UnitId=FAL)
    carried = {x for m in men for x in (m['PrimaryWeaponId'], m.get('SpecialWeaponId')) if x}
    ok(len(after) == 9 and sum(k == 'QBZ-192' for k in after) == 5 and after.count('QLU-11') == 2 and after.count('QLZ-87') == 2, ('kit after', after))
    ok({r['WeaponId'] for r in rows('SquadWeaponsJson', UnitId=FAL)} == carried == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=FAL)}, 'card + ammo = carried')
    ok(sum(m['DeathPriority'] == 1 for m in men) == 1, 'one keeper (death priority 1)')
    rec['osama_falcons_9man_1127'] = {'before': before, 'after': after, 'cost': [85, 75], 'armor_row': [old_row, hit[0], '8 / 40 -> 8 / 45'],
                                      'ammo_per_man': [(W[r['WeaponId']]['HUDName'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=FAL)]}
    print('FALCONS 9 MAN', rec['osama_falcons_9man_1127'])

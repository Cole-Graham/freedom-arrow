"""Osama 27 Nov 2026 22:5x PST, thread 1567745029781454889: "Mountaineers become 12 man" (his DPM-visualizer custom unit 'mountaineers': 10 QBZ-191,
1 QJY-88, 1 QLU-11, 75 pts, armour 8). Mountaineers 高寒山地特战分队 (1196, Light CAB): 8 -> 12 men; the leader keeps his PF-98 (Osama 28 Nov 01:2x "you removed the AT
weapons and launchers of the infantry I reworked"; dev.9 had removed it); one of the two QJY-88 gunners becomes a QBZ-191 rifleman; 4 QBZ-191 riflemen are added (copies of a plain rifleman, death priority 4).
Health stays 5 per man: armour link -> an existing row equal to the current one but 60 HP (vanilla 314 'Armor Infantry Shock 12Men', 8 / 60).
Price stays 75. Seats: transports with fewer infantry seats than the squad are removed from its card (the rule the data already follows:
no card has a transport smaller than its squad); the same check runs for the 9-man Falcons (osama_falcons_9man_1127). In the plb scope (adds rows)."""
MTN, FAL = 1196, 1185


def seats_trim(t, g, unit):
    U, SA, TA = t['Units'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson']
    men = sum(1 for m in t['SquadMembersJson'].values() if m and m['UnitId'] == unit)
    cards = {k for k, r in SA.items() if r and r['UnitId'] == unit}
    out = []
    for k, r in list(TA.items()):
        if r and r.get('SpecializationAvailabilityId') in cards and (U[r['UnitId']].get('InfantrySlots') or 0) < men:
            out.append((U[r['UnitId']]['HUDName'], U[r['UnitId']].get('InfantrySlots'))); g.remove('TransportAvailabilitiesJson', k)
    left = sorted({(U[r['UnitId']]['HUDName'], U[r['UnitId']].get('InfantrySlots')) for r in TA.values() if r and r.get('SpecializationAvailabilityId') in cards})
    return men, sorted(set(out)), left


def apply(t, g, ok, rec):
    U, W, AR = t['Units'], t['WeaponsJson'], t['ArmorsJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    kit = lambda: sorted(W[m['PrimaryWeaponId']]['HUDName'] + (' + ' + W[m['SpecialWeaponId']]['HUDName'] if m.get('SpecialWeaponId') else '') for m in rows('SquadMembersJson', UnitId=MTN))
    before = kit()
    ok(U[MTN]['HUDName'] == 'Mountaineers 高寒山地特战分队' and U[MTN]['Cost'] == 75 and before == ['QBZ-191', 'QBZ-191', 'QBZ-191', 'QBZ-191', 'QBZ-191 + PF-98', 'QJY-88', 'QJY-88', 'QLU-11'], ('Mountaineers before', before))
    (lead,) = [m for m in rows('SquadMembersJson', UnitId=MTN) if m.get('SpecialWeaponId')]
    pf = lead['SpecialWeaponId']
    rifle = [m for m in rows('SquadMembersJson', UnitId=MTN) if W[m['PrimaryWeaponId']]['HUDName'] == 'QBZ-191' and m['Id'] != lead['Id']]
    mg = [m for m in rows('SquadMembersJson', UnitId=MTN) if W[m['PrimaryWeaponId']]['HUDName'] == 'QJY-88']
    g.put('SquadMembersJson', mg[-1]['Id'], {'PrimaryWeaponId': rifle[-1]['PrimaryWeaponId'], 'DeathPriority': rifle[-1]['DeathPriority']})
    for _ in range(4): g.add('SquadMembersJson', rifle[-1], {})
    for i, r in enumerate(sorted(rows('SquadWeaponsJson', UnitId=MTN), key=lambda r: r['Order']), 1):
        if r['Order'] != i: g.put('SquadWeaponsJson', r['Id'], {'Order': i})
    (link,) = rows('UnitArmorsJson', UnitId=MTN); old = link['ArmorId']; cur = AR[old]
    ok(cur['ArmorValue'] == 8 and cur['MaxHealthPoints'] == 40, ('armour 8 / 40 before', cur['ArmorValue'], cur['MaxHealthPoints']))
    hit = sorted(k for k, a in AR.items() if a and a.get('MaxHealthPoints') == 60 and all(a.get(f) == cur.get(f) for f in set(a) | set(cur) if f not in ('Id', 'Name', 'MaxHealthPoints')))
    ok(bool(hit), 'an existing 8 / 60 row'); g.put('UnitArmorsJson', link['Id'], {'ArmorId': hit[0]})
    after = kit(); men = rows('SquadMembersJson', UnitId=MTN)
    carried = {x for m in men for x in (m['PrimaryWeaponId'], m.get('SpecialWeaponId')) if x}
    ok(len(after) == 12 and sum(k.startswith('QBZ-191') for k in after) == 10 and after.count('QBZ-191 + PF-98') == 1 and after.count('QJY-88') == 1 and after.count('QLU-11') == 1 and U[MTN]['Cost'] == 75, ('kit after', after))
    ok({r['WeaponId'] for r in rows('SquadWeaponsJson', UnitId=MTN)} == carried == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=MTN)}, 'card + ammo = carried')
    ok(sum(m['DeathPriority'] == 1 for m in men) == 1, 'one keeper')
    m_men, m_cut, m_left = seats_trim(t, g, MTN)
    f_men, f_cut, f_left = seats_trim(t, g, FAL)
    ok(m_left and f_left, ('both squads keep a transport', m_left, f_left))
    rec['osama_mountaineers_12man_1127'] = {'before': before, 'after': after, 'armor_row': [old, hit[0], '8 / 40 -> 8 / 60'],
                                            'ammo_per_man': [(W[r['WeaponId']]['HUDName'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=MTN)],
                                            'mountaineers_transports_removed': m_cut, 'mountaineers_transports_left': m_left,
                                            'falcons_9_transports_removed': f_cut, 'falcons_transports_left': f_left}
    print('MOUNTAINEERS 12', rec['osama_mountaineers_12man_1127'])

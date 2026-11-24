"""VN-3 air-droppable (Osama 24 Nov 2026 01:2x PST, thread "China cosmetic work": "VN-03 should be paradropable"). Sets IsAirDroppable on the
VN-3's own mobility rows (mk_china_1123.py copied them from the BPM-97 Kord as '<name> PLA VN-3'); refuses if any other unit uses them,
so the Kord and every other unit are unchanged."""
NAME = 'PLA VN-3'


def apply(t, g, ok, rec):
    U, UP, M = t['Units'], t['UnitPropulsionsJson'], t['MobilityJson']
    ids = sorted(i for i, u in U.items() if u and (u.get('Name') == NAME or (u.get('Name') or '').startswith(NAME + ' ')))
    ok(any(U[i]['Name'] == NAME for i in ids), NAME + ' card exists')
    mobs = sorted({r['MobilityId'] for r in UP.values() if r and r['UnitId'] in ids})
    users = {m: sorted({r['UnitId'] for r in UP.values() if r and r['MobilityId'] == m}) for m in mobs}
    ok(mobs and all(set(us) <= set(ids) for us in users.values()), ('VN-3 mobility rows are its own', users))
    before = {m: M[m]['IsAirDroppable'] for m in mobs}
    for m in mobs: g.put('MobilityJson', m, {'IsAirDroppable': True})
    ok(all(M[m]['IsAirDroppable'] is True for m in mobs), 'VN-3 air-droppable')
    rec['vn3_airdrop'] = {'units': ids, 'mobility_before': before}
    print('VN-3 AIRDROP', rec['vn3_airdrop'], [M[m]['Name'] for m in mobs])

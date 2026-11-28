"""Osama 27 Nov 2026 23:0x PST, thread 1567745029781454889: "whistling arrows 95 pts". Whistling Arrows 响箭 (1184 and any other unit row of that
name): Cost -> 95. A unit with loadout swap rows (ReplaceUnitId) is refused here, so no swap price can drift (swap-row price rule). Put-only."""


def apply(t, g, ok, rec):
    U, O, M = t['Units'], t['OptionsJson'], t['ModificationsJson']
    ids = sorted(k for k, u in U.items() if u and (u.get('HUDName') or '').strip().startswith('Whistling Arrows'))
    ok(1184 in ids, ('Whistling Arrows units', ids))
    mods = {k for k, m in M.items() if m and m.get('UnitId') in ids}
    ok(not any(o and o.get('ModificationId') in mods and o.get('ReplaceUnitId') for o in O.values()), 'no loadout swap rows')
    before = {k: U[k]['Cost'] for k in ids}
    for k in ids: g.put('Units', k, {'Cost': 95})
    rec['osama_whistling_price_1127'] = {'cost': before, 'new': 95}
    print('WHISTLING PRICE', rec['osama_whistling_price_1127'])

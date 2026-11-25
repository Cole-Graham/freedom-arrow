"""ZTQ-15 cards 25 points cheaper (Osama 25 Nov 2026 11:3x PST, thread 1567745029781454889: "let's drop both ZTQ-15 light , recon and base by 25
points across the board to compensate for their penetration and reload time loss"). Base unit cost only; the three cards have no loadout options
or swap rows. ZTQ-15 (906) 185 -> 160, ZTQ-15 Recon (1240) 195 -> 170, ZTQ-15 Light (1268) 170 -> 145."""
CARDS = {906: ('ZTQ-15', 185), 1240: ('ZTQ-15 Recon', 195), 1268: ('ZTQ-15 Light', 170)}


def apply(t, g, ok, rec):
    U, M = t['Units'], t['ModificationsJson']
    for uid, (name, cost) in CARDS.items():
        u = U[uid]
        ok(u['HUDName'] == name and u['Cost'] == cost and not u.get('OriginalCost'), (name, u['HUDName'], u['Cost'], u.get('OriginalCost')))
        ok(not any(m and m.get('UnitId') == uid for m in M.values()), name + ' has no loadout options')
        g.put('Units', uid, {'Cost': cost - 25})
        ok(U[uid]['Cost'] == cost - 25, name + ' -25')
    rec['ztq15_cost_1125'] = {uid: [c, c - 25] for uid, (_, c) in CARDS.items()}
    print('ZTQ-15 COST', rec['ztq15_cost_1125'])

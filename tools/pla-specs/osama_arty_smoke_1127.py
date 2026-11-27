"""Artillery smoke rounds (Osama 27 Nov 2026 04:4x PST, thread 1567745029781454889: "lynx howitzer 6x smoke / plz-10 smoke to 8 same with PLZ-25 /
PLL-09 8 smoke / PLL-05 8 smoke"). Only each unit's own smoke weapon-ammo rows change; the smoke rounds themselves are unchanged.
- Lynx Howitzer (1436) row 2021350: 10 -> 6.
- PLZ-10 (1409) rows 2020643 / 2020644 and PLZ-25 (1408) rows 2020617 / 2020618 (one smoke row per gun-mortar weapon row): 15 / 20 -> 8 each.
- PLL-09 (1037) row 2018960: 20 -> 8. PLL-05 (926) row 2018958: 20 -> 8."""
ROWS = {2021350: (1436, 10, 6), 2020643: (1409, 15, 8), 2020644: (1409, 20, 8), 2020617: (1408, 15, 8), 2020618: (1408, 20, 8),
        2018960: (1037, 20, 8), 2018958: (926, 20, 8)}


def apply(t, g, ok, rec):
    U, A, WA = t['Units'], t['AmmunitionsJson'], t['WeaponAmmunitionsJson']
    out = {}
    for r, (u, a, b) in ROWS.items():
        x = WA[r]
        ok(x['UnitId'] == u and A[x['AmmunitionId']].get('GenerateSmoke') and x['Quantity'] == a, (U[u]['HUDName'], 'smoke row', r, x['Quantity']))
        g.put('WeaponAmmunitionsJson', r, {'Quantity': b}); out.setdefault(U[u]['HUDName'], []).append([a, b])
    for u in {v[0] for v in ROWS.values()}:
        ok(all(WA[r]['Quantity'] == ROWS[r][2] for r in ROWS if ROWS[r][0] == u)
           and not [x for x in WA.values() if x and x['UnitId'] == u and A[x['AmmunitionId']].get('GenerateSmoke') and x['Id'] not in ROWS], (U[u]['HUDName'], 'every smoke row set'))
    rec['osama_arty_smoke_1127'] = out
    print('ARTY SMOKE', out)

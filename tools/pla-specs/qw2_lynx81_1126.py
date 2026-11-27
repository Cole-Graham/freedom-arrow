"""PGZ-95 / Lynx SPAAG missiles and Lynx 81 mm mortar range (Osama 26 Nov 2026 22:58 PST, thread 1567745029781454889: "PGZ-95, Lynx SPAAG should
get 8x QW-2", "lynx 81mm mortar range should be 2600").
- QW-2 rounds carried 4 -> 8 on the two units' own WeaponAmmunitions rows: PGZ-95 (1052, row 2010684) and Lynx SPAAG (1439, row 2021383).
  Magazine stays 4 (15 s reload), so each fires 4, reloads, fires 4 more. Round stats unchanged; the PGZ-04A (same round 2009565, own row) keeps 4.
- Lynx 81mm Mortar (1434 'PLA Lynx CS-SM8 81 mm Mortar'): 82mm HE (2021525) and 82mm smoke (2021526), each used only by this unit,
  GroundRange 1850 -> 1300 world (card 3,700 -> 2,600 m). Minimum range 125 and the direct-fire 82mm HEAT (vanilla 135, 1,200 m) unchanged.
Not yet tested in a game."""
QW2_ROWS = {2010684: (1052, 'PGZ-95'), 2021383: (1439, 'Lynx SPAAG')}
MORTAR, ROUNDS, RANGE = 1434, (2021525, 2021526), 1300.0


def apply(t, g, ok, rec):
    U, W, A, WA = t['Units'], t['WeaponsJson'], t['AmmunitionsJson'], t['WeaponAmmunitionsJson']
    out = {}
    for r, (u, h) in QW2_ROWS.items():
        ok(WA[r]['UnitId'] == u and U[u]['HUDName'] == h and W[WA[r]['WeaponId']]['HUDName'] == 'QW-2' and WA[r]['Quantity'] == 4, (h, 'QW-2 row, 4 rounds'))
        g.put('WeaponAmmunitionsJson', r, {'Quantity': 8}); out[h] = WA[r]['Quantity']
    ok(U[MORTAR]['HUDName'] == 'Lynx 81mm Mortar', 'Lynx 81mm Mortar')
    for a in ROUNDS:
        users = {x['UnitId'] for x in WA.values() if x and x['AmmunitionId'] == a}
        ok(users == {MORTAR} and A[a]['GroundRange'] == 1850.0, (A[a]['HUDName'], 'own round, 1850 world', users))
        g.put('AmmunitionsJson', a, {'GroundRange': RANGE})
    rec['qw2_lynx81_1126'] = {'qw2_rounds': out, 'lynx81_range_card_m': {A[a]['HUDName']: 2 * A[a]['GroundRange'] for a in ROUNDS}}
    print('QW-2 x8 + LYNX 81', rec['qw2_lynx81_1126'])

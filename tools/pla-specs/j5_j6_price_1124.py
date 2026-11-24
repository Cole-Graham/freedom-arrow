"""J-5 Drone and J-6W Drone +20 pts (Osama 24 Nov 2026 11:3x PST, thread 1567745029781454889: "J-5 drone and J-6 +20 points").
Units 1089 'PLA Catalogue J-5' and 1091 'PLA Catalogue J-6' (PLARF): Units.Cost +20, so every loadout price on the card goes up by 20.
OriginalCost stays 0 (card price = Cost + options); no loadout swap rows point at these units."""
UNITS = {1089: 'J-5 Drone', 1091: 'J-6W Drone'}


def apply(t, g, ok, rec):
    U, O = t['Units'], t['OptionsJson']
    out = {}
    for u, hud in UNITS.items():
        ok(U[u]['HUDName'] == hud and not U[u].get('OriginalCost') and not any(o and o.get('ReplaceUnitId') == u for o in O.values()), (hud, 'card as expected'))
        old = U[u]['Cost']; g.put('Units', u, {'Cost': old + 20}); out[hud] = [old, old + 20]
    ok(all(U[u]['Cost'] == out[h][1] for u, h in UNITS.items()), 'J-5 / J-6W +20')
    rec['j5_j6_price_1124'] = out
    print('J-5/J-6W PRICE', out)

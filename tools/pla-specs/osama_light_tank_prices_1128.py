"""Light tank prices (Osama 28 Nov 2026 00:3x PST, thread 1567745029781454889: "M10 booker to 85 pts, ztl-11 to 80 pts, m8 ags 65 pts ... double check
those points as a sanity check"): M10 Booker M35 (453) 100 -> 85; the M10 Booker XM913 card (720) keeps its +10 over the M35, 110 -> 95; ZTL-11
(938) 90 -> 80; M8 AGS (183) 70 -> 65. Base Cost only: OriginalCost 0 on all four and no loadout swaps to another unit row (checked). Put-only."""
PRICES = {453: ('M10 Booker M35', 100, 85), 720: ('M10 Booker XM913', 110, 95), 938: ('ZTL-11', 90, 80), 183: ('M8 AGS', 70, 65)}


def apply(t, g, ok, rec):
    U, O, M = t['Units'], t['OptionsJson'], t['ModificationsJson']
    out = {}
    for u, (name, old, new) in PRICES.items():
        ok(U[u]['HUDName'] == name and U[u]['Cost'] == old and not U[u].get('OriginalCost'), (u, U[u]['HUDName'], U[u]['Cost'], U[u].get('OriginalCost')))
        ok(not any(o and o.get('ReplaceUnitId') and M.get(o['ModificationId'], {}).get('UnitId') == u for o in O.values()), (name, 'no loadout swap rows'))
        g.put('Units', u, {'Cost': new}); out[name] = [old, new]
    rec['osama_light_tank_prices_1128'] = out
    print('LIGHT TANK PRICES', out)

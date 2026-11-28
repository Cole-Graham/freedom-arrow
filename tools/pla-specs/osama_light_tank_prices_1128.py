"""Light tank prices (Osama 28 Nov 2026 00:3x PST, thread 1567745029781454889: "M10 booker to 85 pts, ztl-11 to 80 pts, m8 ags 65 pts ... double check
those points as a sanity check"): ZTL-11 (938) 90 -> 80; M8 AGS (183) 70 -> 65. The M10 Booker stays as it is (M35 100, XM913 110): Osama 00:4x "I meant
the m35 booker, lets leave it at 100 right now". Base Cost only: OriginalCost 0 on both and no loadout swaps to another unit row (checked). Put-only."""
PRICES = {938: ('ZTL-11', 90, 80), 183: ('M8 AGS', 70, 65)}


def apply(t, g, ok, rec):
    U, O, M = t['Units'], t['OptionsJson'], t['ModificationsJson']
    out = {}
    for u, (name, old, new) in PRICES.items():
        ok(U[u]['HUDName'] == name and U[u]['Cost'] == old and not U[u].get('OriginalCost'), (u, U[u]['HUDName'], U[u]['Cost'], U[u].get('OriginalCost')))
        ok(not any(o and o.get('ReplaceUnitId') and M.get(o['ModificationId'], {}).get('UnitId') == u for o in O.values()), (name, 'no loadout swap rows'))
        g.put('Units', u, {'Cost': new}); out[name] = [old, new]
    rec['osama_light_tank_prices_1128'] = out
    print('LIGHT TANK PRICES', out)

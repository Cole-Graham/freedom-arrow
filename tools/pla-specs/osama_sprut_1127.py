"""Sprut price (Osama 27 Nov 2026 03:1x PST, bugs thread 1573561286803980289: "Spruts need like 25 points increase across the board"; 04:3x,
thread 1567745029781454889: "we nerfed spruts already right" - it was only proposed, so it is queued here).
Sprut-SD (144) 55 -> 80, Sprut-SDM (722) 70 -> 95. The cage-armour loadout stays +10 (90 / 105 with it). OriginalCost 0, no swap rows."""
PRICES = {144: ('Sprut-SD', 55, 80), 722: ('Sprut-SDM', 70, 95)}


def apply(t, g, ok, rec):
    U, O, M = t['Units'], t['OptionsJson'], t['ModificationsJson']
    out = {}
    for u, (h, a, b) in PRICES.items():
        ok(U[u]['HUDName'] == h and U[u]['Cost'] == a and not U[u].get('OriginalCost'), (h, U[u]['Cost']))
        ok(not any(o and o.get('ReplaceUnitId') and M.get(o['ModificationId'], {}).get('UnitId') == u for o in O.values()), (h, 'no swap rows'))
        g.put('Units', u, {'Cost': b}); out[h] = [a, b]
    rec['osama_sprut_1127'] = out
    print('SPRUT', out)

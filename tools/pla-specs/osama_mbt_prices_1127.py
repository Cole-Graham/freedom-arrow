"""MBT prices (Osama 27 Nov 2026 17:5x PST, thread 1567745029781454889: "SEPV 3 to 280 pts, T-90M to 205, ZTZ-99A to 280 pts" / "T-14 armata to 380"; 17:5x "scratch that, sepv3 sto 265 and ztz-99A to 265,
armata to 360 back to original"): SEP v3 265, T-90M 205, ZTZ-99A 265; the T-14 stays 360.
Base Cost only (OriginalCost 0 on all four). A loadout that swaps the card to another unit row (ReplaceUnitId) keeps that row at base + option,
as vanilla does (audit_swap_prices.py), so swap rows move with the base."""
PRICES = {191: ('M1A2 SEP v3', 265), 238: ('T-90M', 205), 904: ('ZTZ-99A', 265)}


def apply(t, g, ok, rec):
    U, O, M = t['Units'], t['OptionsJson'], t['ModificationsJson']
    out = {}
    for u, (name, new) in PRICES.items():
        ok(U[u]['HUDName'] == name and not U[u].get('OriginalCost'), (u, U[u]['HUDName'], U[u].get('OriginalCost')))
        old = U[u]['Cost']; g.put('Units', u, {'Cost': new}); out[name] = [old, new]
        for o in O.values():
            r = o and o.get('ReplaceUnitId')
            if not r or r == u or M.get(o['ModificationId'], {}).get('UnitId') != u: continue
            ok(U[r]['Cost'] == old + o['Cost'], (name, 'swap row', r, U[r]['Cost'], old, o['Cost']))
            g.put('Units', r, {'Cost': new + o['Cost']}); out[name + ' swap ' + str(r)] = [old + o['Cost'], new + o['Cost']]
    rec['osama_mbt_prices_1127'] = out
    print('MBT PRICES', out)

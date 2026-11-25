"""VN-3 30 -> 35 pts (Osama 25 Nov 2026 01:5x PST, thread 1567745029781454889: "VN-3 should be 35 points"). Card 1402 (BMP-97 copy, transport
for the 10 Airborne squads): base Cost only; its HJ-73D option stays +10 (35 -> 45 with it). No swap-unit rows, so no loadout copies to match."""
VN3 = 1402


def apply(t, g, ok, rec):
    U, O, M = t['Units'], t['OptionsJson'], t['ModificationsJson']
    ok(U[VN3]['HUDName'] == 'VN-3' and U[VN3]['Cost'] == 30 and not U[VN3].get('OriginalCost'), ('VN-3 30 pts', U[VN3]['Cost']))
    mods = {m['Id'] for m in M.values() if m and m['UnitId'] == VN3}
    opts = sorted((o['UIName'], o.get('Cost') or 0) for o in O.values() if o and o['ModificationId'] in mods)
    ok(opts == [('30 mm autocannon', 0), ('30 mm autocannon + HJ-73D (4x)', 10)], ('VN-3 options', opts))
    g.put('Units', VN3, {'Cost': 35})
    rec['vn3_cost_1125'] = {'unit': VN3, 'cost': [30, 35], 'options': opts}
    print('VN-3 COST', rec['vn3_cost_1125'])

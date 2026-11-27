"""J-7 price (Osama 27 Nov 2026 04:1x PST, thread 1567745029781454889: "J-7 +30 points"). The J-7IIH (1092 'PLA Catalogue J-7', PLARF card) is the only
J-7 with a card: 90 -> 120. The J-7E / J-7G row (1093) has no card and is not changed. OriginalCost 0; no swap rows."""
J7 = 1092


def apply(t, g, ok, rec):
    U = t['Units']
    ok(U[J7]['HUDName'] == 'J-7IIH' and U[J7]['Cost'] == 90 and not U[J7].get('OriginalCost'), ('J-7IIH 90', U[J7]['Cost']))
    ok(not any(s and s['UnitId'] == 1093 for s in t['SpecializationAvailabilitiesJson'].values()), 'J-7E / J-7G has no card')
    g.put('Units', J7, {'Cost': 120})
    rec['osama_j7_1127'] = {'J-7IIH': [90, 120]}
    print('J-7', rec['osama_j7_1127'])

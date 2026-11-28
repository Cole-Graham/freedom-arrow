"""ZTZ-96A / ZTZ-96B (Osama 27 Nov 2026 17:2x PST, thread 1567745029781454889: "ztz-96B 150 pts, ztz-96A to 125, both lose KE armor and goes to 600mm
front, ztz-96 goes to marines both variants"). After osama_tanks_1127.
- Price: ZTZ-96B (905) 145 -> 150, ZTZ-96A (1082) 120 -> 125.
- Front KE 650 -> 600 on their own armour rows (96B 2009091, 96A 2011345); front HEAT stays 700, the rest unchanged.
- Cards move from the Heavy CAB (spec 18) to PLAN Naval/Special Forces (spec 20), 8 each as before: 96B card 2008165, 96A card 2008936.
  The base ZTZ-96 (949) stays hidden."""
CARDS = {905: (2008165, 145, 150, 2009091), 1082: (2008936, 120, 125, 2011345)}
HEAVY, PLAN = 18, 20


def apply(t, g, ok, rec):
    U, SA, AR, UA = t['Units'], t['SpecializationAvailabilitiesJson'], t['ArmorsJson'], t['UnitArmorsJson']
    out = {}
    for u, (card, old, new, arm) in CARDS.items():
        ok(U[u]['Cost'] == old and not U[u].get('OriginalCost'), (U[u]['HUDName'], 'price', U[u]['Cost']))
        ok([r['ArmorId'] for r in UA.values() if r and r['UnitId'] == u] == [arm] and [r['UnitId'] for r in UA.values() if r and r['ArmorId'] == arm] == [u]
           and (AR[arm]['KinArmorFront'], AR[arm]['HeatArmorFront']) == (650, 700), (U[u]['HUDName'], 'own armour 650/700'))
        ok([r['Id'] for r in SA.values() if r and r['UnitId'] == u] == [card] and SA[card]['SpecializationId'] == HEAVY, (U[u]['HUDName'], 'one Heavy CAB card'))
        g.put('Units', u, {'Cost': new})
        g.put('ArmorsJson', arm, {'KinArmorFront': 600})
        g.put('SpecializationAvailabilitiesJson', card, {'SpecializationId': PLAN})
        out[U[u]['HUDName']] = {'cost': [old, new], 'front_ke': [650, 600], 'card': [HEAVY, PLAN, SA[card]['MaxAvailabilityXp0']]}
    rec['osama_ztz96_marines_1127'] = out
    print('ZTZ-96 MARINES', out)

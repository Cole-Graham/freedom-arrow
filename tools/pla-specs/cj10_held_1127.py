"""CJ-10 held back (Osama 27 Nov 2026 04:4x PST, thread 1567745029781454889: "cj-10 held off because of model quality").
The CJ-10 (6009, Light Brigade cruise launcher, DF-10A model) loses its only card (3000019, Medium CAB, 2) and is hidden from the Armory, the
euro_held_1125 pattern. The unit, weapon and model rows stay, so it comes back by restoring the card. Not a transport."""
CJ10, CARD = 6009, 3000019


def apply(t, g, ok, rec):
    U, SA = t['Units'], t['SpecializationAvailabilitiesJson']
    cards = [r['Id'] for r in SA.values() if r and r['UnitId'] == CJ10]
    ok(U[CJ10]['HUDName'] == 'CJ-10' and cards == [CARD] and not any(r and r.get('UnitId') == CJ10 for r in t['TransportAvailabilitiesJson'].values()), ('CJ-10 one card', cards))
    g.remove('SpecializationAvailabilitiesJson', CARD)
    g.put('Units', CJ10, {'DisplayInArmory': False})
    ok(not any(r and r['UnitId'] == CJ10 for r in SA.values()) and U[CJ10]['DisplayInArmory'] is False, 'CJ-10 hidden')
    rec['cj10_held_1127'] = {'removed_card': CARD}
    print('CJ-10 HELD', rec['cj10_held_1127'])

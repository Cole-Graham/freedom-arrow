"""J-31 hidden (Osama 27 Nov 2026 21:1x PST, thread "China cosmetic work": "hide J-31 from the game first"). The J-31 (1251) loses every card
and is hidden from the Armory, the cj10_held_1127 pattern. Unit, weapon, ammunition and model rows stay, so it comes back by deleting this
section. Not a transport."""
J31 = 1251


def apply(t, g, ok, rec):
    U, SA = t['Units'], t['SpecializationAvailabilitiesJson']
    cards = [(r['Id'], r['SpecializationId']) for r in SA.values() if r and r['UnitId'] == J31]
    ok(U[J31]['HUDName'] == 'J-31' and cards and not any(r and r.get('UnitId') == J31 for r in t['TransportAvailabilitiesJson'].values()), ('J-31 cards', cards))
    for i, _ in cards: g.remove('SpecializationAvailabilitiesJson', i)
    g.put('Units', J31, {'DisplayInArmory': False})
    ok(not any(r and r['UnitId'] == J31 for r in SA.values()) and U[J31]['DisplayInArmory'] is False, 'J-31 hidden')
    rec['j31_held_1127'] = {'removed_cards': cards}
    print('J-31 HELD', rec['j31_held_1127'])

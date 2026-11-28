"""Infantry cards hidden (Osama 27 Nov 2026, thread 1567745029781454889): 22:4x "PAP AA patrol hide", 23:4x "tiger brigade hidden". Each unit
below loses every card, the transport choices tied to those cards, and is hidden from the Armory (the j31_held_1127 pattern). Unit, squad,
weapon and ammunition rows stay, so a unit comes back by taking it off this list (its transport rows are re-made from its old card's list)."""
HIDDEN = {6004: 'PAP AA Patrol', 6002: 'Tiger Brigade 猛虎旅'}


def apply(t, g, ok, rec):
    U, SA, TA = t['Units'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson']
    out = {}
    for unit, name in HIDDEN.items():
        cards = [(r['Id'], r['SpecializationId']) for r in SA.values() if r and r['UnitId'] == unit]
        ok(U[unit]['HUDName'] == name and cards and not any(r and r.get('UnitId') == unit for r in TA.values()), (name, 'cards', cards))
        ids = {i for i, _ in cards}
        rides = [(k, U[r['UnitId']]['HUDName']) for k, r in TA.items() if r and r.get('SpecializationAvailabilityId') in ids]
        for k, _ in rides: g.remove('TransportAvailabilitiesJson', k)
        for i in ids: g.remove('SpecializationAvailabilitiesJson', i)
        g.put('Units', unit, {'DisplayInArmory': False})
        ok(not any(r and r['UnitId'] == unit for r in SA.values()) and not any(r and r.get('SpecializationAvailabilityId') in ids for r in TA.values()) and U[unit]['DisplayInArmory'] is False, (name, 'hidden'))
        out[name] = {'removed_cards': cards, 'removed_transport_rows': [n for _, n in rides]}
    rec['hidden_infantry_1127'] = out
    print('HIDDEN INFANTRY', out)

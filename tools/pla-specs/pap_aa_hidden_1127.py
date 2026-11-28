"""PAP AA Patrol hidden (Osama 27 Nov 2026 22:4x PST, thread 1567745029781454889: "PAP AA patrol hide"). The PAP AA Patrol (6004, Light CAB
infantry) loses every card, the transport choices tied to those cards, and is hidden from the Armory (the j31_held_1127 pattern). Unit, squad,
weapon and ammunition rows stay, so it comes back by deleting this section (the transport rows are re-made from its old card's list)."""
PAP_AA = 6004


def apply(t, g, ok, rec):
    U, SA, TA = t['Units'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson']
    cards = [(r['Id'], r['SpecializationId']) for r in SA.values() if r and r['UnitId'] == PAP_AA]
    ok(U[PAP_AA]['HUDName'] == 'PAP AA Patrol' and cards and not any(r and r.get('UnitId') == PAP_AA for r in TA.values()), ('PAP AA Patrol cards', cards))
    ids = {i for i, _ in cards}
    rides = [(k, U[r['UnitId']]['HUDName']) for k, r in TA.items() if r and r.get('SpecializationAvailabilityId') in ids]
    for k, _ in rides: g.remove('TransportAvailabilitiesJson', k)
    for i in ids: g.remove('SpecializationAvailabilitiesJson', i)
    g.put('Units', PAP_AA, {'DisplayInArmory': False})
    ok(not any(r and r['UnitId'] == PAP_AA for r in SA.values()) and not any(r and r.get('SpecializationAvailabilityId') in ids for r in TA.values()) and U[PAP_AA]['DisplayInArmory'] is False, 'PAP AA Patrol hidden')
    rec['pap_aa_hidden_1127'] = {'removed_cards': cards, 'removed_transport_rows': [n for _, n in rides]}
    print('PAP AA HIDDEN', rec['pap_aa_hidden_1127'])

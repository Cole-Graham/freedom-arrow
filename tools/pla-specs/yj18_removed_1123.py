"""YJ-18 removed from the game (Osama 23 Nov 2026 17:4x PST, thread 1567745029781454889: "we should remove the YJ-18 unit from the game").
The card 'YJ-18' (unit 1129, 'PLA Catalogue YJ-18 ship launcher', RU_Iskander body, PLAAF Air Force spec 17, 2 cards) is taken out of its only
spec (availability row 2008984) and hidden in the Armory. Its unit, weapon and ammunition rows stay, so nothing that points to them breaks
(saved decks lose the card)."""

YJ18, AVAIL = 1129, 2008984


def apply(t, g, ok, rec):
    U, SA, TA = t['Units'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson']
    ok(U[YJ18]['HUDName'] == 'YJ-18' and U[YJ18]['Name'] == 'PLA Catalogue YJ-18 ship launcher', 'YJ-18 card')
    ok([r['Id'] for r in SA.values() if r and r['UnitId'] == YJ18] == [AVAIL] and not any(r and r['SpecializationAvailabilityId'] == AVAIL for r in TA.values()),
       'one availability row, no transport links')
    ok([u['HUDName'] for u in U.values() if u and 'YJ-18' in (u.get('HUDName') or '')] == ['YJ-18'], 'only one YJ-18 card')
    g.remove('SpecializationAvailabilitiesJson', AVAIL)
    g.put('Units', YJ18, {'DisplayInArmory': False})
    ok(not any(r and r['UnitId'] == YJ18 for r in SA.values()) and U[YJ18]['DisplayInArmory'] is False, 'YJ-18 in no spec, hidden in the Armory')
    rec['yj18_removed'] = {'unit': YJ18, 'availability_removed': AVAIL}
    print('YJ-18 removed', rec['yj18_removed'])

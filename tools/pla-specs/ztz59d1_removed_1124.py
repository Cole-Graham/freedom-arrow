"""ZTZ-59D1 removed from the game (Osama 24 Nov 2026 01:1x PST, thread "blue dragons": "and remove the ztz-59D1").
The PLARF card 'PLA ZTZ-59D1' (unit 1260) is taken out of every spec it is in (including the hidden-units test spec) and hidden in the Armory,
as type19_removed_1123.py did for the Type 19. Its unit, weapon and ammunition rows stay, so nothing that points to them breaks (saved decks
lose the card). Runs last in the batch so the test-spec section cannot add it back."""

U59 = 1260


def apply(t, g, ok, rec):
    U, SA, TA = t['Units'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson']
    ok(U[U59]['Name'] == 'PLA ZTZ-59D1' and U[U59]['HUDName'] == 'ZTZ-59D1', 'ZTZ-59D1 card 1260')
    av = [r['Id'] for r in sorted(SA.values(), key=lambda r: r['Id']) if r and r['UnitId'] == U59]
    ok(len(av) >= 1, ('availability rows', av))
    ok(not any(r and r.get('UnitId') == U59 for r in TA.values()), 'ZTZ-59D1 is nobody\'s transport')
    for a in av: g.remove('SpecializationAvailabilitiesJson', a)
    g.put('Units', U59, {'DisplayInArmory': False})
    ok(not any(r and r['UnitId'] == U59 for r in SA.values()) and U[U59]['DisplayInArmory'] is False, 'ZTZ-59D1 in no spec, hidden in the Armory')
    rec['ztz59d1_removed'] = {'unit': U59, 'availability_removed': av}
    print('ZTZ-59D1 removed', rec['ztz59d1_removed'])

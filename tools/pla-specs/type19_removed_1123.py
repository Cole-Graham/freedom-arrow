"""Type 19 removed from the game (Osama 23 Nov 2026 18:0x PST, thread "blue dragons": "and remove the Type 19").
The Blue Dragon card 'Type 19' (unit 1293, the Japanese wheeled 155 mm howitzer, spec 23) is taken out of every spec it is in and hidden in the
Armory, as yj18_removed_1123.py did for the YJ-18. Its unit, weapon and ammunition rows stay, so nothing that points to them breaks (saved decks
lose the card). The Type 19 model files stay in the Assets until a cleanup is agreed."""

T19 = 1293


def apply(t, g, ok, rec):
    U, SA, TA = t['Units'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson']
    ok(U[T19]['HUDName'] == 'Type 19' and U[T19]['Name'] == 'Type 19', 'Type 19 card')
    av = [r['Id'] for r in sorted(SA.values(), key=lambda r: r['Id']) if r and r['UnitId'] == T19]
    ok(len(av) >= 1 and not any(r and r.get('SpecializationAvailabilityId') in av for r in TA.values()), ('availability rows, no transport links', av))
    ok(not any(r and r.get('UnitId') == T19 for r in TA.values()), 'Type 19 is nobody\'s transport')
    for a in av: g.remove('SpecializationAvailabilitiesJson', a)
    g.put('Units', T19, {'DisplayInArmory': False})
    ok(not any(r and r['UnitId'] == T19 for r in SA.values()) and U[T19]['DisplayInArmory'] is False, 'Type 19 in no spec, hidden in the Armory')
    rec['type19_removed'] = {'unit': T19, 'availability_removed': av}
    print('Type 19 removed', rec['type19_removed'])

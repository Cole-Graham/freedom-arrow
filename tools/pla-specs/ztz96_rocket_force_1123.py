"""ZTZ-96 back in the Rocket Force (Osama 23 Nov 2026 21:4x PST, thread 1567745029781454889: "where's the ztz-96? I don't see it in rocket force").
The base ZTZ-96 card (unit 949, 'PLA ZTZ-96') was in PLARF (spec 19) with 6 cards up to 0.8.0-dev.105 and has been in no spec since 0.9.0-dev.44
(no hide request on record; DisplayInArmory stayed True). One card row again: spec 19, 6 cards (a copy of the ZTZ-96A's Armored Force row).
Withdrawn 24 Nov 01:0x ("remove ZTZ-96 from the rocket force this is the wrong model"), back 24 Nov 01:5x ("put the ztz-96 back in I know I said to
remove it but that was with the wrong model. It's correct now")."""
UNIT, ZTZ96A, ROCKET = 949, 1082, 19


def apply(t, g, ok, rec):
    U, SA, S = t['Units'], t['SpecializationAvailabilitiesJson'], t['SpecializationsJson']
    ok(U[UNIT]['Name'] == 'PLA ZTZ-96' and U[UNIT]['DisplayInArmory'] and not any(r and r['UnitId'] == UNIT for r in SA.values()), 'ZTZ-96 card in no spec')
    ok(S[ROCKET]['Name'].startswith('PLA PLARF') and S[ROCKET]['CountryId'] == 4, 'spec 19 = PLARF')
    tpl = [r for r in SA.values() if r and r['UnitId'] == ZTZ96A]
    ok(len(tpl) == 1, 'ZTZ-96A card row')
    row = g.add('SpecializationAvailabilitiesJson', tpl[0], {'UnitId': UNIT, 'SpecializationId': ROCKET, 'MaxAvailabilityXp0': 6})
    ok([(r['SpecializationId'], r['MaxAvailabilityXp0']) for r in SA.values() if r and r['UnitId'] == UNIT] == [(ROCKET, 6)], 'ZTZ-96 in PLARF, 6 cards')
    rec['ztz96_rocket_force'] = {'unit': UNIT, 'row': row, 'spec': ROCKET, 'cards': 6}
    print('ZTZ-96 PLARF', rec['ztz96_rocket_force'])

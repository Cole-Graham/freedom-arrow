"""ZBD-04 out of the Rocket Force (Osama 24 Nov 2026 03:1x PST, thread 1567745029781454889: "remove the ZBD-04 and ZTZ-96 from rocket force next
patch"; the base ZTZ-96 went in ztz96_removed_1124.py). 'PLA ZBD-04 Rocket Force' (unit 1308) is not a card: it is the transport of 12 PLARF
(spec 19) infantry cards. Those 12 transport links go; every one of those cards keeps its CSK-181 and ZSD-89A (most also ZSD-89) transports.
The unit is hidden (DisplayInArmory False) and recorded in rec['hidden_rows'] as transport-only, so the China test spec 26 shows it
(test_specs_1123.NO_CARD). The ZBD-04A (902, Armored Force transport) is not changed. Runs before test_specs_1123.py."""
UNIT, RF = 1308, 19


def apply(t, g, ok, rec):
    U, SA, TA = t['Units'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson']
    ok(U[UNIT]['Name'] == 'PLA ZBD-04 Rocket Force' and not any(r and r['UnitId'] == UNIT for r in SA.values()), 'ZBD-04 Rocket Force: transport, no card')
    links = [r for r in TA.values() if r and r['UnitId'] == UNIT]
    ok(len(links) == 12 and all(SA[r['SpecializationAvailabilityId']]['SpecializationId'] == RF for r in links), ('12 PLARF transport links', len(links)))
    left = {r['SpecializationAvailabilityId']: [U[x['UnitId']]['HUDName'] for x in TA.values() if x and x['SpecializationAvailabilityId'] == r['SpecializationAvailabilityId']
                                                and x['UnitId'] != UNIT] for r in links}
    ok(all({'CSK-181', 'ZSD-89A'} <= set(v) for v in left.values()), 'every card keeps CSK-181 and ZSD-89A')
    rec.setdefault('hidden_rows', {})[UNIT] = ([], [dict(r) for r in links])   # transport only, for test_specs_1123.py
    for r in links: g.remove('TransportAvailabilitiesJson', r['Id'])
    g.put('Units', UNIT, {'DisplayInArmory': False})
    ok(not any(r and r['UnitId'] == UNIT for r in TA.values()) and U[UNIT]['DisplayInArmory'] is False, 'ZBD-04 Rocket Force: no links, hidden')
    rec['zbd04_rf_removed'] = {'unit': UNIT, 'links_removed': len(links)}
    print('ZBD-04 RF removed', rec['zbd04_rf_removed'])

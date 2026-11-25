"""No visible card in the hidden test specs (Osama 25 Nov 2026 03:0x PST, thread 1567745029781454889: "The Test: Hidden Units is still there,
please remove it", Arsenal screenshot). The PCL-181 (1034) is shown again since it joined the Medium Combined Arms Brigade
(fk3000_pcl181_1124.py) but also stayed in the China test spec 26, so the Arsenal drew a "Test: Hidden Units" heading with test mode off.
A unit shown in the Armory leaves the test specs 26-28 (its real specs keep it); the check after it: no shown unit is in a test spec.
Runs last among the spec sections."""
TEST = (26, 27, 28)


def apply(t, g, ok, rec):
    U, SA, TA = t['Units'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson']
    rows = [r for r in SA.values() if r and r['SpecializationId'] in TEST and U[r['UnitId']].get('DisplayInArmory')]
    out = []
    for r in sorted(rows, key=lambda r: r['Id']):
        other = [x['SpecializationId'] for x in SA.values() if x and x['UnitId'] == r['UnitId'] and x['SpecializationId'] not in TEST]
        ok(other and not any(x and x['SpecializationAvailabilityId'] == r['Id'] for x in TA.values()), ('shown test-spec unit also in a real spec, no transports on the row', r, other))
        g.remove('SpecializationAvailabilitiesJson', r['Id']); out.append({'unit': r['UnitId'], 'name': U[r['UnitId']]['Name'], 'test_spec': r['SpecializationId'], 'other_specs': other})
    ok(out and out[0]['unit'] == 1034, ('PCL-181 found', out))
    ok(not any(r and r['SpecializationId'] in TEST and U[r['UnitId']].get('DisplayInArmory') for r in SA.values()), 'no shown unit in a test spec')
    rec['test_spec_visible_1125'] = out
    print('TEST SPEC VISIBLE', out)

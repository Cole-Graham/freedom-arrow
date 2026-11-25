"""FK-3000 into the hidden China test spec (Osama 25 Nov 2026 11:4x PST, thread 1567745029781454889: "FK-3000 we need to hide in our test mode for
now, it's completely fucked as a model. all the parts are all over hte place"). Its one card row (Medium CAB, spec 21) moves to spec 26
"Test: Hidden Units" with the same card count, and the unit is hidden in the Armory (DisplayInArmory False); runtime-qa/TestSpec.cs shows it only
when test-spec.json is on. Unit, weapon, ammunition and model rows stay. Runs after fk3000_pcl181_1124.py (which creates the card) and after
test_specs_1123.py (which makes spec 26)."""
NAME, MEDIUM, TEST = 'PLA FK-3000', 21, 26


def apply(t, g, ok, rec):
    U, SA, TA, S = t['Units'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson'], t['SpecializationsJson']
    (uid,) = [i for i, u in U.items() if u and u.get('Name') == NAME]
    rows = [r for r in SA.values() if r and r['UnitId'] == uid]
    ok(len(rows) == 1 and rows[0]['SpecializationId'] == MEDIUM and U[uid]['DisplayInArmory'] and S[TEST]['UIName'] == 'Test: Hidden Units'
       and not any(r and r['UnitId'] == uid for r in TA.values()), ('FK-3000: one Medium CAB card, no transport links', [(r['Id'], r['SpecializationId']) for r in rows]))
    g.put('SpecializationAvailabilitiesJson', rows[0]['Id'], {'SpecializationId': TEST})
    g.put('Units', uid, {'DisplayInArmory': False})
    ok([r['SpecializationId'] for r in SA.values() if r and r['UnitId'] == uid] == [TEST] and U[uid]['DisplayInArmory'] is False, 'FK-3000 only in test spec 26, hidden')
    rec['fk3000_hidden_1125'] = {'unit': uid, 'row': rows[0]['Id'], 'spec': [MEDIUM, TEST], 'cards': rows[0].get('MaxAvailabilityXp0')}
    print('FK-3000 HIDDEN', rec['fk3000_hidden_1125'])

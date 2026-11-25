"""Blue Dragon and Eurocorp preview specs (Osama 24 Nov 2026, thread 1567745029781454889).
21:0x first ask, done in 5a06a548 and undone here: specs 23-25 off and Eurocorp hidden unless test mode.
21:2x: "for the BD and Eurocorp preview factions. I want people to go in and see the spec and look around. But I don't want people to click on it
and see the stats. Hide the K-1's too."
- Specs 23 Blue Dragon (Testing Preview), 24 France (Preview), 25 Germany (Preview) and the Eurocorp country stay shown (no data change).
  The stat card is hidden at runtime: runtime-qa/PreviewCards.cs (test-spec.json {"show": true} shows it).
- K1 and K1A1 hidden: their spec 23 rows move to the USA test spec 27 (Test: Hidden Units), as for every hidden card (docs/roster/hidden-units.md)."""
BD, US_TEST = 23, 27
SPECS = {23: 'Blue Dragon (Testing Preview)', 24: 'France (Preview)', 25: 'Germany (Preview)'}
K1 = ('K1', 'K1A1')


def apply(t, g, ok, rec):
    S, SA, C, U = t['SpecializationsJson'], t['SpecializationAvailabilitiesJson'], t['CountriesJson'], t['Units']
    ok(all(S[i]['UIName'] == ui and S[i]['ShowInHangar'] for i, ui in SPECS.items()) and C[5]['Hidden'] is False, 'preview specs and Eurocorp shown')
    ok(S[US_TEST]['UIName'] == 'Test: Hidden Units' and S[US_TEST]['CountryId'] == 2 and S[US_TEST]['ShowInHangar'] is False, 'US test spec 27 off')
    rows = {U[r['UnitId']]['HUDName']: k for k, r in SA.items() if r and r['SpecializationId'] == BD and U[r['UnitId']]['HUDName'] in K1}
    ok(sorted(rows) == sorted(K1), ('K1 rows in Blue Dragon', rows))
    uids = {n: SA[k]['UnitId'] for n, k in rows.items()}
    ok(all(len([r for r in SA.values() if r and r['UnitId'] == u]) == 1 for u in uids.values()), 'K1 cards only in spec 23')
    for k in rows.values():
        g.put('SpecializationAvailabilitiesJson', k, {'SpecializationId': US_TEST})
    ok(all(SA[k]['SpecializationId'] == US_TEST for k in rows.values())
       and not any(r and r['SpecializationId'] == BD and r['UnitId'] in uids.values() for r in SA.values()), 'K1 / K1A1 in the US test spec only')
    rec['preview_specs'] = {'k1_to_test_spec': uids, 'bd_cards': len([r for r in SA.values() if r and r['SpecializationId'] == BD])}
    print('PREVIEW SPECS', rec['preview_specs'])

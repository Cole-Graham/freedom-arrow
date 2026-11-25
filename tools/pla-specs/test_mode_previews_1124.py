"""Blue Dragon and Eurocorp only in test mode (Osama 24 Nov 2026 21:0x PST, thread 1567745029781454889: "can we make it so that the BD and Eurocorp
units don't show unit cards when selected?", "or hidden if the test mode is off").
- Specs 23 Blue Dragon (Testing Preview), 24 France (Preview) and 25 Germany (Preview) ship with ShowInHangar False, like the test specs 26-28.
  The Armory shows a card only through a spec that is shown, and these cards are in no other spec, so no Blue Dragon or Eurocorp card shows.
- Country 5 Eurocorp ships Hidden True (the vanilla switch that hides the Editor country 3), so no empty Eurocorp flag shows.
- runtime-qa/TestSpec.cs: UserData/FreedomArrow/test-spec.json {"show": true} turns all of them back on at database load (restart to change).
  Deck creation still hides spec 23 (ArsenalOnlySpecs.cs) and France/Germany keep battlegroup size 0 (euro_bg_zero_1124.py)."""
SPECS = {23: 'Blue Dragon (Testing Preview)', 24: 'France (Preview)', 25: 'Germany (Preview)'}
EUROCORP = 5
NORMAL_SKIP = {22, 23, 24, 25, 26, 27, 28}


def apply(t, g, ok, rec):
    S, SA, C = t['SpecializationsJson'], t['SpecializationAvailabilitiesJson'], t['CountriesJson']
    ok(all(S[i]['UIName'] == ui and S[i]['ShowInHangar'] for i, ui in SPECS.items()), ('preview specs shown before', SPECS))
    ok(C[EUROCORP]['Name'] == 'Eurocorp' and C[EUROCORP]['Hidden'] is False and C[3]['Hidden'] is True, 'Eurocorp shown; vanilla Editor hidden')
    units = {i: sorted({r['UnitId'] for r in SA.values() if r and r['SpecializationId'] == i}) for i in SPECS}
    normal = {r['UnitId'] for r in SA.values() if r and r['SpecializationId'] not in NORMAL_SKIP}
    ok(not any(u in normal for us in units.values() for u in us), 'Blue Dragon / Eurocorp cards are in no normal spec')
    ok(all(S[s]['CountryId'] == EUROCORP for s in (24, 25)) and not [s for s in S.values() if s and s['CountryId'] == EUROCORP and s['Id'] not in SPECS and s['ShowInHangar']],
       'Eurocorp has no other shown spec')
    for i in SPECS:
        g.put('SpecializationsJson', i, {'ShowInHangar': False})
    g.put('CountriesJson', EUROCORP, {'Hidden': True})
    ok(all(S[i]['ShowInHangar'] is False for i in SPECS) and C[EUROCORP]['Hidden'] is True, 'previews off in the data')
    rec['test_mode_previews'] = {'specs': list(SPECS), 'cards': {SPECS[i]: len(u) for i, u in units.items()}, 'hidden_country': EUROCORP}
    print('TEST MODE PREVIEWS', rec['test_mode_previews'])

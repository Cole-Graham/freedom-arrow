"""Eurocorp: a 4th nation (preview) with the France and Germany specs (Osama 23 Nov 2026 16:4x PST, thread 1567745029781454889: "lets make this
the eurocorp flag and we put the current french spec in there", "and make this the icon to the German spec", "make sure we say (preview)").
- Country 5 'Eurocorp', shown as "Eurocorp (Preview)", flag FA_EUROCORP_FLAG (Osama's EU flag image, framed like FA_CHINA_FLAG); the other fields
  are China's (country 4): MaxPoints 10000, not hidden, no DLC.
- Spec 24 (France, france_preview.py) moves from the USA to Eurocorp and shows as "France (Preview)"; its 3 cards move with it (CountryId 5).
- Spec 25 "Germany (Preview)": a copy of spec 24 with icon FA_GERMANY (Osama's Bundeswehr cross, white like the other spec icons). No cards yet.
The Arsenal and Create Deck layouts for 4 nations are runtime-qa/NationLayout.cs."""

EURO, CHINA, FRANCE, GERMANY = 5, 4, 24, 25


def apply(t, g, ok, rec):
    C, S, SA, U = t['CountriesJson'], t['SpecializationsJson'], t['SpecializationAvailabilitiesJson'], t['Units']
    ok(EURO not in C and C[CHINA]['Name'] == 'China' and not C[CHINA]['Hidden'], 'country 5 free; China template')
    g.put('CountriesJson', EURO, {**{k: v for k, v in C[CHINA].items() if k != 'Id'}, 'Name': 'Eurocorp', 'UIName': 'Eurocorp (Preview)', 'FlagFileName': 'FA_EUROCORP_FLAG'})
    ok(S[FRANCE]['UIName'] == 'France (Testing Preview)' and S[FRANCE]['CountryId'] == 2 and GERMANY not in S, 'France spec 24 under the USA; spec 25 free')
    cards = sorted(r['UnitId'] for r in SA.values() if r and r['SpecializationId'] == FRANCE)
    ok(len(cards) == 3 and all(U[u]['CountryId'] == 2 and not any(r and r['UnitId'] == u and r['SpecializationId'] != FRANCE for r in SA.values()) for u in cards),
       ('France cards only in spec 24', cards))
    g.put('SpecializationsJson', FRANCE, {'CountryId': EURO, 'UIName': 'France (Preview)',
        'UIDescription': 'PREVIEW. Every card is a copy of a US unit: stats, weapons and prices are placeholders.'})
    for u in cards: g.put('Units', u, {'CountryId': EURO})
    g.put('SpecializationsJson', GERMANY, {**{k: v for k, v in S[FRANCE].items() if k != 'Id'}, 'Name': 'EU Germany Preview', 'UIName': 'Germany (Preview)',
        'Icon': 'FA_GERMANY', 'UIDescription': 'PREVIEW. No cards yet.'})
    ok(C[EURO]['FlagFileName'] == 'FA_EUROCORP_FLAG' and sorted(i for i, s in S.items() if s and s['CountryId'] == EURO) == [FRANCE, GERMANY]
       and all(U[u]['CountryId'] == EURO for u in cards) and not any(r and r['SpecializationId'] == GERMANY for r in SA.values()),
       'Eurocorp: France (3 cards) + Germany (no cards)')
    ok(all(s['UIName'].endswith('(Preview)') for i, s in S.items() if s and s['CountryId'] == EURO) and C[EURO]['UIName'].endswith('(Preview)'), 'all say (Preview)')
    rec['eurocorp'] = {'country': EURO, 'specs': {FRANCE: S[FRANCE]['UIName'], GERMANY: S[GERMANY]['UIName']}, 'france_cards': cards}
    print('EUROCORP', rec['eurocorp'])

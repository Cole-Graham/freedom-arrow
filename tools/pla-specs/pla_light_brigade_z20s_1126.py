"""PLA Light Brigade build, Z-20S in PLAN (Osama 26 Nov 2026 20:1x PST, thread 1567745029781454889: "Z-20S recon also copied to SF"). Branch
codex/batch/osama/pla-light-brigade only; the last plb section, so no earlier row id moves.
- Z-20S (1243, Recon tab): its PLAAF card row (2016191, 2 cards) is copied to PLAN Naval/Special Forces (20), the China SF spec, same count; the
  PLAAF card stays. A helicopter card has no transports."""
Z20S, Z20S_CARD, PLAAF, PLAN = 1243, 2016191, 17, 20


def apply(t, g, ok, rec):
    U, SA, S = t['Units'], t['SpecializationAvailabilitiesJson'], t['SpecializationsJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok(U[Z20S]['HUDName'] == 'Z-20S' and SA[Z20S_CARD]['UnitId'] == Z20S and SA[Z20S_CARD]['SpecializationId'] == PLAAF and S[PLAN]['UIName'].startswith('PLAN Naval/Special Forces'), 'Z-20S PLAAF card, PLAN spec')
    ok([c['SpecializationId'] for c in rows('SpecializationAvailabilitiesJson', UnitId=Z20S)] == [PLAAF], 'Z-20S: PLAAF card only')
    ok(not rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=Z20S_CARD), 'no transports')
    nc = g.add('SpecializationAvailabilitiesJson', SA[Z20S_CARD], {'SpecializationId': PLAN})
    cards = sorted((c['SpecializationId'], c['MaxAvailabilityXp0']) for c in rows('SpecializationAvailabilitiesJson', UnitId=Z20S))
    ok(cards == [(PLAAF, SA[Z20S_CARD]['MaxAvailabilityXp0']), (PLAN, SA[Z20S_CARD]['MaxAvailabilityXp0'])], ('Z-20S cards', cards))
    rec['pla_light_brigade_z20s_1126'] = {'card': nc, 'cards': cards}
    print('PLA LIGHT BRIGADE Z-20S', rec['pla_light_brigade_z20s_1126'])

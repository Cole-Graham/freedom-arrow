"""PLA Light Brigade build, FK-3000 out of the Medium CAB (Osama 26 Nov 2026 15:5x PST, thread 1567745029781454889: "Also remove FK-3000 from medium
cab"). Branch codex/batch/osama/pla-light-brigade only; the last plb section. The FK-3000 (1447) keeps only its Light CAB card (the copy made in
pla_light_brigade_late_1126, 4 cards); its Medium CAB card row (2021475, 4 cards, no transports) is removed."""
FK3000, MEDIUM = 1447, 21


def apply(t, g, ok, rec):
    U, SA, S = t['Units'], t['SpecializationAvailabilitiesJson'], t['SpecializationsJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    light = next(s['Id'] for s in S.values() if s and s.get('UIName', '').startswith('PLAGF Light Combined Arms Brigade'))
    cards = rows('SpecializationAvailabilitiesJson', UnitId=FK3000)
    ok(U[FK3000]['HUDName'] == 'FK-3000' and sorted(c['SpecializationId'] for c in cards) == sorted([MEDIUM, light]), ('FK-3000: Medium + Light CAB cards', [c['Id'] for c in cards]))
    (mc,) = [c for c in cards if c['SpecializationId'] == MEDIUM]
    for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=mc['Id']): g.remove('TransportAvailabilitiesJson', r['Id'])
    g.remove('SpecializationAvailabilitiesJson', mc['Id'])
    left = rows('SpecializationAvailabilitiesJson', UnitId=FK3000)
    ok([c['SpecializationId'] for c in left] == [light], 'FK-3000: Light CAB card only')
    rec['pla_light_brigade_fk3000_1126'] = {'removed_card': mc['Id'], 'left': [(c['Id'], c['MaxAvailabilityXp0']) for c in left]}
    print('PLA LIGHT BRIGADE FK-3000', rec['pla_light_brigade_fk3000_1126'])

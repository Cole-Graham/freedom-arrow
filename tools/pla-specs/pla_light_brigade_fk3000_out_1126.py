"""PLA Light Brigade build, FK-3000 out of the game (Osama 26 Nov 2026 20:1x PST, thread 1572407822849810463 "China cosmetic work": "FK-3000 remove
from the game"). Branch codex/batch/osama/pla-light-brigade only; the last plb section. The FK-3000 (1447) had one card left, the Light CAB copy
(pla_light_brigade_fk3000_1126 removed the Medium CAB one): that card and its transport rows are removed, so no deck can take it. The unit,
weapon and model rows stay (nothing else uses them; the HQ-13 SHORAD only borrows the FK-3000 turret look in its own model file)."""
FK3000 = 1447


def apply(t, g, ok, rec):
    U, SA = t['Units'], t['SpecializationAvailabilitiesJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    cards = rows('SpecializationAvailabilitiesJson', UnitId=FK3000)
    ok(U[FK3000]['HUDName'] == 'FK-3000' and len(cards) == 1, ('FK-3000: one card left', [c['Id'] for c in cards]))
    ok(not any(r for r in t['TransportAvailabilitiesJson'].values() if r and r.get('UnitId') == FK3000), 'FK-3000 is no transport')
    tr = 0
    for c in cards:
        for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=c['Id']): g.remove('TransportAvailabilitiesJson', r['Id']); tr += 1
        g.remove('SpecializationAvailabilitiesJson', c['Id'])
    ok(not rows('SpecializationAvailabilitiesJson', UnitId=FK3000), 'FK-3000: no card in any spec')
    rec['pla_light_brigade_fk3000_out_1126'] = {'removed_cards': [(c['Id'], c['SpecializationId'], c['MaxAvailabilityXp0']) for c in cards], 'removed_transport_rows': tr}
    print('PLA LIGHT BRIGADE FK-3000 OUT', rec['pla_light_brigade_fk3000_out_1126'])

"""PLA Light Brigade build, Z-20KA off the infantry cards (Osama 26 Nov 2026 20:5x PST, thread 1567745029781454889: "Z-20KA should not be in the
infantry tab as a transport option"). Branch codex/batch/osama/pla-light-brigade only; the last plb section.
- The Z-20KA (914, PLAAF helicopter card, 13 seats) is removed as a transport from every card that lists it: the 10 PLAAF infantry cards (Airborne,
  HJ-12 Team, Tank Hunters, QLU-11 Team, Pathfinders, Thunder Gods, Snipers, QW-12 Patrol, Assault Raiders, Recon). Each keeps its other
  transports (VN-3, Lynx Troop Carrier, ZBD-251, Airborne Tracked Carrier, and the Z-9 where it had it). The Z-20KA's own card is unchanged."""
Z20KA = 914


def apply(t, g, ok, rec):
    U, SA, TA = t['Units'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok(U[Z20KA]['HUDName'] == 'Z-20KA', 'Z-20KA row')
    tr = rows('TransportAvailabilitiesJson', UnitId=Z20KA)
    cards = [SA[r['SpecializationAvailabilityId']] for r in tr]
    ok(len(tr) == 10 and all(c['SpecializationId'] == 17 and U[c['UnitId']].get('Type') == 2 for c in cards), ('Z-20KA on 10 PLAAF infantry cards', len(tr)))
    for r in tr: g.remove('TransportAvailabilitiesJson', r['Id'])
    ok(not rows('TransportAvailabilitiesJson', UnitId=Z20KA) and all(rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=c['Id']) for c in cards), 'Z-20KA gone, every card keeps a transport')
    rec['pla_light_brigade_z20ka_1126'] = {'removed_from': [U[c['UnitId']]['HUDName'] for c in cards]}
    print('PLA LIGHT BRIGADE Z-20KA', rec['pla_light_brigade_z20ka_1126'])

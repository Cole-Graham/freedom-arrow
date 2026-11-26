"""PLA Light Brigade build, transport spec rules (Osama 26 Nov 2026 04:2x PST, thread 1567745029781454889: "the ZBL-191 only goes in medium cab why do I
see it all over the place? ZBL-08 goes in Marines and Medium cab only"; 02:5x "ZSL-191 should go to medium cab not Light CAB"). Branch
codex/batch/osama/pla-light-brigade only; the last plb section, after every card move.
Cause: squads moved out of the Medium CAB kept their Medium CAB transports (Moto. Riflemen -> Mountaineers and its PAP AA Patrol copy in the Light CAB,
Weapons Squad in PLAN).
- ZBL-191 (979) and ZSL-191 (1403): transport rows on cards outside the Medium CAB (21) go.
- ZBL-08 (903): transport rows on cards outside PLAN (20) and the Medium CAB go.
- Weapons Squad 火力班 (now PLAN) rides the Marines' transports (ZBD-05, Z-20J, CTL-181, ZSD-05, ZBL-08) in place of its Medium CAB set.
- Every card that had a transport keeps one (checked); a check pins the rule for later sections."""
ZBL191, ZSL191, ZBL08, PLAN, MEDIUM, WEAPONS, MARINES = 979, 1403, 903, 20, 21, 1199, 1192
ALLOWED = {ZBL191: {MEDIUM}, ZSL191: {MEDIUM}, ZBL08: {PLAN, MEDIUM}}


def apply(t, g, ok, rec):
    U, SA = t['Units'], t['SpecializationAvailabilitiesJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok([U[u]['HUDName'] for u in (ZBL191, ZSL191, ZBL08)] == ['ZBL-191', 'ZSL-191', 'ZBL-08'], 'ZBL-191, ZSL-191, ZBL-08 rows')
    (wc,) = rows('SpecializationAvailabilitiesJson', UnitId=WEAPONS); (mc,) = rows('SpecializationAvailabilitiesJson', UnitId=MARINES)
    ok(wc['SpecializationId'] == PLAN and mc['SpecializationId'] == PLAN, 'Weapons Squad and Marines cards in PLAN')
    for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=wc['Id']): g.remove('TransportAvailabilitiesJson', r['Id'])
    for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=mc['Id']): g.add('TransportAvailabilitiesJson', r, {'SpecializationAvailabilityId': wc['Id']})
    had = {r['SpecializationAvailabilityId'] for r in t['TransportAvailabilitiesJson'].values() if r}
    removed = []
    for u, allowed in ALLOWED.items():
        for r in rows('TransportAvailabilitiesJson', UnitId=u):
            c = SA[r['SpecializationAvailabilityId']]
            if c['SpecializationId'] not in allowed:
                g.remove('TransportAvailabilitiesJson', r['Id']); removed.append((U[c['UnitId']]['HUDName'], U[u]['HUDName']))
    # checks after
    ok(all(SA[r['SpecializationAvailabilityId']]['SpecializationId'] in ALLOWED[r['UnitId']] for r in t['TransportAvailabilitiesJson'].values() if r and r['UnitId'] in ALLOWED), 'transport spec rules hold')
    ok(all(rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=c) for c in had), 'every card that had a transport keeps one')
    rec['pla_light_brigade_transport_rules_1126'] = {'removed': removed, 'weapons_squad': [U[r['UnitId']]['HUDName'] for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=wc['Id'])]}
    print('PLA LIGHT BRIGADE TRANSPORT RULES', rec['pla_light_brigade_transport_rules_1126'])

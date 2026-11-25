"""ZSD-89A out of the PLAN Naval/Special Forces spec (Osama 25 Nov 2026 01:5x PST, thread 1567745029781454889: "ZSD-89A removed from marines").
The PLAN copy (1250, 'PLA Catalogue Type 89A') is a transport only, for the 12 spec 20 squads (marines and SF); all its links go and it is
hidden in the Armory, as zbd03_zsd89a_hidden_1124.py did for the Airborne copy. Every squad keeps the ZSD-05, CSK-181 and Z-20J
(and the ZBD-05 except Godswords). The ZSD-89A copies of other specs (1065 Rocket Force, 1248 Armored) are not changed."""
ZSD89A = 1250


def apply(t, g, ok, rec):
    U, TA, SA = t['Units'], t['TransportAvailabilitiesJson'], t['SpecializationAvailabilitiesJson']
    ok(U[ZSD89A]['HUDName'] == 'ZSD-89A' and not any(r and r['UnitId'] == ZSD89A for r in SA.values()), 'ZSD-89A 1250: transport only')
    links = sorted([r for r in TA.values() if r and r['UnitId'] == ZSD89A], key=lambda r: r['Id'])
    ok(len(links) == 12 and all(SA[r['SpecializationAvailabilityId']]['SpecializationId'] == 20 for r in links), ('12 PLAN links', len(links)))
    squads = sorted(SA[r['SpecializationAvailabilityId']]['UnitId'] for r in links)
    for r in links: g.remove('TransportAvailabilitiesJson', r['Id'])
    g.put('Units', ZSD89A, {'DisplayInArmory': False})
    left = {q: [U[r['UnitId']]['HUDName'] for r in TA.values() if r and SA[r['SpecializationAvailabilityId']]['UnitId'] == q and SA[r['SpecializationAvailabilityId']]['SpecializationId'] == 20] for q in squads}
    ok(all(len(v) >= 3 and 'ZSD-89A' not in v and 'ZSD-05' in v for v in left.values()), ('PLAN squads keep 3+ transports incl. ZSD-05', left))
    rec['zsd89a_plan_removed_1125'] = {'unit': ZSD89A, 'links_removed': [r['Id'] for r in links], 'squads': squads}
    print('ZSD-89A PLAN', rec['zsd89a_plan_removed_1125'])

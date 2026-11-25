"""ZBD-251 for every Airborne team (Osama 25 Nov 2026 10:0x PST, thread 1567745029781454889: "Airborne teams are missing their ZBD-251 transport").
The ZBD-251 (1056, 9 seats) carried 7 of the 10 PLAAF Air Force (spec 17) squads; Airborne (8 men), Thunder Gods (9) and Assault Raiders (9)
had no link although they fit. Each gets one, copied from an existing ZBD-251 link with its own spec 17 availability row."""
ZBD251, SQUADS = 1056, (1136, 1143, 1146)


def apply(t, g, ok, rec):
    U, TA, SA, SM = t['Units'], t['TransportAvailabilitiesJson'], t['SpecializationAvailabilitiesJson'], t['SquadMembersJson']
    ok(U[ZBD251]['HUDName'] == 'ZBD-251' and U[ZBD251]['InfantrySlots'] == 9, 'ZBD-251 9 seats')
    links = [r for r in TA.values() if r and r['UnitId'] == ZBD251 and SA[r['SpecializationAvailabilityId']]['SpecializationId'] == 17]
    ok(len(links) == 7, ('ZBD-251 airborne links', len(links)))
    added = []
    for q in SQUADS:
        (sa,) = [r for r in SA.values() if r and r['UnitId'] == q and r['SpecializationId'] == 17]
        men = sum(1 for m in SM.values() if m and m['UnitId'] == q)
        ok(men <= 9 and not any(r and r['UnitId'] == ZBD251 and r['SpecializationAvailabilityId'] == sa['Id'] for r in TA.values()), (U[q]['HUDName'], men))
        added.append(g.add('TransportAvailabilitiesJson', links[0], {'SpecializationAvailabilityId': sa['Id']}))
    ok(len([r for r in TA.values() if r and r['UnitId'] == ZBD251 and SA[r['SpecializationAvailabilityId']]['SpecializationId'] == 17]) == 10, 'all 10 airborne squads have the ZBD-251')
    rec['zbd251_airborne_1125'] = {'squads': list(SQUADS), 'links': added}
    print('ZBD-251 AIRBORNE', rec['zbd251_airborne_1125'])

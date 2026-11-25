"""ZBD-03 cards hidden for now, ZSD-89A out of the Airborne spec (Osama 24 Nov 2026 23:2x PST, thread "China cosmetic work": "ZBD-03 recon and
normal version hidden because the models aren't good (this is temporary). ZSD-89A removed from airborne").
- ZBD-03 Recon (1257): its one card row 2018409 (PLAAF Air Force spec 17, 4 cards) goes; hidden in the Armory.
- ZBD-03 (1074): a transport only (Snipers 1144, Recon 1149 in spec 17, rows 2012069 / 2012193); both links go; hidden in the Armory.
- ZSD-89A PLAAF (1249): a transport only, for the 10 spec 17 airborne squads (rows 2018156-2018165); all links go; hidden in the Armory.
  The other ZSD-89A units (1065, 1248, 1250) are not changed.
Unit, weapon and ammunition rows stay, so the cards come back by restoring these rows. Removes rows only; runs after every row-creating section.
Not added to the hidden-units test spec 26 (that section runs earlier and creates rows)."""
ZBD03, ZBD03R, ZSD89A = 1074, 1257, 1249
SA_ZBD03R = [2018409]
TA_ZBD03 = [2012069, 2012193]
TA_ZSD89A = list(range(2018156, 2018166))


def apply(t, g, ok, rec):
    U, SA, TA = t['Units'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson']

    def sa(u): return sorted(r['Id'] for r in SA.values() if r and r['UnitId'] == u)
    def ta(u): return sorted(r['Id'] for r in TA.values() if r and r['UnitId'] == u)
    ok(U[ZBD03]['HUDName'] == 'ZBD-03' and U[ZBD03R]['HUDName'] == 'ZBD-03 Recon' and U[ZSD89A]['Name'] == 'PLA Catalogue Type 89A PLAAF',
       'ZBD-03 / ZBD-03 Recon / ZSD-89A PLAAF units')
    ok(sa(ZBD03R) == SA_ZBD03R and SA[SA_ZBD03R[0]]['SpecializationId'] == 17 and not ta(ZBD03R), ('ZBD-03 Recon: one spec 17 card row', sa(ZBD03R)))
    ok(not sa(ZBD03) and ta(ZBD03) == TA_ZBD03, ('ZBD-03: transport rows only', ta(ZBD03)))
    ok(not sa(ZSD89A) and ta(ZSD89A) == TA_ZSD89A, ('ZSD-89A PLAAF: 10 transport rows only', ta(ZSD89A)))
    squads = sorted({SA[TA[i]['SpecializationAvailabilityId']]['UnitId'] for i in TA_ZBD03 + TA_ZSD89A})
    ok(all(SA[TA[i]['SpecializationAvailabilityId']]['SpecializationId'] == 17 for i in TA_ZBD03 + TA_ZSD89A), 'all links in spec 17')
    others = {u: sorted(r['Id'] for r in SA.values() if r and r['UnitId'] in (1065, 1248, 1250) and r['UnitId'] == u) for u in (1065, 1248, 1250)}
    for i in SA_ZBD03R: g.remove('SpecializationAvailabilitiesJson', i)
    for i in TA_ZBD03 + TA_ZSD89A: g.remove('TransportAvailabilitiesJson', i)
    for u in (ZBD03, ZBD03R, ZSD89A): g.put('Units', u, {'DisplayInArmory': False})
    ok(all(not sa(u) and not ta(u) and U[u]['DisplayInArmory'] is False for u in (ZBD03, ZBD03R, ZSD89A)), 'ZBD-03 x2 and ZSD-89A PLAAF hidden')
    left = {}
    for s in squads:
        avs = [r['Id'] for r in SA.values() if r and r['UnitId'] == s and r['SpecializationId'] == 17]
        left[s] = sorted({U[r['UnitId']]['HUDName'] for r in TA.values() if r and r['SpecializationAvailabilityId'] in avs})
    ok(all(left.values()), ('every affected squad keeps a transport', left))
    ok(others == {u: sorted(r['Id'] for r in SA.values() if r and r['UnitId'] == u) for u in (1065, 1248, 1250)}, 'other ZSD-89A rows unchanged')
    rec['zbd03_zsd89a_hidden_1124'] = {'hidden': [ZBD03, ZBD03R, ZSD89A], 'sa_removed': SA_ZBD03R, 'ta_removed': TA_ZBD03 + TA_ZSD89A,
                                       'squad_transports_left': {U[s]['HUDName']: v for s, v in left.items()}}
    print('ZBD-03 / ZSD-89A', rec['zbd03_zsd89a_hidden_1124'])

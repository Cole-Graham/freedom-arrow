"""Lateralus 22 Nov 2026 17:4x PST, thread 1572962048705429598: "ZTQ-15 Recon optics Good -> Very Good", "ZTL-191 Recon optics Good -> Very Good",
"Snipers (PLAAF) are missing their laser (or missing their laser ability icon on the card? or both..)". Called from batch_0_9_5b.py.
- ZTQ-15 Recon (1240) and ZTL-191 Recon (1263): section 14 linked them to vanilla sensor row 1 "Good Optics" (1650 ground); they now link
  vanilla row 3 "Very Good Optics" (2300 ground, the ZBD-04A Recon / M3A3 CFV level). Shared vanilla rows are not edited.
- Snipers 狙击组 (1144, the PLAAF card): both. The card icons and the battle read the same ability row (docs: ability-card-vs-battle), and
  1144 links row 103 "Sprint30 Smoke" (no laser; it had row 81, also no laser, before section 3). Vanilla row 28 "Sprint Smoke Laser", used by every
  US/RU sniper team and the other China sniper cards (1161, 1202), is row 103 plus the 1200 m laser designator, so 1144 links row 28."""


def apply(t, g, ok, rec):
    U, SN, SU, AB, UAB = t['Units'], t['SensorsJson'], t['SensorUnitsJson'], t['AbilitiesJson'], t['UnitAbilitiesJson']
    ok((SN[1]['Name'], SN[1]['OpticsGround'], SN[3]['Name'], SN[3]['OpticsGround']) == ('Good Optics', 1650.0, 'Very Good Optics', 2300.0), 'vanilla sensor rows 1 / 3')
    out = {}
    for u, n in ((1240, 'ZTQ-15 Recon'), (1263, 'ZTL-191 Recon')):
        r = [x for x in SU.values() if x and x.get('UnitId') == u]
        ok(U[u]['HUDName'].strip() == n and U[u]['CountryId'] == 4 and len(r) == 1 and r[0]['SensorId'] == 1, (n, 'on vanilla sensor row 1'))
        g.put('SensorUnitsJson', r[0]['Id'], {'SensorId': 3})
        out[n] = [1, 3]
    ok(U[1144]['HUDName'].startswith('Snipers') and U[1144]['CountryId'] == 4, '1144 is the China Snipers card')
    keys = set(AB[103]) - {'Id', 'Name', 'IsLaserDesignator', 'LaserMaxRange', 'LaserUsableInMove'}
    ok(all(AB[103].get(k) == AB[28].get(k) for k in keys) and not AB[103]['IsLaserDesignator'] and AB[28]['IsLaserDesignator'] and AB[28]['LaserMaxRange'] == 1200.0,
       'ability 28 = ability 103 + 1200 m laser')
    r = [x for x in UAB.values() if x and x.get('UnitId') == 1144]
    ok(len(r) == 1 and r[0]['AbilityId'] == 103, ('1144 ability links', r))
    g.put('UnitAbilitiesJson', r[0]['Id'], {'AbilityId': 28})
    ok(all(AB[x['AbilityId']]['IsLaserDesignator'] for x in UAB.values() if x and x.get('UnitId') in (1144, 1161, 1202)), 'all China sniper cards have the laser')
    rec['recon_sniper_1122'] = {'optics': out, 'snipers_1144_ability': [103, 28]}

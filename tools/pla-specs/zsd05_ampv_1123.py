"""ZSD-05 = amphibious 8-seat M1283 AMPV (Osama 23 Nov 2026 22:3x PST, thread 1567745029781454889: "ZSD-05 is just a copy of the AMPV except 8 seats
and amphibious"). MODEL BUILD ONLY. Last in the batch, so the new unit id follows every existing card.
- New unit 'PLA ZSD-05': full copy of vanilla 'M1283 AMPV' (41: body, armour, both mobility rows, abilities, sensors, turrets, ammunition, its
  weapon/armour modifications with all 7 options, 25 pts), CountryId 4. InfantrySlots 12 -> 8.
- Amphibious: its own copies of both AMPV mobility rows (206 base, 2019697 reactive armour / APS) with IsAmphibious True; the two options that
  switch mobility point at the copies. WaterDiveOffset 1.23 from the ZBD-05 (the PLA amphibious IFV on the same 05 chassis).
- Like the AMPV it is a transport, no own card: offered to every PLAN Naval/Special Forces (spec 20) infantry card that already has transports.
  No model yet (the ZSD-05 download is pending), so it shows the AMPV until one is staged under models.json 'PLA ZSD-05'."""
AMPV, ZBD05, SPEC, NAME = 41, 1076, 20, 'PLA ZSD-05'


def apply(t, g, ok, rec):
    U, S, SA, TA, O = t['Units'], t['SpecializationsJson'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson'], t['OptionsJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    ok(U[AMPV]['Name'] == 'M1283 AMPV' and U[AMPV]['InfantrySlots'] == 12 and U[ZBD05]['WaterDiveOffset'] == 1.23, 'AMPV 41 (12 seats); ZBD-05 dive offset')
    ok(S[SPEC]['Name'] == 'PLA PLAN Special Forces' and not any(u and NAME in (u.get('Name'), u.get('HUDName')) for u in U.values()), 'spec 20; name free')
    d = dict(U[AMPV]); d.pop('Id')
    d.update({'Name': NAME, 'HUDName': 'ZSD-05', 'OriginalCost': 0, 'CountryId': 4, 'DisplayInArmory': True, 'Description': None, 'OriginalName': None,
              'InfantrySlots': 8, 'WaterDiveOffset': U[ZBD05]['WaterDiveOffset']})
    uid = g.put('Units', max(U) + 1, d)
    for r in rows('UnitArmorsJson', UnitId=AMPV):
        g.add('UnitArmorsJson', r, {'UnitId': uid, 'ArmorId': g.add('ArmorsJson', t['ArmorsJson'][r['ArmorId']], {'Name': f"{t['ArmorsJson'][r['ArmorId']]['Name']} {NAME}"})})
    mob = {}
    for r in rows('UnitPropulsionsJson', UnitId=AMPV):
        mob[r['MobilityId']] = g.add('MobilityJson', t['MobilityJson'][r['MobilityId']], {'Name': f"{t['MobilityJson'][r['MobilityId']]['Name']} {NAME}", 'IsAmphibious': True})
        g.add('UnitPropulsionsJson', r, {'UnitId': uid, 'MobilityId': mob[r['MobilityId']]})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson'):
        for r in rows(tab, UnitId=AMPV): g.add(tab, r, {'UnitId': uid})
    for m in rows('ModificationsJson', UnitId=AMPV):
        nm = g.add('ModificationsJson', m, {'UnitId': uid})
        for o in rows('OptionsJson', ModificationId=m['Id']):
            g.add('OptionsJson', o, {'ModificationId': nm, **({'MobilityId': mob[o['MobilityId']]} if o.get('MobilityId') else {})})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitPropulsionsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson', 'ModificationsJson', 'UnitArmorsJson'):
        ok(len(rows(tab, UnitId=uid)) == len(rows(tab, UnitId=AMPV)), ('ZSD-05', tab, 'copied'))
    opts = [o for m in rows('ModificationsJson', UnitId=uid) for o in rows('OptionsJson', ModificationId=m['Id'])]
    ok(len(opts) == 7 and all(not o.get('MobilityId') or o['MobilityId'] in mob.values() for o in opts), 'ZSD-05: 7 options, mobility options use the amphibious copies')
    ok(all(t['MobilityJson'][r['MobilityId']]['IsAmphibious'] for r in rows('UnitPropulsionsJson', UnitId=uid))
       and not any(t['MobilityJson'][r['MobilityId']]['IsAmphibious'] for r in rows('UnitPropulsionsJson', UnitId=AMPV)), 'ZSD-05 amphibious; AMPV unchanged')
    tpl = next(r for r in sorted(TA.values(), key=lambda r: r['Id']) if r)
    inf = [r for r in sorted(SA.values(), key=lambda r: r['Id']) if r and r['SpecializationId'] == SPEC and U[r['UnitId']].get('Type') == 2
           and any(x and x.get('SpecializationAvailabilityId') == r['Id'] for x in TA.values())]
    ok(len(inf) >= 8, ('PLAN infantry cards with transports', len(inf)))
    for r in inf: g.add('TransportAvailabilitiesJson', tpl, {'SpecializationAvailabilityId': r['Id'], 'UnitId': uid})
    ok(len(rows('TransportAvailabilitiesJson', UnitId=uid)) == len(inf) and not rows('SpecializationAvailabilitiesJson', UnitId=uid), 'transport only')
    rec['zsd05_ampv'] = {'unit': uid, 'cost': U[uid]['Cost'], 'seats': U[uid]['InfantrySlots'], 'mobility': mob, 'options': len(opts),
                         'infantry_cards': [U[r['UnitId']]['HUDName'] for r in inf]}
    print('ZSD-05', rec['zsd05_ampv'])

"""PLA PLZ-25 card for the MarkII_ PLZ-25 model (Osama 23 Nov 2026 21:5x PST, thread "China cosmetic work": "did we add the PLZ25? it should go into
navy"). The PLZ-25 is the 120 mm gun-mortar of the PLL-05 (926) on the amphibious tracked 05 chassis, so: a full copy of PLL-05 (weapons, ammo,
options, abilities, sensors, 80 pts) with its own copies of the ZBD-05 (1076) armour row (front 100 / sides 60 / rear+top 40, 12 HP) and mobility
row (70 road / 55 cross-country, tracked speeds), 3 cards in PLAN Naval/Special Forces (20) beside the PLZ-07B. Runs last; model work/c5-cn-1123
slug plz25 (models.json key = Name)."""
GUN, CHASSIS, NAME, HUD, SPEC, CARDS = 926, 1076, 'PLA PLZ-25', 'PLZ-25', 20, 3


def apply(t, g, ok, rec):
    U, S, SA = t['Units'], t['SpecializationsJson'], t['SpecializationAvailabilitiesJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    ok(U[GUN]['Name'] == 'PLA PLL-05' and U[CHASSIS]['Name'] == 'PLA Catalogue ZBD-05', 'PLL-05 / ZBD-05 rows')
    ok(not any(u and NAME in (u.get('Name'), u.get('HUDName')) for u in U.values()), NAME + ' name free')
    ok(S[SPEC]['UIName'].startswith('PLAN Naval/Special Forces'), 'spec 20 = navy')
    tpl = next(r for r in rows('SpecializationAvailabilitiesJson', SpecializationId=SPEC) if U[r['UnitId']]['Name'] == 'PLA PLZ-07B')
    d = dict(U[GUN]); d.pop('Id'); d.update({'Name': NAME, 'HUDName': HUD, 'OriginalCost': 0, 'DisplayInArmory': True, 'Description': None, 'OriginalName': None})
    uid = g.put('Units', max(U) + 1, d)
    for tab, field, target in (('UnitArmorsJson', 'ArmorId', 'ArmorsJson'), ('UnitPropulsionsJson', 'MobilityId', 'MobilityJson')):
        src = rows(tab, UnitId=CHASSIS); ok(len(src) == 1 and len(rows(tab, UnitId=GUN)) == 1, (tab, 'one row each'))
        g.add(tab, rows(tab, UnitId=GUN)[0], {'UnitId': uid, field: g.add(target, t[target][src[0][field]], {'Name': f'PLA PLZ-25 {target}'})})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson'):
        for r in rows(tab, UnitId=GUN): g.add(tab, r, {'UnitId': uid})
    nopt = 0
    for m in rows('ModificationsJson', UnitId=GUN):
        nm = g.add('ModificationsJson', m, {'UnitId': uid})
        for o in rows('OptionsJson', ModificationId=m['Id']): g.add('OptionsJson', o, {'ModificationId': nm}); nopt += 1
    g.add('SpecializationAvailabilitiesJson', tpl, {'UnitId': uid, 'SpecializationId': SPEC, 'MaxAvailabilityXp0': CARDS})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson', 'ModificationsJson', 'UnitArmorsJson', 'UnitPropulsionsJson'):
        ok(len(rows(tab, UnitId=uid)) == len(rows(tab, UnitId=GUN)), (NAME, tab, 'copied'))
    a = t['ArmorsJson'][rows('UnitArmorsJson', UnitId=uid)[0]['ArmorId']]; mo = t['MobilityJson'][rows('UnitPropulsionsJson', UnitId=uid)[0]['MobilityId']]
    ok((a['KinArmorFront'], a['MaxHealthPoints'], mo['MaxSpeedRoad']) == (100, 12, 70.0), 'ZBD-05 armour + mobility')
    rec['plz25'] = {'unit': uid, 'cost': U[uid]['Cost'], 'spec': SPEC, 'cards': CARDS, 'options': nopt, 'armour': [a['KinArmorFront'], a['KinArmorSides'], a['KinArmorRear'], a['MaxHealthPoints']], 'road': mo['MaxSpeedRoad']}
    print('PLZ-25', rec['plz25'])

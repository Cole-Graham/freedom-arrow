"""ZBD-04 for the PLARF Rocket Conscript Force (Osama 23 Nov 2026 15:1x PST, thread "blue dragons": "let's make the ZBD-04 for rocket force",
"same stats as the ZBD-04A but we make it much less armored", "probably BMP-3 level?").
Full copy of PLA ZBD-04A (902) with the vanilla BMP-3 base armour row (2000440 'Armor BMP3 Base': KE/HEAT front 100, sides 60, rear 40, top 40, 12 HP),
linked as it is (Lateralus: link an existing row with the wanted values). ZBD-04A had HEAT front 350 / sides 150, rear 60.
Offered the way ZBD-04A is in Armored Force: as a transport, here for every PLARF infantry card that already has transports (12).
FAModels draws Shawn's modified ZBD-04 (work/china-new-20261122 m_zbd04_*; models.json key = NAME)."""
NAME, HUD, PARENT, ARMOR, SPEC = 'PLA ZBD-04 Rocket Force', 'ZBD-04', 902, 2000440, 19


def apply(t, g, ok, rec):
    U, S, SA, TA, AR = t['Units'], t['SpecializationsJson'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson'], t['ArmorsJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    ok(U[PARENT]['Name'] == 'PLA ZBD-04A' and S[SPEC]['Name'] == 'PLA PLARF Rocket Conscript Force', 'ZBD-04A 902, PLARF spec 19')
    a = AR[ARMOR]
    ok(a['Name'] == 'Armor BMP3 Base' and (a['KinArmorFront'], a['HeatArmorFront'], a['KinArmorSides'], a['HeatArmorSides'], a['KinArmorRear'], a['KinArmorTop'], a['MaxHealthPoints']) == (100, 100, 60, 60, 40, 40, 12),
       'BMP-3 base armour row')
    ok(not any(u and NAME in (u.get('Name'), u.get('HUDName')) for u in U.values()), NAME + ' name free')
    d = dict(U[PARENT]); d.pop('Id'); d.update({'Name': NAME, 'HUDName': HUD, 'OriginalCost': 0})
    uid = g.put('Units', max(U) + 1, d)
    (ua,) = rows('UnitArmorsJson', UnitId=PARENT)
    g.add('UnitArmorsJson', ua, {'UnitId': uid, 'ArmorId': ARMOR})
    for r in rows('UnitPropulsionsJson', UnitId=PARENT):
        g.add('UnitPropulsionsJson', r, {'UnitId': uid, 'MobilityId': g.add('MobilityJson', t['MobilityJson'][r['MobilityId']], {'Name': f'{t["MobilityJson"][r["MobilityId"]]["Name"]} {NAME}'})})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson'):
        for r in rows(tab, UnitId=PARENT): g.add(tab, r, {'UnitId': uid})
    for m in rows('ModificationsJson', UnitId=PARENT):
        nm = g.add('ModificationsJson', m, {'UnitId': uid})
        for o in rows('OptionsJson', ModificationId=m['Id']): g.add('OptionsJson', o, {'ModificationId': nm})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitPropulsionsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson', 'ModificationsJson', 'UnitArmorsJson'):
        ok(len(rows(tab, UnitId=uid)) == len(rows(tab, UnitId=PARENT)), (NAME, tab, 'copied'))
    tpl = next(r for r in TA.values() if r and r.get('UnitId') == PARENT)
    inf = [r for r in sorted(SA.values(), key=lambda r: r['Id']) if r and r['SpecializationId'] == SPEC and any(x and x.get('SpecializationAvailabilityId') == r['Id'] for x in TA.values())]
    ok(len(inf) == 12 and all(U[r['UnitId']].get('Type') == 2 for r in inf), ('12 PLARF infantry cards with transports', len(inf)))
    for r in inf: g.add('TransportAvailabilitiesJson', tpl, {'SpecializationAvailabilityId': r['Id'], 'UnitId': uid})
    ok(sum(1 for x in TA.values() if x and x.get('UnitId') == uid) == 12, 'ZBD-04 Rocket Force offered to 12 PLARF infantry cards')
    ok(U[uid]['Cost'] == U[PARENT]['Cost'], 'price = ZBD-04A')
    rec['zbd04_rocket_force'] = {'unit': uid, 'parent': PARENT, 'cost': U[uid]['Cost'], 'armor': ARMOR, 'spec': SPEC,
                                 'infantry_cards': [U[r['UnitId']]['HUDName'] for r in inf]}

"""PLA ZTZ-98 (Osama 23 Nov 2026 15:0x, thread 1572407822849810463: "did Shawn uploada ZTZ-98 model for us?", "add it to our model build and boot it
up, armory focused only", "we'll give it to the rocket force"). Full copy of PLA Catalogue ZTZ-99 (1083) with its option slots, same price and
cards, in PLA PLARF Rocket Conscript Force (spec 19). Stats are the ZTZ-99's until balance values are given. FAModels draws Shawn's ZTZ-98
(models.json key = NAME; work/ztz98-1123)."""
NAME, HUD, PARENT, SPEC = 'PLA ZTZ-98', 'ZTZ-98', 1083, 19


def apply(t, g, ok, rec):
    U, S = t['Units'], t['SpecializationsJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    ok(U[PARENT]['Name'] == 'PLA Catalogue ZTZ-99' and S[SPEC]['Name'] == 'PLA PLARF Rocket Conscript Force', 'ZTZ-98 parent ZTZ-99 1083, spec 19 Rocket Force')
    ok(not any(u and NAME in (u.get('Name'), u.get('HUDName')) for u in U.values()), NAME + ' name free')
    d = dict(U[PARENT]); d.pop('Id'); d.update({'Name': NAME, 'HUDName': HUD, 'OriginalCost': 0, 'DisplayInArmory': True})
    uid = g.put('Units', max(U) + 1, d)
    for tab, field, target in (('UnitArmorsJson', 'ArmorId', 'ArmorsJson'), ('UnitPropulsionsJson', 'MobilityId', 'MobilityJson')):
        for r in rows(tab, UnitId=PARENT):
            g.add(tab, r, {'UnitId': uid, field: g.add(target, t[target][r[field]], {'Name': f'{t[target][r[field]]["Name"]} {NAME}'})})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson'):
        for r in rows(tab, UnitId=PARENT): g.add(tab, r, {'UnitId': uid})
    for m in rows('ModificationsJson', UnitId=PARENT):
        nm = g.add('ModificationsJson', m, {'UnitId': uid})
        for o in rows('OptionsJson', ModificationId=m['Id']): g.add('OptionsJson', o, {'ModificationId': nm})
    sa = rows('SpecializationAvailabilitiesJson', UnitId=PARENT)
    ok(len(sa) >= 1, 'ZTZ-99 has a card row')
    g.add('SpecializationAvailabilitiesJson', sa[0], {'UnitId': uid, 'SpecializationId': SPEC})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitArmorsJson', 'UnitPropulsionsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson', 'ModificationsJson'):
        ok(len(rows(tab, UnitId=uid)) == len(rows(tab, UnitId=PARENT)), (NAME, tab, 'copied'))
    av = [(r['SpecializationId'], r['MaxAvailabilityXp0']) for r in rows('SpecializationAvailabilitiesJson', UnitId=uid)]
    ok(av == [(SPEC, sa[0]['MaxAvailabilityXp0'])] and U[uid]['Cost'] == U[PARENT]['Cost'], 'ZTZ-98 in Rocket Force, ZTZ-99 price and cards')
    rec['ztz98'] = {'unit': uid, 'name': NAME, 'cost': U[uid]['Cost'], 'spec': SPEC, 'cards': av}
    print('ZTZ-98', rec['ztz98'])

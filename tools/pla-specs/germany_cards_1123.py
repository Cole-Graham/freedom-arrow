"""Germany (Preview) cards for the 3 German set-piece models Osama bought (23 Nov 2026 16:5x PST, thread "blue dragons": "I downloaded 3 german
vehicles, can you please add them into the game? theyre setpieces so allocate higher budget for their armory models"). Runs after eurocorp_1123.py
(spec 25, country 5). Like france_preview.py, each card is a full copy of a US unit WITH its options; stats, weapons and prices are placeholders.
FAModels draws the CGTrader models (work/german-20261123; models.json key = Name)."""
GERMANY, EURO = 25, 5
# Name: (HUDName, parent unit id, parent HUDName, cost, cards)
CARDS = {
    'DE Leopard 2A6': ('Leopard 2A6', 191, 'M1A2 SEP v3', 260, 2),
    'DE Puma': ('Puma', 16, 'M2A3 Bradley', 65, 4),
    'DE Marder 1A3': ('Marder 1A3', 15, 'M2A2 Bradley', 50, 4),
}


def apply(t, g, ok, rec):
    U, S, SA = t['Units'], t['SpecializationsJson'], t['SpecializationAvailabilitiesJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    ok(S[GERMANY]['UIName'] == 'Germany (Preview)' and S[GERMANY]['CountryId'] == EURO and not any(r and r['SpecializationId'] == GERMANY for r in SA.values()),
       'Germany spec 25 under Eurocorp, no cards yet')
    g.put('SpecializationsJson', GERMANY, {'UIDescription': 'PREVIEW. Every card is a copy of a US unit: stats, weapons and prices are placeholders.'})
    tpl = next(r for r in SA.values() if r and r['UnitId'] == 2 and r['SpecializationId'] == 4)
    res = {}
    for name, (hud, parent, phud, cost, n) in CARDS.items():
        ok(U[parent]['HUDName'] == phud and U[parent]['CountryId'] == 2, (name, 'parent', parent, U[parent]['HUDName']))
        ok(not any(u and name in (u.get('Name'), u.get('HUDName')) for u in U.values()), name + ' name free')
        d = dict(U[parent]); d.pop('Id')
        d.update({'Name': name, 'HUDName': hud, 'Cost': cost, 'OriginalCost': 0, 'Description': None, 'OriginalName': None, 'DisplayInArmory': True, 'CountryId': EURO})
        uid = g.put('Units', max(U) + 1, d)
        for tab, field, target in (('UnitArmorsJson', 'ArmorId', 'ArmorsJson'), ('UnitPropulsionsJson', 'MobilityId', 'MobilityJson')):
            for r in rows(tab, UnitId=parent):
                g.add(tab, r, {'UnitId': uid, field: g.add(target, t[target][r[field]], {'Name': f'{t[target][r[field]]["Name"]} {name} GermanyPreview'})})
        for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson'):
            for r in rows(tab, UnitId=parent): g.add(tab, r, {'UnitId': uid})
        nopt = 0
        for m in rows('ModificationsJson', UnitId=parent):
            nm = g.add('ModificationsJson', m, {'UnitId': uid})
            for o in rows('OptionsJson', ModificationId=m['Id']): g.add('OptionsJson', o, {'ModificationId': nm}); nopt += 1
        g.add('SpecializationAvailabilitiesJson', tpl, {'UnitId': uid, 'SpecializationId': GERMANY, 'MaxAvailabilityXp0': n})
        for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitArmorsJson', 'UnitPropulsionsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson', 'ModificationsJson'):
            ok(len(rows(tab, UnitId=uid)) == len(rows(tab, UnitId=parent)), (name, tab, 'copied'))
        res[name] = {'unit': uid, 'hud': hud, 'parent': f'{phud} ({parent})', 'cost': cost, 'cards': n, 'options': nopt}
    ok(sorted(r['UnitId'] for r in SA.values() if r and r['SpecializationId'] == GERMANY) == sorted(v['unit'] for v in res.values()), 'spec 25 = the 3 German cards')
    rec['germany_cards'] = {'spec': GERMANY, 'cards': res}
    print('GERMANY', res)

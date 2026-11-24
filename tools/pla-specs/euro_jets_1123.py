"""Rafale C (France preview, spec 24), Eurofighter Typhoon and Leopard 2A7 (Germany preview, spec 25) cards for Osama's two set-piece jets
(23 Nov 2026 20:1x PST, thread "China cosmetic work": "I downloaded the Typhoon and Rafale, again these are set pieces so make sure they look
good. you can put it on the next build"; 20:1x "prep these two planes for the one after that"). Same pattern as the Mirage 2000D RMV card
(france_preview.py): a full copy of the F-16C (285) WITH its options; stats, weapons and prices are placeholders. Runs LAST in the batch so
the new unit ids come after every existing card (no id shifts for saved decks). FAModels draws work/euro-jets-1123 (models.json key = Name)."""
FRANCE, GERMANY, EURO = 24, 25, 5
# Name: (HUDName, spec, parent unit id, parent HUDName, cost, cards)
CARDS = {
    'FR Rafale C': ('Rafale C', FRANCE, 285, 'F-16C Fighting Falcon', 145, 3),
    'DE Eurofighter Typhoon': ('Eurofighter Typhoon', GERMANY, 285, 'F-16C Fighting Falcon', 145, 3),
    # Osama 23 Nov 2026 21:0x: "I just downloaded a Leopard 2a6 (let's call it Leopard 2A7) and add it to the armory preview" (copy of the M1A2 SEP v3,
    # as the DE Leopard 2A6 card; model work/leo2a7-1123)
    'DE Leopard 2A7': ('Leopard 2A7', GERMANY, 191, 'M1A2 SEP v3', 260, 2),
}


def apply(t, g, ok, rec):
    U, S, SA = t['Units'], t['SpecializationsJson'], t['SpecializationAvailabilitiesJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    ok(S[FRANCE]['UIName'] == 'France (Preview)' and S[GERMANY]['UIName'] == 'Germany (Preview)' and S[FRANCE]['CountryId'] == S[GERMANY]['CountryId'] == EURO,
       ('France / Germany preview specs under Eurocorp', S[FRANCE]['UIName'], S[GERMANY]['UIName']))
    mirage = next(r for r in SA.values() if r and r['SpecializationId'] == FRANCE and U[r['UnitId']]['Name'] == 'FR Mirage 2000D RMV')
    res = {}
    for name, (hud, spec, parent, phud, cost, n) in CARDS.items():
        ok(U[parent]['HUDName'] == phud and U[parent]['CountryId'] == 2, (name, 'parent', parent, U[parent]['HUDName']))
        ok(not any(u and name in (u.get('Name'), u.get('HUDName')) for u in U.values()), name + ' name free')
        d = dict(U[parent]); d.pop('Id')
        d.update({'Name': name, 'HUDName': hud, 'Cost': cost, 'OriginalCost': 0, 'Description': None, 'OriginalName': None, 'DisplayInArmory': True,
                  'CountryId': U[mirage['UnitId']]['CountryId']})
        uid = g.put('Units', max(U) + 1, d)
        for tab, field, target in (('UnitArmorsJson', 'ArmorId', 'ArmorsJson'), ('UnitPropulsionsJson', 'MobilityId', 'MobilityJson')):
            for r in rows(tab, UnitId=parent):
                g.add(tab, r, {'UnitId': uid, field: g.add(target, t[target][r[field]], {'Name': f'{t[target][r[field]]["Name"]} {name} EuroPreview'})})
        for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson'):
            for r in rows(tab, UnitId=parent): g.add(tab, r, {'UnitId': uid})
        nopt = 0
        for m in rows('ModificationsJson', UnitId=parent):
            nm = g.add('ModificationsJson', m, {'UnitId': uid})
            for o in rows('OptionsJson', ModificationId=m['Id']): g.add('OptionsJson', o, {'ModificationId': nm}); nopt += 1
        g.add('SpecializationAvailabilitiesJson', mirage, {'UnitId': uid, 'SpecializationId': spec, 'MaxAvailabilityXp0': n})
        for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitArmorsJson', 'UnitPropulsionsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson', 'ModificationsJson'):
            ok(len(rows(tab, UnitId=uid)) == len(rows(tab, UnitId=parent)), (name, tab, 'copied'))
        res[name] = {'unit': uid, 'hud': hud, 'spec': spec, 'parent': f'{phud} ({parent})', 'cost': cost, 'cards': n, 'options': nopt}
    rec['euro_jets'] = res
    print('EURO JETS', res)

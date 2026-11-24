"""Euro set 2 (Osama 24 Nov 2026 11:1x PST, thread "blue dragons": "unpack these models and turn them into cards for our German faction. Same
process as yesterday (MRAP will be for the US and Panhard for French)"). Shawn's Drive folder 18aKzR0x...: 10 CGTrader UDIM vehicles, converted in
work/euro-1124 (tools/udim2glb.py + build_eu.sh; models.json key = card Name).
- Germany (Preview) 25 and France (Preview) 24, as germany_cards_1123.py: each card is a full copy of a US unit WITH its options, Eurocorp
  (country 5); stats, weapons and prices are placeholders. Both specs have battlegroup size 0 (euro_bg_zero_1124.py): Armory only.
  Parents are base-game units (no DLC gate): the vanilla PzH-2000 and Leopard 2A8 are DLC2.
- US MaxxPro MRAP: a transport, as VN-3 / ZSL-191 (mk_china_1123.py): copy of the Humvee GMV (48, 30 pts) with its options, offered to every
  US infantry card that already offers the Humvee GMV. No card of its own.
Runs last, so the new unit ids follow every existing card."""
GERMANY, FRANCE, EURO = 25, 24, 5
# Name: (HUDName, spec, parent unit id, parent HUDName, cost, cards)
CARDS = {
    'DE KF51 Panther': ('KF51 Panther', GERMANY, 191, 'M1A2 SEP v3', 260, 2),
    'DE KF41 Lynx': ('KF41 Lynx', GERMANY, 16, 'M2A3 Bradley', 65, 4),
    'DE Wiesel AWC': ('Wiesel AWC', GERMANY, 29, 'LAV-25', 40, 4),
    'DE TPz Fuchs': ('TPz Fuchs', GERMANY, 22, 'Stryker ICV', 30, 4),
    'DE PzH 2000': ('PzH 2000', GERMANY, 162, 'M109A7 Paladin', 270, 2),
    'DE Flakpanzer Gepard': ('Flakpanzer Gepard', GERMANY, 188, 'M163 PIVADS', 80, 2),
    'DE MAN HX77': ('MAN HX77', GERMANY, 242, 'HEMTT', 50, 4),
    'FR VAB': ('VAB', FRANCE, 22, 'Stryker ICV', 30, 4),
    'FR Panhard GD': ('Panhard GD', FRANCE, 467, 'M-ATV', 35, 4),
}
MRAP, GMV = 'US MaxxPro MRAP', 48


def apply(t, g, ok, rec):
    U, S, SA, TA = t['Units'], t['SpecializationsJson'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    def copy_unit(name, parent, upd):
        ok(not any(u and name in (u.get('Name'), u.get('HUDName')) for u in U.values()), name + ' name free')
        d = dict(U[parent]); d.pop('Id'); d.update({'OriginalCost': 0, 'Description': None, 'OriginalName': None, 'DisplayInArmory': True, **upd})
        uid = g.put('Units', max(U) + 1, d)
        for tab, field, target in (('UnitArmorsJson', 'ArmorId', 'ArmorsJson'), ('UnitPropulsionsJson', 'MobilityId', 'MobilityJson')):
            for r in rows(tab, UnitId=parent):
                g.add(tab, r, {'UnitId': uid, field: g.add(target, t[target][r[field]], {'Name': f'{t[target][r[field]]["Name"]} {name}'})})
        for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson'):
            for r in rows(tab, UnitId=parent): g.add(tab, r, {'UnitId': uid})
        nopt = 0
        for m in rows('ModificationsJson', UnitId=parent):
            nm = g.add('ModificationsJson', m, {'UnitId': uid})
            for o in rows('OptionsJson', ModificationId=m['Id']): g.add('OptionsJson', o, {'ModificationId': nm}); nopt += 1
        for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitArmorsJson', 'UnitPropulsionsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson', 'ModificationsJson'):
            ok(len(rows(tab, UnitId=uid)) == len(rows(tab, UnitId=parent)), (name, tab, 'copied'))
        return uid, nopt

    ok(S[GERMANY]['UIName'] == 'Germany (Preview)' and S[FRANCE]['UIName'] == 'France (Preview)' and S[GERMANY]['CountryId'] == S[FRANCE]['CountryId'] == EURO,
       'France / Germany preview specs under Eurocorp')
    tpl = next(r for r in SA.values() if r and r['UnitId'] == 2 and r['SpecializationId'] == 4)
    res = {}
    for name, (hud, spec, parent, phud, cost, n) in CARDS.items():
        ok(U[parent]['HUDName'].strip() == phud and U[parent]['CountryId'] == 2 and U[parent].get('ContentMembership') == -1, (name, 'parent', parent, U[parent]['HUDName']))
        uid, nopt = copy_unit(name, parent, {'Name': name, 'HUDName': hud, 'Cost': cost, 'CountryId': EURO})
        g.add('SpecializationAvailabilitiesJson', tpl, {'UnitId': uid, 'SpecializationId': spec, 'MaxAvailabilityXp0': n})
        res[name] = {'unit': uid, 'spec': spec, 'parent': f'{phud} ({parent})', 'cost': cost, 'cards': n, 'options': nopt}
    for spec in (GERMANY, FRANCE):
        names = [n for n, v in CARDS.items() if v[1] == spec]
        ok(all(any(r['SpecializationId'] == spec for r in rows('SpecializationAvailabilitiesJson', UnitId=res[n]['unit'])) for n in names), (spec, 'cards placed'))
    # US MaxxPro: transport for every US infantry card that offers the Humvee GMV
    ok(U[GMV]['HUDName'].strip() == 'Humvee GMV' and U[GMV]['CountryId'] == 2, 'Humvee GMV 48')
    uid, nopt = copy_unit(MRAP, GMV, {'Name': MRAP, 'HUDName': 'MaxxPro MRAP'})
    gmv = [r for r in sorted(TA.values(), key=lambda r: r['Id']) if r and r['UnitId'] == GMV]
    ok(len(gmv) >= 1 and all(U[SA[r['SpecializationAvailabilityId']]['UnitId']].get('Type') == 2 for r in gmv), ('GMV offered to infantry cards', len(gmv)))
    for r in gmv: g.add('TransportAvailabilitiesJson', r, {'UnitId': uid})
    ok(len(rows('TransportAvailabilitiesJson', UnitId=uid)) == len(gmv) and not rows('SpecializationAvailabilitiesJson', UnitId=uid), 'MaxxPro: transport only')
    res[MRAP] = {'unit': uid, 'parent': f'Humvee GMV ({GMV})', 'cost': U[uid]['Cost'], 'options': nopt,
                 'infantry_cards': [U[SA[r['SpecializationAvailabilityId']]['UnitId']]['HUDName'] for r in gmv]}
    rec['euro_set_1124'] = res
    print('EURO SET', res)

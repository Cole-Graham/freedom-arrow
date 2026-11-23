"""France (Testing Preview) spec for viewing focolate's SCORPION models in the Arsenal (Osama 22 Nov 2026 20:3x PST, thread 1573418243715113213:
"Can you make a France build so I can view these models in the Armory"). LOCAL TEST ONLY, not for a release.
Each card is a full copy of a US base-game parent WITH its loadout options (as blue_dragon_jp2.py); names and prices are from focolate's SCORPION
card.json, all stats are the parent's placeholders. Models: work/french-assets-20261122 (models.json keys = the Name below).
The spec is a copy of Armored Brigade (4), Arsenal-only like Blue Dragon (spec 23)."""

SPEC = 24
# Name: (HUDName, parent unit id, parent HUDName, cost, cards)
CARDS = {
    'FR Leclerc XLR': ('Leclerc XLR', 191, 'M1A2 SEP v3', 260, 2),
    'FR EBRC Jaguar': ('EBRC Jaguar', 29, 'LAV-25', 145, 4),
    'FR VBCI Mk2 RCT40': ('VBCI Mk2 RCT40', 22, 'Stryker ICV', 95, 4),
    'FR VBCI VCI 25': ('VBCI VCI 25', 29, 'LAV-25', 70, 4),
    'FR Griffon VTT': ('Griffon VTT', 22, 'Stryker ICV', 50, 4),
    'FR VBL MILAN': ('VBL MILAN', 6, 'Humvee TOW-2', 65, 3),
    'FR CAESAR Mk II': ('CAESAR Mk II', 452, 'Stryker SPH', 190, 2),  # Brutus (388) has turret weapons without ammo rows (audit_mp_equipment)
    'FR SAMP/T NG': ('SAMP/T NG', 251, 'Patriot PAC-3', 250, 2),
    'FR Rafale C F3-R': ('Rafale C F3-R', 284, 'F-16V Viper', 180, 2),
    'FR Mirage 2000D RMV': ('Mirage 2000D RMV', 285, 'F-16C Fighting Falcon', 145, 3),
    'FR Tigre HAD': ('EC665 Tigre HAD', 270, 'AH-64E Guardian', 100, 2),
    'FR NH90': ('NH90', 81, 'UH-60M Blackhawk', 95, 4),
    'FR H160M': ('H160M Guepard', 159, 'UH-1Y Venom', 65, 4),
    'FR Gazelle': ('SA342M1 Gazelle Viviane', 267, 'OH-58D Kiowa Warrior', 70, 4),
}


def apply(t, g, ok, rec):
    U, S, SA = t['Units'], t['SpecializationsJson'], t['SpecializationAvailabilitiesJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    ok(SPEC not in S and S[4]['Name'] == 'Armored Brigade' and S[4]['CountryId'] == 2, 'spec 24 free; Armored Brigade template')
    g.put('SpecializationsJson', SPEC, {**{k: v for k, v in S[4].items() if k != 'Id'}, 'Name': 'US France Preview',
        'UIName': 'France (Testing Preview)',
        'UIDescription': 'TESTING PREVIEW. French models by focolate (SCORPION). Every card is a copy of a US unit: stats, weapons and prices are placeholders.',
        'ShowInHangar': True, 'ContentMembership': -1})
    tpl = next(r for r in SA.values() if r and r['UnitId'] == 2 and r['SpecializationId'] == 4)
    res = {}
    for name, (hud, parent, phud, cost, n) in CARDS.items():
        ok(U[parent]['HUDName'] == phud and U[parent]['CountryId'] == 2, (name, 'parent', parent, U[parent]['HUDName']))
        ok(not any(u and name in (u.get('Name'), u.get('HUDName')) for u in U.values()), name + ' name free')
        d = dict(U[parent]); d.pop('Id')
        d.update({'Name': name, 'HUDName': hud, 'Cost': cost, 'OriginalCost': 0, 'Description': None, 'OriginalName': None, 'DisplayInArmory': True, 'CountryId': 2})
        uid = g.put('Units', max(U) + 1, d)
        for tab, field, target in (('UnitArmorsJson', 'ArmorId', 'ArmorsJson'), ('UnitPropulsionsJson', 'MobilityId', 'MobilityJson')):
            for r in rows(tab, UnitId=parent):
                g.add(tab, r, {'UnitId': uid, field: g.add(target, t[target][r[field]], {'Name': f'{t[target][r[field]]["Name"]} {name} FrancePreview'})})
        for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson'):
            for r in rows(tab, UnitId=parent):
                g.add(tab, r, {'UnitId': uid})
        nopt = 0
        for m in rows('ModificationsJson', UnitId=parent):
            nm = g.add('ModificationsJson', m, {'UnitId': uid})
            for o in rows('OptionsJson', ModificationId=m['Id']):
                g.add('OptionsJson', o, {'ModificationId': nm}); nopt += 1
        g.add('SpecializationAvailabilitiesJson', tpl, {'UnitId': uid, 'SpecializationId': SPEC, 'MaxAvailabilityXp0': n})
        for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitArmorsJson', 'UnitPropulsionsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson', 'ModificationsJson'):
            ok(len(rows(tab, UnitId=uid)) == len(rows(tab, UnitId=parent)), (name, tab, 'copied'))
        res[name] = {'unit': uid, 'hud': hud, 'parent': f'{phud} ({parent})', 'cost': cost, 'cards': n, 'options': nopt}
    ok(sorted(r['UnitId'] for r in SA.values() if r and r['SpecializationId'] == SPEC) == sorted(v['unit'] for v in res.values()), 'spec 24 = the France preview cards')
    rec['france_preview'] = {'spec': SPEC, 'cards': res}

"""PLZ-10 120 mm self-propelled gun-mortar for the MarkII_ China models (Osama 23 Nov 2026 22:1x PST, thread "blue dragons":
"PLZ-10 should be a vena clone but for the Heavy CAB", "so its a stat clone of the PLZ-25", "just in different specs").
PLA PLZ-10 = full copy of PLA PLZ-25 (plz25_navy_1123.py: the 2S31 Vena clone with renamed Chinese weapons and rounds, 22:0x "change the
name of the ammunition so the russian names aren't there"), sharing its turrets/weapons, WITH its options, 100 pts, 3 cards, in PLAGF Armored Force
(spec 18, the heavy combined-arms brigade spec). Runs after plz25_navy_1123.
FAModels draws the MarkII_ models (models.json key = Name, work/c5-cn-1123)."""
NEW = {'PLA PLZ-10': ('PLZ-10', 18)}


def apply(t, g, ok, rec):
    U, S, SA = t['Units'], t['SpecializationsJson'], t['SpecializationAvailabilitiesJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    (PARENT,) = [k for k, u in U.items() if u and u.get('Name') == 'PLA PLZ-25']
    ok(U[PARENT]['Cost'] == U[210]['Cost'] and U[PARENT]['ContentMembership'] == -1, ('PLA PLZ-25 is the Vena clone', PARENT))
    ok(S[18]['Name'] == 'PLA PLAGF Armored Force', 'spec 18 armored')
    tpl = rows('SpecializationAvailabilitiesJson', UnitId=PARENT)
    ok(len(tpl) >= 1, ('Vena card rows', len(tpl)));tpl = tpl[0]
    out = {}
    for name, (hud, spec) in NEW.items():
        ok(not any(u and name in (u.get('Name'), u.get('HUDName')) for u in U.values()), name + ' name free')
        d = dict(U[PARENT]); d.pop('Id')
        d.update({'Name': name, 'HUDName': hud, 'OriginalCost': 0, 'CountryId': 4, 'DisplayInArmory': True, 'Description': None, 'OriginalName': None})
        uid = g.put('Units', max(U) + 1, d)
        for tab, field, target in (('UnitArmorsJson', 'ArmorId', 'ArmorsJson'), ('UnitPropulsionsJson', 'MobilityId', 'MobilityJson')):
            for r in rows(tab, UnitId=PARENT):
                g.add(tab, r, {'UnitId': uid, field: g.add(target, t[target][r[field]], {'Name': f'{t[target][r[field]]["Name"]} {name}'})})
        for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson'):
            for r in rows(tab, UnitId=PARENT): g.add(tab, r, {'UnitId': uid})
        nopt = 0
        for m in rows('ModificationsJson', UnitId=PARENT):
            nm = g.add('ModificationsJson', m, {'UnitId': uid})
            for o in rows('OptionsJson', ModificationId=m['Id']): g.add('OptionsJson', o, {'ModificationId': nm}); nopt += 1
        g.add('SpecializationAvailabilitiesJson', tpl, {'UnitId': uid, 'SpecializationId': spec})
        for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitArmorsJson', 'UnitPropulsionsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson', 'ModificationsJson'):
            ok(len(rows(tab, UnitId=uid)) == len(rows(tab, UnitId=PARENT)), (name, tab, 'copied'))
        ok(U[uid]['Cost'] == U[PARENT]['Cost'] and len(rows('SpecializationAvailabilitiesJson', UnitId=uid)) == 1, (name, 'price and one card row'))
        out[name] = {'unit': uid, 'cost': U[uid]['Cost'], 'spec': spec, 'cards': tpl.get('MaxAvailabilityXp0'), 'options': nopt}
    rec['mk_mortars_1123'] = out
    print('MK MORTARS', out)

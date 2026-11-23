"""Blue Dragon (spec 23) K9 Thunder and K21 IFV cards for Shawn's 23 Nov model drop (Osama 23 Nov 2026 15:3x PST, thread "blue dragons":
"can you add the K-9 to the SK spec? I don't see it", "add the new blue dragons units to the spec").
- K9 Thunder: full copy of the Baltic DLC K9 Kõu (539: CN98 155 mm, HE/Vulcano/smoke, extended-range option, cupola M2, 230 pts) WITH its options,
  but ContentMembership -1 and the non-DLC US_M109A6 body + sound (vanilla's own non-DLC 'BALT M109A5Ö' 429 uses the same body; same turret
  layout: main gun + child cupola, two loadouts). M109A6 card art (the K9 Kõu art lives in the DLC). 2 cards.
- K21 KNIFV: full copy of the M2A3 Bradley (16) WITH its options, 65 pts, 4 cards (as the Type 89 FV, 1286, a Bradley-based IFV in this spec).
  Placeholder stats: the 40 mm gun is still the Bradley's 25 mm Bushmaster.
FAModels draws the C5 models (models.json keys = Name)."""
SPEC = 23
CARDS = {'K9 Thunder': (539, 'K9 Thunder', 2, 247), 'K21 KNIFV': (16, 'K21 KNIFV', 4, None)}


def apply(t, g, ok, rec):
    U, S, SA = t['Units'], t['SpecializationsJson'], t['SpecializationAvailabilitiesJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    ok(S[SPEC]['Name'] == 'US Blue Dragon' and U[539]['HUDName'] == 'K9 Kõu' and U[247]['ModelFileName'] == 'US_M109A6' and U[16]['HUDName'] == 'M2A3 Bradley', 'Blue Dragon, K9 Kõu, M109A6 body, M2A3')
    tpl = next(r for r in sorted(SA.values(), key=lambda r: r['Id']) if r and r['SpecializationId'] == SPEC and r['UnitId'] == 1286)   # Type 89 FV row
    res = {}
    for name, (parent, hud, n, body) in CARDS.items():
        ok(not any(u and name in (u.get('Name'), u.get('HUDName')) for u in U.values()), name + ' name free')
        d = dict(U[parent]); d.pop('Id')
        d.update({'Name': name, 'HUDName': hud, 'OriginalCost': 0, 'Description': None, 'OriginalName': None, 'DisplayInArmory': True, 'CountryId': 2, 'ContentMembership': -1})
        if body:
            d.update({k: U[body][k] for k in ('ModelFileName', 'AudioPreset', 'PortraitFileName', 'ThumbnailFileName')})
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
        g.add('SpecializationAvailabilitiesJson', tpl, {'UnitId': uid, 'SpecializationId': SPEC, 'MaxAvailabilityXp0': n})
        for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitArmorsJson', 'UnitPropulsionsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson', 'ModificationsJson'):
            ok(len(rows(tab, UnitId=uid)) == len(rows(tab, UnitId=parent)), (name, tab, 'copied'))
        ok(U[uid]['Cost'] == U[parent]['Cost'] and U[uid]['ContentMembership'] == -1, (name, 'price and no DLC gate'))
        res[name] = {'unit': uid, 'parent': parent, 'cost': U[uid]['Cost'], 'cards': n, 'options': nopt, 'body': U[uid]['ModelFileName']}
    ok(not any(u and u.get('ModelFileName', '').startswith('DLC') for k, u in U.items() if u and u.get('Name') in CARDS), 'no DLC body on the new cards')
    rec['blue_dragon_k9_k21'] = res

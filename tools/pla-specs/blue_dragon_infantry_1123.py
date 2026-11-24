"""Blue Dragon test infantry: Korean and Japanese basic rifle squads (Osama 23 Nov 2026 17:3x PST, thread 1567745029781454889: "please get them in
and put them in test infantry squads", "just basic riflemen"). Each card is a full copy of the US Mech. Riflemen (57: 6 men, 40 pts, M4A1/M203,
US_Rangers body) in Blue Dragon (spec 23, Arsenal-only), placeholder stats. The bodies are the seller models rigged to the 40 BA bones
(work/bd-inf-20261123: cgmodel 785245 South Korean soldier, cgmodel 803757 JGSDF soldier); FAModels draws them through infantry-bodies.json
(unitId rules) and InfantryBodyIdentity (approved unit list). Fixed unit IDs, so the body rules stay valid when later sections add units."""
SPEC = 23
PARENT = 57
CARDS = {1400: ('BD Korean Riflemen', 'Korean Riflemen (Test)'), 1401: ('BD Japanese Riflemen', 'Japanese Riflemen (Test)')}


def apply(t, g, ok, rec):
    U, S, SA = t['Units'], t['SpecializationsJson'], t['SpecializationAvailabilitiesJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    ok(S[SPEC]['Name'] == 'US Blue Dragon' and U[PARENT]['HUDName'] == 'Mech. Riflemen' and U[PARENT]['Type'] == 2, 'Blue Dragon; US Mech. Riflemen')
    tpl = next(r for r in sorted(SA.values(), key=lambda r: r['Id']) if r and r['SpecializationId'] == SPEC and r['UnitId'] == 1286)   # Type 89 FV row
    res = {}
    for uid, (name, hud) in CARDS.items():
        ok(uid not in U and not any(u and name in (u.get('Name'), u.get('HUDName')) for u in U.values()), (uid, name, 'free'))
        d = dict(U[PARENT]); d.pop('Id')
        d.update({'Name': name, 'HUDName': hud, 'OriginalCost': 0, 'Description': None, 'OriginalName': None, 'DisplayInArmory': True, 'CountryId': 2, 'ContentMembership': -1})
        g.put('Units', uid, d)
        for tab, field, target in (('UnitArmorsJson', 'ArmorId', 'ArmorsJson'), ('UnitPropulsionsJson', 'MobilityId', 'MobilityJson')):
            for r in rows(tab, UnitId=PARENT):
                g.add(tab, r, {'UnitId': uid, field: g.add(target, t[target][r[field]], {'Name': f'{t[target][r[field]]["Name"]} {name}'})})
        for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'WeaponAmmunitionsJson', 'SquadMembersJson', 'SquadWeaponsJson'):
            for r in rows(tab, UnitId=PARENT): g.add(tab, r, {'UnitId': uid})
        g.add('SpecializationAvailabilitiesJson', tpl, {'UnitId': uid, 'SpecializationId': SPEC, 'MaxAvailabilityXp0': 4})
        for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitArmorsJson', 'UnitPropulsionsJson', 'WeaponAmmunitionsJson', 'SquadMembersJson', 'SquadWeaponsJson'):
            ok(len(rows(tab, UnitId=uid)) == len(rows(tab, UnitId=PARENT)) > 0, (name, tab, 'copied'))
        ok(not rows('ModificationsJson', UnitId=PARENT) and U[uid]['Cost'] == U[PARENT]['Cost'], (name, 'no loadouts; price'))
        res[hud] = {'unit': uid, 'name': name, 'men': len(rows('SquadMembersJson', UnitId=uid)), 'cost': U[uid]['Cost'], 'cards': 4}
    rec['blue_dragon_infantry'] = res
    print('BD INFANTRY', res)

"""Blue Dragon cards for the rest of Shawn's "Blue Dragon Models" folder (Osama 22 Nov 2026 00:3x PST, thread 1573418243715113213: "all of these
models should be made into units"). Full copies of base-game parents WITH their armory options (loadouts), placeholder stats/prices, spec 23:
- F-2A: F-16C Fighting Falcon (285).            - KF-21 Boramae: F-16V Viper (284); F-16 model until Shawn exports the .max to FBX.
- F-35B (JASDF) and F-35B (ROKN): F-35B (295).   - Type 19: PCL-181 / SH-15 (1034, wheeled 155 mm), US side.
Models (F-2, both F-35Bs, Type 19) are Assets in work/blue-dragon-models-20261122. K2 / Type 16 / Type 74 cards exist (blue_dragon_tanks.py)."""

SPEC = 23
# The FA F-35 wingtip AIM-9 test slot (modification 2001435, options 20163/20164, slots 5-6) is held for Osama's call in check_mount_weapons.py; the
# copies keep only the vanilla bay loadouts.
SKIP_MODS = {2001435}
CARDS = {'F-2A': (285, 120, 2), 'KF-21 Boramae': (284, 160, 2), 'F-35B (JASDF)': (295, 265, 2), 'F-35B (ROKN)': (295, 265, 2), 'Type 19': (1034, 175, 2)}


def apply(t, g, ok, rec):
    U, SA = t['Units'], t['SpecializationAvailabilitiesJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    ok((U[285]['HUDName'], U[284]['HUDName'], U[295]['HUDName'], U[1034]['HUDName']) == ('F-16C Fighting Falcon', 'F-16V Viper', 'F-35B', 'PCL-181'), 'parents')
    tpl = next(r for r in SA.values() if r and r['SpecializationId'] == SPEC)
    res = {}
    for name, (parent, cost, n) in CARDS.items():
        ok(not any(u and name in (u.get('Name'), u.get('HUDName')) for u in U.values()), name + ' name free')
        d = dict(U[parent]); d.pop('Id')
        d.update({'Name': name, 'HUDName': name, 'Cost': cost, 'OriginalCost': 0, 'Description': None, 'OriginalName': None, 'DisplayInArmory': True, 'CountryId': 2})
        uid = g.put('Units', max(U) + 1, d)
        for tab, field, target in (('UnitArmorsJson', 'ArmorId', 'ArmorsJson'), ('UnitPropulsionsJson', 'MobilityId', 'MobilityJson')):
            for r in rows(tab, UnitId=parent):
                g.add(tab, r, {'UnitId': uid, field: g.add(target, t[target][r[field]], {'Name': f'{t[target][r[field]]["Name"]} {name} BlueDragon'})})
        mods = [m for m in rows('ModificationsJson', UnitId=parent) if m['Id'] not in SKIP_MODS]
        skip_t = {v for m in rows('ModificationsJson', UnitId=parent) if m['Id'] in SKIP_MODS for o in rows('OptionsJson', ModificationId=m['Id'])
                  for k, v in o.items() if k.startswith('Turret') and k.endswith('Id') and v}
        keep_t = [r for r in rows('TurretUnitsJson', UnitId=parent) if r['TurretId'] not in skip_t]
        keep_w = {w['WeaponId'] for r in keep_t for w in rows('TurretWeaponsJson', TurretId=r['TurretId'])}
        for tab in ('UnitAbilitiesJson', 'SensorUnitsJson'):
            for r in rows(tab, UnitId=parent):
                g.add(tab, r, {'UnitId': uid})
        for r in keep_t:
            g.add('TurretUnitsJson', r, {'UnitId': uid})
        for r in rows('WeaponAmmunitionsJson', UnitId=parent):
            if r['WeaponId'] in keep_w:
                g.add('WeaponAmmunitionsJson', r, {'UnitId': uid})
        nopt = 0
        for m in mods:
            nm = g.add('ModificationsJson', m, {'UnitId': uid})
            for o in rows('OptionsJson', ModificationId=m['Id']):
                g.add('OptionsJson', o, {'ModificationId': nm}); nopt += 1
        g.add('SpecializationAvailabilitiesJson', tpl, {'UnitId': uid, 'SpecializationId': SPEC, 'MaxAvailabilityXp0': n})
        for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitArmorsJson', 'UnitPropulsionsJson'):
            ok(len(rows(tab, UnitId=uid)) == len(rows(tab, UnitId=parent)), (name, tab, 'copied'))
        ok(len(rows('ModificationsJson', UnitId=uid)) == len(mods) and nopt == sum(len(rows('OptionsJson', ModificationId=m['Id'])) for m in mods), (name, 'options copied'))
        ok({w['WeaponId'] for r in rows('TurretUnitsJson', UnitId=uid) for w in rows('TurretWeaponsJson', TurretId=r['TurretId'])} == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=uid)}, (name, 'weapons == ammo weapons'))
        res[name] = {'unit': uid, 'parent': f"{U[parent]['HUDName']} ({parent})", 'cost': cost, 'cards': n, 'options': nopt}
    ok(sum(1 for r in SA.values() if r and r['SpecializationId'] == SPEC and r['UnitId'] in {v['unit'] for v in res.values()}) == len(CARDS), 'cards in spec 23')
    rec['blue_dragon_jp2'] = res

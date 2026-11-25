"""Build-time copy of the game's WeaponCoverage check (mod/source/runtime-qa/WeaponCoverage.cs). In the game a single failure refuses ALL
Freedom Arrow data: 0.9.7-dev.1 loaded as plain vanilla, China included, because the new Assaultmen SRAW A copied vanilla 332's unused M27 IAR
squad-weapon row, which has no ammo row (Lateralus 24 Nov 2026 18:0x, thread 1572962048705429598: "all the gameplay modifications are missing").
Same rule as the game, on the patches this build writes: every patched SquadWeapons or TurretWeapons row that sets WeaponId needs a
WeaponAmmunitions row (0 rounds is fine) for its unit, and for a turret weapon for every unit that mounts that turret (TurretUnits, or an option's Turret*Id)."""


def check(t, patches, ok):
    def changed(tab):
        return {int(k) for k, v in patches[tab].items() if v is not None and 'WeaponId' in v}
    ammo = {(r['UnitId'], r['WeaponId']) for r in t['WeaponAmmunitionsJson'].values() if r}
    missing = []
    for i in sorted(changed('SquadWeaponsJson')):
        r = t['SquadWeaponsJson'].get(i)
        if r and (r['UnitId'], r['WeaponId']) not in ammo:missing.append(('squad', i, r['UnitId'], r['WeaponId']))
    consumers = {}
    for r in t['TurretUnitsJson'].values():
        if r:consumers.setdefault(r['TurretId'], set()).add(r['UnitId'])
    mods = {r['Id']: r['UnitId'] for r in t['ModificationsJson'].values() if r}
    for r in t['OptionsJson'].values():
        if r and r.get('ModificationId') in mods:
            for k, v in r.items():
                if k.startswith('Turret') and k.endswith('Id') and isinstance(v, int) and v > 0:consumers.setdefault(v, set()).add(mods[r['ModificationId']])
    for i in sorted(changed('TurretWeaponsJson')):
        r = t['TurretWeaponsJson'].get(i)
        if not r:continue
        for unit in sorted(consumers.get(r['TurretId'], ())):
            if (unit, r['WeaponId']) not in ammo:missing.append(('turret', i, unit, r['WeaponId']))
    ok(not missing, ('weapon rows without an ammo row: the game would refuse ALL Freedom Arrow data', missing))
    return len(changed('SquadWeaponsJson')) + len(changed('TurretWeaponsJson'))

"""FH-97A: the "Light strike (4x LS-6 500kg)" loadout removed (Osama 27 Nov 2026 15:5x PST, bugs thread 1573561286803980289, on ishtar's
"more bombs for less money" screenshot: 4x LS-6 at +60 was cheaper than 2x LS-6 at +75; "Loadout supposed to be removed" / "Remove this loadout").
Option 31032 (weapon package 2018503) is removed, with its turret 2018522 ("PLA air pylon LS-6 x2": TurretUnits 2018525, TurretWeapons 2018524),
which nothing else uses, so no orphan turret is left on the unit. Its weapon 2018523 and that weapon's ammo rows go too if no other turret
of the FH-97A uses the weapon. The other five FH-97A loadouts are unchanged."""
UNIT, MOD, OPT = 1253, 2018503, 31032


def apply(t, g, ok, rec):
    U, O, M = t['Units'], t['OptionsJson'], t['ModificationsJson']
    o = O.get(OPT)
    ok(U[UNIT]['HUDName'] == 'FH-97A' and o and o['ModificationId'] == MOD and M[MOD]['UnitId'] == UNIT
       and o['UIName'] == 'Light strike (4x LS-6 500kg)' and o['Cost'] == 60 and not o.get('IsDefault'), ('FH-97A 4x LS-6 option', o))
    turret = o['Turret0Id']
    g.remove('OptionsJson', OPT)
    TU, TW, WA = t['TurretUnitsJson'], t['TurretWeaponsJson'], t['WeaponAmmunitionsJson']
    ok(not any(x and turret in (x.get('Turret0Id'), x.get('Turret1Id'), x.get('Turret2Id')) for x in O.values()), ('turret used by another option', turret))
    tu = [r for r in TU.values() if r and r['TurretId'] == turret]
    tw = [r for r in TW.values() if r and r['TurretId'] == turret]
    ok([r['UnitId'] for r in tu] == [UNIT] and len(tw) == 1, ('turret rows', tu, tw))
    weapon = tw[0]['WeaponId']
    for r in tu: g.remove('TurretUnitsJson', r['Id'])
    for r in tw: g.remove('TurretWeaponsJson', r['Id'])
    if not any(r and r['TurretId'] == turret for tab in ('TurretUnitsJson',) for r in t[tab].values()) and turret in t['TurretsJson']:
        g.remove('TurretsJson', turret)
    still = {r['TurretId'] for r in TU.values() if r and r['UnitId'] == UNIT}
    used = any(r and r['WeaponId'] == weapon and r['TurretId'] in still for r in TW.values())
    gone_wa = []
    if not used:
        for r in [r for r in WA.values() if r and r['UnitId'] == UNIT and r['WeaponId'] == weapon]: g.remove('WeaponAmmunitionsJson', r['Id']); gone_wa.append(r['Id'])
    left = sorted((x['UIName'], x['Cost']) for x in O.values() if x and x['ModificationId'] == MOD)
    ok(len(left) == 5 and not any(x and x['ModificationId'] == MOD and x['Id'] == OPT for x in O.values()), ('FH-97A loadouts left', left))
    rec['osama_fh97_4xls6_1127'] = {'removed': [OPT, 'Light strike (4x LS-6 500kg)', 60], 'turret': turret, 'weapon': weapon, 'weapon_still_used': used, 'ammo_rows_removed': gone_wa, 'left': left}
    print('FH-97A 4x LS-6 removed', rec['osama_fh97_4xls6_1127'])

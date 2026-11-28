"""PHL-16: the "2x Fire Dragon 480" loadout removed (Osama 28 Nov 2026 12:15 PST, bugs thread 1573561286803980289, on Wero's #oversights screenshot:
PHL-16 with 2x Fire Dragon 480 at 380 vs the PHL-191 Ballistic with the same missiles at 225, both in Motorized; "Phl-16 should have lost that
option"). Option 24553 is removed; any turret only it used goes with its rows (no orphan turret), and that turret's weapon ammo rows on the
PHL-16 go if no remaining PHL-16 turret fires the weapon. The 10x BRE3 300 mm and 8x BRE6/BRE8 370 mm (default) loadouts are unchanged."""
UNIT, MOD, OPT = 1035, 2017444, 24553


def apply(t, g, ok, rec):
    U, O, M = t['Units'], t['OptionsJson'], t['ModificationsJson']
    TU, TW, WA = t['TurretUnitsJson'], t['TurretWeaponsJson'], t['WeaponAmmunitionsJson']
    o = O.get(OPT)
    ok(U[UNIT]['HUDName'] == 'PHL-16' and o and o['ModificationId'] == MOD and M[MOD]['UnitId'] == UNIT
       and o['UIName'] == '2x Fire Dragon 480' and not o.get('IsDefault'), ('PHL-16 Fire Dragon 480 option', o))
    turrets = [o.get(k) for k in ('Turret0Id', 'Turret1Id', 'Turret2Id') if o.get(k)]
    g.remove('OptionsJson', OPT)
    gone = {'turrets': [], 'ammo_rows': []}
    for turret in turrets:
        if any(x and turret in (x.get('Turret0Id'), x.get('Turret1Id'), x.get('Turret2Id')) for x in O.values()): continue   # shared with another loadout
        tu = [r for r in TU.values() if r and r['TurretId'] == turret]
        if any(r['UnitId'] != UNIT for r in tu): continue                                                                      # used by another unit
        weapons = [r['WeaponId'] for r in TW.values() if r and r['TurretId'] == turret]
        for r in tu: g.remove('TurretUnitsJson', r['Id'])
        for r in [r for r in TW.values() if r and r['TurretId'] == turret]: g.remove('TurretWeaponsJson', r['Id'])
        if turret in t['TurretsJson'] and not any(r and r['TurretId'] == turret for r in TU.values()): g.remove('TurretsJson', turret)
        gone['turrets'].append(turret)
        still = {r['TurretId'] for r in TU.values() if r and r['UnitId'] == UNIT}
        for w in weapons:
            if not any(r and r['WeaponId'] == w and r['TurretId'] in still for r in TW.values()):
                for r in [r for r in WA.values() if r and r['UnitId'] == UNIT and r['WeaponId'] == w]: g.remove('WeaponAmmunitionsJson', r['Id']); gone['ammo_rows'].append(r['Id'])
    left = sorted((x['UIName'], x['Cost'], bool(x.get('IsDefault'))) for x in O.values() if x and x['ModificationId'] == MOD)
    ok([l[0] for l in left] == ['10x BRE3 300 mm', '8x BRE6/BRE8 370 mm'] and any(l[2] for l in left), ('PHL-16 loadouts left', left))
    rec['osama_phl16_fd480_1128'] = {'removed': [OPT, '2x Fire Dragon 480', o['Cost']], **gone, 'left': left}
    print('PHL-16 Fire Dragon 480 removed', rec['osama_phl16_fd480_1128'])

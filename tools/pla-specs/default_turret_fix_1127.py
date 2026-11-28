"""Units with no default turret (Osama 27 Nov 21:0x, 4th report: "add the armament on the HQ-13", Arsenal card "Unit has no weapons"): a unit
without loadouts shows and uses the turret marked IsDefault; every vanilla single-turret unit without loadouts has IsDefault True (20 of 20).
The HQ-13 SHORAD's turret (3000000, a copy of a PGL-625 mount with IsDefault False) had none, so its 12 HQ-13 missiles never appeared. Rule
applied to every unit with no loadouts whose top turrets carry weapons but none is default: its first own (unshared) top turret becomes default."""


def apply(t, g, ok, rec):
    U, T, TU, TW, MO = t['Units'], t['TurretsJson'], t['TurretUnitsJson'], t['TurretWeaponsJson'], t['ModificationsJson']
    users = {}
    for r in TU.values():
        if r: users.setdefault(r['TurretId'], set()).add(r['UnitId'])
    armed = {x['TurretId'] for x in TW.values() if x}
    mods = {m['UnitId'] for m in MO.values() if m}
    fixed = []
    for u in sorted((u for u in U.values() if u), key=lambda u: u['Id']):
        if u['Id'] in mods: continue
        top = sorted((r for r in TU.values() if r and r['UnitId'] == u['Id'] and not T.get(r['TurretId'], {}).get('ParentTurretId')), key=lambda r: (r.get('Order') or 0, r['Id']))
        if not top or any(T[r['TurretId']].get('IsDefault') for r in top): continue
        own = [r['TurretId'] for r in top if r['TurretId'] in armed and users[r['TurretId']] == {u['Id']}]
        if not own: continue
        g.put('TurretsJson', own[0], {'IsDefault': True}); fixed.append((u['Id'], u.get('HUDName'), own[0]))
    ok(any(f[0] == 6008 for f in fixed), ('HQ-13 SHORAD fixed', fixed))
    rec['default_turret_fix_1127'] = fixed
    print('DEFAULT TURRET', fixed)

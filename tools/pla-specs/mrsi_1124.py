"""MRSI loadout for the PzH 2000 and the M109A6 (Osama 24 Nov 2026 22:3x PST, thread 1575024642593398836: "try to build it as best as you can to be
multiplayer friendly. keep it simple and minimal hooks. we want reliability. Dont put it into the build yet"). Batch branch codex/batch/osama/mrsi only.
Idea from the SCORPION "Artillery MRSI" kit 1.1.0 (owner-PC only, desyncs online); this version is data + one runtime postfix (Mrsi.cs).
- Each unit gets one more ammunition option, "MRSI (3 rounds)": a copy of its HE loadout whose gun is a copy of the HE gun that fires 3 rounds in every
  fire mission (Short/Normal/Long ground attack burst 3). Same rounds and quantities, same cupola MG, same cost as the HE option (price: Osama's call).
- The deck holds the option, so every PC knows the gun (weapon id). mrsi.json lists the MRSI gun ids and the time between shots that the runtime plans
  for: MagazineReloadTimeMax + 1 s, at least 6 s (the kit's rule). The runtime slows and raises each shell so the 3 land together on every PC.
Creates rows: keep after every other row-creating section so no earlier id moves (saved decks keep options by id)."""
FILE = 'UserData/FreedomArrow/mrsi.json'
SALVO = 3
# unit: (HE option Name, HE gun id)
UNITS = {540: ('Loadout DLC2PZH2000 HE', 646), 247: ('Loadout M109A6 HE', 344)}
UI = 'MRSI (3 rounds)'


def apply(t, g, ok, rec):
    U, O, M, T, TU, TW, W, WA = (t[k] for k in ('Units', 'OptionsJson', 'ModificationsJson', 'TurretsJson', 'TurretUnitsJson', 'TurretWeaponsJson',
                                                'WeaponsJson', 'WeaponAmmunitionsJson'))

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    out, cfg = {}, {}
    for uid, (opt_name, gun) in UNITS.items():
        mods = {m['Id'] for m in rows('ModificationsJson', UnitId=uid)}
        mine = [o for o in O.values() if o and o['ModificationId'] in mods]
        (he,) = [o for o in mine if o['Name'] == opt_name]
        main = he['Turret0Id']
        ok(not any(o.get('UIName') == UI for o in mine), (uid, 'no MRSI option yet'))
        ok([r['WeaponId'] for r in rows('TurretWeaponsJson', TurretId=main)] == [gun], (uid, 'HE loadout turret fires the HE gun', main, gun))
        ok(not T[main].get('ParentTurretId'), (uid, 'HE turret is a main turret'))
        kids = [T[r['TurretId']] for r in rows('TurretUnitsJson', UnitId=uid) if T[r['TurretId']].get('ParentTurretId') == main]
        ok(len(kids) <= 1, (uid, 'at most one child turret on the HE turret', [k['Id'] for k in kids]))
        w = W[gun]
        interval = max(6.0, float(max(w.get('MagazineReloadTimeMax') or 0, w.get('TimeBetweenBurstsMax') or 0, w.get('TimeBetweenShotsInBurst') or 0)) + 1)
        ok(w.get('MagazineSize') == 1 and interval <= 15, (uid, gun, 'one round per reload', interval))
        wid = g.add('WeaponsJson', w, {'Name': w['Name'] + ' MRSI', 'ShortGroundAttackBurst': SALVO, 'NormalGroundAttackBurst': SALVO,
                                       'LongGroundAttackBurst': SALVO})
        # Turret copies keep the source Name and link Order (B-21 / Abrams X rule); the child keeps its parent link on the new main turret.
        # Not a second default main turret: the M109A6 HE turret 457 is IsDefault (copying that showed the Abrams X 'M256 x2' bug).
        tur = g.add('TurretsJson', T[main], {'IsDefault': False})
        for r in rows('TurretWeaponsJson', TurretId=main): g.add('TurretWeaponsJson', r, {'TurretId': tur, 'WeaponId': wid})
        for r in rows('TurretUnitsJson', UnitId=uid, TurretId=main): g.add('TurretUnitsJson', r, {'TurretId': tur})
        for k in kids:
            kid = g.add('TurretsJson', k, {'ParentTurretId': tur})
            for r in rows('TurretWeaponsJson', TurretId=k['Id']): g.add('TurretWeaponsJson', r, {'TurretId': kid})
            for r in rows('TurretUnitsJson', UnitId=uid, TurretId=k['Id']): g.add('TurretUnitsJson', r, {'TurretId': kid})
        ammo = rows('WeaponAmmunitionsJson', UnitId=uid, WeaponId=gun)
        ok(len(ammo) >= 1, (uid, 'HE gun has ammunition rows'))
        for r in ammo: g.add('WeaponAmmunitionsJson', r, {'WeaponId': wid})
        order = 1 + max(o.get('Order') or 0 for o in mine)
        oid = g.add('OptionsJson', he, {'Name': opt_name.replace(' HE', ' MRSI'), 'UIName': UI, 'IsDefault': False, 'Order': order, 'Turret0Id': tur})
        ok(0 < oid <= 32767, (uid, 'option id fits the network short', oid))
        ok(O[oid].get('Cost') == he.get('Cost'), (uid, 'MRSI option costs the same as HE until Osama prices it'))
        got = [(r['AmmunitionId'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=uid, WeaponId=wid)]
        ok(got == [(r['AmmunitionId'], r['Quantity']) for r in ammo], (uid, 'MRSI gun carries the HE loadout rounds', got))
        mains = [r['TurretId'] for r in rows('TurretUnitsJson', UnitId=uid) if T[r['TurretId']].get('IsDefault') and not T[r['TurretId']].get('ParentTurretId')]
        ok(len(mains) <= 1 and tur not in mains, (uid, 'one default main turret, not the MRSI copy', mains))
        cfg[str(wid)] = {'interval': interval, 'unit': uid, 'name': U[uid]['HUDName']}
        out[uid] = {'unit': U[uid]['HUDName'], 'option': oid, 'cost': he.get('Cost', 0), 'gun': wid, 'from_gun': gun, 'turret': tur, 'interval': interval,
                    'rounds': got}
    rec['mrsi_1124'] = out
    print('MRSI', out)
    return {'salvo': SALVO, 'weapons': cfg}

"""F-35A and F-35C get the MAKO, one missile per weapon bay, exactly like the F-22 (Osama 23 Nov 2026 00:1x PST, thread 1567745029781454889:
"F-35 A and F-35C get the MAKO option at one missile per bay EXACTLY LIKE THE F-22").
The F-22's MAKO (f22_mako_mig31bsm.py, 0.7): mount 2002026 (the JSOW bay mount with the single-AMRAAM model) carrying weapon 2002025 "Cruise MAKO"
(1 round of 2002024), linked to the F-22 by one TurretUnits row and one WeaponAmmunitions row (Quantity 1), and one "1x MAKO" option per bay
(31000 left bay slot 1, 31001 right bay slot 2): the bay's JSOW option with the bay mount swapped for 2002026, Cost 80, TimeModifierRefund 261,
picture MOD_KINZHAL_HE, last in the bay list. The F-35A (294) and F-35C (741) bays use the same slots (left 1, right 2) and the same JSOW mount 551,
so each gets the same two rows and two options, copied from its own JSOW bay options. Nothing else on either plane changes."""

F22, MAKO_MOUNT, MAKO_WEAPON, MAKO_AMMO, F22_LEFT, F22_RIGHT = 297, 2002026, 2002025, 2002024, 31000, 31001
PLANES = {294: ('F-35A', 'F35A'), 741: ('F-35C', 'F35C')}
COPY = ('UIName', 'Cost', 'TimeModifierRefund', 'TimeModifierResurrect', 'OptionPicture')


def apply(t, g, ok, rec):
    O, M, TU, WA, U = t['OptionsJson'], t['ModificationsJson'], t['TurretUnitsJson'], t['WeaponAmmunitionsJson'], t['Units']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    turrets = lambda o: {i: o[f'Turret{i}Id'] for i in range(21) if o.get(f'Turret{i}Id')}
    tu22, wa22 = rows('TurretUnitsJson', UnitId=F22, TurretId=MAKO_MOUNT), rows('WeaponAmmunitionsJson', UnitId=F22, WeaponId=MAKO_WEAPON)
    ok(len(tu22) == 1 and len(wa22) == 1 and wa22[0]['AmmunitionId'] == MAKO_AMMO and wa22[0]['Quantity'] == 1, 'F-22 MAKO mount and ammo rows')
    ok(turrets(O[F22_LEFT]).get(1) == MAKO_MOUNT and turrets(O[F22_RIGHT]) == {2: MAKO_MOUNT}, 'F-22 MAKO options: left bay slot 1, right bay slot 2')
    ref = {k: O[F22_LEFT][k] for k in COPY}
    ok(ref['UIName'] == '1x MAKO' and ref['Cost'] == 80 and all(O[F22_RIGHT][k] == ref[k] for k in COPY), ('F-22 MAKO option values', ref))
    out = {}
    for uid, (hud, short) in PLANES.items():
        ok(U[uid]['HUDName'] == hud and not rows('TurretUnitsJson', UnitId=uid, TurretId=MAKO_MOUNT), (hud, 'no MAKO yet'))
        g.add('TurretUnitsJson', tu22[0], {'UnitId': uid})
        g.add('WeaponAmmunitionsJson', wa22[0], {'UnitId': uid})
        made = []
        for side, slot in (('Left', 1), ('Right', 2)):
            bay = [m for m in rows('ModificationsJson', UnitId=uid) if any(turrets(o).get(slot) == 551 and o['UIName'].startswith('1x AGM-154') for o in rows('OptionsJson', ModificationId=m['Id']))]
            ok(len(bay) == 1, (hud, side, 'bay with a JSOW option on slot', slot))
            opts = rows('OptionsJson', ModificationId=bay[0]['Id'])
            jsow = [o for o in opts if turrets(o).get(slot) == 551][0]
            fields = {**{k: ref[k] for k in COPY}, 'Name': f'{side}Bay {short} 1xMAKO', 'IsDefault': False, 'Order': 1 + max(o['Order'] for o in opts),
                      f'Turret{slot}Id': MAKO_MOUNT}
            oid = g.add('OptionsJson', jsow, fields)
            want = {**turrets(jsow), slot: MAKO_MOUNT}
            ok(0 < oid <= 32767 and turrets(O[oid]) == want and O[oid]['ModificationId'] == bay[0]['Id'] and all(O[oid][k] == ref[k] for k in COPY),
               (hud, side, 'MAKO option', oid))
            made.append(oid)
        ok(len(rows('TurretUnitsJson', UnitId=uid, TurretId=MAKO_MOUNT)) == 1 and [(r['AmmunitionId'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=uid, WeaponId=MAKO_WEAPON)] == [(MAKO_AMMO, 1)],
           (hud, 'MAKO mount linked, 1 round per mount'))
        out[hud] = made
    rec['mako_f35'] = {'options': out, 'mount': MAKO_MOUNT, 'weapon': MAKO_WEAPON, 'cost': ref['Cost']}
    print('MAKO F-35', rec['mako_f35'])

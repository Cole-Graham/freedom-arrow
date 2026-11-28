"""ZSL-92B ATGM loadout (Osama 27 Nov 17:4x, thread "China cosmetic work": "ZSL-92B give the option for ATGM, the 35 points currently is fine but
the loadout should add +10 points"). Unit 1079 ('PLA Catalogue ZSL-92 family', card ZSL-92B) keeps 35 pts and its default: 30 mm on mount 0
(vanilla BMD-2 tower, point 0) and the Type 86 7.62 mm on mount 1 (point 1). New loadout (Leopard 2A8 weapon-package pattern, as the ZSD-251):
'+ 4x HJ-73D' (+10) = a copy of the mount 0 tower with the HJ-73D at Order 2, as vanilla's BTR-82AT carries the Konkurs-M on the same
RU_BTR82A body slot 0 (3 weapon points) (weapon 2011151, round 2011153, 4 missiles as
the ZBD-05 / ZBL-08 / VN-3 carry it; no new weapon or round rows). The model does not show the launcher (Arsenal/battle model unchanged)."""
ZSL92B, HJ73D, HJ73D_A, N, COST, ATGM_COST = 1079, 2011151, 2011153, 4, 35, 10


def apply(t, g, ok, rec):
    U, W, A, T, O, MO = t['Units'], t['WeaponsJson'], t['AmmunitionsJson'], t['TurretsJson'], t['OptionsJson'], t['ModificationsJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok(U[ZSL92B]['HUDName'] == 'ZSL-92B' and U[ZSL92B]['Cost'] == COST and not rows('ModificationsJson', UnitId=ZSL92B), 'ZSL-92B 35 pts, no loadouts yet')
    ok(W[HJ73D]['HUDName'] == 'HJ-73D' and A[HJ73D_A]['HUDName'] and any(r['WeaponId'] == HJ73D and r['Quantity'] == N for r in rows('WeaponAmmunitionsJson', UnitId=1413)), 'HJ-73D as the ZBD-05 carries it')
    tus = rows('TurretUnitsJson', UnitId=ZSL92B); ok([r.get('Order') for r in tus] == [0, 1], 'two mounts')
    m0 = tus[0]['TurretId']; tw0 = rows('TurretWeaponsJson', TurretId=m0)
    ok(T[m0]['ModelFileName'] == 'RU_BMD-2/RU_BMD_2_base_tower' and [(x['Order'], W[x['WeaponId']]['HUDName']) for x in tw0] == [(0, '30 mm autocannon')], 'mount 0: BMD-2 tower, 30 mm on point 0')
    ok([(x['Order'], W[x['WeaponId']]['HUDName']) for x in rows('TurretWeaponsJson', TurretId=tus[1]['TurretId'])] == [(1, 'Type 86 7.62 mm')], 'mount 1: Type 86 on point 1')
    # ATGM tower: 30 mm 0 + HJ-73D on the Konkurs point 2 (point 1 is the coax on mount 1)
    ta = g.add('TurretsJson', T[m0], {'Name': 'PLA ZSL-92 family mount 0 HJ-73D'})
    g.add('TurretWeaponsJson', tw0[0], {'TurretId': ta})
    g.add('TurretWeaponsJson', tw0[0], {'TurretId': ta, 'WeaponId': HJ73D, 'Order': 2})
    g.add('TurretUnitsJson', tus[0], {'TurretId': ta})   # the option tower is linked too, on the same body slot 0 (Leopard 2A8 / ZSD-251 pattern)
    wa = rows('WeaponAmmunitionsJson', UnitId=ZSL92B)[0]
    g.add('WeaponAmmunitionsJson', wa, {'WeaponId': HJ73D, 'AmmunitionId': HJ73D_A, 'Quantity': N, 'Order': 0})
    mp = MO[594]; ok(mp['UnitId'] == 503 and mp['UIName'] == 'Custom_Slot_Weapon_package', 'Leopard 2A8 weapon package mod')
    nm = g.add('ModificationsJson', mp, {'UnitId': ZSL92B, 'Name': 'Weapons ZSL-92B'})
    o1 = g.add('OptionsJson', O[2118], {'ModificationId': nm, 'Name': 'MainTurret ZSL-92B 30 mm', 'UIName': '30 mm autocannon', 'OptionPicture': O[2118].get('OptionPicture'),
                                        'Turret0Id': m0, 'Cost': 0, 'IsDefault': True})
    o2 = g.add('OptionsJson', O[2119], {'ModificationId': nm, 'Name': 'MainTurret ZSL-92B HJ-73D', 'UIName': '+ 4x HJ-73D', 'OptionPicture': 'KONKURS_VEHICAL',
                                        'Turret0Id': ta, 'Cost': ATGM_COST})
    ok(all(0 < o <= 32767 for o in (o1, o2)), ('option ids fit the network short', o1, o2))
    ok([r.get('Order') for r in rows('TurretUnitsJson', UnitId=ZSL92B)] == [0, 1, 0], 'option tower on body slot 0')
    lay = lambda tid: [(x['Order'], W[x['WeaponId']]['HUDName']) for x in rows('TurretWeaponsJson', TurretId=tid)]
    ok(lay(ta) == [(0, '30 mm autocannon'), (2, 'HJ-73D')] and U[ZSL92B]['Cost'] == COST and O[o2]['Cost'] == ATGM_COST, ('ZSL-92B ATGM tower, 35 + 10', lay(ta)))
    rec['zsl92b_atgm_1127'] = {'unit': ZSL92B, 'cost': COST, 'default': lay(m0), 'atgm_option': (o2, ATGM_COST, lay(ta))}
    print('ZSL-92B ATGM', rec['zsl92b_atgm_1127'])

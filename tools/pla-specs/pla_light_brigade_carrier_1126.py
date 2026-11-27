"""PLA Light Brigade build, Airborne Tracked Carrier armament and price (Osama 26 Nov 2026 20:4x PST, thread 1567745029781454889: "Airborne tracked
Carrier should be 55 points and have an additional 50 cal, it can shoot the 50 cal and agl at the same time. But make sure we have a unit that has
enough weapon slots" / "Sorry it should be 45 points base price and then option to add HJ-8H for 10 points"). Branch
codex/batch/osama/pla-light-brigade only; the last plb section.
- Weapon slots: the carrier (pla_light_brigade_vut10_para_1126) sits on the ZBD-251 body (RU_Kurganets). A weapon on its second hull mount never
  fires on that body (player fire logs, docs extra-body-slot-weapons), so every weapon goes on mount 0, the BMD-2 tower: vanilla gives that
  turret 3 weapon points (BMD-2: 30 mm 0, PKT 1, Konkurs 2). The carrier uses them the same way: QLZ-87 35 mm AGL 0, QJC-88 12.7 mm 1, HJ-8H 2.
  Weapons on one turret fire at the same time (each picks its own target in the turret's arc).
- 12.7 mm: the existing China vehicle M2 row 2020753 'QJC-88 12.7 mm' (ZSD-05 / ZTD-05) with its round 2020757, 200 rounds (ZTD-05); no copy.
- Loadout, the vanilla Leopard 2A8 MG pattern (modification Type 3 'Custom_Slot_Weapon_package'): default turret AGL + 12.7 mm; option
  '+ 4x HJ-8H' (+10 pts) = the same turret with the HJ-8H on point 2 (4 missiles as before).
- Price 80 (placeholder) -> 45."""
NAME, HMG, HMG_A, HMG_N, HJ8H, AGL, COST, ATGM_COST = 'PLA Airborne Tracked Carrier', 2020753, 2020757, 200, 2021477, 2018609, 45, 10


def apply(t, g, ok, rec):
    U, W, A, T = t['Units'], t['WeaponsJson'], t['AmmunitionsJson'], t['TurretsJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    (c,) = [i for i, u in U.items() if u and u.get('Name') == NAME]
    ok(W[HMG]['HUDName'] == 'QJC-88 12.7 mm' and W[HMG]['Type'] == 28 and A[HMG_A]['HUDName'] == '12.7 mm', 'QJC-88 row')
    (tu,) = rows('TurretUnitsJson', UnitId=c); tur = tu['TurretId']
    tw = rows('TurretWeaponsJson', TurretId=tur)
    ok(T[tur]['ModelFileName'] == 'RU_BMD-2/RU_BMD_2_base_tower' and [(x['Order'], x['WeaponId']) for x in sorted(tw, key=lambda x: x['Order'])] == [(0, AGL), (1, HJ8H)], 'carrier mount 0: AGL 0, HJ-8H 1')
    ok(not rows('ModificationsJson', UnitId=c) and U[c]['Cost'] == 80, 'no loadouts yet, 80 pts')
    # ATGM turret = the existing one: AGL 0, 12.7 mm 1, HJ-8H 2
    (hj,) = [x for x in tw if x['WeaponId'] == HJ8H]; (agl,) = [x for x in tw if x['WeaponId'] == AGL]
    g.put('TurretWeaponsJson', hj['Id'], {'Order': 2})
    g.add('TurretWeaponsJson', agl, {'WeaponId': HMG, 'Order': 1})
    g.put('TurretsJson', tur, {'Name': 'PLA Airborne Tracked Carrier mount 0 HJ-8H'})
    # base turret: AGL 0, 12.7 mm 1
    tb = g.add('TurretsJson', T[tur], {'Name': 'PLA Airborne Tracked Carrier mount 0'})
    g.add('TurretWeaponsJson', agl, {'TurretId': tb, 'WeaponId': AGL, 'Order': 0})
    g.add('TurretWeaponsJson', agl, {'TurretId': tb, 'WeaponId': HMG, 'Order': 1})
    g.put('TurretUnitsJson', tu['Id'], {'TurretId': tb})
    g.add('TurretUnitsJson', tu, {'TurretId': tur})   # the option turret is linked too, as the Leopard 2A8's three (audit_mp_equipment)
    wa = rows('WeaponAmmunitionsJson', UnitId=c)[0]
    g.add('WeaponAmmunitionsJson', wa, {'WeaponId': HMG, 'AmmunitionId': HMG_A, 'Quantity': HMG_N, 'Order': 0})
    # loadout (Leopard 2A8 MG pattern)
    O, MO = t['OptionsJson'], t['ModificationsJson']
    m0 = MO[594]; ok(m0['UnitId'] == 503 and m0['UIName'] == 'Custom_Slot_Weapon_package', 'Leopard 2A8 weapon package mod')
    nm = g.add('ModificationsJson', m0, {'UnitId': c, 'Name': 'Weapons Airborne Tracked Carrier'})
    o1 = g.add('OptionsJson', O[2118], {'ModificationId': nm, 'Name': 'MainTurret Airborne Tracked Carrier AGL HMG', 'UIName': 'QLZ-87 AGL, QJC-88 12.7 mm',
                                        'OptionPicture': 'M2_BROWNING', 'Turret0Id': tb, 'Cost': 0, 'IsDefault': True})
    o2 = g.add('OptionsJson', O[2119], {'ModificationId': nm, 'Name': 'MainTurret Airborne Tracked Carrier HJ-8H', 'UIName': '+ 4x HJ-8H',
                                        'OptionPicture': 'KONKURS_VEHICAL', 'Turret0Id': tur, 'Cost': ATGM_COST})
    ok(all(0 < o <= 32767 for o in (o1, o2)), ('option ids fit the network short', o1, o2))
    g.put('Units', c, {'Cost': COST})
    # checks after
    lay = lambda tid: [W[x['WeaponId']]['HUDName'] for x in sorted(rows('TurretWeaponsJson', TurretId=tid), key=lambda x: x['Order'])]
    ok(lay(tb) == ['QLZ-87 35 mm AGL', 'QJC-88 12.7 mm'] and lay(tur) == ['QLZ-87 35 mm AGL', 'QJC-88 12.7 mm', 'HJ-8H'], ('carrier turrets', lay(tb), lay(tur)))
    ok(sorted(x['Order'] for x in rows('TurretWeaponsJson', TurretId=tur)) == [0, 1, 2] and sorted(x['Order'] for x in rows('TurretWeaponsJson', TurretId=tb)) == [0, 1], 'orders 0..n-1, within the BMD-2 tower 3 points')
    ok(sorted((r['WeaponId'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=c)) == sorted([(AGL, 480), (HJ8H, 4), (HMG, HMG_N)]), 'carrier ammo')
    ok(U[c]['Cost'] == COST and O[o2]['Cost'] == ATGM_COST, 'price 45, HJ-8H +10')
    ok([r['TurretId'] for r in rows('TurretUnitsJson', UnitId=c)] == [tb, tur], 'both turrets linked, default first')
    rec['pla_light_brigade_carrier_1126'] = {'carrier': c, 'cost': COST, 'default': lay(tb), 'hj8h_option': (o2, ATGM_COST, lay(tur))}
    print('PLA LIGHT BRIGADE CARRIER', rec['pla_light_brigade_carrier_1126'])

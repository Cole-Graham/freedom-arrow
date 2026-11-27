"""PLA Light Brigade build, two new vehicles for Osama's 26 Nov 2026 model downloads (19:3x PST, thread "blue dragons" 1573418243715113213:
"VU-T10 added to Light CAB." / "Airborne Tracked Carrier, AGL and 4x HJ-8H and same armor as ZBD-251 for airborne transport").
Branch codex/batch/osama/pla-light-brigade only; the last plb section. Models: work/c5-cn-1123 slugs vut10 / para (models.json key = unit Name).
- 'PLA VU-T10' (card 'VU-T10'): a copy of the ZRZ-100 UGV (1410: armour, mobility, sensor, price 45, 6 cards) in the Light CAB (70). 19:4x
  "VU-T10 is more similar to the Russian one, it has a 30mm autocannon and 4 HJ-12's": its mount is a copy of the vanilla Uran-9 Ataka turret
  (1222, DLC3_Uran9_Ataka) carrying the China equivalents in the same slots: ZPT-99 30 mm (2009027; AP 30 / HE 70 as the Uran-9's 2A72),
  Type 86 7.62 mm coax (2010743, 400) and the HJ-12 (2011864, 4 missiles, as the HJ-12 Team). One default weapon option (copy of the ZRZ-100's).
  19:4x "it is air droppable just like the ZRZ should be": the ZRZ-100's own mobility row (2020655, used by the ZRZ-100 only, shared by the
  VU-T10) gets IsAirDroppable.
- 'PLA Airborne Tracked Carrier' (card 'Airborne Tracked Carrier'): a copy of the ZBD-251 (1056): same armour row, mobility, sensor, 9 seats,
  abilities. Its mount 0 turret is a copy of the ZBD-251 mount with the QLZ-87 35 mm AGL (2018609, 480 rounds as the Lynx ATV) and the HJ-8H
  (2021477, 4 missiles; Lynx IFV round 2018802); existing weapon and round rows are reused (Lateralus 26 Nov: no redundant copies). No MG mount,
  no APS option (Osama 26 Nov 19:0x "remove the 2 APS"). Transport only, like the ZBD-251: it is linked to every squad card that can take the
  ZBD-251 (10 PLAAF squads). Price 80: Osama gave none (ZBD-251 90 with its 40 mm CT), a placeholder."""
ZRZ, ZBD251, LIGHT, URAN_T, ZRZ_MOB = 1410, 1056, 70, 1222, 2020655
VW = ((2009027, ((2009029, 30), (2009031, 70))), (2010743, ((2010747, 400),)), (2011864, ((2011865, 4),)))   # 30 mm, coax, HJ-12 (slot order)
AGL, AGL_A, AGL_N, HJ8H, HJ8H_A, HJ8H_N = 2018609, 2018606, 480, 2021477, 2018802, 4
VUT, CAR = ('PLA VU-T10', 'VU-T10'), ('PLA Airborne Tracked Carrier', 'Airborne Tracked Carrier')
CAR_COST = 80


def apply(t, g, ok, rec):
    U, W, A, SA, TA = t['Units'], t['WeaponsJson'], t['AmmunitionsJson'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok(U[ZRZ]['HUDName'] == 'ZRZ-100' and U[ZBD251]['HUDName'] == 'ZBD-251' and U[ZBD251]['InfantrySlots'] == 9, 'ZRZ-100 / ZBD-251 rows')
    ok(not any(u and (u.get('Name') in (VUT[0], CAR[0]) or u.get('HUDName') in (VUT[1], CAR[1])) for u in U.values()), 'names free')
    ok(W[AGL]['HUDName'] == 'QLZ-87 35 mm AGL' and A[AGL_A]['HUDName'] == '35 mm HE-fragmentation' and W[HJ8H]['HUDName'] == 'HJ-8H' and A[HJ8H_A]['HUDName'] == 'HJ-8H', 'AGL / HJ-8H rows')
    links = ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitArmorsJson', 'UnitPropulsionsJson')
    # VU-T10: full ZRZ-100 copy, Light CAB card
    ok([W[w]['HUDName'] for w, _ in VW] == ['ZPT-99 30 mm', 'Type 86 7.62 mm', 'HJ-12'] and t['TurretsJson'][URAN_T]['ModelFileName'] == 'DLC3_Uran9/DLC3_Uran9_Ataka'
       and len(rows('TurretWeaponsJson', TurretId=URAN_T)) == 3, 'VU-T10 weapons and the Uran-9 Ataka turret')
    v = g.add('Units', U[ZRZ], {'Name': VUT[0], 'HUDName': VUT[1], 'Description': None, 'OriginalName': None})
    for tab in links:
        for r in rows(tab, UnitId=ZRZ): g.add(tab, r, {'UnitId': v})
    vt = g.add('TurretsJson', t['TurretsJson'][URAN_T], {'Name': 'MainTurret VU-T10'})
    for tw, (w, ams) in zip(rows('TurretWeaponsJson', TurretId=URAN_T), VW):
        g.add('TurretWeaponsJson', tw, {'TurretId': vt, 'WeaponId': w})
        for i, (a, n) in enumerate(ams): g.add('WeaponAmmunitionsJson', rows('WeaponAmmunitionsJson', UnitId=ZRZ)[0], {'UnitId': v, 'WeaponId': w, 'AmmunitionId': a, 'Quantity': n, 'Order': i})
    g.add('TurretUnitsJson', rows('TurretUnitsJson', UnitId=ZRZ)[0], {'UnitId': v, 'TurretId': vt, 'Order': 0})
    for m in rows('ModificationsJson', UnitId=ZRZ):
        nm = g.add('ModificationsJson', m, {'UnitId': v, 'Name': m['Name'].replace('ZRZ-100', 'VU-T10')})
        for o in rows('OptionsJson', ModificationId=m['Id']):
            ok(o['Turret0Id'] == rows('TurretUnitsJson', UnitId=ZRZ)[0]['TurretId'], 'ZRZ-100 option = its mount')
            oid = g.add('OptionsJson', o, {'ModificationId': nm, 'Name': 'MainTurret VU-T10', 'UIName': '30 mm, 4x HJ-12, Type 86', 'Turret0Id': vt})
            ok(0 < oid <= 32767, ('VU-T10 option id fits the network short', oid))
    M = t['MobilityJson']
    ok([r['MobilityId'] for r in rows('UnitPropulsionsJson', UnitId=ZRZ)] == [ZRZ_MOB] and M[ZRZ_MOB]['IsAirDroppable'] is False, 'ZRZ-100 mobility row, not air-droppable yet')
    ok(sorted(r['UnitId'] for r in t['UnitPropulsionsJson'].values() if r and r['MobilityId'] == ZRZ_MOB) == [ZRZ, v] and not any(o and o.get('MobilityId') == ZRZ_MOB for o in t['OptionsJson'].values()), 'mobility row used by ZRZ-100 + VU-T10 only')
    g.put('MobilityJson', ZRZ_MOB, {'IsAirDroppable': True})
    ok(sorted((r['WeaponId'], r['AmmunitionId'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=v)) == sorted((w, a, n) for w, ams in VW for a, n in ams)
       and [x['WeaponId'] for x in rows('TurretWeaponsJson', TurretId=vt)] == [w for w, _ in VW] and [r['TurretId'] for r in rows('TurretUnitsJson', UnitId=v)] == [vt], 'VU-T10: 30 mm + coax + 4 HJ-12')
    (zc,) = rows('SpecializationAvailabilitiesJson', UnitId=ZRZ)
    ok(zc['SpecializationId'] == LIGHT, 'ZRZ-100 card is in the Light CAB')
    vc = g.add('SpecializationAvailabilitiesJson', zc, {'UnitId': v})
    # Airborne Tracked Carrier: ZBD-251 copy, own mount 0 (AGL + HJ-8H)
    c = g.add('Units', U[ZBD251], {'Name': CAR[0], 'HUDName': CAR[1], 'Description': None, 'OriginalName': None, 'OriginalCost': 0, 'Cost': CAR_COST})
    for tab in links:
        for r in rows(tab, UnitId=ZBD251): g.add(tab, r, {'UnitId': c})
    tu0 = rows('TurretUnitsJson', UnitId=ZBD251, Order=0)[0];tw = rows('TurretWeaponsJson', TurretId=tu0['TurretId'])
    tur = g.add('TurretsJson', t['TurretsJson'][tu0['TurretId']], {'Name': 'PLA Airborne Tracked Carrier mount 0'})
    for i, w in enumerate((AGL, HJ8H)): g.add('TurretWeaponsJson', tw[min(i, len(tw) - 1)], {'TurretId': tur, 'WeaponId': w, 'Order': i})
    g.add('TurretUnitsJson', tu0, {'UnitId': c, 'TurretId': tur, 'Order': 0})
    wa = rows('WeaponAmmunitionsJson', UnitId=ZBD251)[0]
    for i, (w, a, n) in enumerate(((AGL, AGL_A, AGL_N), (HJ8H, HJ8H_A, HJ8H_N))): g.add('WeaponAmmunitionsJson', wa, {'UnitId': c, 'WeaponId': w, 'AmmunitionId': a, 'Quantity': n, 'Order': 0})
    new = []
    for r in [r for r in TA.values() if r and r['UnitId'] == ZBD251]: new.append(g.add('TransportAvailabilitiesJson', r, {'UnitId': c}))
    # checks after
    ok([(r['ArmorId']) for r in rows('UnitArmorsJson', UnitId=c)] == [r['ArmorId'] for r in rows('UnitArmorsJson', UnitId=ZBD251)], 'carrier armour = ZBD-251')
    ok(sorted((r['WeaponId'], r['AmmunitionId'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=c)) == sorted([(AGL, AGL_A, AGL_N), (HJ8H, HJ8H_A, HJ8H_N)]), 'carrier: AGL 480 + 4 HJ-8H')
    ok([x['WeaponId'] for x in rows('TurretWeaponsJson', TurretId=tur)] == [AGL, HJ8H] and [r['TurretId'] for r in rows('TurretUnitsJson', UnitId=c)] == [tur], 'carrier: one mount, AGL then HJ-8H')
    ok(len(new) == 10 and not rows('SpecializationAvailabilitiesJson', UnitId=c) and not rows('ModificationsJson', UnitId=c), 'carrier: transport for the 10 ZBD-251 squads, no card, no APS option')
    ok(SA[vc]['SpecializationId'] == LIGHT and SA[vc]['MaxAvailabilityXp0'] == zc['MaxAvailabilityXp0'] and U[v]['Cost'] == U[ZRZ]['Cost'], 'VU-T10 Light CAB card as the ZRZ-100')
    sq = sorted({U[SA[TA[i]['SpecializationAvailabilityId']]['UnitId']]['HUDName'] for i in new})
    rec['pla_light_brigade_vut10_para_1126'] = {'vut10': v, 'vut10_turret': vt, 'airdrop_mobility': ZRZ_MOB, 'vut10_card': vc, 'vut10_cost': U[v]['Cost'], 'vut10_cards': SA[vc]['MaxAvailabilityXp0'], 'carrier': c,
        'carrier_cost': CAR_COST, 'carrier_turret': tur, 'carrier_seats': U[c]['InfantrySlots'], 'carrier_squads': sq}
    print('PLA LIGHT BRIGADE VU-T10 + AIRBORNE CARRIER', rec['pla_light_brigade_vut10_para_1126'])

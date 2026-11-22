"""HQ-9 rework (Osama 22 Nov 2026 15:2x PST, thread 1572407822849810463): "for the current hq9c we replace it and call the hq-9b. And then there's an
ammo option where you can switch from four missiles to eight missiles. When you switch to the eight missiles you get the hq9c model and you get eight
missiles of course with the 1,175 range and this should Cost Plus 50. The current hq9b should be renamed hq9a and changed to semi active ... for the new
hq9c can you please find an existing unit that has a similar role perhaps the PAC-3 MSE?"
- Card 911 ('PLA HQ-9', Motorized): shown as HQ-9B. Its missile row (active seeker 50, range 1300, damage 20) stays as the HQ-9B missile. New weapon
  package slot, as the vanilla PAC-3 MSE (mod 533): 4x HQ-9B (default, the existing launcher/turret) or 8x HQ-9C (+0 since 15:5x, was +50; a copy of that launcher with an
  8-round magazine and its own turret). The HQ-9C missile is the vanilla PAC-3 MSE round (497: damage 16, seeker 50, acceleration 400, burn 3 s, blast
  32.5, fuse 26, supply 200 / 10 s) with range 1200 (Osama 15:5x: "1200 range and +0"; first pass 1175, +50) and the HQ-9's own missile model and icon. FAModels: HQ-9B model, HQ-9C model on the 8x option.
- Card 1233 ('PLA HQ-9B', Rocket Conscript Force): shown as HQ-9A; its missile becomes semi-active (Seeker 100, as the vanilla PAC-2 GEM+ / 48N6 /
  9M83M); other numbers unchanged. Card 1234 ('PLA HQ-9A') is in no division (unused) and is left alone.
Numbers are a first pass; Osama expects balance changes, especially after Lateralus's AA rework.
- 15:3x (Osama: "Make the HQ 9A the new version in rocket Force the exact same price and stats of a patriot Pack 2"): card 1233 = vanilla Patriot PAC-2
  (unit 163): cost 145; armour row values = PAC-2 row 132 (10 all round, HP 10) with the PAC-2 armour slot (base / B-kit row 133 values, +5); drive
  speeds = PAC-2 row 64 (50 / 100 / 25); missile = MIM-104E GEM+ (154: already identical after the semi-active change, checked); weapon slot as
  the PAC-2 (mod 118): 2x missiles default (+0, magazine 2) or 4x (+80, the existing launcher). Kept: model/size/sound (HQ-9B model),
  optics (same values as the PAC-2 row 8), card count. Not copied: the PAC-2 machine-gun slot (the S-300PM body has no hull mount for it)."""

HQ9, HQ9A_CARD, MSE, MSE_MOD = 911, 1233, 497, 533
NAME_8X = 'PLA HQ-9 8x HQ-9C'


def apply(t, g, ok, rec):
    U, A, W, T, O, M = t['Units'], t['AmmunitionsJson'], t['WeaponsJson'], t['TurretsJson'], t['OptionsJson'], t['ModificationsJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    tu = rows('TurretUnitsJson', UnitId=HQ9)
    wa = rows('WeaponAmmunitionsJson', UnitId=HQ9)
    ok((U[HQ9]['Name'], U[HQ9]['HUDName'], U[HQ9A_CARD]['Name'], U[HQ9A_CARD]['HUDName']) == ('PLA HQ-9', 'HQ-9C', 'PLA HQ-9B', 'HQ-9B'), 'HQ-9 cards before')
    ok(len(tu) == 1 and len(wa) == 1 and wa[0]['Quantity'] == 4 and not rows('ModificationsJson', UnitId=HQ9), 'HQ-9 (911): one launcher, 4 missiles, no options before')
    TUR, WPN, AMO = tu[0]['TurretId'], wa[0]['WeaponId'], wa[0]['AmmunitionId']
    ok({r['UnitId'] for r in t['WeaponAmmunitionsJson'].values() if r and r['WeaponId'] == WPN} == {HQ9}, 'HQ-9 launcher only on 911')
    w9a = rows('WeaponAmmunitionsJson', UnitId=HQ9A_CARD)
    ok(len(w9a) == 1 and {r['UnitId'] for r in t['WeaponAmmunitionsJson'].values() if r and r['AmmunitionId'] == w9a[0]['AmmunitionId']} == {HQ9A_CARD}, 'HQ-9B card missile only on 1233')
    ok(A[MSE]['HUDName'] == 'MIM-104F MSE' and A[MSE]['Seeker'] == 50 and M[MSE_MOD]['UIName'] == 'Custom_Slot_Weapon_package', 'vanilla PAC-3 MSE round and slot')

    # 911 -> HQ-9B (4x), 8x HQ-9C option
    g.put('Units', HQ9, {'HUDName': 'HQ-9B'})
    g.put('WeaponsJson', WPN, {'HUDName': 'HQ-9B missile'})
    g.put('AmmunitionsJson', AMO, {'HUDName': 'HQ-9B missile'})
    keep = {k: A[AMO][k] for k in ('ModelFileName', 'HUDIcon')}
    c_am = g.add('AmmunitionsJson', A[MSE], {'Name': 'PLA HQ-9C missile', 'HUDName': 'HQ-9C missile', 'LowAltRange': 1200.0, 'HighAltRange': 1200.0, **keep})
    c_w = g.add('WeaponsJson', W[WPN], {'Name': 'PLA HQ-9C launcher x8', 'HUDName': 'HQ-9C missile', 'MagazineSize': 8})
    c_t = g.add('TurretsJson', T[TUR], {'Name': 'PLA HQ-9C mount x8', 'IsDefault': False})
    g.add('TurretWeaponsJson', rows('TurretWeaponsJson', TurretId=TUR)[0], {'TurretId': c_t, 'WeaponId': c_w})
    g.add('TurretUnitsJson', tu[0], {'TurretId': c_t})
    g.add('WeaponAmmunitionsJson', wa[0], {'WeaponId': c_w, 'AmmunitionId': c_am, 'Quantity': 8})
    mod = g.add('ModificationsJson', M[MSE_MOD], {'UnitId': HQ9, 'Name': 'PLA HQ-9 missiles', 'Order': 0})
    mo = {o['UIName']: o for o in rows('OptionsJson', ModificationId=MSE_MOD)}
    o4 = g.add('OptionsJson', mo['Custom_Option_4xMissiles'], {'ModificationId': mod, 'Name': 'PLA HQ-9 4x HQ-9B', 'UIName': '4x HQ-9B', 'Order': 0, 'Cost': 0,
                                                                'Turret0Id': TUR, 'OptionPicture': W[WPN]['HUDIcon']})
    o8 = g.add('OptionsJson', mo['Custom_Option_8xMissiles'], {'ModificationId': mod, 'Name': NAME_8X, 'UIName': '8x HQ-9C', 'Order': 1, 'Cost': 0,
                                                                'Turret0Id': c_t, 'OptionPicture': W[WPN]['HUDIcon']})

    # 1233 -> HQ-9A, semi-active
    a9 = w9a[0]
    g.put('Units', HQ9A_CARD, {'HUDName': 'HQ-9A'})
    g.put('WeaponsJson', a9['WeaponId'], {'HUDName': 'HQ-9A missile'})
    g.put('AmmunitionsJson', a9['AmmunitionId'], {'HUDName': 'HQ-9A missile', 'Seeker': 100})

    # 1233 = Patriot PAC-2 (unit 163) price and stats
    PAC2, AR = 163, t['ArmorsJson']
    pa = [r['ArmorId'] for r in rows('UnitArmorsJson', UnitId=PAC2)]
    ua = rows('UnitArmorsJson', UnitId=HQ9A_CARD); up = rows('UnitPropulsionsJson', UnitId=HQ9A_CARD); us = rows('SensorUnitsJson', UnitId=HQ9A_CARD)
    ok(pa == [132, 133] and len(ua) == len(up) == len(us) == 1, 'PAC-2 armour rows / HQ-9A own rows')
    ok(all(len(rows(tb, **{f: r[f]})) == 1 for tb, f, r in (('UnitArmorsJson', 'ArmorId', ua[0]), ('UnitPropulsionsJson', 'MobilityId', up[0]), ('SensorUnitsJson', 'SensorId', us[0]))), 'HQ-9A rows not shared')
    vals = lambda row: {k: v for k, v in row.items() if k not in ('Id', 'Name')}
    g.put('Units', HQ9A_CARD, {'Cost': U[PAC2]['Cost']})
    g.put('ArmorsJson', ua[0]['ArmorId'], vals(AR[132]))
    bk = g.add('ArmorsJson', AR[133], {'Name': 'PLA HQ-9A B-kit'})
    g.add('UnitArmorsJson', ua[0], {'ArmorId': bk})
    mob = t['MobilityJson'][rows('UnitPropulsionsJson', UnitId=PAC2)[0]['MobilityId']]
    g.put('MobilityJson', up[0]['MobilityId'], {k: mob[k] for k in ('MaxCrossCountrySpeed', 'MaxSpeedRoad', 'MaxSpeedReverse')})
    am = g.add('ModificationsJson', M[115], {'UnitId': HQ9A_CARD, 'Name': 'PLA HQ-9A armour'})
    g.add('OptionsJson', O[308], {'ModificationId': am, 'Name': 'PLA HQ-9A armour base', 'ArmorId': ua[0]['ArmorId']})
    g.add('OptionsJson', O[309], {'ModificationId': am, 'Name': 'PLA HQ-9A armour B-kit', 'ArmorId': bk})
    t4 = rows('TurretUnitsJson', UnitId=HQ9A_CARD)
    ok(len(t4) == 1 and a9['Quantity'] == 4 and W[a9['WeaponId']]['MagazineSize'] == 4, 'HQ-9A: one 4x launcher before')
    T4 = t4[0]['TurretId']
    w2 = g.add('WeaponsJson', W[a9['WeaponId']], {'Name': 'PLA HQ-9A launcher x2', 'MagazineSize': 2})
    t2 = g.add('TurretsJson', T[T4], {'Name': 'PLA HQ-9A mount x2', 'IsDefault': True})
    g.put('TurretsJson', T4, {'IsDefault': False})
    g.add('TurretWeaponsJson', rows('TurretWeaponsJson', TurretId=T4)[0], {'TurretId': t2, 'WeaponId': w2})
    g.add('TurretUnitsJson', t4[0], {'TurretId': t2})
    g.add('WeaponAmmunitionsJson', a9, {'WeaponId': w2, 'Quantity': 2})
    wm = g.add('ModificationsJson', M[118], {'UnitId': HQ9A_CARD, 'Name': 'PLA HQ-9A missiles'})
    g.add('OptionsJson', O[324], {'ModificationId': wm, 'Name': 'PLA HQ-9A 2x', 'Turret0Id': t2, 'OptionPicture': W[WPN]['HUDIcon']})
    g.add('OptionsJson', O[326], {'ModificationId': wm, 'Name': 'PLA HQ-9A 4x', 'Turret0Id': T4, 'OptionPicture': W[WPN]['HUDIcon']})

    # checks
    same = lambda x, y, skip=(): all(x[k] == y[k] for k in x if k not in ('Id', 'Name', 'HUDName', 'HUDIcon', 'ModelFileName', *skip))
    ok(U[HQ9A_CARD]['Cost'] == U[PAC2]['Cost'] == 145 and same(A[a9['AmmunitionId']], A[154]), 'HQ-9A: 145, missile = MIM-104E GEM+')
    ok(same(AR[ua[0]['ArmorId']], AR[132]) and same(AR[bk], AR[133]) and all(t['MobilityJson'][up[0]['MobilityId']][k] == mob[k] for k in ('MaxCrossCountrySpeed', 'MaxSpeedRoad', 'MaxSpeedReverse')), 'HQ-9A armour / speed = PAC-2')
    ok(same(t['SensorsJson'][us[0]['SensorId']], t['SensorsJson'][8]), 'HQ-9A optics = PAC-2 optics')
    ok([(o['Cost'], o['Turret0Id']) for o in rows('OptionsJson', ModificationId=wm)] == [(0, t2), (80, T4)] and [o['Cost'] for o in rows('OptionsJson', ModificationId=am)] == [0, 5], 'HQ-9A slots = PAC-2: 2x / 4x +80, armour / B-kit +5')
    ok(same(W[w2], W[238], ('AudioPreset',)) or all(W[w2][k] == W[238][k] for k in ('Type', 'AimTimeMin', 'AimTimeMax', 'MagazineSize')), 'HQ-9A 2x launcher = PAC-2 x2 launcher')
    ok(U[HQ9]['HUDName'] == 'HQ-9B' and U[HQ9]['Cost'] == 325 and A[AMO]['LowAltRange'] == 1300.0 and A[AMO]['Seeker'] == 50, 'HQ-9B card: 325, active, 1300')
    ok(all(A[c_am][k] == A[MSE][k] for k in A[MSE] if k not in ('Id', 'Name', 'HUDName', 'LowAltRange', 'HighAltRange', 'ModelFileName', 'HUDIcon'))
       and (A[c_am]['LowAltRange'], A[c_am]['HighAltRange'], A[c_am]['Seeker']) == (1200.0, 1200.0, 50), 'HQ-9C missile = PAC-3 MSE round at 1200')
    ok(W[c_w]['MagazineSize'] == 8 and all(W[c_w][k] == W[WPN][k] for k in W[WPN] if k not in ('Id', 'Name', 'HUDName', 'MagazineSize')), 'HQ-9C launcher = HQ-9 launcher, 8 rounds')
    ok([(r['TurretId'], T[r['TurretId']]['IsDefault']) for r in rows('TurretUnitsJson', UnitId=HQ9)] == [(TUR, True), (c_t, False)], '4x default, 8x turret linked')
    ok([(O[o]['Cost'], O[o]['Turret0Id']) for o in (o4, o8)] == [(0, TUR), (0, c_t)] and all(not O[o].get(f'Turret{i}Id') for o in (o4, o8) for i in range(1, 21)), 'weapon slot: 4x / 8x, both +0')
    ok(U[HQ9A_CARD]['HUDName'] == 'HQ-9A' and A[a9['AmmunitionId']]['Seeker'] == 100 and A[a9['AmmunitionId']]['LowAltRange'] == 1175.0, 'HQ-9A card: semi-active')
    rec['hq9_rework_1122'] = {'hq9b_card': HQ9, 'hq9a_card': HQ9A_CARD, 'hq9c_missile': c_am, 'hq9c_launcher': c_w, 'hq9c_turret': c_t, 'options': [o4, o8],
                              'option_8x_name': NAME_8X}
    print('HQ9', rec['hq9_rework_1122'])

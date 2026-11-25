"""Lynx MRL (Osama 25 Nov 2026 03:2x PST, thread 1567745029781454889: "lynx 107mm MRL (just rename to Lynx MRL) fires a salvo 12 rounds at a
time. but it has 24 rounds total. only 1 salvo option. Base version is HE, +20 points for smoke only version. Range is 2800, dispersion lets
try this for now").
- 1437 'Lynx 66 107 mm MRL' shown as 'Lynx MRL'.
- Its rocket launcher (own weapon 2021358): one 12-rocket salvo; MagazineSize 40 -> 12; ground-attack salvo options Short 10 / Normal 20 /
  Long 40 -> 0 / 12 / 0, the game's single-salvo setup (as the vanilla HIMARS ATACMS weapon 569: 0 / 1 / 0).
- HE: its own copy of the rocket (the hidden 8x8 1438 keeps 2021360), GroundRange 1850 -> 1400 (card 2800 m); 12 -> 24 rockets; dispersion unchanged.
- Smoke-only loadout +20: a 107 mm copy of the vanilla Grad smoke rocket (73: smoke 60 s, 30 m) with the HE copy's range, minimum range,
  dispersion, flight and supply values; its own copy of the launcher on its own copy of the mount; 24 rockets. New weapon modification
  'Custom_Slot_Weapon_package' with two options, HE (default, +0) and Smoke (+20), the same way as the Lynx Troop Carrier's weapon options.
Creates rows: after every other row-creating section."""
MRL, HE_OLD, LAUNCHER, MOUNT, GRAD_SMK, TEMPLATE_OPT, TEMPLATE_MOD = 1437, 2021360, 2021358, 2021357, 73, 31415, 2021279
FLIGHT = ('GroundRange', 'MinimalRange', 'DispersionHorizontalRadius', 'DispersionVerticalRadius', 'DispersionMinimal', 'MuzzleVelocity',
          'MaxSpeed', 'Acceleration', 'BurnTime', 'TrajectoryType', 'SupplyCost', 'ResupplyTime', 'ModelFileName', 'AudioPreset')


def apply(t, g, ok, rec):
    U, W, A, WA, TW, TU, M, O, SU, T = (t[k] for k in ('Units', 'WeaponsJson', 'AmmunitionsJson', 'WeaponAmmunitionsJson', 'TurretWeaponsJson',
                                                     'TurretUnitsJson', 'ModificationsJson', 'OptionsJson', 'SensorUnitsJson', 'TurretsJson'))
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok(U[MRL]['HUDName'] == 'Lynx 66 107 mm MRL' and not rows('ModificationsJson', UnitId=MRL), 'Lynx 107 mm MRL, no modification yet')
    (wa,) = rows('WeaponAmmunitionsJson', UnitId=MRL)
    ok(wa['WeaponId'] == LAUNCHER and wa['AmmunitionId'] == HE_OLD and wa['Quantity'] == 12 and [r['UnitId'] for r in rows('WeaponAmmunitionsJson', WeaponId=LAUNCHER)] == [MRL]
       and [r['TurretId'] for r in rows('TurretWeaponsJson', WeaponId=LAUNCHER)] == [MOUNT] and [r['UnitId'] for r in rows('TurretUnitsJson', TurretId=MOUNT)] == [MRL],
       ('MRL own launcher on its own mount, HE 12', wa))
    ok(A[GRAD_SMK]['Name'] == 'MLRS 122 Grad SMK' and A[GRAD_SMK].get('SmokeDuration') and W[569]['HUDName'] == 'HIMARS'
       and (W[569]['ShortGroundAttackBurst'], W[569]['NormalGroundAttackBurst'], W[569]['LongGroundAttackBurst']) == (0, 1, 0), 'Grad smoke rocket; HIMARS single-salvo pattern')
    salvo = {'MagazineSize': 12, 'ShortGroundAttackBurst': 0, 'NormalGroundAttackBurst': 12, 'LongGroundAttackBurst': 0}
    g.put('WeaponsJson', LAUNCHER, salvo)
    he = g.add('AmmunitionsJson', A[HE_OLD], {'Name': 'PLA Lynx MRL 107 mm HE rocket', 'GroundRange': 1400.0})
    g.put('WeaponAmmunitionsJson', wa['Id'], {'AmmunitionId': he, 'Quantity': 24})
    smk = g.add('AmmunitionsJson', A[GRAD_SMK], {'Name': 'PLA Lynx MRL 107 mm smoke rocket', 'HUDName': '107 mm smoke', **{k: A[he].get(k) for k in FLIGHT}})
    sw = g.add('WeaponsJson', W[LAUNCHER], {'Name': 'PLA Lynx MRL 107 mm smoke rockets', 'HUDName': '107 mm rockets (smoke)'})
    smount = g.add('TurretsJson', T[MOUNT], {'Name': 'PLA Lynx MRL mount smoke', 'IsDefault': False})
    (tw,) = rows('TurretWeaponsJson', TurretId=MOUNT)
    g.add('TurretWeaponsJson', tw, {'TurretId': smount, 'WeaponId': sw})
    (tu,) = rows('TurretUnitsJson', TurretId=MOUNT)
    g.add('TurretUnitsJson', tu, {'TurretId': smount})
    g.add('WeaponAmmunitionsJson', wa, {'WeaponId': sw, 'AmmunitionId': smk, 'Quantity': 24})
    (su,) = rows('SensorUnitsJson', UnitId=MRL)
    mod = g.add('ModificationsJson', M[TEMPLATE_MOD], {'UnitId': MRL, 'Name': 'Weapons PLA Lynx MRL'})
    base = {k: v for k, v in O[TEMPLATE_OPT].items() if k != 'Id'}
    o_he = g.add('OptionsJson', base, {'ModificationId': mod, 'Name': 'PLA Lynx MRL HE', 'UIName': '107 mm HE rockets', 'Order': 0, 'IsDefault': True, 'Cost': 0,
                                       'OptionPicture': 'MLRS_HE', 'MainSensorId': su['SensorId'], 'Turret0Id': MOUNT, 'ConcatenateWithUnitName': None})
    o_sm = g.add('OptionsJson', base, {'ModificationId': mod, 'Name': 'PLA Lynx MRL Smoke', 'UIName': '107 mm smoke rockets', 'Order': 1, 'IsDefault': False, 'Cost': 20,
                                       'OptionPicture': 'ARTY_SMOKE', 'MainSensorId': su['SensorId'], 'Turret0Id': smount, 'ConcatenateWithUnitName': ' Smoke'})
    g.put('Units', MRL, {'HUDName': 'Lynx MRL'})
    got = sorted((W[r['WeaponId']]['HUDName'], A[r['AmmunitionId']]['HUDName'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=MRL))
    ok(got == [('107 mm rockets', '107 mm rockets ammunition', 24), ('107 mm rockets (smoke)', '107 mm smoke', 24)] and A[he]['GroundRange'] == A[smk]['GroundRange'] == 1400
       and A[HE_OLD]['GroundRange'] == 1850 and O[o_he]['Cost'] == 0 and O[o_sm]['Cost'] == 20 and max(o_he, o_sm) < 32768, ('Lynx MRL rows', got, o_he, o_sm))
    rec['lynx_mrl_1125'] = {'unit': MRL, 'he': he, 'smoke': smk, 'smoke_weapon': sw, 'smoke_mount': smount, 'modification': mod, 'options': [o_he, o_sm], 'salvo': salvo}
    print('LYNX MRL', rec['lynx_mrl_1125'])

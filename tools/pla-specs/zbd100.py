"""ZBD-100 (Shawn's Type 100 combat support vehicle model, 100_ZYZC) as a new China unit (Osama 22 Nov 2026 02:2x PST, thread 1572407822849810463:
"add it with a Bradley stand in, it has the armor profile of the ZBD-20. Exactly the same armor and driving profile. (btw zbd-20 should not be amphibious).
It is a 35mm telescoped round (let's model it after the same gun on the ZBD-20) except the KE rounds armor penetration is 100-180 and 2/s dps (zbd-20 has
1.55/s currently). Its HE round has 1200m range and same stats as the ZBD-20's HE gun. It gets smoke and can carry 6 people. It should have 2000 (armory)
optics, 80 points with +40 for APS option. and it has loadout option that adds 8x CH-901"; 02:3x "we call this the ZBD-100").
- Body: M2A3 Bradley stand-in (model, portrait, size, turret model). Armour row 2009807 and drive row 2009809 are the ZBD-20's own rows, linked, so the two
  stay identical. Drive row 2009809 (used only by the ZBD-20) is no longer amphibious.
- 35 mm gun: copy of the ZBD-20 ZPT-99 30 mm (same fire rate). KE round: penetration 180 close / 100 at range; damage 1.5 x 2 / 1.55 = 1.94, so the card
  damage per second goes from the ZBD-20's 1.55 to 2.0 (card DPS = damage x RateOfFireSecond, same weapon). HE round: the ZBD-20 HE with GroundRange 600
  (card 1200 m). KE keeps the ZBD-20 range (550, card 1100 m). Same round counts as the ZBD-20 (100 KE, 234 HE).
- Smoke + light supply: the ZBD-20 ability row 2000212. InfantrySlots 6. Optics: vanilla row 3 "Very Good Optics" (raw 2300, spotting cap 1000, the card
  shows 2000 m), the ZBD-20 Recon row. Cost 80. APS +40: ability 82 (GL-5 / Iron Fist, 2 charges, 10 s), as the ZBD-20.
- Loadout: 35 mm only (default) or 35 mm + 8x CH-901 (the Blood Wolves launcher 2018447 / round 2018448, CH-901 on mount Order 1). The CH-901 is
  laser-guided. Every ZBD-100 has the vanilla vehicle laser (Osama 22 Nov 02:39 "does it have a laser designator?" ... "it should"): row 8 "Laser Veh",
  1500, usable on the move, the row the ZBD-20 links, in ability slot 3 of BOTH loadout options (slot 3 is used by no other ZBD-100 modification).
  CH_COST +40 (Osama 22 Nov 03:0x: "CH-901 adds +40 points to the vehicle").
- Availability: transport for the ZBD-20's spec-18 squads whose squad fits 6 seats (Osama did not say where it goes)."""

CH_COST = 40
NAME = 'ZBD-100'


def apply(t, g, ok, rec):
    U, W, A, AB = t['Units'], t['WeaponsJson'], t['AmmunitionsJson'], t['AbilitiesJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    Z, BR = 945, 16
    GUN, KE, HE, CHW, CHA = 2009827, 2009829, 2009831, 2018447, 2018448
    ARM, MOB, SMOKE, APS, VG, LASER = 2009807, 2009809, 2000212, 82, 3, 8
    ok((U[Z]['HUDName'], U[BR]['HUDName']) == ('ZBD-20', 'M2A3 Bradley'), 'ZBD-20 and Bradley rows')
    ok(not any(u and NAME in (u.get('HUDName') or '') for u in U.values()), NAME + ' name free')
    ok([r['ArmorId'] for r in rows('UnitArmorsJson', UnitId=Z)] == [ARM] and [r['MobilityId'] for r in rows('UnitPropulsionsJson', UnitId=Z)] == [MOB], 'ZBD-20 armour / drive rows')
    ok({r['UnitId'] for r in rows('UnitPropulsionsJson', MobilityId=MOB)} == {Z} and t['MobilityJson'][MOB]['IsAmphibious'] is True, 'drive row only on ZBD-20, amphibious')
    ok(not any(o.get('MobilityId') == MOB for o in t['OptionsJson'].values() if o), 'no option swaps in the ZBD-20 drive row')
    ok([(r['WeaponId'], r['AmmunitionId'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=Z)][:2] == [(GUN, KE, 100), (GUN, HE, 234)], 'ZBD-20 gun rounds')
    ok((A[KE]['Damage'], A[KE]['PenetrationAtMinRange'], A[KE]['PenetrationAtGroundRange'], A[HE]['GroundRange']) == (1.5, 150.0, 75.0, 550.0), 'ZBD-20 KE 1.5 / 150-75, HE 550')
    ok((W[CHW]['HUDName'], A[CHA]['HUDName'], A[CHA]['LaserGuided']) == ('CH-901', 'CH-901', True), 'CH-901 rows')
    ok(t['SensorsJson'][VG]['Name'] == 'Very Good Optics' and t['SensorsJson'][VG]['OpticsGround'] == 2300.0, 'Very Good Optics 2300')
    ok(AB[APS]['IsAPS'] and AB[APS]['APSQuantity'] == 2 and AB[SMOKE]['IsSmoke'] and AB[LASER]['IsLaserDesignator'] and AB[LASER]['Name'] == 'Laser Veh' and not AB[LASER]['IsDefault'], 'ability rows')

    g.put('MobilityJson', MOB, {'IsAmphibious': False})

    d = dict(U[Z]); d.pop('Id')
    d.update({k: U[BR][k] for k in ('ModelFileName', 'PortraitFileName', 'ThumbnailFileName', 'Length', 'Width', 'Height')})
    d.update({'Name': 'PLA ' + NAME, 'HUDName': NAME, 'Cost': 80, 'OriginalCost': 0, 'InfantrySlots': 6, 'Description': None, 'OriginalName': None})
    uid = g.put('Units', max(U) + 1, d)
    g.add('UnitArmorsJson', rows('UnitArmorsJson', UnitId=Z)[0], {'UnitId': uid})
    g.add('UnitPropulsionsJson', rows('UnitPropulsionsJson', UnitId=Z)[0], {'UnitId': uid})
    g.add('SensorUnitsJson', rows('SensorUnitsJson', UnitId=Z)[0], {'UnitId': uid, 'SensorId': VG})
    tpl_ua = rows('UnitAbilitiesJson', UnitId=Z)[0]
    for ab in (SMOKE, 4, APS, LASER):
        g.add('UnitAbilitiesJson', tpl_ua, {'UnitId': uid, 'AbilityId': ab})

    gun = g.add('WeaponsJson', W[GUN], {'Name': 'PLA ZBD-100 35 mm', 'HUDName': '35 mm CT'})
    ke = g.add('AmmunitionsJson', A[KE], {'Name': 'PLA ZBD-100 35 mm APFSDS', 'HUDName': '35 mm CT APFSDS', 'Damage': 1.94,
                                          'PenetrationAtMinRange': 180.0, 'PenetrationAtGroundRange': 100.0})
    he = g.add('AmmunitionsJson', A[HE], {'Name': 'PLA ZBD-100 35 mm HE', 'HUDName': '35 mm CT HE', 'GroundRange': 600.0})
    wa = rows('WeaponAmmunitionsJson', UnitId=Z)
    g.add('WeaponAmmunitionsJson', wa[0], {'UnitId': uid, 'WeaponId': gun, 'AmmunitionId': ke})
    g.add('WeaponAmmunitionsJson', wa[1], {'UnitId': uid, 'WeaponId': gun, 'AmmunitionId': he})
    g.add('WeaponAmmunitionsJson', wa[1], {'UnitId': uid, 'WeaponId': CHW, 'AmmunitionId': CHA, 'Order': 2, 'Quantity': 8})

    T, TW = t['TurretsJson'], rows('TurretWeaponsJson', TurretId=53)
    base = g.add('TurretsJson', T[53], {'Name': 'PLA ZBD-100 mount 0'})
    chm = g.add('TurretsJson', T[53], {'Name': 'PLA ZBD-100 mount 0 CH-901'})
    for tur in (base, chm):
        g.add('TurretWeaponsJson', TW[0], {'TurretId': tur, 'WeaponId': gun})
    g.add('TurretWeaponsJson', TW[1], {'TurretId': chm, 'WeaponId': CHW})
    for tur in (base, chm):
        g.add('TurretUnitsJson', rows('TurretUnitsJson', UnitId=Z)[0], {'UnitId': uid, 'TurretId': tur})

    zm = {m['Type']: m for m in rows('ModificationsJson', UnitId=Z)}
    lm = g.add('ModificationsJson', zm[3], {'UnitId': uid, 'Name': 'PLA ZBD-100 loadout', 'Order': 0})
    lo = rows('OptionsJson', ModificationId=zm[3]['Id'])
    g.add('OptionsJson', lo[0], {'ModificationId': lm, 'Name': 'PLA ZBD-100 35 mm', 'UIName': '35 mm CT', 'OptionPicture': 'EMPTY',
                                 'Turret0Id': base, 'Ability3Id': LASER})
    g.add('OptionsJson', lo[1], {'ModificationId': lm, 'Name': 'PLA ZBD-100 CH-901', 'UIName': '8x CH-901', 'Cost': CH_COST,
                                 'Turret0Id': chm, 'Ability3Id': LASER})
    am = g.add('ModificationsJson', zm[6], {'UnitId': uid, 'Name': 'PLA ZBD-100 APS', 'Order': 1})
    ao = {o['Ability2Id']: o for o in rows('OptionsJson', ModificationId=zm[6]['Id'])}
    g.add('OptionsJson', ao[4], {'ModificationId': am, 'Name': 'PLA ZBD-100 No APS'})
    g.add('OptionsJson', ao[APS], {'ModificationId': am, 'Name': 'PLA ZBD-100 GL-5 APS', 'Cost': 40, 'Order': 1})

    SA, TA = t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson']
    men = lambda u: len(rows('SquadMembersJson', UnitId=u))
    fit, big = [], []
    for r in rows('TransportAvailabilitiesJson', UnitId=Z):
        sq = SA[r['SpecializationAvailabilityId']]['UnitId']
        (fit if 0 < men(sq) <= 6 else big).append((sq, U[sq]['HUDName'], men(sq)))
        if 0 < men(sq) <= 6:
            g.add('TransportAvailabilitiesJson', r, {'UnitId': uid})

    # checks
    ok(t['MobilityJson'][MOB]['IsAmphibious'] is False, 'ZBD-20 / ZBD-100 drive row not amphibious')
    ok([r['ArmorId'] for r in rows('UnitArmorsJson', UnitId=uid)] == [ARM] and [r['MobilityId'] for r in rows('UnitPropulsionsJson', UnitId=uid)] == [MOB], 'ZBD-100 = ZBD-20 armour and drive rows')
    ok((U[uid]['Cost'], U[uid]['InfantrySlots'], U[uid]['ModelFileName'], U[uid]['CountryId']) == (80, 6, 'US_M2A3', 4), 'ZBD-100 card: 80, 6 seats, Bradley model, China')
    ok([r['SensorId'] for r in rows('SensorUnitsJson', UnitId=uid)] == [VG], 'ZBD-100 Very Good Optics (card 2000 m)')
    ok(all(W[gun][k] == W[GUN][k] for k in W[GUN] if k not in ('Id', 'Name', 'HUDName')), '35 mm gun = ZBD-20 gun (fire rate)')
    ok(abs(A[ke]['Damage'] / A[KE]['Damage'] * 1.55 - 2.0) < 0.01, ('KE card DPS 1.55 -> 2.0', round(A[ke]['Damage'] / A[KE]['Damage'] * 1.55, 3)))
    ok(all(A[he][k] == A[HE][k] for k in A[HE] if k not in ('Id', 'Name', 'HUDName', 'GroundRange')) and A[he]['GroundRange'] * 2 == 1200, 'HE = ZBD-20 HE, card 1200 m')
    opts = [o for m in rows('ModificationsJson', UnitId=uid) for o in rows('OptionsJson', ModificationId=m['Id'])]
    for k in (1, 2, 3):
        used = {m['Id'] for m in rows('ModificationsJson', UnitId=uid) for o in rows('OptionsJson', ModificationId=m['Id']) if o.get(f'Ability{k}Id')}
        ok(len(used) <= 1, (NAME, f'ability slot {k} used by one modification', used))
    ok(sorted(o['Ability3Id'] for o in opts if o['ModificationId'] == lm) == [LASER, LASER], 'laser on both loadouts')
    linked = {r['AbilityId'] for r in rows('UnitAbilitiesJson', UnitId=uid)}
    ok(all(o.get(f'Ability{k}Id', 0) in linked | {0} for o in opts for k in (1, 2, 3)), 'every option ability linked')
    tw = {tur: [(w['Order'], w['WeaponId']) for w in rows('TurretWeaponsJson', TurretId=tur)] for tur in (base, chm)}
    ok(tw == {base: [(0, gun)], chm: [(0, gun), (1, CHW)]}, ('mounts', tw))
    ok({w for v in tw.values() for _, w in v} == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=uid)}, 'mount weapons == ammo weapons')
    ok(len(rows('TransportAvailabilitiesJson', UnitId=uid)) == len(fit) > 0, ('transport cards', fit, 'too big', big))
    rec['zbd100'] = {'unit': uid, 'gun': gun, 'ke': ke, 'he': he, 'mounts': [base, chm], 'options': [o['Id'] for o in opts], 'ch901_cost': CH_COST,
                     'transport_for': fit, 'not_fitting': big, 'zbd20_amphibious': [True, False]}
    print('ZBD100', rec['zbd100'])

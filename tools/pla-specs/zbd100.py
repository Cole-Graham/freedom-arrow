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
- Loadout (one slot, vanilla unit-swap pattern as Buk-M2 -> Buk-M3): 35 mm (this card, 80) / GL-5 APS (+40) / 8x CH-901 (+40) / both (+80). Each
  choice is its own unit row with ONE turret (IsUnitModification, swap row Cost = 80 + option). The CH-901 launcher is a copy of the Blood Wolves
  launcher 2018447 without its infantry Javelin model; round 2018448 (laser-guided, in nlos.json). Every ZBD-100 has the vanilla vehicle laser (Osama
  22 Nov 02:39 "it should"): 1500, usable on the move, built into the default ability row with smoke + light supply.
- 22 Nov 13:4x (Osama, Arsenal in dev.29: "the APS should be under protection package section", "Weapon 8x CH-901 should change to 9x", "1200 low
  alt range I mean on the HE"): weapon package = 35 mm CT / 9x CH-901 (+40, the two swap rows); GL-5 APS (+40) is its own protection slot, the
  Bradley's own pattern (modification type 6 Custom_Slot_Protection_system, option Ability1Id 82), not a swap row. HE LowAltRange 600 (card 1200).
- 22 Nov 13:5x (Osama: "yeah lets run those armor values, probably make the vehicle 120 points base. Give its CH-901 60mm penetration"): own armour
  row (source: ~700 mm RHAe KE front, more vs HEAT, sides proof against 30 mm): KE front 650 / sides 180 / rear 60 / top 60, HEAT front 900 /
  sides 500 / rear 60 / top 60, HP 12; the VN-17 (ZBD-20) keeps row 2009807. Base 120 (CH-901 row 160). Own CH-901 round (penetration 60 / 60,
  the Blood Wolves round stays 30), added to nlos.json ammunition by apply_0_9_4_dev1.py so it keeps the NLOS lock.
  Why not turret-swapping options (dev.19-26, measured on Osama's PC, GameLogs "Couldn't load unit", AnimatorConnect duplicate trigger 'Shot'): on the
  Bradley body two turret rows only work when each fills the three Bradley weapon slots, as vanilla (dev.27: our two turrets fail even without options,
  the vanilla rows 53/52 work, one turret + an APS-only slot works). The ZBD-20 pattern works on its BMP-3 body only.
- Availability: a Recon-tab card in spec 18 PLAGF Armored Force (Osama 22 Nov 02:4x: "you put it in armored spec right?", "in the recon tab?"):
  Units.CategoryType 0 and a SpecializationAvailabilities row copied from the ZBD-04A Recon's spec-18 card (same card count). Also a transport for the
  ZBD-20's spec-18 squads whose squad fits 6 seats."""

CH_COST = 40
BASE = 120
NAME = 'ZBD-100'


def apply(t, g, ok, rec):
    U, W, A, AB = t['Units'], t['WeaponsJson'], t['AmmunitionsJson'], t['AbilitiesJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    Z, BR = 945, 16
    GUN, KE, HE, CHW, CHA, MG = 2009827, 2009829, 2009831, 2018447, 2018448, 2009833
    ARM, MOB, SMOKE, APS, VG, LASER = 2009807, 2009809, 2000212, 82, 3, 8
    ok((U[Z]['HUDName'], U[BR]['HUDName']) == ('ZBD-20', 'M2A3 Bradley'), 'ZBD-20 and Bradley rows')
    ok(not any(u and NAME in (u.get('HUDName') or '') for u in U.values()), NAME + ' name free')
    ok([r['ArmorId'] for r in rows('UnitArmorsJson', UnitId=Z)] == [ARM] and [r['MobilityId'] for r in rows('UnitPropulsionsJson', UnitId=Z)] == [MOB], 'ZBD-20 armour / drive rows')
    ok({r['UnitId'] for r in rows('UnitPropulsionsJson', MobilityId=MOB)} == {Z} and t['MobilityJson'][MOB]['IsAmphibious'] is True, 'drive row only on ZBD-20, amphibious')
    ok(not any(o.get('MobilityId') == MOB for o in t['OptionsJson'].values() if o), 'no option swaps in the ZBD-20 drive row')
    ok([(r['WeaponId'], r['AmmunitionId'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=Z)][:3] == [(GUN, KE, 100), (GUN, HE, 234), (MG, 2009835, 800)], 'ZBD-20 gun + coax rounds')
    ok((A[KE]['Damage'], A[KE]['PenetrationAtMinRange'], A[KE]['PenetrationAtGroundRange'], A[HE]['GroundRange']) == (1.5, 150.0, 75.0, 550.0), 'ZBD-20 KE 1.5 / 150-75, HE 550')
    ok((W[CHW]['HUDName'], A[CHA]['HUDName'], A[CHA]['LaserGuided']) == ('CH-901', 'CH-901', True), 'CH-901 rows')
    ok(t['SensorsJson'][VG]['Name'] == 'Very Good Optics' and t['SensorsJson'][VG]['OpticsGround'] == 2300.0, 'Very Good Optics 2300')
    ok(AB[APS]['IsAPS'] and AB[APS]['APSQuantity'] == 2 and AB[SMOKE]['IsSmoke'] and AB[LASER]['IsLaserDesignator'] and AB[LASER]['Name'] == 'Laser Veh' and not AB[LASER]['IsDefault'], 'ability rows')

    g.put('MobilityJson', MOB, {'IsAmphibious': False})

    d = dict(U[Z]); d.pop('Id')
    # Body values of the stand-in, not the amphibious BMP-3 of the ZBD-20: WaterDiveOffset 0 (the ZBD-20's 1.23 came along in dev.19) and the
    # Bradley sound preset.
    d.update({k: U[BR][k] for k in ('ModelFileName', 'PortraitFileName', 'ThumbnailFileName', 'Length', 'Width', 'Height', 'WaterDiveOffset', 'AudioPreset')})
    d.update({'Name': 'PLA ' + NAME, 'HUDName': NAME, 'Cost': BASE, 'OriginalCost': 0, 'InfantrySlots': 6, 'Description': None, 'OriginalName': None})
    uid = g.put('Units', max(U) + 1, d)
    arm = g.add('ArmorsJson', t['ArmorsJson'][ARM], {'Name': 'PLA Type 100 CSV', 'KinArmorFront': 650, 'KinArmorSides': 180, 'KinArmorRear': 60,
                                                    'KinArmorTop': 60, 'HeatArmorFront': 900, 'HeatArmorSides': 500, 'HeatArmorRear': 60,
                                                    'HeatArmorTop': 60, 'MaxHealthPoints': 12})
    g.add('UnitArmorsJson', rows('UnitArmorsJson', UnitId=Z)[0], {'UnitId': uid, 'ArmorId': arm})
    g.add('UnitPropulsionsJson', rows('UnitPropulsionsJson', UnitId=Z)[0], {'UnitId': uid})
    g.add('SensorUnitsJson', rows('SensorUnitsJson', UnitId=Z)[0], {'UnitId': uid, 'SensorId': VG})
    gun = g.add('WeaponsJson', W[GUN], {'Name': 'PLA ZBD-100 35 mm', 'HUDName': '35 mm CT'})
    ke = g.add('AmmunitionsJson', A[KE], {'Name': 'PLA ZBD-100 35 mm APFSDS', 'HUDName': '35 mm CT APFSDS', 'Damage': 1.94,
                                          'PenetrationAtMinRange': 180.0, 'PenetrationAtGroundRange': 100.0})
    he = g.add('AmmunitionsJson', A[HE], {'Name': 'PLA ZBD-100 35 mm HE', 'HUDName': '35 mm CT HE', 'GroundRange': 600.0, 'LowAltRange': 600.0})
    chl = g.add('WeaponsJson', W[CHW], {'Name': 'PLA ZBD-100 CH-901 launcher', 'ModelFileName': None})
    T, TW = t['TurretsJson'], rows('TurretWeaponsJson', TurretId=53)
    base = g.add('TurretsJson', T[53], {'Name': 'PLA ZBD-100 mount 0'})
    chm = g.add('TurretsJson', T[53], {'Name': 'PLA ZBD-100 mount 0 CH-901'})
    g.add('TurretWeaponsJson', TW[0], {'TurretId': base, 'WeaponId': gun})
    g.add('TurretWeaponsJson', TW[0], {'TurretId': chm, 'WeaponId': gun})
    g.add('TurretWeaponsJson', TW[1], {'TurretId': chm, 'WeaponId': chl})
    # default ability row (one per unit, IsDefault): smoke + light supply (2000212) + laser (row 8 fields); APS comes from the protection slot
    las = {k: AB[LASER][k] for k in ('IsLaserDesignator', 'LaserMaxRange', 'LaserUsableInMove')}
    def ability(name, extra):   # ability-row reuse rule: link an existing row with exactly these values, add one only for a new combination
        want = dict(AB[SMOKE], **extra)
        same = [i for i, r in AB.items() if r and all(r.get(k) == v for k, v in want.items() if k not in ('Id', 'Name'))]
        return same[0] if same else g.add('AbilitiesJson', AB[SMOKE], {'Name': name, **extra})
    ab_l = ability('PLA ZBD-100 smoke supply laser', las)
    wa, tpl_ua, tpl_tu = rows('WeaponAmmunitionsJson', UnitId=Z), rows('UnitAbilitiesJson', UnitId=Z)[0], rows('TurretUnitsJson', UnitId=Z)[0]
    units = {}
    cha = g.add('AmmunitionsJson', A[CHA], {'Name': 'PLA Type 100 CH-901', 'PenetrationAtMinRange': 60.0, 'PenetrationAtGroundRange': 60.0})
    for key, cost, tur, ab in (('', BASE, base, ab_l), (' CH-901', BASE + CH_COST, chm, ab_l)):
        e = dict(d, Name='PLA ' + NAME + key, Cost=cost, IsUnitModification=bool(key))
        u = uid if not key else g.put('Units', max(U) + 1, e)
        units[key] = u
        if key:
            g.add('UnitArmorsJson', rows('UnitArmorsJson', UnitId=Z)[0], {'UnitId': u, 'ArmorId': arm})
            g.add('UnitPropulsionsJson', rows('UnitPropulsionsJson', UnitId=Z)[0], {'UnitId': u})
            g.add('SensorUnitsJson', rows('SensorUnitsJson', UnitId=Z)[0], {'UnitId': u, 'SensorId': VG})
        g.add('UnitAbilitiesJson', tpl_ua, {'UnitId': u, 'AbilityId': ab})
        g.add('TurretUnitsJson', tpl_tu, {'UnitId': u, 'TurretId': tur})
        g.add('WeaponAmmunitionsJson', wa[0], {'UnitId': u, 'WeaponId': gun, 'AmmunitionId': ke})
        g.add('WeaponAmmunitionsJson', wa[1], {'UnitId': u, 'WeaponId': gun, 'AmmunitionId': he})
        if tur == chm:
            g.add('WeaponAmmunitionsJson', wa[1], {'UnitId': u, 'WeaponId': chl, 'AmmunitionId': cha, 'Order': 2, 'Quantity': 9})
    zm = {m['Type']: m for m in rows('ModificationsJson', UnitId=Z)}
    lm = g.add('ModificationsJson', zm[3], {'UnitId': uid, 'Name': 'PLA ZBD-100 loadout', 'Order': 0})
    tpl_o = rows('OptionsJson', ModificationId=zm[3]['Id'])[0]
    for n, (key, ui, pic) in enumerate(((' ', '35 mm CT', 'EMPTY'), (' CH-901', '9x CH-901', 'VEH_SPIKE_LR'))):
        r = units[key.rstrip()]
        g.add('OptionsJson', tpl_o, {'ModificationId': lm, 'Name': 'PLA ZBD-100 loadout' + key.rstrip(), 'UIName': ui, 'OptionPicture': pic, 'Order': n,
                                     'IsDefault': False, 'Cost': U[r]['Cost'] - BASE, 'ReplaceUnitId': r, 'ReplaceUnitName': None if r == uid else NAME,
                                     'Turret0Id': 0, 'Ability1Id': 0, 'Ability2Id': 0, 'Ability3Id': 0, 'ArmorId': 0})
    # protection slot: copy of the Bradley's (mod 483 'Ability M2A3', type 6): None / GL-5 APS. Only Ability1Id is set (82); the turret stays the
    # swap row's own (Turret0Id 0, where the Bradley swaps its turret 53 -> 52 for the Iron Fist model).
    bp = rows('ModificationsJson', UnitId=BR, Type=6)
    ok(len(bp) == 1 and bp[0]['UIName'] == 'Custom_Slot_Protection_system', 'Bradley protection slot')
    pm = g.add('ModificationsJson', bp[0], {'UnitId': uid, 'Name': 'PLA ZBD-100 protection', 'Order': 1})
    bo = {o['UIName']: o for o in rows('OptionsJson', ModificationId=bp[0]['Id'])}
    # option abilities need a (unit, ability) UnitAbilities link for multiplayer (audit_mp_equipment.py; the Bradley links 88 the same way); the
    # CH-901 swap row gets one too, since it is the unit that spawns with that loadout
    for u in units.values():
        g.add('UnitAbilitiesJson', tpl_ua, {'UnitId': u, 'AbilityId': APS})
    for n, (src, ui, cost, ab) in enumerate((('Custom_Option_None', 'Custom_Option_None', 0, 0), ('Custom_Option_IronFist_APS', 'GL-5 APS', 40, APS))):
        g.add('OptionsJson', bo[src], {'ModificationId': pm, 'Name': 'PLA ZBD-100 protection ' + ('APS' if ab else 'none'), 'UIName': ui, 'Order': n,
                                       'Cost': cost, 'Turret0Id': 0, 'Ability1Id': ab, 'Ability2Id': 0, 'Ability3Id': 0, 'ReplaceUnitId': 0})

    SA, TA = t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson']
    ARMD = 18
    ok(t['SpecializationsJson'][ARMD]['Name'] == 'PLA PLAGF Armored Force', 'spec 18 = Armored Force')
    r04 = [r for r in SA.values() if r and r['SpecializationId'] == ARMD and U[r['UnitId']]['HUDName'].strip() == 'ZBD-04A Recon']
    ok(len(r04) == 1 and U[r04[0]['UnitId']]['CategoryType'] == 0, ('ZBD-04A Recon: one Recon-tab card in Armored', r04))
    g.put('Units', uid, {'CategoryType': 0})
    g.add('SpecializationAvailabilitiesJson', r04[0], {'UnitId': uid})
    men = lambda u: len(rows('SquadMembersJson', UnitId=u))
    fit, big = [], []
    for r in rows('TransportAvailabilitiesJson', UnitId=Z):
        sq = SA[r['SpecializationAvailabilityId']]['UnitId']
        (fit if 0 < men(sq) <= 6 else big).append((sq, U[sq]['HUDName'], men(sq)))
        if 0 < men(sq) <= 6:
            g.add('TransportAvailabilitiesJson', r, {'UnitId': uid})

    # checks
    ok(t['MobilityJson'][MOB]['IsAmphibious'] is False, 'ZBD-20 / ZBD-100 drive row not amphibious')
    ok(all([r['ArmorId'] for r in rows('UnitArmorsJson', UnitId=u)] == [arm] and [r['MobilityId'] for r in rows('UnitPropulsionsJson', UnitId=u)] == [MOB] for u in units.values()), 'Type 100 own armour row, ZBD-20 drive row')
    ok([r['ArmorId'] for r in rows('UnitArmorsJson', UnitId=Z)] == [ARM] and all(t['ArmorsJson'][arm][k] == t['ArmorsJson'][ARM][k] for k in ('IsDefault', 'ModelFileName', 'ArmorValue')), 'VN-17 keeps its armour row; Type 100 row = copy')
    ok(all(A[cha][k] == A[CHA][k] for k in A[CHA] if k not in ('Id', 'Name', 'PenetrationAtMinRange', 'PenetrationAtGroundRange')) and (A[cha]['PenetrationAtMinRange'], A[cha]['PenetrationAtGroundRange'], A[CHA]['PenetrationAtGroundRange']) == (60.0, 60.0, 30.0), 'Type 100 CH-901 round: penetration 60, Blood Wolves round unchanged')
    ok((U[uid]['Cost'], U[uid]['InfantrySlots'], U[uid]['ModelFileName'], U[uid]['CountryId'], U[uid]['WaterDiveOffset']) == (BASE, 6, 'US_M2A3', 4, U[BR]['WaterDiveOffset']), 'ZBD-100 card: 120, 6 seats, Bradley model and dive offset, China')
    ok([r['SensorId'] for r in rows('SensorUnitsJson', UnitId=uid)] == [VG], 'ZBD-100 Very Good Optics (card 2000 m)')
    ok(all(W[gun][k] == W[GUN][k] for k in W[GUN] if k not in ('Id', 'Name', 'HUDName')), '35 mm gun = ZBD-20 gun (fire rate)')
    ok(abs(A[ke]['Damage'] / A[KE]['Damage'] * 1.55 - 2.0) < 0.01, ('KE card DPS 1.55 -> 2.0', round(A[ke]['Damage'] / A[KE]['Damage'] * 1.55, 3)))
    ok(all(A[he][k] == A[HE][k] for k in A[HE] if k not in ('Id', 'Name', 'HUDName', 'GroundRange', 'LowAltRange')) and A[he]['GroundRange'] * 2 == 1200, 'HE = ZBD-20 HE, card 1200 m')
    opts = rows('OptionsJson', ModificationId=lm)
    ok(len(rows('ModificationsJson', UnitId=uid)) == 2 and [(o['Cost'], o['ReplaceUnitId'], o['UIName']) for o in opts] == [(0, uid, '35 mm CT'), (CH_COST, units[' CH-901'], '9x CH-901')], 'weapon slot: 35 mm / 9x CH-901')
    popts = rows('OptionsJson', ModificationId=pm)
    ok(t['ModificationsJson'][pm]['Type'] == 6 and [(o['Cost'], o['Ability1Id'], o['Ability2Id'], o['Ability3Id'], o['ReplaceUnitId'], o['Turret0Id']) for o in popts] == [(0, 0, 0, 0, 0, 0), (40, APS, 0, 0, 0, 0)], 'protection slot: none / GL-5 APS +40')
    ok(not AB[APS]['IsDefault'], 'APS option ability is not a default ability (AddAbility skips defaults)')
    ok([r['Quantity'] for r in rows('WeaponAmmunitionsJson', UnitId=units[' CH-901'], WeaponId=chl)] == [9] and A[he]['LowAltRange'] == 600.0, '9 CH-901, HE low-altitude 600 (card 1200)')
    ok(all(U[o['ReplaceUnitId']]['Cost'] == U[uid]['Cost'] + o['Cost'] for o in opts), 'swap rows cost = base + option (audit_swap_prices rule)')
    for key, u in units.items():
        tu = rows('TurretUnitsJson', UnitId=u)
        ok(len(tu) == 1 and [AB[r['AbilityId']]['IsDefault'] for r in rows('UnitAbilitiesJson', UnitId=u)] == [True, False] and not rows('ModificationsJson', UnitId=u) or u == uid, (key, 'one turret, one default ability'))
        ok({w['WeaponId'] for w in rows('TurretWeaponsJson', TurretId=tu[0]['TurretId'])} == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=u)}, (key, 'mount weapons == ammo weapons'))
        abr = AB[rows('UnitAbilitiesJson', UnitId=u)[0]['AbilityId']]
        ok(rows('UnitAbilitiesJson', UnitId=u)[1]['AbilityId'] == APS, (key, 'APS option ability linked'))
        ok(abr['IsDefault'] and abr['IsSmoke'] and abr['IsLaserDesignator'] and not abr['IsAPS'], (key, 'smoke + laser, APS only from the protection slot'))
    ok(W[chl]['ModelFileName'] is None and all(W[chl][k] == W[CHW][k] for k in W[CHW] if k not in ('Id', 'Name', 'ModelFileName')), 'vehicle CH-901 launcher = Blood Wolves launcher without the Javelin model')
    ok(len(rows('TransportAvailabilitiesJson', UnitId=uid)) == len(fit) > 0, ('transport cards', fit, 'too big', big))
    card = [r for r in SA.values() if r and r['UnitId'] == uid]
    ok(len(card) == 1 and card[0]['SpecializationId'] == ARMD and U[uid]['CategoryType'] == 0, ('ZBD-100 Recon card in Armored', card))
    rec['zbd100'] = {'armored_recon_card': {k: card[0].get(k) for k in card[0] if k.startswith('Max') or k == 'SpecializationId'}, 'unit': uid, 'swap_units': units, 'gun': gun, 'ke': ke, 'he': he, 'mounts': [base, chm], 'options': [o['Id'] for o in opts], 'protection_options': [o['Id'] for o in popts], 'armor': arm, 'ch901_round': cha, 'ch901_cost': CH_COST,
                     'transport_for': fit, 'not_fitting': big, 'zbd20_amphibious': [True, False]}
    print('ZBD100', rec['zbd100'])

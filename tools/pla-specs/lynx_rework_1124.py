"""Lynx family rework (Osama 24 Nov 2026 19:15 PST, thread 1567745029781454889, with a screenshot of the CS/VP16B card).
Runs at the END of the batch (after the FK-3000 / PCL-181 cards): every row it makes gets a new id after all existing ones, so no unit, option or
row id made earlier moves (saved decks keep units by id). Cards are made by lynx_cards_1124.py; this only changes them.
- "6x6 Laser Weapon renamed Lynx Laser, Ly-1 but no missile or high altitude range, only helos and ground. has laser aps. ground range is 800
  (armory) and 1100 (armory). no radar.": the LY-1 laser (weapon 2019445) on its own mount, its pulse copied as ground 400 / low 550 / high 0
  (the Armory shows 2x: 800 / 1100), TargetType 47 (ground, infantry, vehicle, helicopter, ship; no aircraft, no missiles), and the LY-1
  laser defense as a laser-APS-only row (no radar).
- "CS/VP16B (should be renamed Lynx Troop Carrier) ... make it carry 9 people": HUDName, InfantrySlots 9. The bigger model and the armed-option
  model swap are in work/model-rework-096/stage.py (FAModels variants).
- "CS/VP16B Mortar removed", "CS/VP17 command remove", "CS/VP17 Drone carrier, remove", "We will only have one lynx MLRS, that's the new model
  you add" (the Lynx 66 107 mm MRL): the CS/VP16B Mortar, CS/VP17 Command, CS/VP17 Drone Carrier and Lynx 8x8 107 mm MRL leave the airborne spec
  and are hidden in the Armory; unit rows stay.
- "CS/VP16B Recon (Lynx Recon) should have Very Good level of optics": sensor 3 'Very Good Optics' (ground 2300).
- "CS/CP17 120mm Mortar (renamed Lynx 120mm mortar), cut down the ammo to 1/3": 60/15 -> 20/5.
- "CS/VP 17 Rapid-fire gun renamed Lynx Rapid-Fire Gun, no passengers, its in the Veh tab. it has 2x HJ-8H. 35 points": InfantrySlots 0,
  CategoryType 2, cost 35; its turrets are copied (the ZSL-92's stay as they are) and mount 0 gets an HJ-8H launcher in the WZ-551's HJ-8E slot
  (Order 2; a copy of the WZ-551's vehicle HJ-8E launcher, named HJ-8H) firing the Marine HJ-8H round (2018802), 2 missiles.
- "CS-SM8 81mm mortar rename Lynx 81mm Mortar and ammo is down to 25%": 80/24/25 -> 20/6/6.
- "Lynx 66 120mm howitzer renamed Lynx Howitzer, ammo cut down to 1/2. 60pts.": every ammunition row halved, cost 60 (all cuts rounded to the nearest whole round).
- "Lynx 66 SPAAG, rename Lynx SPAAG, remove the radar, gun: remove Low alt. range, high alt. range. Only targets ground and helicopters. FB-10
  replaced by QW-2 and 4 ammo. 80 points.": radar ability rows dropped; the gun's rounds copied with Low/High 0 and TargetType 47; its turret is
  copied (the PGL-625's stays) with the FB-10 launcher swapped for the PGZ-04A's QW-2 launcher (2009561, round 2009565) x4; cost 80."""
LY1_WEAPON, LY1_ROUND, LY1_ABILITY = 2019445, 2019446, 2019443
VERY_GOOD_OPTICS = 3
HJ8E_VEH_WEAPON, HJ8H_ROUND = 2010149, 2018802          # WZ-551 HJ-8E launcher; Marine HJ-8H round
QW2_WEAPON, QW2_ROUND = 2009561, 2009565                # PGZ-04A QW-2 launcher and round
GROUND_HELI = 1 | 2 | 4 | 8 | 32                         # TargetType: Ground, Infantry, Vehicle, Helicopter, Ship
HIDE = ('PLA Lynx CS/VP16B Mortar', 'PLA Lynx CS/VP17 Command', 'PLA Lynx CS/VP17 Drone Carrier', 'PLA Lynx 8x8 107 mm MRL')
RENAME = {'PLA Lynx 6x6 Laser Weapon': 'Lynx Laser', 'PLA Lynx CS/VP16B': 'Lynx Troop Carrier', 'PLA Lynx CS/VP16B Recon': 'Lynx Recon',
          'PLA Lynx CS/VP17 120 mm Mortar': 'Lynx 120mm Mortar', 'PLA Lynx CS/VP17 Rapid-Fire Gun': 'Lynx Rapid-Fire Gun',
          'PLA Lynx CS-SM8 81 mm Mortar': 'Lynx 81mm Mortar', 'PLA Lynx 66 120 mm Mortar-Howitzer': 'Lynx Howitzer', 'PLA Lynx 66 SPAAG': 'Lynx SPAAG'}
AMMO_SCALE = {'PLA Lynx CS/VP17 120 mm Mortar': 1 / 3, 'PLA Lynx CS-SM8 81 mm Mortar': 0.25, 'PLA Lynx 66 120 mm Mortar-Howitzer': 0.5}
COST = {'PLA Lynx CS/VP17 Rapid-Fire Gun': 35, 'PLA Lynx 66 120 mm Mortar-Howitzer': 60, 'PLA Lynx 66 SPAAG': 80}


def apply(t, g, ok, rec):
    U, SA, TA, AB, W, A = t['Units'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson'], t['AbilitiesJson'], t['WeaponsJson'], t['AmmunitionsJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    uid = {}
    for name in set(HIDE) | set(RENAME) | set(AMMO_SCALE) | set(COST):
        m = [i for i, u in U.items() if u and u.get('Name') == name]
        ok(len(m) == 1, (name, 'one unit')); uid[name] = m[0]
    out = {'hidden': {}, 'changed': {}}

    def weapons(u):
        return [(x['Order'], W[x['WeaponId']]['HUDName']) for r in rows('TurretUnitsJson', UnitId=u) for x in rows('TurretWeaponsJson', TurretId=r['TurretId'])]

    def own_turret(u, swap):
        """Copy each of the unit's turrets (shared with the parent card) and point the unit at the copies; swap(tw) edits each copied weapon row."""
        for tu in rows('TurretUnitsJson', UnitId=u):
            new = g.add('TurretsJson', t['TurretsJson'][tu['TurretId']], {'Name': f"{t['TurretsJson'][tu['TurretId']].get('Name')} {U[u]['Name']}"})
            for x in rows('TurretWeaponsJson', TurretId=tu['TurretId']):
                f = swap(x)
                if f is not None: g.add('TurretWeaponsJson', x, {'TurretId': new, **f})
            g.put('TurretUnitsJson', tu['Id'], {'TurretId': new})

    # hidden
    for name in HIDE:
        u = uid[name]; sa = [r['Id'] for r in rows('SpecializationAvailabilitiesJson', UnitId=u)]
        ok(not rows('TransportAvailabilitiesJson', UnitId=u), (name, 'no transport links'))
        for i in sa: g.remove('SpecializationAvailabilitiesJson', i)
        g.put('Units', u, {'DisplayInArmory': False})
        ok(not rows('SpecializationAvailabilitiesJson', UnitId=u) and U[u]['DisplayInArmory'] is False, (name, 'hidden'))
        out['hidden'][name] = {'unit': u, 'availability_removed': sa}
    # names, costs, seats, tab
    for name, hud in RENAME.items(): g.put('Units', uid[name], {'HUDName': hud})
    for name, c in COST.items(): g.put('Units', uid[name], {'Cost': c})
    g.put('Units', uid['PLA Lynx CS/VP16B'], {'InfantrySlots': 9})
    g.put('Units', uid['PLA Lynx CS/VP17 Rapid-Fire Gun'], {'InfantrySlots': 0, 'CategoryType': 2})
    # ammunition cuts
    for name, k in AMMO_SCALE.items():
        for r in rows('WeaponAmmunitionsJson', UnitId=uid[name]):
            g.put('WeaponAmmunitionsJson', r['Id'], {'Quantity': max(1, round(r['Quantity'] * k))})
    # recon optics
    rc = uid['PLA Lynx CS/VP16B Recon']; su = rows('SensorUnitsJson', UnitId=rc)
    ok(len(su) == 1 and t['SensorsJson'][VERY_GOOD_OPTICS]['Name'] == 'Very Good Optics' and t['SensorsJson'][VERY_GOOD_OPTICS]['OpticsGround'] == 2300.0, 'Lynx Recon sensor')
    g.put('SensorUnitsJson', su[0]['Id'], {'SensorId': VERY_GOOD_OPTICS})
    # Rapid-Fire Gun: + HJ-8H x2 on its own turret copy
    rf = uid['PLA Lynx CS/VP17 Rapid-Fire Gun']
    ok(W[HJ8E_VEH_WEAPON]['HUDName'] == 'HJ-8E' and A[HJ8H_ROUND]['HUDName'] == 'HJ-8H', 'HJ-8E vehicle launcher, HJ-8H round')
    hj = g.add('WeaponsJson', W[HJ8E_VEH_WEAPON], {'Name': 'PLA Lynx Rapid-Fire Gun HJ-8H', 'HUDName': 'HJ-8H'})
    tu0 = rows('TurretUnitsJson', UnitId=rf)[0]; tw = rows('TurretWeaponsJson', TurretId=tu0['TurretId'])
    own_turret(rf, lambda x: {})
    new0 = rows('TurretUnitsJson', UnitId=rf)[0]['TurretId']
    # Same slot as the WZ-551's HJ-8E: mount 0, Order 2 / priority 2 (the Type 86 is Order 1 on mount 1); same ZSL-92 family stand-in.
    hjtw = [x for x in t['TurretWeaponsJson'].values() if x and x['WeaponId'] == HJ8E_VEH_WEAPON]
    ok(len(hjtw) == 1 and hjtw[0]['Order'] == 2, ('WZ-551 HJ-8E slot', [(x['TurretId'], x['Order']) for x in hjtw]))
    ok(len(tw) == 1 and 'autocannon' in W[tw[0]['WeaponId']]['HUDName'], ('Rapid-Fire Gun mount 0 = autocannon only', [W[x['WeaponId']]['HUDName'] for x in tw]))
    g.add('TurretWeaponsJson', hjtw[0], {'TurretId': new0, 'WeaponId': hj})
    wa0 = rows('WeaponAmmunitionsJson', UnitId=rf)[0]
    g.add('WeaponAmmunitionsJson', wa0, {'WeaponId': hj, 'AmmunitionId': HJ8H_ROUND, 'Order': 0, 'Quantity': 2})
    # SPAAG: no radar, gun ground + helicopters only, FB-10 -> QW-2 x4
    sp = uid['PLA Lynx 66 SPAAG']
    rad = [r for r in rows('UnitAbilitiesJson', UnitId=sp) if AB[r['AbilityId']].get('IsRadar')]
    ok(rad and all(not any(AB[r['AbilityId']].get(k) for k in ('IsAPS', 'IsSmoke', 'IsSprint', 'IsJammer', 'IsLaserDesignator', 'IsResupplyAbility')) for r in rad), ('SPAAG radar rows are radar only', [r['AbilityId'] for r in rad]))
    for r in rad: g.remove('UnitAbilitiesJson', r['Id'])
    fb = [x for tu in rows('TurretUnitsJson', UnitId=sp) for x in rows('TurretWeaponsJson', TurretId=tu['TurretId']) if 'FB-10' in W[x['WeaponId']]['HUDName']]
    ok(len({x['WeaponId'] for x in fb}) == 1, ('SPAAG one FB-10 launcher', [x['WeaponId'] for x in fb])); fbw = fb[0]['WeaponId']
    ok(W[QW2_WEAPON]['HUDName'] == 'QW-2' and A[QW2_ROUND]['HUDName'] == 'QW-2 ammunition', 'PGZ-04A QW-2 launcher and round')
    own_turret(sp, lambda x: {'WeaponId': QW2_WEAPON} if x['WeaponId'] == fbw else {})
    gun_rounds = {}
    for r in rows('WeaponAmmunitionsJson', UnitId=sp):
        if r['WeaponId'] == fbw:
            g.put('WeaponAmmunitionsJson', r['Id'], {'WeaponId': QW2_WEAPON, 'AmmunitionId': QW2_ROUND, 'Quantity': 4})
        else:
            a = r['AmmunitionId']
            if a not in gun_rounds:
                gun_rounds[a] = g.add('AmmunitionsJson', A[a], {'Name': f"PLA Lynx SPAAG {A[a].get('HUDName')}", 'LowAltRange': 0.0, 'HighAltRange': 0.0, 'TargetType': GROUND_HELI})
            g.put('WeaponAmmunitionsJson', r['Id'], {'AmmunitionId': gun_rounds[a]})
    qw = [r for r in rows('WeaponAmmunitionsJson', UnitId=sp) if r['WeaponId'] == QW2_WEAPON]
    ok(len(qw) == 1 and qw[0]['Quantity'] == 4 and not any('FB-10' in w for _, w in weapons(sp)), ('SPAAG QW-2 x4, no FB-10', weapons(sp)))
    ok(not any(AB[r['AbilityId']].get('IsRadar') for r in rows('UnitAbilitiesJson', UnitId=sp)), 'SPAAG no radar')
    # Laser: LY-1 laser on its own mount, ground 400 / heli 550 / no high, laser APS without radar
    lz = uid['PLA Lynx 6x6 Laser Weapon']
    ok(W[LY1_WEAPON]['HUDName'] == 'LY-1 laser' and A[LY1_ROUND]['HUDName'] == 'LY-1 laser pulse' and AB[LY1_ABILITY].get('IsAPS') and AB[LY1_ABILITY].get('IsRadar'), 'LY-1 rows')
    ok(not rows('TurretUnitsJson', UnitId=lz) and not rows('WeaponAmmunitionsJson', UnitId=lz), 'Lynx Laser had no weapon')
    pulse = g.add('AmmunitionsJson', A[LY1_ROUND], {'Name': 'PLA Lynx Laser pulse', 'GroundRange': 400.0, 'LowAltRange': 550.0, 'HighAltRange': 0.0, 'TargetType': GROUND_HELI})
    ly1u = 1275; ok(U[ly1u]['HUDName'] == 'LY-1', 'LY-1 unit')
    ltu = rows('TurretUnitsJson', UnitId=ly1u); ok(len(ltu) == 1, 'LY-1 one turret')
    mount = g.add('TurretsJson', t['TurretsJson'][ltu[0]['TurretId']], {'Name': 'PLA Lynx Laser mount'})
    for x in rows('TurretWeaponsJson', TurretId=ltu[0]['TurretId']): g.add('TurretWeaponsJson', x, {'TurretId': mount})
    g.add('TurretUnitsJson', ltu[0], {'UnitId': lz, 'TurretId': mount})
    for r in rows('WeaponAmmunitionsJson', UnitId=ly1u): g.add('WeaponAmmunitionsJson', r, {'UnitId': lz, 'AmmunitionId': pulse})
    # One default ability per unit (build guard): the LY-1's laser APS values go into the card's default ability row (the CS/VN3C one,
    # smoke-free), as vanilla combines APS with sprint/smoke in one row; an existing row with exactly those values is reused.
    APSK = [k for k in AB[LY1_ABILITY] if k.startswith('APS')] + ['IsAPS']
    sig = lambda r: {k: v for k, v in r.items() if k not in ('Id', 'Name')}
    defaults = [r for r in rows('UnitAbilitiesJson', UnitId=lz) if AB[r['AbilityId']].get('IsDefault')]
    ok(len(defaults) <= 1 and not any(AB[r['AbilityId']].get('IsRadar') or AB[r['AbilityId']].get('IsAPS') for r in rows('UnitAbilitiesJson', UnitId=lz)), ('Lynx Laser abilities before', [r['AbilityId'] for r in rows('UnitAbilitiesJson', UnitId=lz)]))
    if defaults:
        base = AB[defaults[0]['AbilityId']]; want = {**base, **{k: AB[LY1_ABILITY][k] for k in APSK}}
        same = [i for i, x in sorted(AB.items()) if x and sig(x) == sig(want)]
        apsid = same[0] if same else g.add('AbilitiesJson', base, {**{k: AB[LY1_ABILITY][k] for k in APSK}, 'Name': f"{base['Name']} + LY-1 laser APS"})
        g.put('UnitAbilitiesJson', defaults[0]['Id'], {'AbilityId': apsid})
    else:
        want = {k: v for k, v in AB[LY1_ABILITY].items()}
        for k in list(want):
            if k.startswith('Radar'): want[k] = 0.0 if isinstance(want[k], float) else 0
        want['IsRadar'] = False
        same = [i for i, x in sorted(AB.items()) if x and sig(x) == sig(want)]
        apsid = same[0] if same else g.add('AbilitiesJson', AB[LY1_ABILITY], {**{k: want[k] for k in want if k.startswith('Radar') or k == 'IsRadar'}, 'Name': 'PLA Lynx Laser APS'})
        g.add('UnitAbilitiesJson', rows('UnitAbilitiesJson', UnitId=ly1u)[0], {'UnitId': lz, 'AbilityId': apsid})
    ok(sum(1 for r in rows('UnitAbilitiesJson', UnitId=lz) if AB[r['AbilityId']].get('IsDefault')) <= 1, 'Lynx Laser one default ability')
    ok(not any(AB[r['AbilityId']].get('IsRadar') for r in rows('UnitAbilitiesJson', UnitId=lz)) and any(AB[r['AbilityId']].get('IsAPS') for r in rows('UnitAbilitiesJson', UnitId=lz)), 'Lynx Laser: laser APS, no radar')
    # every weapon of a changed card has ammunition
    for name in set(RENAME) - set(HIDE):
        u = uid[name]; am = {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=u)}
        ok(all(x['WeaponId'] in am for r in rows('TurretUnitsJson', UnitId=u) for x in rows('TurretWeaponsJson', TurretId=r['TurretId'])), (name, 'every weapon has ammunition'))
        out['changed'][name] = {'unit': u, 'hud': U[u]['HUDName'], 'cost': U[u]['Cost'], 'seats': U[u].get('InfantrySlots'), 'cat': U[u].get('CategoryType'),
                                'weapons': weapons(u), 'ammo': [(W[r['WeaponId']]['HUDName'], A[r['AmmunitionId']]['HUDName'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=u)],
                                'abilities': [AB[r['AbilityId']]['Name'] for r in rows('UnitAbilitiesJson', UnitId=u)]}
    out['laser_pulse'], out['laser_aps'], out['spaag_gun_rounds'], out['hj8h_weapon'] = pulse, apsid, gun_rounds, hj
    rec['lynx_rework_1124'] = out
    print('LYNX REWORK', out)

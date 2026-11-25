"""Lynx airborne family, stat cards (Osama 24 Nov 2026 16:0x PST, thread "blue dragons": "Start making stat cards for these. They have no
armor by the way. 10/10 all around. 8 HP. 90/40 speed (make them nimble if we can). And then give them weapons based on existing unit weapons
... They are all amphibious and airborne. No smoke."). The 11 cgmodel Lynx listings named from his screenshots (work/lynx-1124/
listings_tracker.json). Models are not bought yet: each card keeps its parent's body as a stand-in until FAModels draws the Lynx.
- Every card is a copy of a China unit that already carries the right weapon (turret, weapon points and ammunition come with it), or of a
  light body with the weapon set swapped in. Common: armour 10 KE / 10 HEAT on every face, 8 HP; road 90, off-road 40, turn rate 80 -> 120,
  acceleration 10 -> 15 ("nimble"); amphibious; air-droppable; no smoke (the parent's smoke ability is replaced by the same row without
  smoke, else dropped); CountryId 4 (China), base game (ContentMembership -1).
- Osama 16:0x: "Obviously all for airborne", "They can be loaded in the Z-8 helicopter": spec 17 PLAAF Air Force (the airborne spec). The two
  troop carriers are transports (no card of their own), offered to every spec-17 infantry card that already has transports, as the VN-3.
  Units.Weight 5000: a helicopter carries a vehicle while the weights fit its HeavyLiftWeight (OrderedUnit.TryAddCargo, docs/engine/
  cargo-capacity.md): Z-8L 16000 takes up to three, CH-47 12500 two, the Z-20 (4000) none.
- Prices and card counts are placeholders for Osama."""
AIRBORNE, CN, WEIGHT = 17, 4, 5000
TRANSPORTS = ('PLA Lynx CS/VP16B Carrier', 'PLA Lynx CS/VP16B Assault')
SMOKE = ('IsSmoke', 'SmokeAmmunitionId', 'SmokeAmmunitionQuantity', 'SmokeCooldown')
# Name: (HUDName, parent, cost, cards, CategoryType, InfantrySlots, weapons)
#   weapons None = keep the parent's; [] = no weapon; else [(weapon id, new weapon HUDName or None, [(ammunition id, quantity)])]
CARDS = {
    'PLA Lynx CS/VP16B Carrier': ('CS/VP16B Carrier', 1057, 20, 4, 2, 6, []),
    'PLA Lynx CS/VP16B Assault': ('CS/VP16B Assault', 1057, 30, 4, 2, 6, None),                  # QJZ-89 12.7 mm RWS
    'PLA Lynx CS/VP17 Rapid-Fire Gun': ('CS/VP17 Rapid-Fire Gun', 1079, 45, 4, 2, 4, None),     # 30 mm autocannon + Type 86 7.62 mm
    'PLA Lynx CS-SM8 81 mm Mortar': ('CS-SM8 81 mm Mortar', 926, 50, 4, 3, 0,
                                     [(285, '81 mm rapid-fire mortar', [(410, 80), (135, 24), (136, 25)])]),   # 2B9 82 mm (MT-LB Mortar)
    'PLA Lynx CS/VP17 120 mm Mortar': ('CS/VP17 120 mm Mortar', 926, 70, 4, 3, 0,
                                       [(286, '120 mm mortar', [(183, 60), (87, 15)])]),                          # 2B12 120 mm (MT-LB Mortar)
    'PLA Lynx 66 120 mm Mortar-Howitzer': ('Lynx 66 120 mm Mortar-Howitzer', 926, 80, 4, 3, 0, None),         # PLL-05 120 mm gun-mortar
    'PLA Lynx 66 107 mm MRL': ('Lynx 66 107 mm MRL', 963, 60, 4, 3, 0, [(2010159, '107 mm rockets', [(2010163, 12, '107 mm rockets ammunition')])]),
    'PLA Lynx 8x8 107 mm MRL': ('Lynx 8x8 107 mm MRL', 963, 110, 4, 3, 0, [(2010159, '107 mm rockets', [(2010163, 36, '107 mm rockets ammunition')])]),
    'PLA Lynx 66 SPAAG': ('Lynx 66 SPAAG', 920, 120, 4, 3, 0, None),                             # PGL-625: six-barrel 25 mm + FB-10
    'PLA Lynx CS/VP17 Command': ('CS/VP17 Command', 1057, 30, 4, 0, 0, []),
    'PLA Lynx CS/VP17 Swarm Launcher': ('CS/VP17 Swarm Launcher', 1295, 150, 4, 3, 0, 'CH901'),  # Type 100 CH-901 only (NLOS rounds)
}
# Per-weapon ammunition counts on cards that keep their parent's weapons (the Lynx 66 SPAAG carries 4 missiles, the PGL-625 8).
AMMO = {'PLA Lynx 66 SPAAG': {'FB-10': 4}}
PARENTS = {1057: 'CS/VN3C MG', 1079: 'ZSL-92', 926: 'PLL-05', 963: 'PHL-81', 920: 'PGL-625', 1295: 'Type 100 CSV'}


def apply(t, g, ok, rec):
    U, S, SA, AB, W = t['Units'], t['SpecializationsJson'], t['SpecializationAvailabilitiesJson'], t['AbilitiesJson'], t['WeaponsJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    sig = lambda r: {k: v for k, v in r.items() if k not in ('Id', 'Name')}
    def no_smoke(aid):
        """The parent's ability row without smoke: an existing row with exactly those values, else a new one; None if nothing is left."""
        r = dict(AB[aid])
        if not r.get('IsSmoke'): return aid
        for k in SMOKE: r[k] = False if k == 'IsSmoke' else 0
        if not any(r.get(k) for k in ('IsResupplyAbility', 'IsRadar', 'IsLaserDesignator', 'IsAPS', 'IsJammer', 'IsSprint')): return None
        same = [i for i, a in sorted(AB.items()) if a and sig(a) == sig(r)]
        return same[0] if same else g.add('AbilitiesJson', AB[aid], {**{k: r[k] for k in SMOKE}, 'Name': AB[aid]['Name'].replace('Smoke x1 ', '') + ' NoSmoke'})

    ok(S[AIRBORNE]['Name'] == 'PLA PLAAF Air Force' and S[AIRBORNE]['CountryId'] == CN, 'airborne spec 17')
    for pid, hud in PARENTS.items(): ok(U[pid]['HUDName'] == hud and U[pid]['CountryId'] == CN, ('parent', pid, U[pid]['HUDName']))
    ok(not any(rows('ModificationsJson', UnitId=p) for p in PARENTS), 'parents have no loadout options')
    ch901 = rec['zbd100']['ch901_round']
    tw901 = [x for x in rows('TurretWeaponsJson', TurretId=rows('TurretUnitsJson', UnitId=1295)[0]['TurretId']) if W[x['WeaponId']]['HUDName'] == 'CH-901']
    ok(len(tw901) == 1, 'Type 100 CH-901 weapon row')
    tpl_sa = next(r for r in sorted(SA.values(), key=lambda r: r['Id']) if r and r['SpecializationId'] == AIRBORNE)
    TA = t['TransportAvailabilitiesJson']
    tpl_ta = next(r for r in sorted(TA.values(), key=lambda r: r['Id']) if r)
    inf = [r for r in sorted(SA.values(), key=lambda r: r['Id']) if r and r['SpecializationId'] == AIRBORNE
           and any(x and x.get('SpecializationAvailabilityId') == r['Id'] for x in TA.values())]
    ok(len(inf) >= 8 and all(U[r['UnitId']].get('Type') == 2 for r in inf), ('airborne infantry cards with transports', len(inf)))
    res, rounds = {}, {}
    for name, (hud, parent, cost, n, cat, slots, weapons) in CARDS.items():
        ok(not any(u and name in (u.get('Name'), u.get('HUDName')) for u in U.values()), name + ' name free')
        d = dict(U[parent]); d.pop('Id')
        d.update({'Name': name, 'HUDName': hud, 'Cost': cost, 'OriginalCost': 0, 'CountryId': CN, 'DisplayInArmory': True, 'Description': None,
                  'OriginalName': None, 'CategoryType': cat, 'InfantrySlots': slots, 'ContentMembership': -1, 'Weight': WEIGHT})
        uid = g.put('Units', max(U) + 1, d)
        for r in rows('UnitArmorsJson', UnitId=parent):
            a = t['ArmorsJson'][r['ArmorId']]
            g.add('UnitArmorsJson', r, {'UnitId': uid, 'ArmorId': g.add('ArmorsJson', a, {'Name': f'{name} ArmorsJson', 'MaxHealthPoints': 8, **{
                f'{k}Armor{f}': 10 for k in ('Kin', 'Heat') for f in ('Front', 'Rear', 'Sides', 'Top')}})})
        for r in rows('UnitPropulsionsJson', UnitId=parent):
            g.add('UnitPropulsionsJson', r, {'UnitId': uid, 'MobilityId': g.add('MobilityJson', t['MobilityJson'][r['MobilityId']], {
                'Name': f'Wheels {name}', 'MaxSpeedRoad': 90.0, 'MaxCrossCountrySpeed': 40.0, 'TurnRate': 120.0, 'Acceleration': 15.0,
                'IsAmphibious': True, 'IsAirDroppable': True})})
        for r in rows('UnitAbilitiesJson', UnitId=parent):
            a = no_smoke(r['AbilityId'])
            if a is not None: g.add('UnitAbilitiesJson', r, {'UnitId': uid, 'AbilityId': a})
        for r in rows('SensorUnitsJson', UnitId=parent): g.add('SensorUnitsJson', r, {'UnitId': uid})
        tu = rows('TurretUnitsJson', UnitId=parent)
        if weapons is None:   # the parent's weapons as they are
            for r in tu: g.add('TurretUnitsJson', r, {'UnitId': uid})
            for r in rows('WeaponAmmunitionsJson', UnitId=parent):
                g.add('WeaponAmmunitionsJson', r, {'UnitId': uid, 'Quantity': AMMO.get(name, {}).get(W[r['WeaponId']]['HUDName'], r['Quantity'])})
        elif weapons:         # one new mount on the parent's first turret slot, weapons at Order 0..n-1
            if weapons == 'CH901':
                weapons = [(tw901[0]['WeaponId'], None, [(ch901, q['Quantity']) for q in rows('WeaponAmmunitionsJson', UnitId=1295) if q['WeaponId'] == tw901[0]['WeaponId']])]
            ok(len(tu) >= 1, (name, 'parent mount'))
            mount = g.add('TurretsJson', t['TurretsJson'][tu[0]['TurretId']], {'Name': f'{name} mount 0'})
            tw0 = rows('TurretWeaponsJson', TurretId=tu[0]['TurretId'])[0]
            wa0 = rows('WeaponAmmunitionsJson', UnitId=parent)[0]
            for k, (wid, wname, ammo) in enumerate(weapons):
                if wname: wid = g.add('WeaponsJson', W[wid], {'Name': f'{name} {wname}', 'HUDName': wname})
                g.add('TurretWeaponsJson', tw0, {'TurretId': mount, 'WeaponId': wid, 'Order': k, 'WeaponPriority': k})
                for o, (aid, q, *rn) in enumerate(ammo):
                    if rn:   # own round, renamed (107 mm: the PHL-81 122 mm round under its own name; stats unchanged, to tune)
                        aid = rounds.setdefault((aid, rn[0]), None) or rounds.__setitem__((aid, rn[0]), g.add('AmmunitionsJson', t['AmmunitionsJson'][aid], {'Name': f'PLA Lynx {rn[0]}', 'HUDName': rn[0]})) or rounds[(aid, rn[0])]
                    g.add('WeaponAmmunitionsJson', wa0, {'UnitId': uid, 'WeaponId': wid, 'AmmunitionId': aid, 'Order': o, 'Quantity': q})
            g.add('TurretUnitsJson', tu[0], {'UnitId': uid, 'TurretId': mount})
        if name in TRANSPORTS:
            for r in inf: g.add('TransportAvailabilitiesJson', tpl_ta, {'SpecializationAvailabilityId': r['Id'], 'UnitId': uid})
            ok(len(rows('TransportAvailabilitiesJson', UnitId=uid)) == len(inf), (name, 'offered to every airborne infantry card'))
        else:
            g.add('SpecializationAvailabilitiesJson', tpl_sa, {'UnitId': uid, 'SpecializationId': AIRBORNE, 'MaxAvailabilityXp0': n})
        abil = [r['AbilityId'] for r in rows('UnitAbilitiesJson', UnitId=uid)]
        ok(not any(AB[a].get('IsSmoke') for a in abil), (name, 'no smoke'))
        ok(sum(1 for a in abil if AB[a].get('IsDefault')) <= 1, (name, 'one default ability'))
        arm = t['ArmorsJson'][rows('UnitArmorsJson', UnitId=uid)[0]['ArmorId']]; mob = t['MobilityJson'][rows('UnitPropulsionsJson', UnitId=uid)[0]['MobilityId']]
        ok(arm['MaxHealthPoints'] == 8 and arm['KinArmorFront'] == arm['HeatArmorTop'] == 10 and mob['IsAmphibious'] and mob['IsAirDroppable']
           and (mob['MaxSpeedRoad'], mob['MaxCrossCountrySpeed']) == (90.0, 40.0), (name, 'common stats'))
        loadout = [(x['Order'], W[x['WeaponId']]['HUDName']) for r in rows('TurretUnitsJson', UnitId=uid) for x in rows('TurretWeaponsJson', TurretId=r['TurretId'])]
        ammo = [(W[r['WeaponId']]['HUDName'], t['AmmunitionsJson'][r['AmmunitionId']]['HUDName'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=uid)]
        ok(bool(loadout) == (weapons != []) and all(any(a[0] == w for a in ammo) for _, w in loadout), (name, 'every weapon has ammunition', loadout, ammo))
        res[name] = {'transport_for': len(inf) if name in TRANSPORTS else 0, 'unit': uid, 'hud': hud, 'parent': f'{PARENTS[parent]} ({parent})', 'cost': cost, 'cards': n, 'abilities': abil, 'weapons': loadout, 'ammo': ammo}
    rec['lynx_cards_1124'] = res
    print('LYNX', res)

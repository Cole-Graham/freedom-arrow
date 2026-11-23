"""Blue Dragon tank tab (Osama, thread 1573418243715113213, 21 Nov 2026 01:1x PST: "lets build it all make sure their optics values are similar
to the US values. I think KSTAM needs to be SA"). Called from batch_0_9_5b.py; all cards stay HIDDEN (DisplayInArmory False, no deck card)
until a spec is chosen. Stats: War Thunder converted to FA scale (work/blue-dragon-wt-20261120/REPORT.md) plus the thread's decisions:
Japan 4-5 s reload (Type 10, Type 90, Type 74 STB-2); Korea 5-6 s (K2) / 6-7 s (K1A1, hand-loaded like M1A1 HC); 105 mm guns 5-6 s.
Optics = the matching US tank: SEP v3 Good, SEP v2/FEP/Stryker MGS Medium Plus, M1A1 HC/M60A1 Medium. Prices are placeholders.
No models yet: each card shows its parent's model (TUA Abrams, Russian T-80U, Stryker MGS)."""

GOOD, MEDIUM_PLUS, MEDIUM = 1, 23, 2
SMOKE_DEFAULT = 2000197  # 'Smoke x1 NoModel Default' (existing row, Lateralus row-reuse rule)


def apply(t, g, ok, rec):
    U, A, W, TJ, AR, MO, AB = (t[k] for k in ('Units', 'AmmunitionsJson', 'WeaponsJson', 'TurretsJson', 'ArmorsJson', 'MobilityJson', 'AbilitiesJson'))

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    def one(tab, **kw):
        r = rows(tab, **kw); ok(len(r) == 1, (tab, kw, len(r))); return r[0]

    out = {}
    # ---- parents and templates, checked against 0.9.3 values
    ok(U[2]['HUDName'] == 'M1A2 SEP v2 TUA' and not rows('ModificationsJson', UnitId=2), 'TUA parent, no options')
    ok(U[239]['HUDName'] == 'T-80U' and U[239]['CountryId'] == 1, 'T-80U parent (Russia)')
    ok(U[24]['HUDName'] == 'Stryker MGS', 'Stryker MGS parent')
    ok([r['TurretId'] for r in rows('TurretUnitsJson', UnitId=2)] == [436, 440, 441], 'TUA turrets')
    ok((A[254]['HUDName'].strip(), A[256]['HUDName'].strip(), A[253]['HUDName'].strip(), A[23]['HUDName'].strip(), A[171]['HUDName'].strip())
       == ('M829A3 APFSDS', 'M829A1 APFSDS', 'M830 HEAT', 'M900A1 APFSDS', 'M393A1 HESH'), 'round templates')
    ok((A[2000161]['HUDName'], A[2000161]['IsTopArmorArmorAttack'], A[2000159]['HUDName'], A[2000159]['Seeker']) == ('Sokol-V', True, 'Invar-M 9M119M', 100), 'GLATGM templates')
    ok(AB[SMOKE_DEFAULT]['IsDefault'] and AB[SMOKE_DEFAULT]['IsSmoke'], 'default smoke ability')
    ok((W[266]['MagazineReloadTimeMin'], W[266]['MagazineReloadTimeMax'], W[11]['MagazineReloadTimeMin'], W[11]['MagazineReloadTimeMax']) == (6.0, 7.0, 5.0, 6.0), 'M256 6-7 s, M68 5-6 s')

    def rnd(src, name, **kw):
        return g.add('AmmunitionsJson', A[src], {'Name': f'Round {name} BlueDragon', 'HUDName': name, **kw})

    # ---- rounds
    k279 = rnd(254, 'K279 APFSDS', PenetrationAtMinRange=525.0, PenetrationAtGroundRange=475.0)
    k276 = rnd(256, 'K276 APFSDS', PenetrationAtMinRange=500.0, PenetrationAtGroundRange=450.0)
    k280 = rnd(253, 'K280 HEAT-MP', GroundRange=700.0)
    k277 = rnd(253, 'K277 HEAT-MP')
    k270 = rnd(23, 'K270 APFSDS', PenetrationAtMinRange=350.0, PenetrationAtGroundRange=300.0)
    km456 = rnd(253, 'KM456A2 HEAT', PenetrationAtMinRange=500.0, PenetrationAtGroundRange=500.0, GroundRange=600.0)
    t93 = rnd(23, 'Type 93 APFSDS', PenetrationAtMinRange=300.0, PenetrationAtGroundRange=250.0)
    t91 = rnd(253, 'Type 91 HEAT', PenetrationAtMinRange=500.0, PenetrationAtGroundRange=500.0, GroundRange=600.0)
    t75 = rnd(171, 'Type 75 HESH')
    # KSTAM: Sokol-V (gun-launched top attack, already in the game) with Invar-M's semi-active guidance (seeker 100, 800 m seeker reach,
    # 30 deg cone, aim 1-2 s) and Javelin's top-attack warhead (140 vs top armour, crit x1). Range 800 = the other GLATGMs.
    sa = {k: A[2000159][k] for k in ('Seeker', 'MaxSeekerDistance', 'SeekerAngle', 'RotationSpeed', 'AimTimeMinOverride', 'AimTimeMaxOverride')}
    kstam = g.add('AmmunitionsJson', A[2000161], {'Name': 'Missile GLAT KSTAM BlueDragon', 'HUDName': 'KSTAM', 'HUDIcon': A[2000174]['HUDIcon'],
        'PenetrationAtMinRange': 140.0, 'PenetrationAtGroundRange': 140.0, 'CriticMultiplier': 1.0, 'GroundRange': 800.0, 'SupplyCost': 75.0, **sa})
    ok(A[kstam]['IsTopArmorArmorAttack'] and A[kstam]['Seeker'] == 100 and A[kstam]['GroundRange'] == 800.0 and A[kstam]['PenetrationAtMinRange'] == 140.0, 'KSTAM: SA top attack 800')

    # ---- guns
    k2gun = g.add('WeaponsJson', W[266], {'Name': 'MainGun 120 K2 CN08 L55 autoloader', 'HUDName': '120mm CN08', 'AutoLoaded': True,
                                         'MagazineReloadTimeMin': 5.0, 'MagazineReloadTimeMax': 6.0})
    stbgun = g.add('WeaponsJson', W[11], {'Name': 'MainGun 105 Type 74 STB-2 loading aid', 'HUDName': '105mm L7', 'MagazineReloadTimeMin': 4.0, 'MagazineReloadTimeMax': 5.0})

    def card(name, parent, cost, *, sensor, armour, mob, turrets, ammo, mg_rows, extra_unit=None):
        """turrets: list of (src_turret, weapon_swap {old:new}, clone?) in link order; ammo: list of (weapon, round, qty, order)."""
        ok(not any(u and (u.get('Name') == name or u.get('HUDName') == name) for u in U.values()), name + ' name free')
        d = dict(U[parent]); d.pop('Id')
        d.update({'Name': name, 'HUDName': name, 'Cost': cost, 'OriginalCost': 0, 'Description': None, 'OriginalName': None, 'DisplayInArmory': False, **(extra_unit or {})})
        uid = g.put('Units', max(U) + 1, d)
        g.add('SensorUnitsJson', {'UnitId': uid, 'SensorId': sensor})
        g.add('UnitAbilitiesJson', {'UnitId': uid, 'AbilityId': SMOKE_DEFAULT})
        src_arm, vals = armour
        arm = g.add('ArmorsJson', AR[src_arm], {'Name': f'Armor {name} BlueDragon', 'IsDefault': True, **vals})
        g.add('UnitArmorsJson', {'UnitId': uid, 'ArmorId': arm})
        src_mob, mvals = mob
        mo = g.add('MobilityJson', MO[src_mob], {'Name': f'Mobility {name} BlueDragon', **mvals})
        g.add('UnitPropulsionsJson', {'UnitId': uid, 'MobilityId': mo})
        tmap = {}
        for order, (src, swap, clone, default) in enumerate(turrets):
            if clone:
                parent_t = TJ[src].get('ParentTurretId')
                new = g.add('TurretsJson', TJ[src], {'IsDefault': default, 'ParentTurretId': tmap.get(parent_t, parent_t)})
                for r in rows('TurretWeaponsJson', TurretId=src):
                    g.add('TurretWeaponsJson', r, {'TurretId': new, 'WeaponId': swap.get(r['WeaponId'], r['WeaponId'])})
                tmap[src] = new
            else:
                tmap[src] = src
        for src, *_ in turrets:
            link = [r for r in t['TurretUnitsJson'].values() if r and r['TurretId'] == src and r['UnitId'] == parent]
            ok(len(link) == 1, (name, 'parent turret link', src))
            g.add('TurretUnitsJson', link[0], {'UnitId': uid, 'TurretId': tmap[src]})
        for w, a, q, o in ammo + mg_rows:
            g.add('WeaponAmmunitionsJson', {'UnitId': uid, 'WeaponId': w, 'AmmunitionId': a, 'Quantity': q, 'Order': o})
        # every weapon on the card's turrets has ammunition, and no ammunition row points at a weapon the card lacks
        weps = {r['WeaponId'] for nt in tmap.values() for r in rows('TurretWeaponsJson', TurretId=nt)}
        ok(weps == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=uid)}, (name, 'weapons == ammo weapons'))
        a_ = AR[arm]
        out[name] = {'unit': uid, 'parent': U[parent]['HUDName'], 'cost': cost, 'sensor': sensor, 'turrets': list(tmap.values()),
                     'KE': [a_['KinArmorFront'], a_['KinArmorSides'], a_['KinArmorRear'], a_['KinArmorTop']],
                     'HEAT': [a_['HeatArmorFront'], a_['HeatArmorSides'], a_['HeatArmorRear'], a_['HeatArmorTop']], 'HP': a_['MaxHealthPoints'],
                     'road_xc_rev': [MO[mo]['MaxSpeedRoad'], MO[mo]['MaxCrossCountrySpeed'], MO[mo]['MaxSpeedReverse']],
                     'rounds': [(A[a]['HUDName'], A[a]['PenetrationAtMinRange'], A[a]['PenetrationAtGroundRange'], q,
                                 [W[w]['MagazineReloadTimeMin'], W[w]['MagazineReloadTimeMax']]) for w, a, q, o in ammo]}
        return uid

    tua_mg = [(18, 19, 200, 0), (27, 27, 1140, 0)]
    kv = lambda f, s, r, tp, hf, hs, hr, ht, hp=14: {'KinArmorFront': f, 'KinArmorSides': s, 'KinArmorRear': r, 'KinArmorTop': tp,
                                                      'HeatArmorFront': hf, 'HeatArmorSides': hs, 'HeatArmorRear': hr, 'HeatArmorTop': ht, 'MaxHealthPoints': hp}
    tua_turrets = lambda gun: [(436, {266: gun}, True, True), (440, {}, True, False), (441, {}, True, False)]

    card('K2 Black Panther', 2, 255, sensor=GOOD, armour=(2000397, kv(850, 120, 100, 80, 1100, 200, 100, 100)), mob=(1, {}),
         turrets=tua_turrets(k2gun), ammo=[(k2gun, k279, 16, 0), (k2gun, k280, 12, 1), (k2gun, kstam, 4, 2)], mg_rows=tua_mg)
    card('K1A1', 2, 155, sensor=MEDIUM_PLUS, armour=(2000397, kv(650, 120, 100, 60, 750, 200, 100, 100)),
         mob=(1, {'MaxSpeedRoad': 65.0, 'MaxCrossCountrySpeed': 50.0}),
         turrets=[(436, {}, False, True), (440, {}, False, False), (441, {}, False, False)], ammo=[(266, k276, 16, 0), (266, k277, 24, 1)], mg_rows=tua_mg)
    card('K1', 2, 95, sensor=MEDIUM, armour=(2000397, kv(500, 120, 100, 60, 650, 200, 100, 100)), mob=(1, {'MaxSpeedRoad': 65.0, 'MaxCrossCountrySpeed': 50.0}),
         turrets=tua_turrets(11), ammo=[(11, k270, 20, 0), (11, km456, 20, 1)], mg_rows=tua_mg)
    # M48A5K (Osama 21 Nov 01:2x: "we have the M48 also for Korea ... build this out for our tank tab"; model cgmodel 896549, not bought).
    # M60A1 base configuration (turret 12 + M85 cupola 110, M68 5-6 s, M60A1 tracks 50/45/15) without its options; thinner cast armour, no ERA.
    ok(U[14]['HUDName'] == 'M60A1' and [r['TurretId'] for r in rows('TurretUnitsJson', UnitId=14)] == [12, 110] and TJ[12]['IsDefault'], 'M60A1 parent turrets')
    card('M48A5K', 14, 50, sensor=MEDIUM, armour=(2000455, kv(250, 100, 60, 60, 300, 150, 60, 60)), mob=(9, {}),
         turrets=[(12, {}, False, True), (110, {}, False, False)], ammo=[(11, k270, 20, 0), (11, km456, 20, 1)], mg_rows=[(83, 19, 120, 0), (27, 27, 800, 0)])
    card('Type 74 STB-2', 2, 65, sensor=MEDIUM, armour=(2000397, kv(250, 100, 60, 60, 400, 250, 60, 80)), mob=(9, {}),
         turrets=tua_turrets(stbgun), ammo=[(stbgun, t93, 20, 0), (stbgun, t91, 20, 1)], mg_rows=tua_mg)
    # T-80U (ROK): South Korea received T-80U/UK from Russia in the 1990s. Russian T-80U obr. 90 configuration without options, US side.
    t80 = [(419, {}, True, True), (423, {}, True, False)]
    t80_ammo = [(r['WeaponId'], r['AmmunitionId'], r['Quantity'], r['Order']) for r in rows('WeaponAmmunitionsJson', UnitId=239) if r['WeaponId'] in (335, 7, 97)]
    ok(sorted((A[a]['HUDName'].strip(), q) for w, a, q, o in t80_ammo) == sorted([('125mm AP Vant', 14), ('125mm HE', 22), ('Invar-M 9M119M', 3), ('125mm HEAT', 6),
                                                                                   ('7.62x54mm', 400), ('12.7x108mm', 60)]), 'T-80U obr. 90 ammunition')
    card('T-80U (ROK)', 239, 135, sensor=MEDIUM_PLUS, armour=(2000475, {}), mob=(107, {}), turrets=t80,
         ammo=[x for x in t80_ammo if x[0] == 335], mg_rows=[x for x in t80_ammo if x[0] != 335], extra_unit={'CountryId': 2})
    card('Type 16 MCV', 24, 75, sensor=MEDIUM_PLUS, armour=(2000016, {}), mob=(12, {}), turrets=[(30, {}, False, True), (108, {}, False, False)],
         ammo=[(24, t93, 12, 0), (24, t91, 8, 1), (24, t75, 8, 2)], mg_rows=[(18, 19, 200, 0), (27, 27, 400, 0)])

    # ---- Type 10 / Type 90 (hidden since 0.9.3): optics to the US level (were Very Good, the TUA's)
    for nm, s in (('Type 10', GOOD), ('Type 90', MEDIUM_PLUS)):
        u = one('Units', Name=nm); su = rows('SensorUnitsJson', UnitId=u['Id']); ok(len(su) == 1 and su[0]['SensorId'] == 3, nm + ' Very Good optics before')
        g.put('SensorUnitsJson', su[0]['Id'], {'SensorId': s}); out[nm] = {'unit': u['Id'], 'sensor': [3, s]}
    ok(all(not U[v['unit']]['DisplayInArmory'] for v in out.values()) and not any(r and r['UnitId'] in {v['unit'] for v in out.values()} for r in t['SpecializationAvailabilitiesJson'].values()),
       'all Blue Dragon cards hidden, no deck cards (add_spec shows them in spec 23)')
    rec['blue_dragon_tank_tab'] = out


# ---- Blue Dragon spec (Osama 21 Nov 2026 14:0x PST: "we can add the blue dragons spec in the next build but it needs to have (testing preview)
# next to it with the units"; 14:1x "WAPC won't make it since its just a armored spec"). US spec 23, a copy of Armored Brigade (4): same slots and
# points. Cards = the hidden Blue Dragon tank tab, now shown. Icon FA_US_BLUE_DRAGON (runtime-qa/icons, seeded by ChinaUi like the China icons).
SPEC = 23
CARDS = {'K2 Black Panther': 2, 'Type 10': 2, 'K1A1': 3, 'Type 90': 3, 'T-80U (ROK)': 2, 'K1': 4, 'Type 74 STB-2': 4, 'Type 16 MCV': 3, 'M48A5K': 4}


def add_spec(t, g, ok, rec):
    U, S, SA = t['Units'], t['SpecializationsJson'], t['SpecializationAvailabilitiesJson']
    ok(SPEC not in S and S[4]['Name'] == 'Armored Brigade' and S[4]['CountryId'] == 2, 'spec 23 free; Armored Brigade template')
    g.put('SpecializationsJson', SPEC, {**{k: v for k, v in S[4].items() if k != 'Id'}, 'Name': 'US Blue Dragon',
        'UIName': 'Blue Dragon (Testing Preview)',
        'UIDescription': 'TESTING PREVIEW. Korean and Japanese armour fighting alongside the US. Models are stand-ins and stats and prices '
                         'will change. Japanese tanks reload faster; Korean tanks hit harder.',
        'Icon': 'FA_US_BLUE_DRAGON', 'ShowInHangar': True, 'ContentMembership': -1})
    tpl = next(r for r in SA.values() if r and r['UnitId'] == 2 and r['SpecializationId'] == 4)
    out = {}
    for name, n in CARDS.items():
        u = [x for x in U.values() if x and x.get('Name') == name]; ok(len(u) == 1 and u[0]['CountryId'] == 2 and not u[0]['DisplayInArmory'], (name, 'hidden US card'))
        uid = u[0]['Id']
        ok(not any(r and r['UnitId'] == uid for r in SA.values()), (name, 'no deck card yet'))
        g.add('SpecializationAvailabilitiesJson', tpl, {'UnitId': uid, 'SpecializationId': SPEC, 'MaxAvailabilityXp0': n})
        g.put('Units', uid, {'DisplayInArmory': True})
        out[name] = {'unit': uid, 'cards': n, 'cost': U[uid]['Cost']}
    ok(sorted(r['UnitId'] for r in SA.values() if r and r['SpecializationId'] == SPEC) == sorted(v['unit'] for v in out.values()), 'spec 23 = the 9 Blue Dragon cards')
    rec['blue_dragon_spec'] = {'spec': SPEC, 'name': S[SPEC]['UIName'], 'icon': S[SPEC]['Icon'], 'template': 'Armored Brigade (4)', 'cards': out}

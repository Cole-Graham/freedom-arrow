"""China balance patch for 0.9.4 (Osama 21 Nov 2026 18:2x PST, thread 1567745029781454889, Doc "China changes 9.4"
1uhNb7jt0RmhXCnNYMXUrVSoZHo05R1eOnTTv_vRxEX4: "I have a list of new changes for you", "Balance patch"). Called from apply_0_9_4_dev1.py.
Readings used (tell Osama): "remove the rifles" = drop the plain riflemen until the squad has the stated size (the crew weapons stay);
"1400 optics (armory stat, medium +)" = vanilla sensor row 23 Medium Plus (the Stryker MGS row); infantry armour 8 keeps 5 HP per man;
PHL-16 "300mm loadout ... be 300 points" = base 350 -> 300 with the 370 mm (+50) and Fire Dragon (+80) loadouts priced so their totals stay 350/380;
"blast radius 150m" = card metres (raw x2), so HealthAOERadius 82.5 -> 75. HJ-10 = 140 points (Osama 18:3x: "Meant to say HJ-10 120 points", "Sorry 140 points")."""


def apply(t, g, ok, rec):
    U, SM, SW, WA, W, A, AR, UA, SU, O, SA, AB, UAB, TU, UP, MO = (t[k] for k in (
        'Units', 'SquadMembersJson', 'SquadWeaponsJson', 'WeaponAmmunitionsJson', 'WeaponsJson', 'AmmunitionsJson', 'ArmorsJson',
        'UnitArmorsJson', 'SensorUnitsJson', 'OptionsJson', 'SpecializationAvailabilitiesJson', 'AbilitiesJson', 'UnitAbilitiesJson',
        'TurretUnitsJson', 'UnitPropulsionsJson', 'MobilityJson'))
    out = {}
    hud = lambda u: (U[u].get('HUDName') or '').strip()
    men = lambda u: sorted([m for m in SM.values() if m and m.get('UnitId') == u], key=lambda m: m['Id'])
    wn = lambda i: (W.get(i) or {}).get('HUDName', '') if i else ''
    users = lambda tab, f, v: {r['UnitId'] for r in t[tab].values() if r and r.get(f) == v}
    one = lambda tab, **kw: [r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())]

    def cost(u, name, old, new):
        ok(hud(u).startswith(name) and U[u]['Cost'] == old, (u, name, 'cost', U[u]['Cost'], old))
        g.put('Units', u, {'Cost': new}); out.setdefault(name, {})['cost'] = [old, new]
        # loadout swap rows cost base + option (audit_swap_prices.py), so they move with the base price
        for o in [o for o in O.values() if o and o.get('ReplaceUnitId') and t['ModificationsJson'].get(o.get('ModificationId'), {}).get('UnitId') == u]:
            r = o['ReplaceUnitId']
            if r != u:
                ok(U[r]['Cost'] == old + (o.get('Cost') or 0), (name, 'swap row', r, U[r]['Cost'], old, o.get('Cost')))
                g.put('Units', r, {'Cost': new + (o.get('Cost') or 0)}); out[name].setdefault('swap_rows', {})[r] = U[r]['Cost']

    def drop_men(u, pred, n, why):
        ms = [m for m in men(u) if pred(m)]
        ok(len(ms) >= n, (u, why, len(ms)))
        for m in ms[-n:]: g.remove('SquadMembersJson', m['Id'])
        out.setdefault(hud(u), {})['men'] = len(men(u))

    def unused_weapon_rows(u):
        carried = {m.get(k) for m in men(u) for k in ('PrimaryWeaponId', 'SpecialWeaponId')}
        for tab in ('SquadWeaponsJson', 'WeaponAmmunitionsJson'):
            for r in [r for r in t[tab].values() if r and r.get('UnitId') == u and r['WeaponId'] not in carried]: g.remove(tab, r['Id'])

    def own_armour(u, av=None, hp=None):
        r = one('UnitArmorsJson', UnitId=u); ok(len(r) == 1, (u, 'one armour row')); a = r[0]['ArmorId']
        ok(users('UnitArmorsJson', 'ArmorId', a) == {u}, (u, 'own armour row', a))
        f = {}
        if av is not None: f['ArmorValue'] = av
        if hp is not None: f['MaxHealthPoints'] = hp
        g.put('ArmorsJson', a, f); return a

    def link_armour(u, a):
        r = one('UnitArmorsJson', UnitId=u); ok(len(r) == 1, (u, 'one armour row')); g.put('UnitArmorsJson', r[0]['Id'], {'ArmorId': a})

    def medium_plus(u):
        r = one('SensorUnitsJson', UnitId=u); ok(len(r) == 1, (u, 'one sensor')); g.put('SensorUnitsJson', r[0]['Id'], {'SensorId': 23})
    ok(t['SensorsJson'][23]['Name'] == 'Medium Plus Optics' and one('SensorUnitsJson', UnitId=24)[0]['SensorId'] == 23, 'row 23 = Medium Plus = Stryker MGS')

    def reload(w, old, new):
        ok((W[w]['MagazineReloadTimeMin'], W[w]['MagazineReloadTimeMax']) == old, (w, wn(w), 'reload', old))
        g.put('WeaponsJson', w, {'MagazineReloadTimeMin': new[0], 'MagazineReloadTimeMax': new[1]})

    def opt_cost(o, label, old, new):
        ok(O[o]['Cost'] == old and label in (O[o].get('UIName') or ''), (o, label, O[o]['Cost']))
        g.put('OptionsJson', o, {'Cost': new})

    def swap_weapon(u, old_w, new_w, new_a, qty):
        # every member with primary old_w gets new_w; the unit's SW/WA rows for old_w become new_w
        for m in men(u):
            if m.get('PrimaryWeaponId') == old_w: g.put('SquadMembersJson', m['Id'], {'PrimaryWeaponId': new_w})
        have = one('SquadWeaponsJson', UnitId=u, WeaponId=new_w)
        for r in one('SquadWeaponsJson', UnitId=u, WeaponId=old_w):
            if have: g.remove('SquadWeaponsJson', r['Id'])
            else: g.put('SquadWeaponsJson', r['Id'], {'WeaponId': new_w})
        hw = one('WeaponAmmunitionsJson', UnitId=u, WeaponId=new_w)
        for r in one('WeaponAmmunitionsJson', UnitId=u, WeaponId=old_w):
            if hw: g.remove('WeaponAmmunitionsJson', r['Id'])
            else: g.put('WeaponAmmunitionsJson', r['Id'], {'WeaponId': new_w, 'AmmunitionId': new_a, 'Quantity': qty})

    QBZ191, QBZ192, QBZ192A, QLU11, QBU10, PF89, FLASH = 2003998, 2013087, 2013088, 2004002, 2012054, 2011887, 590
    ok(wn(QBZ192) == 'QBZ-192' and A[QBZ192A]['HUDName'] == 'QBZ-192 ammunition' and wn(PF89) == 'PF-89' and W[PF89]['Type'] == 63 and wn(FLASH) == 'Flashbang', 'weapon ids')

    # --- infantry
    # Chinese Airborne (1136): one QJY-201 gunner out (9 -> 8 men), 70 -> 80; armour Shock 9Men (shared with US) -> vanilla Shock 8Men 291 (AV 8, 40 HP)
    drop_men(1136, lambda m: wn(m.get('PrimaryWeaponId')) == 'QJY-201', 1, 'QJY-201 gunners'); link_armour(1136, 291); cost(1136, 'Airborne', 70, 80)
    ok(AR[291]['ArmorValue'] == 8 and AR[291]['MaxHealthPoints'] == 40 and len(men(1136)) == 8, 'Airborne 8 men, Shock 8Men')
    # QLU-11 Team (1140): one QLU-11 gunner out (4 -> 3); armour 4Men (80) -> 3Men (79)
    drop_men(1140, lambda m: m.get('PrimaryWeaponId') == QLU11, 1, 'QLU-11 gunners'); link_armour(1140, 79)
    ok(len(men(1140)) == 3 and sum(m.get('PrimaryWeaponId') == QLU11 for m in men(1140)) == 1 and AR[79]['MaxHealthPoints'] == 15, 'QLU-11 Team 3 men, 1 QLU-11')
    # QJZ-89 Team (1157, mechanized): 2 plain QBZ-191 riflemen out (4 -> 2); own armour 20 -> 10 HP
    drop_men(1157, lambda m: m.get('PrimaryWeaponId') == QBZ191 and not m.get('SpecialWeaponId'), 2, 'QJZ-89 riflemen'); own_armour(1157, hp=10)
    ok(len(men(1157)) == 2 and all(wn(m.get('SpecialWeaponId')) == 'QJZ-89' for m in men(1157)), 'QJZ-89 Team 2 gunners')
    # Rocket Conscripts PF-98 Team (1172): 5 men (riflemen out), armour 8, Medium Plus optics, 55 -> 45; DZD98A HE 25% ignore cover
    def conscripts(u, name, size, c=None):
        rf = lambda m: wn(m.get('PrimaryWeaponId')) == 'QBZ-95' and not m.get('SpecialWeaponId')
        drop_men(u, rf, len(men(u)) - size, name + ' riflemen'); own_armour(u, av=8, hp=5 * size); medium_plus(u)
        ok(len(men(u)) == size, (name, size))
        if c: cost(u, name, *c)
    conscripts(1172, 'PF-98 Team', 5, (55, 45))
    ok(A[2016261]['HUDName'] == 'DZD98A HE' and users('WeaponAmmunitionsJson', 'AmmunitionId', 2016261) == {1172}, 'DZD98A only on PF-98 Team')
    g.put('AmmunitionsJson', 2016261, {'IgnoreCover': 0.25})
    conscripts(1170, 'QJZ-89 Team', 6); conscripts(1171, 'QLZ-87 Team', 6)
    # Whistling Arrows (1184): QBU-10 marksman out (4 -> 3); own armour 20 -> 15 HP
    drop_men(1184, lambda m: m.get('PrimaryWeaponId') == QBU10, 1, 'QBU-10'); unused_weapon_rows(1184); own_armour(1184, hp=15)
    ok(len(men(1184)) == 3 and not one('SquadWeaponsJson', UnitId=1184, WeaponId=QBU10), 'Whistling Arrows 3 men, no QBU-10')
    # Beijing Swords (1187): 70 -> 55, laser (Sprint30 Smoke x4 -> existing 'Sprint30 Smoke x4 Laser' 2000611), one flashbang (vanilla 590 pattern)
    cost(1187, 'Beijing Swords', 70, 55)
    r = one('UnitAbilitiesJson', UnitId=1187); ok(len(r) == 1 and r[0]['AbilityId'] == 81, 'Beijing Swords ability 81')
    ok(AB[2000611]['IsLaserDesignator'] and all(AB[2000611].get(k) == AB[81].get(k) for k in ('IsInfantrySprint', 'SprintDuration', 'SprintCooldown', 'IsSmoke')), '2000611 = 81 + laser')
    g.put('UnitAbilitiesJson', r[0]['Id'], {'AbilityId': 2000611})
    fm = [m for m in men(1187) if not m.get('SpecialWeaponId')]; ok(fm, 'Beijing Swords member free for a flashbang')
    g.put('SquadMembersJson', fm[0]['Id'], {'SpecialWeaponId': FLASH})
    tw = one('SquadWeaponsJson', UnitId=117, WeaponId=FLASH)[0]; ta = one('WeaponAmmunitionsJson', UnitId=117, WeaponId=FLASH)[0]
    g.add('SquadWeaponsJson', tw, {'UnitId': 1187}); g.add('WeaponAmmunitionsJson', ta, {'UnitId': 1187})
    # Mountain Leopards (1186): armour 10 -> 8 (own row)
    own_armour(1186, av=8)
    # Marine Recon (1224): 6 men, 3 QBZ-192 (the QBZ-191 rifleman -> QBZ-192, +2), PF-89 disposable 1 per carrier on 4 carriers, 45 -> 60, Shock 6Men
    ms = men(1224); ok(len(ms) == 4 and sum(m.get('PrimaryWeaponId') == QBZ191 for m in ms) == 1, 'Marine Recon 4 men, 1 QBZ-191')
    rif = [m for m in ms if m.get('PrimaryWeaponId') == QBZ191][0]
    for _ in range(2): g.add('SquadMembersJson', rif, {})
    swap_weapon(1224, QBZ191, QBZ192, QBZ192A, 160)
    for m in men(1224):
        if wn(m.get('PrimaryWeaponId')) in ('QBZ-192', 'QBU-191'): g.put('SquadMembersJson', m['Id'], {'SpecialWeaponId': PF89})
    pf = one('WeaponAmmunitionsJson', UnitId=1224, WeaponId=PF89); ok(len(pf) == 1, 'PF-89 ammo row'); g.put('WeaponAmmunitionsJson', pf[0]['Id'], {'Quantity': 1})
    link_armour(1224, 289); cost(1224, 'Marine Recon', 45, 60)
    ms = men(1224); ok(len(ms) == 6 and sum(wn(m['PrimaryWeaponId']) == 'QBZ-192' for m in ms) == 3 and sum(m.get('SpecialWeaponId') == PF89 for m in ms) == 4
                       and AR[289]['Name'] == 'Armor Infantry Shock 6Men', 'Marine Recon 6 men, 3 QBZ-192, 4 PF-89 x1')
    # Taishan Eagles (1203): the 3 QMK carbines -> QBZ-192
    qmk = [m['PrimaryWeaponId'] for m in men(1203) if wn(m.get('PrimaryWeaponId')) == 'QMK']; ok(len(qmk) == 3 and len(set(qmk)) == 1, 'Taishan 3 QMK')
    swap_weapon(1203, qmk[0], QBZ192, QBZ192A, 160)
    ok(sum(wn(m['PrimaryWeaponId']) == 'QBZ-192' for m in men(1203)) == 3 and not one('SquadWeaponsJson', UnitId=1203, WeaponId=qmk[0]), 'Taishan 3 QBZ-192')
    cost(1176, 'Counter-Raid Team', 55, 45)
    cost(129, 'Rosgvardia', 50, 55)

    # --- vehicles
    cost(968, 'ZTZ-100', 340, 355)
    a = own_armour(1056); ok(AR[a]['KinArmorFront'] == 120 and AR[a]['KinArmorSides'] == 100, 'ZBD-251 KE 120/100'); g.put('ArmorsJson', a, {'KinArmorFront': 30, 'KinArmorSides': 20})
    cost(1274, 'VN20', 250, 220)
    a = own_armour(906); ok((AR[a]['KinArmorFront'], AR[a]['KinArmorSides']) == (300, 100), 'ZTQ-15 KE 300/100'); g.put('ArmorsJson', a, {'KinArmorFront': 200, 'KinArmorSides': 80})
    cost(906, 'ZTQ-15', 175, 185)
    a = own_armour(1268); ok(AR[a]['KinArmorSides'] == 80, 'ZTQ-15 Light KE side 80'); g.put('ArmorsJson', a, {'KinArmorSides': 30}); cost(1268, 'ZTQ-15 Light', 155, 170)
    link_armour(1240, 2009119)  # ZTQ-15 Recon shares the (changed) ZTQ-15 row
    cost(904, 'ZTZ-99A', 230, 250); reload(2009071, (7.0, 8.0), (6.0, 7.0))
    cost(1054, 'CTL-181 NLOS', 180, 160)
    medium_plus(1080); cost(1080, 'ZTL-191', 160, 140); cost(1263, 'ZTL-191 Recon', 180, 160)
    ok(users('WeaponAmmunitionsJson', 'WeaponId', 2009665) == {938}, 'ZTL-11 gun own'); reload(2009665, (5.0, 6.0), (6.0, 7.0))
    cost(739, 'KamAZ-6560 Cargo', 50, 40)
    # CSK-131 (1266, the transport: 21 transport rows): QJZ-89 12.7 mm RWS of the CSK-131 Recon (same Tigr model) instead of the empty mount
    r = one('TurretUnitsJson', UnitId=1266); ok(len(r) == 1 and r[0]['TurretId'] == 2018554, 'CSK-131 empty mount')
    rr = one('TurretUnitsJson', UnitId=1265)[0]; ok(U[1265]['ModelFileName'] == U[1266]['ModelFileName'] == 'DLC3_Tigr' and rr['TurretId'] == 2009002, 'same Tigr model, recon RWS turret')
    g.put('TurretUnitsJson', r[0]['Id'], {'TurretId': 2009002})
    g.add('WeaponAmmunitionsJson', one('WeaponAmmunitionsJson', UnitId=1265, WeaponId=2009001)[0], {'UnitId': 1266})
    # --- helicopters and air
    opt_cost(24545, '72x 57 mm', 50, 20)
    s = [r for r in SA.values() if r and r.get('UnitId') == 1252]; ok(len(s) == 1 and s[0]['MaxAvailabilityXp0'] == 4, 'WZ-8 4 cards'); g.put('SpecializationAvailabilitiesJson', s[0]['Id'], {'MaxAvailabilityXp0': 2})
    cost(1104, 'Z-21', 110, 140)
    cost(936, 'HJ-10', 170, 140)
    # HJ-10 smoke and radar removed (Osama 18:4x: "HJ-10 remove its smoke", "HJ-10 remove radar"): its own radar+smoke+laser row 2019696 ->
    # vanilla 'Laser Veh Default' 10, the laser it was built from (same 1500 m laser); the NLOS laser stays.
    r = one('UnitAbilitiesJson', UnitId=936); ok(len(r) == 1 and r[0]['AbilityId'] == 2019696 and AB[2019696]['IsRadar'] and AB[2019696]['IsSmoke'], 'HJ-10 radar+smoke+laser row')
    ok(AB[10]['IsLaserDesignator'] and not AB[10]['IsRadar'] and not AB[10]['IsSmoke'] and AB[10]['LaserMaxRange'] == AB[2019696]['LaserMaxRange'], 'row 10 = same laser only')
    g.put('UnitAbilitiesJson', r[0]['Id'], {'AbilityId': 10})
    cost(911, 'HQ-9C', 300, 325)
    # H-6K: shares mobility 128 'Plane TU22M3' with the Tu-22M3 -> own copy without afterburner
    p = one('UnitPropulsionsJson', UnitId=919); ok(len(p) == 1 and p[0]['MobilityId'] == 128 and MO[128]['IsAfterburner'], 'H-6K on Tu-22M3 mobility')
    g.put('UnitPropulsionsJson', p[0]['Id'], {'MobilityId': g.add('MobilityJson', MO[128], {'Name': 'Plane H-6K FA', 'IsAfterburner': False})})
    cost(318, 'MiG-31K', 400, 300)
    opt_cost(1387, 'Kh32', 150, 50)
    o = O[24664]; ok('6x LD-8A' in o['UIName'], 'J-36 Heavy SEAD option'); g.put('OptionsJson', 24664, {'UIName': o['UIName'].replace('6x LD-8A', '4x LD-8A')})
    ld = [r for r in WA.values() if r and r.get('UnitId') == 929 and wn(r['WeaponId']) == 'LD-8A']
    ok(len(ld) == 1 and ld[0]['Quantity'] == 3, ('J-36 LD-8A 3 per pylon x2', ld)); g.put('WeaponAmmunitionsJson', ld[0]['Id'], {'Quantity': 2})
    cost(929, 'J-36', 415, 445)
    opt_cost(24659, 'Heavy SEAD', 155, 210)  # "J-31 Heavy SEAD +55" read as +55 on its price, like "Z-21 +30 points" and "HQ-9C +25 pts"
    # PHL-16: 300 mm loadout = 300 points (base 350 -> 300; 370 mm +0 -> +50, Fire Dragon +30 -> +80, so those stay 350 / 380); BRE3 48 -> 33 damage, AOE 82.5 -> 75 raw (150 m)
    cost(1035, 'PHL-16', 350, 300); opt_cost(24552, 'BRE6', 0, 50); opt_cost(24553, 'Fire Dragon', 30, 80)
    ok(O[24551]['Cost'] == 0 and users('WeaponAmmunitionsJson', 'AmmunitionId', 2017442) == {1035} and A[2017442]['Damage'] == 48.0 and A[2017442]['HealthAOERadius'] == 82.5, 'BRE3 own round 48 / 82.5')
    g.put('AmmunitionsJson', 2017442, {'Damage': 33.0, 'HealthAOERadius': 75.0})
    rec['china_balance_094'] = out

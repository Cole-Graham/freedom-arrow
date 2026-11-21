"""Blue Dragon changes for 0.9.4-dev.2 (thread 1573418243715113213).
1. K2 front HEAT 1100 -> 1075 (Osama 21 Nov 14:5x: "make sure their tanks follow our new HEAT rules"; top tier = 1075). The other Blue Dragon tanks
   already sit inside the proposed bands (Type 10 800 modern; K1A1 750, T-80U (ROK) 700 mid; Type 90 600, K1 650 old; Type 74 / M48 / Type 16 below).
2. Type 74 (G) (Osama 21 Nov 14:5x: "add a Type 74G that's the normal real loader option"): the Type 74 STB-2 card with the plain M60 M68 105 mm
   (hand-loaded, 5-6 s) instead of the STB-2 loading aid (4-5 s). Same armour, tracks, optics, rounds. Spec 23, 4 cards, 55 pts (placeholder)."""


def apply(t, g, ok, rec):
    U, W, TJ, AR = t['Units'], t['WeaponsJson'], t['TurretsJson'], t['ArmorsJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    def unit(name):
        u = [x for x in U.values() if x and x.get('Name') == name]; ok(len(u) == 1, (name, 'one card')); return u[0]

    out = {}
    # 1. K2 front HEAT
    k2 = unit('K2 Black Panther'); ua = rows('UnitArmorsJson', UnitId=k2['Id']); ok(len(ua) == 1, 'K2 one armour row')
    arm = AR[ua[0]['ArmorId']]; ok((arm['KinArmorFront'], arm['HeatArmorFront']) == (850, 1100), 'K2 KE 850 / HEAT 1100 before')
    ok(not any(r and r['ArmorId'] == arm['Id'] and r['UnitId'] != k2['Id'] for r in t['UnitArmorsJson'].values()), 'K2 armour row is its own')
    g.put('ArmorsJson', arm['Id'], {'HeatArmorFront': 1075}); ok(AR[arm['Id']]['HeatArmorFront'] == 1075, 'K2 HEAT 1075')
    out['K2 Black Panther'] = {'unit': k2['Id'], 'armour_row': arm['Id'], 'HeatArmorFront': [1100, 1075]}

    # 2. Type 74 (G)
    stb = unit('Type 74 STB-2'); sid = stb['Id']
    ok(not any(u and u.get('Name') == 'Type 74 (G)' for u in U.values()), 'Type 74 (G) name free')
    links = rows('TurretUnitsJson', UnitId=sid); main = [r for r in links if TJ[r['TurretId']].get('ParentTurretId') is None]
    ok(len(links) == 3 and len(main) == 1, 'STB-2: main turret + 2 cupolas')
    stbgun = [r['WeaponId'] for r in rows('TurretWeaponsJson', TurretId=main[0]['TurretId']) if 'STB-2' in str(W[r['WeaponId']].get('Name'))]
    ok(len(stbgun) == 1 and (W[stbgun[0]]['MagazineReloadTimeMin'], W[stbgun[0]]['MagazineReloadTimeMax']) == (4.0, 5.0), 'STB-2 gun 4-5 s')
    ok(W[11]['Name'] == 'MainGun 105 M60A3 M68' and (W[11]['MagazineReloadTimeMin'], W[11]['MagazineReloadTimeMax']) == (5.0, 6.0), 'M68 5-6 s')
    d = dict(stb); d.pop('Id'); d.update({'Name': 'Type 74 (G)', 'HUDName': 'Type 74 (G)', 'Cost': 55})
    gid = g.put('Units', max(U) + 1, d)
    for tab in ('SensorUnitsJson', 'UnitAbilitiesJson', 'UnitPropulsionsJson'):
        for r in rows(tab, UnitId=sid): g.add(tab, r, {'UnitId': gid})
    for r in rows('UnitArmorsJson', UnitId=sid):
        g.add('UnitArmorsJson', r, {'UnitId': gid, 'ArmorId': g.add('ArmorsJson', AR[r['ArmorId']], {'Name': 'Armor Type 74 (G) BlueDragon'})})
    tmap = {}
    for r in sorted(links, key=lambda r: TJ[r['TurretId']].get('ParentTurretId') is not None):
        src = r['TurretId']; par = TJ[src].get('ParentTurretId')
        tmap[src] = g.add('TurretsJson', TJ[src], {'ParentTurretId': tmap.get(par, par)})
        for tw in rows('TurretWeaponsJson', TurretId=src):
            g.add('TurretWeaponsJson', tw, {'TurretId': tmap[src], 'WeaponId': 11 if tw['WeaponId'] == stbgun[0] else tw['WeaponId']})
    for r in links: g.add('TurretUnitsJson', r, {'UnitId': gid, 'TurretId': tmap[r['TurretId']]})
    for r in rows('WeaponAmmunitionsJson', UnitId=sid):
        g.add('WeaponAmmunitionsJson', r, {'UnitId': gid, 'WeaponId': 11 if r['WeaponId'] == stbgun[0] else r['WeaponId']})
    sa = rows('SpecializationAvailabilitiesJson', UnitId=sid); ok(len(sa) == 1 and sa[0]['SpecializationId'] == 23, 'STB-2 in spec 23')
    g.add('SpecializationAvailabilitiesJson', sa[0], {'UnitId': gid, 'MaxAvailabilityXp0': 4})
    weps = {r['WeaponId'] for nt in tmap.values() for r in rows('TurretWeaponsJson', TurretId=nt)}
    ok(weps == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=gid)} and 11 in weps and stbgun[0] not in weps, 'Type 74 (G): M68 5-6 s, ammo on every weapon')
    ok([(TJ[r['TurretId']]['Name'], r['Order']) for r in rows('TurretUnitsJson', UnitId=gid)] == [(TJ[r['TurretId']]['Name'], r['Order']) for r in links], 'Type 74 (G) turret links mirror STB-2')
    ok(sorted(r['UnitId'] for r in t['SpecializationAvailabilitiesJson'].values() if r and r['SpecializationId'] == 23).count(gid) == 1, 'Type 74 (G) in spec 23')
    out['Type 74 (G)'] = {'unit': gid, 'from': 'Type 74 STB-2', 'gun': 'M68 (weapon 11) 5-6 s', 'cost': 55, 'cards': 4, 'turrets': list(tmap.values())}
    rec['blue_dragon_dev2'] = out

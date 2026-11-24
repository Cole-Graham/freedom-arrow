"""ZBD-05 = ZSD-05 with an autocannon (Osama 23 Nov 2026 22:3x PST, thread 1567745029781454889: "and lastly we have a ZBD-05 that's a ZSD-05 but with
an autocannon, you can pay +10 pts for the HJ-73D atgm (4x)"). MODEL BUILD ONLY. After zsd05_ampv_1123.py, last in the batch.
- New unit 'PLA ZBD-05': copy of the new 'PLA ZSD-05' (AMPV copy: 8 seats, amphibious, armour options default / reactive / BRAT2 APS kept).
- Weapon slot: two options instead of the AMPV's four. Default = the Bushmaster II autocannon turret (30 mm + M240), +0; the unit costs 35 (the ZSD-05's
  25 plus the AMPV's +10 for that turret). +10 = 'Autocannon + HJ-73D (4x)': a copy of the AMPV Bushmaster II + Javelin turret (3 weapon slots)
  with the HJ-73D vehicle launcher (2011151, as the ZBD-03 / ZBL-08) in the Javelin slot, 4 missiles. M2, Mk19 and Javelin options, turret links
  and ammunition rows are not copied.
- Transport for the 11 PLAN cards that had the old 'PLA Catalogue ZBD-05' (1076, a ZBD-86-model stand-in): those links now point at the new unit;
  the old unit stays (it is in no spec), renamed 'PLA Catalogue ZBD-05 (old)'. No new model yet (shows the AMPV until 'PLA ZBD-05' is staged)."""
OLD, NAME, SPEC = 1076, 'PLA ZBD-05', 20
T_AUTO, T_JAV, W_JAV, W_HJ73D, A_HJ73D = 61, 62, None, 2011151, 2011153


def apply(t, g, ok, rec):
    U, TA, O, T, TW, W = t['Units'], t['TransportAvailabilitiesJson'], t['OptionsJson'], t['TurretsJson'], t['TurretWeaponsJson'], t['WeaponsJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    zsd = [i for i, u in U.items() if u and u.get('Name') == 'PLA ZSD-05']
    ok(len(zsd) == 1 and U[OLD]['Name'] == 'PLA Catalogue ZBD-05' and not rows('SpecializationAvailabilitiesJson', UnitId=OLD), 'ZSD-05 made; old ZBD-05 1076 in no spec')
    src = zsd[0]
    jav = [x for x in rows('TurretWeaponsJson', TurretId=T_JAV)]
    ok([(W[x['WeaponId']]['HUDName'], x['Order']) for x in jav] == [('Bushmaster II', 0), ('M240', 1), ('Javelin', 2)] and W[W_HJ73D]['HUDName'] == 'HJ-73D',
       'AMPV Javelin turret 62: Bushmaster II, M240, Javelin')
    d = dict(U[src]); d.pop('Id'); d.update({'Name': NAME, 'HUDName': 'ZBD-05', 'Cost': 35})
    uid = g.put('Units', max(U) + 1, d)
    for tab in ('UnitArmorsJson', 'UnitPropulsionsJson', 'UnitAbilitiesJson', 'SensorUnitsJson'):
        for r in rows(tab, UnitId=src): g.add(tab, r, {'UnitId': uid})   # armour and mobility rows shared with the ZSD-05 (same chassis)
    tid = g.add('TurretsJson', T[T_JAV], {'Name': 'MainTurret ZBD-05 Bushmaster II HJ-73D'})
    for x in jav: g.add('TurretWeaponsJson', x, {'TurretId': tid, 'WeaponId': W_HJ73D if W[x['WeaponId']]['HUDName'] == 'Javelin' else x['WeaponId']})
    keep_w = {x['WeaponId'] for x in rows('TurretWeaponsJson', TurretId=T_AUTO)}
    for r in rows('TurretUnitsJson', UnitId=src):
        if r['TurretId'] == T_AUTO: g.add('TurretUnitsJson', r, {'UnitId': uid})
        elif r['TurretId'] == T_JAV: g.add('TurretUnitsJson', r, {'UnitId': uid, 'TurretId': tid})
    for r in rows('WeaponAmmunitionsJson', UnitId=src):
        if r['WeaponId'] in keep_w: g.add('WeaponAmmunitionsJson', r, {'UnitId': uid})
    hj = next(r for r in t['WeaponAmmunitionsJson'].values() if r and r['WeaponId'] == W_HJ73D and r['AmmunitionId'] == A_HJ73D and r['Quantity'] == 4)
    g.add('WeaponAmmunitionsJson', hj, {'UnitId': uid})
    for m in rows('ModificationsJson', UnitId=src):
        opts = rows('OptionsJson', ModificationId=m['Id'])
        weap = any(o.get('Turret0Id') for o in opts)
        nm = g.add('ModificationsJson', m, {'UnitId': uid})
        for o in opts:
            if not weap: g.add('OptionsJson', o, {'ModificationId': nm})
            elif o['Turret0Id'] == T_AUTO: g.add('OptionsJson', o, {'ModificationId': nm, 'Cost': 0, 'IsDefault': True})
            elif o['Turret0Id'] == T_JAV: g.add('OptionsJson', o, {'ModificationId': nm, 'Cost': 10, 'IsDefault': False, 'UIName': 'Autocannon + HJ-73D (4x)', 'Turret0Id': tid})
    links = rows('TransportAvailabilitiesJson', UnitId=OLD)
    for r in links: g.put('TransportAvailabilitiesJson', r['Id'], {'UnitId': uid})
    g.put('Units', OLD, {'Name': 'PLA Catalogue ZBD-05 (old)'})
    wo = sorted((o['UIName'], o['Cost']) for m in rows('ModificationsJson', UnitId=uid) for o in rows('OptionsJson', ModificationId=m['Id']) if o.get('Turret0Id'))
    ok(wo == [('Autocannon + HJ-73D (4x)', 10), ('Custom_Option_Bushmaster2_autocannon', 0)] and U[uid]['Cost'] == 35, ('ZBD-05 weapon options', wo))
    has = sorted((W[r['WeaponId']]['HUDName'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=uid))
    ok(('HJ-73D', 4) in has and not any(n in ('Javelin', 'M2 Browning', 'Mk19 AGL') for n, _ in has), ('ZBD-05 ammunition', has))
    ok(sorted(r['TurretId'] for r in rows('TurretUnitsJson', UnitId=uid)) == sorted([T_AUTO, tid]) and len(rows('TransportAvailabilitiesJson', UnitId=uid)) == len(links) == 11
       and not rows('TransportAvailabilitiesJson', UnitId=OLD), 'ZBD-05 turrets; transport for the old ZBD-05 cards')
    ok(all(t['MobilityJson'][r['MobilityId']]['IsAmphibious'] for r in rows('UnitPropulsionsJson', UnitId=uid)) and U[uid]['InfantrySlots'] == 8, 'ZBD-05 amphibious, 8 seats')
    rec['zbd05_ifv'] = {'unit': uid, 'cost': 35, 'weapon_options': wo, 'ammo': has, 'turret': tid, 'transport_for': len(links), 'old': OLD}
    print('ZBD-05', rec['zbd05_ifv'])

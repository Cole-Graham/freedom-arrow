"""Blue Dragon Japanese vehicles with their own models (Osama 21 Nov 2026 23:4x PST, thread 1573418243715113213: "I just installed a bunch of
Japanese units, can you please add them to the units in our armory"; 22 Nov 00:0x: "please make armory models for these and paint schemes with the
various textures they loaded"). Shawn's CGTrader models: Type 10, Type 90 (cards since 0.9.3), Type 89 FV, Type 87 AW and Type 93 Kin-SAM (new
cards here, spec 23 = Arsenal only). Models, LODs and paint schemes: work/blue-dragon-models-20261122 (Assets, not in this data).
New cards are copies of base-game parents without their options; stats and prices are placeholders until Osama sets them:
- Type 89 FV: M2A3 Bradley (16) base configuration; 35 mm KDE (Bradley M242 copy with the CV-9035 35 mm rounds 569/570 and its 105-round
  magazine); Type 79 Jyu-MAT = TOW-2A (5) copy, direct attack, penetration 500 (older SACLOS than TOW-2A 650); 7 seats; Bradley tracks/armour.
- Type 87 AW: PGZ-09 (909) twin 35 mm SPAAG rows linked as they are (row-reuse rule), CountryId US.
- Type 93 Kin-SAM: AN/TWQ-1 Avenger (10) with its twin-pod turret (67: 8 ready missiles + .50 cal) as the default; Type 91 Kin-SAM = Stinger (18)
  copy with the same values."""

SPEC = 23
SMOKE_DEFAULT = 2000197  # 'Smoke x1 NoModel Default', as the Blue Dragon tanks
CARDS = {'Type 89 FV': 4, 'Type 87 AW': 2, 'Type 93 Kin-SAM': 4}


def apply(t, g, ok, rec):
    U, A, W, TJ, AR, MO = (t[k] for k in ('Units', 'AmmunitionsJson', 'WeaponsJson', 'TurretsJson', 'ArmorsJson', 'MobilityJson'))
    SA = t['SpecializationAvailabilitiesJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    def tw(tid):
        return [r['WeaponId'] for r in rows('TurretWeaponsJson', TurretId=tid)]

    # ---- parents and templates (vanilla / 0.9.3 values)
    ok((U[16]['HUDName'], U[10]['HUDName'], U[909]['HUDName']) == ('M2A3 Bradley', 'AN/TWQ-1 Avenger', 'PGZ-09'), 'parents')
    ok(sorted(r['TurretId'] for r in rows('TurretUnitsJson', UnitId=16)) == [52, 53] and TJ[53]['IsDefault'] and tw(53) == [13, 27, 25], 'Bradley M2A3 turret 53')
    ok((A[569]['HUDName'], A[570]['HUDName'], A[5]['HUDName'], A[5]['IsTopArmorArmorAttack'], A[18]['HUDName']) ==
       ('35x228mm API', '35x228mm HEI-T', 'TOW-2A', False, 'FIM-92K Stinger'), 'round templates')
    ok(TJ[67]['Name'] == 'MainTurret Avenger TwinStinger' and sorted(tw(67)) == [16, 39], 'Avenger twin-pod turret 67')
    ok(AR[2000013]['IsDefault'] and MO[10]['IsDefault'] and AR[68]['IsDefault'] and MO[20]['IsDefault'], 'default armour/mobility rows')
    for nm in CARDS:
        ok(not any(u and nm in (u.get('Name'), u.get('HUDName')) for u in U.values()), nm + ' name free')

    def unit(parent, name, cost, **kw):
        d = dict(U[parent]); d.pop('Id')
        d.update({'Name': name, 'HUDName': name, 'Cost': cost, 'OriginalCost': 0, 'Description': None, 'OriginalName': None, 'DisplayInArmory': True, **kw})
        return g.put('Units', max(U) + 1, d)

    def links(uid, sensor, ability, armour, mobility):
        g.add('SensorUnitsJson', {'UnitId': uid, 'SensorId': sensor})
        g.add('UnitAbilitiesJson', {'UnitId': uid, 'AbilityId': ability})
        g.add('UnitArmorsJson', {'UnitId': uid, 'ArmorId': armour})
        g.add('UnitPropulsionsJson', {'UnitId': uid, 'MobilityId': mobility})

    out = {}
    # ---- Type 89 FV
    kde = g.add('WeaponsJson', W[13], {'Name': 'Autocannon 35 Type 89 KDE BlueDragon', 'HUDName': '35mm KDE', 'MagazineSize': 105})
    jyu = g.add('AmmunitionsJson', A[5], {'Name': 'Missile AT Type 79 Jyu-MAT BlueDragon', 'HUDName': 'Type 79 Jyu-MAT',
                                          'PenetrationAtMinRange': 500.0, 'PenetrationAtGroundRange': 500.0})
    u89 = unit(16, 'Type 89 FV', 65)
    links(u89, t['SensorUnitsJson'][rows('SensorUnitsJson', UnitId=16)[0]['Id']]['SensorId'], SMOKE_DEFAULT,
          g.add('ArmorsJson', AR[2000013], {'Name': 'Armor Type 89 FV BlueDragon'}), 10)
    tur = g.add('TurretsJson', TJ[53], {'IsDefault': True})
    for r in rows('TurretWeaponsJson', TurretId=53):
        g.add('TurretWeaponsJson', r, {'TurretId': tur, 'WeaponId': kde if r['WeaponId'] == 13 else r['WeaponId']})
    g.add('TurretUnitsJson', rows('TurretUnitsJson', UnitId=16, TurretId=53)[0], {'UnitId': u89, 'TurretId': tur})
    for w, a_, q in ((kde, 569, 35), (kde, 570, 70), (25, jyu, 4), (27, 27, 400)):
        g.add('WeaponAmmunitionsJson', {'UnitId': u89, 'WeaponId': w, 'AmmunitionId': a_, 'Quantity': q, 'Order': 0})
    out['Type 89 FV'] = u89

    # ---- Type 87 AW: PGZ-09 rows as they are
    u87 = unit(909, 'Type 87 AW', 120, CountryId=2)
    for tab in ('SensorUnitsJson', 'UnitAbilitiesJson', 'UnitArmorsJson', 'UnitPropulsionsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson'):
        for r in rows(tab, UnitId=909):
            g.add(tab, r, {'UnitId': u87})
    out['Type 87 AW'] = u87

    # ---- Type 93 Kin-SAM
    kin = g.add('AmmunitionsJson', A[18], {'Name': 'Missile AA Type 91 Kin-SAM BlueDragon', 'HUDName': 'Type 91 Kin-SAM'})
    u93 = unit(10, 'Type 93 Kin-SAM', 100)
    links(u93, rows('SensorUnitsJson', UnitId=10)[0]['SensorId'], SMOKE_DEFAULT, 68, 20)
    t93 = g.add('TurretsJson', TJ[67], {'IsDefault': True})
    for r in rows('TurretWeaponsJson', TurretId=67):
        g.add('TurretWeaponsJson', r, {'TurretId': t93})
    g.add('TurretUnitsJson', rows('TurretUnitsJson', UnitId=10, TurretId=20)[0], {'UnitId': u93, 'TurretId': t93})
    for w, a_, q in ((16, kin, 16), (39, 19, 50)):
        g.add('WeaponAmmunitionsJson', {'UnitId': u93, 'WeaponId': w, 'AmmunitionId': a_, 'Quantity': q, 'Order': 0})
    out['Type 93 Kin-SAM'] = u93

    # ---- checks: every turret weapon has ammunition and no ammunition row points at a missing weapon; one default turret; spec 23
    tpl = next(r for r in SA.values() if r and r['SpecializationId'] == SPEC)
    res = {}
    for nm, uid in out.items():
        tl = rows('TurretUnitsJson', UnitId=uid)
        weps = {w for r in tl for w in tw(r['TurretId'])}
        ok(weps == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=uid)}, (nm, 'weapons == ammo weapons', weps))
        ok(sum(1 for r in tl if TJ[r['TurretId']].get('IsDefault') and TJ[r['TurretId']].get('ParentTurretId') is None) == 1, (nm, 'one default main turret'))
        ok(not rows('ModificationsJson', UnitId=uid) and len(rows('UnitArmorsJson', UnitId=uid)) == 1 and len(rows('UnitPropulsionsJson', UnitId=uid)) == 1, (nm, 'base configuration'))
        g.add('SpecializationAvailabilitiesJson', tpl, {'UnitId': uid, 'SpecializationId': SPEC, 'MaxAvailabilityXp0': CARDS[nm]})
        res[nm] = {'unit': uid, 'cost': U[uid]['Cost'], 'cards': CARDS[nm], 'country': U[uid]['CountryId'],
                   'rounds': [(A[r['AmmunitionId']]['HUDName'], r['Quantity'], A[r['AmmunitionId']]['PenetrationAtMinRange']) for r in rows('WeaponAmmunitionsJson', UnitId=uid)]}
    ok(U[u87]['CountryId'] == 2 and U[u89]['InfantrySlots'] == U[16]['InfantrySlots'], 'Type 87 US side; Type 89 Bradley seats')
    ok(sum(1 for r in SA.values() if r and r['SpecializationId'] == SPEC and r['UnitId'] in out.values()) == 3, 'three new cards in spec 23')
    rec['blue_dragon_jp'] = res

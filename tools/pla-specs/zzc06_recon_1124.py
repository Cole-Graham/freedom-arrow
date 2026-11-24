"""PLA ZZC-06 (MarkII_ model work/c5-cn-1123 zzc06) replaces the ZBD-04A Recon (Osama 24 Nov 2026 01:1x PST, thread "China cosmetic work":
"were missing the recon for the ZSD-89 called the ZZC-06? it should be in armored recon and replace the ZBD-04 recon unit"; 01:23, thread
"blue dragons": "It's a ZBD-04A recon exacatly but it doesn't have a 100mm gun and is 45 points"; 01:2x, thread "China cosmetic
work": "ZZC do NOT have infantry seats" -> InfantrySlots 7 -> 0).
A full copy of the ZBD-04A Recon (1255: recon tab, Very Good Optics, its abilities, own copies of its armour and mobility rows) at 45 pts (75 -> 45),
without the 100 mm gun / HJ-9 launcher and its two ammo rows. The mount is a copy of 'PLA ZBD-04A mount 0' with the ZPT-99 30 mm at Order 0 and the
Type 86 7.62 mm at Order 1 (Orders 0..n-1: no null weapon slot, see check_mount_weapons.py; the BMP-3 body turret has 3 weapon points).
It takes the ZBD-04A Recon's availability row (PLAGF Heavy Combined Arms Brigade, 4 cards); the ZBD-04A Recon is hidden in the Armory (its rows
stay, saved decks lose the card). Model: models.json key = Name (stage.py MK); icon: card_icons_1124.py."""
OLD, NAME, HUD, COST, SPEC = 1255, 'PLA ZZC-06', 'ZZC-06', 45, 18
GUN, MOUNT = 2009019, 2009020


def apply(t, g, ok, rec):
    U, S, SA, T, TW = t['Units'], t['SpecializationsJson'], t['SpecializationAvailabilitiesJson'], t['TurretsJson'], t['TurretWeaponsJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    ok(U[OLD]['Name'] == 'PLA ZBD-04A Recon' and U[OLD]['CategoryType'] == 0 and U[OLD]['Cost'] == 75, 'ZBD-04A Recon 1255, recon tab, 75 pts')
    ok(not any(u and NAME in (u.get('Name'), u.get('HUDName')) for u in U.values()), NAME + ' name free')
    ok([r['TurretId'] for r in rows('TurretUnitsJson', UnitId=OLD)] == [MOUNT] and T[MOUNT]['Name'] == 'PLA ZBD-04A mount 0', 'ZBD-04A Recon: one mount')
    tw = rows('TurretWeaponsJson', TurretId=MOUNT)
    ok([(r['Order'], r['WeaponId']) for r in tw] == [(0, GUN), (1, 2009027), (2, 2009033)] and t['WeaponsJson'][GUN]['HUDName'] == '100 mm gun / HJ-9 launcher',
       ('mount 0 = 100 mm gun, ZPT-99 30 mm, Type 86 7.62 mm', tw))
    av = rows('SpecializationAvailabilitiesJson', UnitId=OLD)
    ok(len(av) == 1 and av[0]['SpecializationId'] == SPEC and S[SPEC]['UIName'].startswith('PLAGF Heavy Combined Arms Brigade'), ('ZBD-04A Recon availability', av))
    d = dict(U[OLD]); d.pop('Id'); d.update({'Name': NAME, 'HUDName': HUD, 'Cost': COST, 'OriginalCost': 0, 'InfantrySlots': 0, 'DisplayInArmory': True,
                                             'Description': None, 'OriginalName': None})
    uid = g.put('Units', max(U) + 1, d)
    for tab, field, target in (('UnitArmorsJson', 'ArmorId', 'ArmorsJson'), ('UnitPropulsionsJson', 'MobilityId', 'MobilityJson')):
        for r in rows(tab, UnitId=OLD):
            g.add(tab, r, {'UnitId': uid, field: g.add(target, t[target][r[field]], {'Name': f'{t[target][r[field]]["Name"]} ZZC-06'})})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson'):
        for r in rows(tab, UnitId=OLD): g.add(tab, r, {'UnitId': uid})
    mount = g.add('TurretsJson', T[MOUNT], {'Name': 'PLA ZZC-06 mount 0'})
    for order, r in enumerate(r for r in tw if r['WeaponId'] != GUN): g.add('TurretWeaponsJson', r, {'TurretId': mount, 'Order': order})
    g.add('TurretUnitsJson', rows('TurretUnitsJson', UnitId=OLD)[0], {'UnitId': uid, 'TurretId': mount})
    for r in rows('WeaponAmmunitionsJson', UnitId=OLD):
        if r['WeaponId'] != GUN: g.add('WeaponAmmunitionsJson', r, {'UnitId': uid})
    g.put('SpecializationAvailabilitiesJson', av[0]['Id'], {'UnitId': uid})
    g.put('Units', OLD, {'DisplayInArmory': False})
    ok(not any(r and r['UnitId'] == OLD for r in SA.values()) and U[OLD]['DisplayInArmory'] is False, 'ZBD-04A Recon in no spec, hidden')
    ok([r['MaxAvailabilityXp0'] for r in rows('SpecializationAvailabilitiesJson', UnitId=uid)] == [4], 'ZZC-06: 4 cards in spec 18')
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitArmorsJson', 'UnitPropulsionsJson'):
        ok(len(rows(tab, UnitId=uid)) == len(rows(tab, UnitId=OLD)), ('ZZC-06', tab, 'copied'))
    loadout = [(r['Order'], t['WeaponsJson'][r['WeaponId']]['HUDName']) for r in rows('TurretWeaponsJson', TurretId=mount)]
    ammo = [(t['WeaponsJson'][r['WeaponId']]['HUDName'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=uid)]
    ok(loadout == [(0, 'ZPT-99 30 mm'), (1, 'Type 86 7.62 mm')] and len(ammo) == 3, ('ZZC-06 loadout without the 100 mm gun', loadout, ammo))
    ok(U[uid]['CategoryType'] == 0 and U[uid]['Cost'] == COST and U[uid]['InfantrySlots'] == 0, 'ZZC-06 recon tab, 45 pts, no infantry seats')
    rec['zzc06_recon'] = {'unit': uid, 'replaces': OLD, 'spec': SPEC, 'cost': COST, 'mount': mount, 'loadout': loadout, 'ammo': ammo,
                          'sensors': [r['SensorId'] for r in rows('SensorUnitsJson', UnitId=uid)],
                          'abilities': [r['AbilityId'] for r in rows('UnitAbilitiesJson', UnitId=uid)], 'slots': U[uid].get('InfantrySlots')}
    print('ZZC-06', rec['zzc06_recon'])

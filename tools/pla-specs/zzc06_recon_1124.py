"""PLA ZZC-06 (ZSD-89 based recon vehicle, MarkII_ model work/c5-cn-1123 zzc06) replaces the ZBD-04A Recon (Osama 24 Nov 2026 01:1x PST,
thread "China cosmetic work": "were missing the recon for the ZSD-89 called the ZZC-06? it should be in armored recon and replace the ZBD-04
recon unit"). Made the way the China recon vehicles are (ZBD-04A Recon 1255 from ZBD-04A 902, ZBL-08 Recon 1407 from ZBL-08 903): a copy of the
ZSD-89 (1064) in the recon tab (CategoryType 0), vanilla "Very Good Optics" (sensor 3), its own armour and mobility rows, +10 pts (35 -> 45).
It takes the ZBD-04A Recon's availability row (PLAGF Heavy Combined Arms Brigade, 4 cards); the ZBD-04A Recon is hidden in the Armory (its
rows stay, saved decks lose the card). Model: models.json key = Name (stage.py MK)."""
BASE, OLD, NAME, HUD, COST, SPEC = 1064, 1255, 'PLA ZZC-06', 'ZZC-06', 45, 18
VGO = 3


def apply(t, g, ok, rec):
    U, S, SA = t['Units'], t['SpecializationsJson'], t['SpecializationAvailabilitiesJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    ok(U[BASE]['Name'] == 'PLA Catalogue Type 89' and U[BASE]['HUDName'] == 'ZSD-89' and U[BASE]['Cost'] == 35, 'ZSD-89 base row 1064')
    ok(U[OLD]['Name'] == 'PLA ZBD-04A Recon' and U[OLD]['CategoryType'] == 0, 'ZBD-04A Recon 1255')
    ok(not any(u and NAME in (u.get('Name'), u.get('HUDName')) for u in U.values()), NAME + ' name free')
    ok(t['SensorsJson'][VGO]['Name'] == 'Very Good Optics', 'sensor 3 = Very Good Optics')
    av = rows('SpecializationAvailabilitiesJson', UnitId=OLD)
    ok(len(av) == 1 and av[0]['SpecializationId'] == SPEC and S[SPEC]['UIName'].startswith('PLAGF Heavy Combined Arms Brigade'), ('ZBD-04A Recon availability', av))
    d = dict(U[BASE]); d.pop('Id'); d.update({'Name': NAME, 'HUDName': HUD, 'Cost': COST, 'OriginalCost': 0, 'CategoryType': 0, 'DisplayInArmory': True,
                                              'Description': None, 'OriginalName': None})
    uid = g.put('Units', max(U) + 1, d)
    for tab, field, target in (('UnitArmorsJson', 'ArmorId', 'ArmorsJson'), ('UnitPropulsionsJson', 'MobilityId', 'MobilityJson')):
        for r in rows(tab, UnitId=BASE):
            g.add(tab, r, {'UnitId': uid, field: g.add(target, t[target][r[field]], {'Name': f'{t[target][r[field]]["Name"]} ZZC-06'})})
    for tab in ('TurretUnitsJson', 'UnitAbilitiesJson', 'WeaponAmmunitionsJson'):
        for r in rows(tab, UnitId=BASE): g.add(tab, r, {'UnitId': uid})
    sens = rows('SensorUnitsJson', UnitId=BASE)
    ok(len(sens) == 1, ('ZSD-89 one sensor row', sens))
    g.add('SensorUnitsJson', sens[0], {'UnitId': uid, 'SensorId': VGO})
    g.put('SpecializationAvailabilitiesJson', av[0]['Id'], {'UnitId': uid})
    g.put('Units', OLD, {'DisplayInArmory': False})
    ok(not any(r and r['UnitId'] == OLD for r in SA.values()) and U[OLD]['DisplayInArmory'] is False, 'ZBD-04A Recon in no spec, hidden')
    ok([r['MaxAvailabilityXp0'] for r in rows('SpecializationAvailabilitiesJson', UnitId=uid)] == [4], 'ZZC-06: 4 cards in spec 18')
    ok([r['SensorId'] for r in rows('SensorUnitsJson', UnitId=uid)] == [VGO] and U[uid]['CategoryType'] == 0, 'ZZC-06 recon tab + VGO')
    rec['zzc06_recon'] = {'unit': uid, 'replaces': OLD, 'spec': SPEC, 'cost': COST,
                          'base_abilities': [r['AbilityId'] for r in rows('UnitAbilitiesJson', UnitId=BASE)],
                          'old_abilities': [r['AbilityId'] for r in rows('UnitAbilitiesJson', UnitId=OLD)],
                          'turrets': [r['TurretId'] for r in rows('TurretUnitsJson', UnitId=uid)], 'slots': U[uid].get('InfantrySlots')}
    print('ZZC-06', rec['zzc06_recon'])

"""Lynx IFV, a new Lynx ATV, Lynx icons (Osama 25 Nov 2026 00:1x-00:2x PST, thread "China cosmetic work").
- "lynx IFV (autocannon uses the same cannon as the Type 100 CSV) 65 points and no supplies": the Rapid-Fire Gun (1433, model 609673) is shown as
  'Lynx IFV'; its 30 mm autocannon (2011271, AP 38 / HE 88) on its own mount 0 becomes the Type 100's 40 mm CT (2019882) with the Type 100's
  rounds (APFSDS 100, HE 234); HJ-8H x2 and Type 86 stay; 35 -> 65 pts; its only ability row (Supply Light, resupply 250) goes: no supplies.
- "lynx ATV (make a new unit called this and it's the same as the Troop carrier but it's 7 seats)": made by the Troop Carrier's own generator
  (lynx_cards_1124.apply: CS/VN3C parent, Lynx armour/mobility, Unarmed / QJZ-89 +5 / QLZ-87 +5 options, 20 pts, transport for every
  airborne infantry card) with 7 seats; model m_315224 (his picture). The old placeholder 'PLA Lynx ATV' (1228: US M1297 icon, vanilla stand-in
  model, 9 seats) is renamed '... (old stand-in)', hidden and loses its 10 transport links, so only one Lynx ATV is offered.
- Icons (white side views from each card's battle model, pla-unit-icons sil.py + style.py): Troop Carrier, IFV, Recon (CategoryType 0 = Recon tab,
  checked), SPAAG, 120 mm Mortar, 81 mm Mortar, MLRS (Lynx 66 107 mm), ATV (moved from 1228 to the new card).
Creates rows (the ATV): after every other row-creating section."""
import os
import lynx_cards_1124
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'mod', 'source', 'runtime-qa', 'icons')
IFV, T100, OLD_ATV = 1433, 1295, 1228
ICON = {1431: 'LYNXTC', 1433: 'LYNXIFV', 1443: 'LYNXREC', 1439: 'LYNXSPAAG', 1435: 'LYNXMOR', 1434: 'LYNXMOR81', 1437: 'LYNXMLRS'}


def apply(t, g, ok, rec):
    U, W, A, WA, TW, TU, UA, TA = (t[k] for k in ('Units', 'WeaponsJson', 'AmmunitionsJson', 'WeaponAmmunitionsJson', 'TurretWeaponsJson',
                                                 'TurretUnitsJson', 'UnitAbilitiesJson', 'TransportAvailabilitiesJson'))
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok([U[i]['HUDName'] for i in (IFV, T100, OLD_ATV)] == ['Lynx Rapid-Fire Gun', 'Type 100 CSV', 'Lynx ATV'], 'Rapid-Fire Gun / Type 100 / old Lynx ATV')
    # IFV
    mounts = [r['TurretId'] for r in rows('TurretUnitsJson', UnitId=IFV)]
    ac = [x for m in mounts for x in rows('TurretWeaponsJson', TurretId=m) if W[x['WeaponId']]['HUDName'] == '30 mm autocannon']
    ok(len(ac) == 1 and ac[0]['Order'] == 0 and not any(r['UnitId'] != IFV for r in rows('TurretUnitsJson', TurretId=ac[0]['TurretId'])), ('IFV own mount, autocannon at 0', ac))
    old = ac[0]['WeaponId']; ct = [x['WeaponId'] for m in rows('TurretUnitsJson', UnitId=T100) for x in rows('TurretWeaponsJson', TurretId=m['TurretId']) if W[x['WeaponId']]['HUDName'] == '40 mm CT']
    ok(len(ct) == 1, ('Type 100 40 mm CT', ct)); ct = ct[0]
    old_wa = rows('WeaponAmmunitionsJson', UnitId=IFV, WeaponId=old); ct_wa = rows('WeaponAmmunitionsJson', UnitId=T100, WeaponId=ct)
    ok(len(old_wa) == 2 and len(ct_wa) == 2, ('IFV AP/HE, Type 100 APFSDS/HE', old_wa, ct_wa))
    g.put('TurretWeaponsJson', ac[0]['Id'], {'WeaponId': ct})
    for o, n in zip(old_wa, sorted(ct_wa, key=lambda r: r['Order'])):
        g.put('WeaponAmmunitionsJson', o['Id'], {'WeaponId': ct, 'AmmunitionId': n['AmmunitionId'], 'Quantity': n['Quantity'], 'Order': n['Order']})
    ab = rows('UnitAbilitiesJson', UnitId=IFV); AB = t['AbilitiesJson']
    ok(len(ab) == 1 and AB[ab[0]['AbilityId']].get('IsResupplyAbility') and not any(AB[ab[0]['AbilityId']].get(k) for k in
       ('IsSmoke', 'IsAPS', 'IsRadar', 'IsJammer', 'IsLaserDesignator', 'IsSprint')), ('IFV: one ability, supply only', ab))
    g.remove('UnitAbilitiesJson', ab[0]['Id'])
    g.put('Units', IFV, {'HUDName': 'Lynx IFV', 'Cost': 65})
    ifv = [(W[r['WeaponId']]['HUDName'], A[r['AmmunitionId']]['HUDName'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=IFV)]
    ok(not rows('UnitAbilitiesJson', UnitId=IFV) and U[IFV]['Cost'] == 65 and sorted(ifv) == sorted([('40 mm CT', '40 mm CT APFSDS', 100), ('40 mm CT', '40 mm CT HE', 234),
       ('Type 86 7.62 mm', 'Type 86 7.62 mm ammunition', 400), ('HJ-8H', 'HJ-8H', 2)]), ('Lynx IFV', ifv))
    # old ATV out, new ATV in
    ta_old = [r['Id'] for r in rows('TransportAvailabilitiesJson', UnitId=OLD_ATV)]
    ok(len(ta_old) == 10 and not rows('SpecializationAvailabilitiesJson', UnitId=OLD_ATV), ('old Lynx ATV: 10 transport links only', ta_old))
    for i in ta_old: g.remove('TransportAvailabilitiesJson', i)
    g.put('Units', OLD_ATV, {'Name': 'PLA Lynx ATV (old stand-in)', 'HUDName': 'Lynx ATV (old)', 'DisplayInArmory': False})
    keep = lynx_cards_1124.TRANSPORTS; lynx_cards_1124.TRANSPORTS = keep + ('PLA Lynx ATV',)
    try: lynx_cards_1124.apply(t, g, ok, rec, cards={'PLA Lynx ATV': ('Lynx ATV', 1057, 20, 4, 2, 7, 'LOADOUT')}, key='lynx_atv_1125')
    finally: lynx_cards_1124.TRANSPORTS = keep
    atv = rec['lynx_atv_1125']['PLA Lynx ATV']['unit']
    tc_squads = sorted(t['SpecializationAvailabilitiesJson'][r['SpecializationAvailabilityId']]['UnitId'] for r in rows('TransportAvailabilitiesJson', UnitId=1431))
    atv_squads = sorted(t['SpecializationAvailabilitiesJson'][r['SpecializationAvailabilityId']]['UnitId'] for r in rows('TransportAvailabilitiesJson', UnitId=atv))
    ok(U[atv]['InfantrySlots'] == 7 and U[atv]['Cost'] == U[1431]['Cost'] and atv_squads == tc_squads and len(rows('OptionsJson', ModificationId=rows('ModificationsJson', UnitId=atv)[0]['Id'])) == 3,
       ('Lynx ATV = Troop Carrier with 7 seats', U[atv]['InfantrySlots'], atv_squads == tc_squads))
    # icons
    ok(U[1443]['CategoryType'] == 0, 'Lynx Recon in the Recon tab')
    allicons = {**{i: 'FA_PLA_VEH_' + k for i, k in ICON.items()}, atv: 'FA_PLA_VEH_LYNXATV'}
    ok(all(os.path.isfile(os.path.join(DIR, a + s + '.png')) for a in allicons.values() for s in ('', '_OUTLINE')), 'Lynx icons + outlines in runtime-qa/icons')
    before = {i: U[i].get('ThumbnailFileName') for i in allicons}
    for i, a in allicons.items(): g.put('Units', i, {'ThumbnailFileName': a})
    g.put('Units', OLD_ATV, {'ThumbnailFileName': before.get(OLD_ATV) or 'US_M1297-Label'})
    rec['lynx_ifv_atv_1125'] = {'ifv': ifv, 'old_atv_transports_removed': ta_old, 'atv': atv, 'icons_before': before}
    print('LYNX IFV/ATV', rec['lynx_ifv_atv_1125'])

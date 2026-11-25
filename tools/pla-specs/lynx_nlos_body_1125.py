"""Audit fixes after 0.9.7-dev.11 (Osama 25 Nov 2026 03:5x PST "check every single change we applied", thread 1567745029781454889).
- Lynx NLOS (1441) did not show in the Arsenal at all (search "Lynx" found the other 10 Lynx cards). Its stand-in body was the Bradley
  (US_M2A3), which has refused FA turret setups before (bradley-turret-swap note); the CTL-181 (1054) carries the same NLOS launcher on the
  Tigr body (DLC3_Tigr) and shows. The Lynx NLOS now uses the Tigr body and the CTL-181's launcher mount (2010706), like the CTL-181.
  FAModels still draws the Lynx model over it.
- dev.12 still hid it: the real cause is IsUnitModification True on 1441 (copied from its template), which marks a row as a loadout variant,
  not a card of its own. Now False, as on the CTL-181 and every other Lynx card. Its icon was still the Bradley label: now FA_PLA_VEH_LYNXNLOS
  (white side view of its own battle model, pla-unit-icons sil.py + style.py), portrait the CTL-181's.
- Lynx Cargo (1432) carried 3000 supply; Osama 25 Nov 01:1x asked "up to 2500 cargo capacity": its own mobility row 3000 -> 2500."""
NLOS, CTL, CARGO = 1441, 1054, 1432


def apply(t, g, ok, rec):
    U, TU, MO, UP = t['Units'], t['TurretUnitsJson'], t['MobilityJson'], t['UnitPropulsionsJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok(U[NLOS]['HUDName'] == 'Lynx NLOS' and U[NLOS]['ModelFileName'] == 'US_M2A3' and U[CTL]['ModelFileName'] == 'DLC3_Tigr', 'Lynx NLOS on the Bradley body; CTL-181 on the Tigr')
    (ctu,) = rows('TurretUnitsJson', UnitId=CTL); (ntu,) = rows('TurretUnitsJson', UnitId=NLOS)
    ok([r['WeaponId'] for r in rows('TurretWeaponsJson', TurretId=ctu['TurretId'])] == [r['WeaponId'] for r in rows('TurretWeaponsJson', TurretId=ntu['TurretId'])],
       ('same NLOS launcher on both mounts', ctu, ntu))
    ok(U[NLOS]['IsUnitModification'] is True and U[CTL]['IsUnitModification'] is False, 'Lynx NLOS marked as a loadout variant')
    import os
    ok(all(os.path.isfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'mod', 'source', 'runtime-qa', 'icons', 'FA_PLA_VEH_LYNXNLOS' + x + '.png')) for x in ('', '_OUTLINE')), 'Lynx NLOS icon')
    g.put('Units', NLOS, {'ModelFileName': U[CTL]['ModelFileName'], 'IsUnitModification': False, 'ThumbnailFileName': 'FA_PLA_VEH_LYNXNLOS', 'PortraitFileName': U[CTL]['PortraitFileName']})
    g.put('TurretUnitsJson', ntu['Id'], {'TurretId': ctu['TurretId'], 'Order': ctu['Order']})
    (up,) = rows('UnitPropulsionsJson', UnitId=CARGO)
    ok(U[CARGO]['HUDName'] == 'Lynx Cargo' and MO[up['MobilityId']]['HeavyLiftWeight'] == 3000 and [r['UnitId'] for r in rows('UnitPropulsionsJson', MobilityId=up['MobilityId'])] == [CARGO],
       'Lynx Cargo own mobility, 3000')
    g.put('MobilityJson', up['MobilityId'], {'HeavyLiftWeight': 2500})
    # Guard: a card offered in a spec and shown in the Armory must not carry IsUnitModification unless a loadout option swaps to it.
    swap = {o.get('ReplaceUnitId') for o in t['OptionsJson'].values() if o and o.get('ReplaceUnitId')}
    bad = sorted({r['UnitId'] for r in t['SpecializationAvailabilitiesJson'].values() if r and U[r['UnitId']].get('DisplayInArmory')
                  and U[r['UnitId']].get('IsUnitModification') and r['UnitId'] not in swap and r['UnitId'] >= 900})
    ok(not bad, ('FA cards hidden as loadout variants', [(u, U[u]['HUDName']) for u in bad]))
    rec['lynx_nlos_body_1125'] = {'nlos_body': 'DLC3_Tigr', 'nlos_mount': ctu['TurretId'], 'cargo_supply': [3000, 2500]}
    print('AUDIT FIXES', rec['lynx_nlos_body_1125'])

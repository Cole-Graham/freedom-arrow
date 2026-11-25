"""Lynx NLOS, CSK-131 out of Airborne, Lynx Laser APS symbol (Osama 25 Nov 2026 01:4x-01:5x PST, thread 1567745029781454889).
- "we need to remove CSK-131 from Airborne": the CSK-131 transport (1266, 'PLA CSK-181 4x4') loses its 10 transport links to the PLAAF Air Force
  (Airborne, spec 17) squads; every one of those squads keeps Z-20KA, VN-3 and the Lynx Troop Carrier. The Motorized (21) links stay.
- "CS/VP17 we just call it Lynx NLOS. It's the same as the CTL-181 NLOS but 10 rounds. only 60 pts, no optics but yes laser": the Swarm Launcher
  (1441) is shown as 'Lynx NLOS'; its CH-901 mount and ammo row get the CTL-181's launcher (2018322) and NLOS missile (2018321), 10 rounds;
  150 -> 60 pts; optics Very Good -> Bad (sensor 4, the lowest ground optics); its laser designator ability stays. 01:5x "NLOS goes to VEH
  tab": CategoryType 3 (Support) -> 2 (Vehicles), as the CTL-181.
- "this needs the laser defense system APS symbol ... the exact same one on the LY-1": UserData/FreedomArrow/dazzler.json lists the Lynx
  Laser with the LY-1, and its renamed weapon '50 kW laser' with 'LY-1 laser'; checked here so a shifted unit id stops the build."""
import json, os
CSK, TC, SWARM, CTL, LASER = 1266, 1431, 1441, 1054, 1446
DAZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'mod', 'source', 'UserData', 'FreedomArrow', 'dazzler.json')


def apply(t, g, ok, rec):
    U, TA, SA, TW, WA, SU, W, A, UA, AB = (t[k] for k in ('Units', 'TransportAvailabilitiesJson', 'SpecializationAvailabilitiesJson', 'TurretWeaponsJson',
                                                         'WeaponAmmunitionsJson', 'SensorUnitsJson', 'WeaponsJson', 'AmmunitionsJson', 'UnitAbilitiesJson', 'AbilitiesJson'))
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok([U[i]['HUDName'] for i in (CSK, SWARM, CTL, LASER)] == ['CSK-131', 'CS/VP17 Swarm Launcher', 'CTL-181 NLOS', 'Lynx Laser'], 'CSK-131 / Swarm / CTL-181 / Lynx Laser')
    # CSK-131 out of Airborne
    air = [r for r in rows('TransportAvailabilitiesJson', UnitId=CSK) if SA[r['SpecializationAvailabilityId']]['SpecializationId'] == 17]
    ok(len(air) == 10, ('CSK-131 airborne links', len(air)))
    for r in air: g.remove('TransportAvailabilitiesJson', r['Id'])
    squads = sorted(SA[r['SpecializationAvailabilityId']]['UnitId'] for r in air)
    ok(all(any(r['UnitId'] == TC and SA[r['SpecializationAvailabilityId']]['UnitId'] == q for r in TA.values() if r) for q in squads)
       and not any(SA[r['SpecializationAvailabilityId']]['SpecializationId'] == 17 for r in rows('TransportAvailabilitiesJson', UnitId=CSK)), 'Airborne squads keep the Troop Carrier, no CSK-131')
    # Lynx NLOS
    (ctw,) = [x for m in rows('TurretUnitsJson', UnitId=CTL) for x in rows('TurretWeaponsJson', TurretId=m['TurretId'])]
    (cwa,) = rows('WeaponAmmunitionsJson', UnitId=CTL)
    (stw,) = [x for m in rows('TurretUnitsJson', UnitId=SWARM) for x in rows('TurretWeaponsJson', TurretId=m['TurretId'])]
    (swa,) = rows('WeaponAmmunitionsJson', UnitId=SWARM)
    ok(W[ctw['WeaponId']]['HUDName'] == 'CTL-181 NLOS launcher' and A[cwa['AmmunitionId']]['HUDName'] == 'NLOS missile' and W[stw['WeaponId']]['HUDName'] == 'CH-901'
       and len(rows('TurretUnitsJson', TurretId=stw['TurretId'])) == 1, ('CTL-181 launcher / Swarm own CH-901 mount', ctw, cwa, stw))
    g.put('TurretWeaponsJson', stw['Id'], {'WeaponId': ctw['WeaponId']})
    g.put('WeaponAmmunitionsJson', swa['Id'], {'WeaponId': ctw['WeaponId'], 'AmmunitionId': cwa['AmmunitionId'], 'Quantity': 10})
    (su,) = rows('SensorUnitsJson', UnitId=SWARM)
    ok(su['SensorId'] == 3 and t['SensorsJson'][4]['Name'] == 'Bad Optics', ('Swarm Very Good optics; sensor 4 Bad', su))
    g.put('SensorUnitsJson', su['Id'], {'SensorId': 4})
    ok(U[SWARM]['CategoryType'] == 3 and U[CTL]['CategoryType'] == 2, 'Swarm in Support, CTL-181 in Vehicles')
    g.put('Units', SWARM, {'HUDName': 'Lynx NLOS', 'Cost': 60, 'CategoryType': 2})
    ok(U[SWARM]['OriginalCost'] in (0, None) and any(AB[r['AbilityId']].get('IsLaserDesignator') for r in rows('UnitAbilitiesJson', UnitId=SWARM)), 'Lynx NLOS: 60 pts, laser designator kept')
    # Lynx Laser APS symbol: dazzler.json
    d = json.load(open(DAZ, encoding='utf-8'))
    ok(LASER in d['units'] and 1275 in d['units'] and U[1275]['HUDName'] == 'LY-1' and '50 kW laser' in d['laserWeaponNames']
       and any(W[r['WeaponId']]['HUDName'] == '50 kW laser' for r in rows('WeaponAmmunitionsJson', UnitId=LASER)), ('dazzler.json: Lynx Laser + LY-1', d['units'], d['laserWeaponNames']))
    rec['lynx_nlos_csk_1125'] = {'csk_airborne_links_removed': [r['Id'] for r in air], 'squads': squads, 'nlos': {'unit': SWARM, 'weapon': ctw['WeaponId'], 'ammo': cwa['AmmunitionId'], 'rounds': 10, 'cost': 60, 'sensor': 4, 'category': 2}}
    print('LYNX NLOS / CSK', rec['lynx_nlos_csk_1125'])

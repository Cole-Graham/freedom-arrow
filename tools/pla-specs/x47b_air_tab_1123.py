"""X-47B in the Air tab with plane optics, ECM and flares (Osama 23 Nov 2026 22:0x PST, thread 1567745029781454889): "did we not move the x47 to
the air tab? like I said? you moved it to recon, and remove its ground optics, it should be plane optics only", "and please give it its ecm and
flares", "45% ecm same as others". (20:4x "X-47 moved to Marines in the Air tab": x47b_marines_1123.py moved the card to USMC but the tab comes
from Units.CategoryType, which stayed 0 = Recon.)
- Tab: CategoryType 0 -> 6 (Air) and Role 100 -> 164, as the FH-97A and F-16C. Type 16 (plane) unchanged.
- Optics: vanilla 'Optics Drone 2250' (33: ground 5250, low 1600, high 1000) -> vanilla 'Optics Plane Air Superiority' (6: ground 0, low 2000,
  high 8000), the FH-97A's and F-16C's.
- ECM 45% + flares: vanilla ability 2001399 'ECM Plane 20 + Laser Default FA 0.55' (ECM x0.55, laser designator, 25 flares), the one the FH-97A
  and MD-22 use, instead of the laser + flares row from ucav_flares_1123.py."""
X47, FH97, DRONE_OPT, PLANE_OPT, ECM_FLARES = 969, 1253, 33, 6, 2001399


def apply(t, g, ok, rec):
    U, SU, SN, UA, A = t['Units'], t['SensorUnitsJson'], t['SensorsJson'], t['UnitAbilitiesJson'], t['AbilitiesJson']
    ok(U[X47]['HUDName'] == 'X-47B' and (U[X47]['CategoryType'], U[X47]['Role']) == (0, 100) and (U[FH97]['CategoryType'], U[FH97]['Role']) == (6, 164),
       'X-47B in the Recon tab; FH-97A Air tab, role 164')
    su = [r for r in SU.values() if r and r['UnitId'] == X47]
    ok([r['SensorId'] for r in su] == [DRONE_OPT] and SN[PLANE_OPT]['OpticsGround'] == 0 and [r['SensorId'] for r in SU.values() if r and r['UnitId'] == FH97] == [PLANE_OPT],
       'X-47B drone optics; FH-97A plane optics (no ground)')
    ua = [r for r in UA.values() if r and r['UnitId'] == X47]
    ok(len(ua) == 1 and A[ECM_FLARES]['ECMAccuracyMultiplier'] == 0.55 and A[ECM_FLARES]['IsDecoy'] and A[ECM_FLARES]['IsLaserDesignator'], 'X-47B one ability row; 2001399 = ECM 0.55 + laser + flares')
    old_ab = ua[0]['AbilityId']
    g.put('Units', X47, {'CategoryType': 6, 'Role': 164})
    g.put('SensorUnitsJson', su[0]['Id'], {'SensorId': PLANE_OPT})
    g.put('UnitAbilitiesJson', ua[0]['Id'], {'AbilityId': ECM_FLARES})
    ok((U[X47]['CategoryType'], [r['SensorId'] for r in SU.values() if r and r['UnitId'] == X47], [r['AbilityId'] for r in UA.values() if r and r['UnitId'] == X47])
       == (6, [PLANE_OPT], [ECM_FLARES]), 'X-47B: Air tab, plane optics, ECM 45% + flares')
    ok(any(r and r['AbilityId'] == old_ab for r in UA.values()), 'the UCAV laser + flares row keeps its other users (S-70, GJ-11)')
    rec['x47b_air_tab'] = {'unit': X47, 'category': [0, 6], 'role': [100, 164], 'sensor': [DRONE_OPT, PLANE_OPT], 'ability': [old_ab, ECM_FLARES]}
    print('X-47B AIR', rec['x47b_air_tab'])

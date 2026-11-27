"""HQ-16 range and price (Osama 27 Nov 2026 04:3x PST, thread 1567745029781454889: "HQ-16 to 1950 low and high range, 165 points").
- Round 2010615 'HQ-16 ammunition' (only the HQ-16, 1048, fires it): LowAltRange and HighAltRange 925 -> 975 world (card 1,850 -> 1,950 m).
  Minimum range 300, seeker, speed and motor unchanged. Flight reach from the motor (docs/engine/missile-flight.md: burn 2 s at +350/s to 700,
  coast -91/s to 210) is about 3,150 world, so the missile still reaches 975.
- HQ-16 (1048) 150 -> 165 pts. OriginalCost 0, no loadouts."""
HQ16, AMMO = 1048, 2010615


def apply(t, g, ok, rec):
    U, A = t['Units'], t['AmmunitionsJson']
    users = {r['UnitId'] for r in t['WeaponAmmunitionsJson'].values() if r and r['AmmunitionId'] == AMMO}
    a = A[AMMO]
    ok(U[HQ16]['HUDName'] == 'HQ-16' and users == {HQ16} and (a['LowAltRange'], a['HighAltRange']) == (925.0, 925.0) and U[HQ16]['Cost'] == 150 and not U[HQ16].get('OriginalCost'),
       ('HQ-16 own round 925/925, 150 pts', users, a['LowAltRange'], a['HighAltRange'], U[HQ16]['Cost']))
    g.put('AmmunitionsJson', AMMO, {'LowAltRange': 975.0, 'HighAltRange': 975.0})
    g.put('Units', HQ16, {'Cost': 165})
    rec['osama_hq16_1127'] = {'range_card_m': [1850, 2 * A[AMMO]['LowAltRange']], 'cost': [150, U[HQ16]['Cost']]}
    print('HQ-16', rec['osama_hq16_1127'])

"""FB-10 = AMRAAM stat clone (Lateralus 24 Nov 2026 18:4x PST, thread 1568104480459722894: "Change the FB-10 missile into an AMRAAM stat clone
(same as the AMRAAM on the SLAMRAAM unit)").
Round 2009373 "PLA PGL-625 FB-10 ammunition" (PGL-625 920, Lynx 66 SPAAG 1439) takes every value of 464 "Missile AA AMRAAM Ground" (SLAMRAAM,
NASAMS) except its own name, icon, missile model, sound and impact effect. Runs BEFORE shorad_radar_1124.py (Lateralus 18:5x 'queue it', China radar
proposal): the PGL-625 and Lynx 66 SPAAG then carry a radar-guided missile, so the split puts them on SA SHORAD, and the burn table gives the FB-10 the
AMRAAM's 2.65 s. Before: Seeker 10 (IR) 1200 low / 1200 high / 600 ground, MaxSpeed 700; after: Seeker 50 (active radar) as AMRAAM.
Its helicopter range follows the AMRAAM's."""
FB10, AMRAAM = 2009373, 464
KEEP = ('Id', 'Name', 'HUDName', 'HUDIcon', 'ModelFileName', 'AudioPreset', 'FXPreset')


def apply(t, g, ok, rec, heli):
    A, WA, U = t['AmmunitionsJson'], t['WeaponAmmunitionsJson'], t['Units']
    ok(A[FB10]['HUDName'] == 'FB-10 ammunition' and A[AMRAAM]['Name'] == 'Missile AA AMRAAM Ground', 'FB-10 and AMRAAM ground rows')
    users = sorted({r['UnitId'] for r in WA.values() if r and r['AmmunitionId'] == FB10})
    ok(users == [920, 1439], ('FB-10 users: PGL-625 and Lynx 66 SPAAG', users))
    before = {k: v for k, v in A[FB10].items() if k not in KEEP and A[AMRAAM].get(k) != v}
    g.put('AmmunitionsJson', FB10, {k: v for k, v in A[AMRAAM].items() if k not in KEEP})
    ok(all(A[FB10].get(k) == v for k, v in A[AMRAAM].items() if k not in KEEP), 'FB-10 has every AMRAAM stat')
    if str(AMRAAM) in heli['ammo']:heli['ammo'][str(FB10)] = heli['ammo'][str(AMRAAM)]
    else:heli['ammo'].pop(str(FB10), None)
    rec['fb10_amraam_1124'] = {'round': FB10, 'from': AMRAAM, 'changed': {k: [v, A[FB10][k]] for k, v in before.items()},
                               'users': {u: U[u]['HUDName'] for u in users}}
    return rec['fb10_amraam_1124']

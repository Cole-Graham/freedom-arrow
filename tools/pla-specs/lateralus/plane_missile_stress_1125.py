"""Plane fire-and-forget / terminal-guidance missiles ignore the shooter's stress in hit chance (Lateralus 25 Nov 2026 16:1x PST, thread
1568104480459722894: "Queue up just the low risk missile accuracy debuff removal"; feasibility in docs/engine/stress.md).
Vanilla multiplies missile hit chance by the shooter's stress multiplier (planes: shocked 0.85, panicked 0.6). The runtime (MissileHitChance.Chance)
uses 1 instead for these rounds when a plane fires them. Aim time, time between bursts and reload stay debuffed (not part of this change).
- planeStressExempt: Seeker 10 (fire-and-forget) or 50 (terminal guidance) rounds that a plane (Units.Type 16) fires.
- planeStressShared: those of them that a non-plane unit also fires (helicopters: PL-5E, PL-9, PL-10 on Z-10/Z-21); the runtime then checks the
  missile's shooter (WarheadComponent.ShooterWeapon -> its unit's Type) and keeps the stress for non-plane shooters."""


def apply(t, ok, rec, heli):
    U, A, WA = t['Units'], t['AmmunitionsJson'], t['WeaponAmmunitionsJson']
    plane, other = set(), set()
    for r in WA.values():
        if not r:continue
        a = A.get(r['AmmunitionId']);u = U.get(r['UnitId'])
        if not a or not u or a.get('Seeker') not in (10, 50):continue
        (plane if u.get('Type') == 16 else other).add(a['Id'])
    shared = plane & other
    ok(len(plane) >= 30 and {2016381, 2016975, 2017060} <= shared, ('plane FF/TG rounds', len(plane), sorted(shared)))
    heli['planeStressExempt'] = sorted(plane)
    heli['planeStressShared'] = sorted(shared)
    rec['plane_missile_stress_1125'] = {'rounds': len(plane), 'shared': {i: A[i]['Name'] for i in sorted(shared)}}
    return rec['plane_missile_stress_1125']

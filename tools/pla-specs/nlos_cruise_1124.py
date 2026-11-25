"""NLOS missiles act like vanilla cruise missiles (Osama 24 Nov 2026 17:1x-17:2x PST, bugs thread 1573561286803980289: "HJ-10 is still bugged, now it
seeks targets on its own even if it doesn't see", "they shouldn't track", "it should just act like a cruise missile, why is that so hard?").
His 0.9.6 log (17:08-17:13): all 20 NLOS launches were at a ground spot, and NlosTrait.cs then locked each missile on the enemy nearest that spot
(1-58 away) with no visibility check, and held the lock. Fix = vanilla cruise guidance, the Iskander-K 219 / Tomahawk 35 pattern:
Seeker 0, SeekerAngle 0, MaxSeekerDistance 0, CanReaquire False, LaserGuided False, TargetType 1 (ground position only: fired with Fire Position,
flies to the spot and dives, no auto fire, no tracking). Damage, penetration, range, speed and flight stay. nlos.json lists no rounds, units or
launchers any more, so NlosTrait.cs installs no hooks (empty list).
Option A (Osama 24 Nov 17:4x, "and they can optionally be laser guided?" ... "ok I'll test it with A"): vanilla cruise rounds are never laser guided,
so the rounds take the vanilla Iskander-M ballistic guidance and flight instead (round 218: path 300, LaserGuided, seeker 0, TargetType 1, speed 800,
burn 8 s) and the launchers become Type 83 (ballistic; a Type 82 launcher does not fire a path-300 round, as a Type 81 did not fire path 200 in 0.9.4).
Fire Position lands on the spot; a friendly laser on a target near it adds homing, as for the Iskander-M, GMLRS and guided shells."""
import json
from pathlib import Path
ROUNDS = {2009623: 'HJ-10', 2009651: 'QN-502', 2018321: 'CTL-181', 2018448: 'CH-901 (Blood Wolves)', 2019891: 'CH-901 (Type 100)'}
VANILLA = 218   # Missile Ballistic 500 IskanderM HE (laser guided)
GUIDANCE = ('TrajectoryType', 'Seeker', 'SeekerAngle', 'MaxSeekerDistance', 'CanReaquire', 'LaserGuided', 'TargetType', 'MuzzleVelocity', 'MaxSpeed',
            'Acceleration', 'BurnTime', 'RotationSpeed', 'MainEngineIgnitionDelay')
LAUNCHERS = {2009619: 'HJ-10', 2009647: 'QN-502', 2018322: 'CTL-181', 2018447: 'CH-901 (Blood Wolves)', 2019885: 'CH-901 (Type 100, Lynx Swarm)'}
NLOS = Path(__file__).resolve().parents[2] / 'mod/source/UserData/FreedomArrow/nlos.json'


def apply(t, g, ok, rec):
    A = t['AmmunitionsJson']; v = A[VANILLA]
    ok(v['Name'] == 'Missile Ballistic 500 IskanderM HE' and v['TrajectoryType'] == 300 and v['LaserGuided'] is True, 'vanilla Iskander-M round 218')
    want = {k: v[k] for k in GUIDANCE}
    ok({k: want[k] for k in ('Seeker', 'LaserGuided', 'TargetType', 'MaxSpeed')} == {'Seeker': 0, 'LaserGuided': True, 'TargetType': 1, 'MaxSpeed': 800.0}, ('Iskander-M guidance', want))
    W = t['WeaponsJson']; WA = t['WeaponAmmunitionsJson']
    for wid, name in LAUNCHERS.items():
        ok({r['AmmunitionId'] for r in WA.values() if r and r['WeaponId'] == wid} <= set(ROUNDS) and W[wid]['Type'] == 82, (name, wid, 'NLOS launcher, cruise type 82'))
        g.put('WeaponsJson', wid, {'Type': 83})
        ok(W[wid]['Type'] == 83 and W[wid]['IsVerticalLauncher'] is True, (name, 'ballistic launcher type 83'))
    before = {}
    for rid, name in ROUNDS.items():
        a = A[rid]
        ok(a['TrajectoryType'] in (200, 300), (name, rid, 'cruise path before'))
        before[rid] = {k: a[k] for k in GUIDANCE}
        rest = {k: x for k, x in a.items() if k not in GUIDANCE}
        g.put('AmmunitionsJson', rid, want)
        ok({k: A[rid][k] for k in GUIDANCE} == want and {k: x for k, x in A[rid].items() if k not in GUIDANCE} == rest, (name, 'Iskander-M guidance and flight, damage/range/everything else unchanged'))
    n = json.loads(NLOS.read_text())
    ok(sorted(n['ammunition']) == sorted(ROUNDS) or n['ammunition'] == [], ('nlos.json rounds', n['ammunition']))
    if n['ammunition']:
        n.update(version='0.9.7', ammunition=[], fire_weapons=[], fire_units=[], weapons=[], units={},
                 note='0.9.7 (Osama 24 Nov 2026 "it should just act like a cruise missile"): no NLOS rounds or units. The HJ-10, QN-502, CTL-181 and '
                      'CH-901 rounds use vanilla Iskander-M guidance (Fire Position, optional laser) (tools/pla-specs/nlos_cruise_1124.py); with an empty list NlosTrait.cs installs no hooks.')
        n.pop('type100_ch901', None)
        NLOS.write_text(json.dumps(n, indent=2, ensure_ascii=False) + '\n')
    ok(json.loads(NLOS.read_text())['ammunition'] == [] and json.loads(NLOS.read_text())['fire_units'] == [], 'nlos.json empty')
    rec['nlos_cruise_1124'] = {'rounds': ROUNDS, 'before': before, 'guidance': want}
    print('NLOS ISKANDER-M', {r: before[r] for r in ROUNDS})

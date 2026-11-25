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
Fire Position lands on the spot; a friendly laser on a target near it adds homing, as for the Iskander-M, GMLRS and guided shells.
Back to cruise (Osama 24 Nov 21:2x: "You made the NLOS missiles the Iskander ballistc missiles....not the cruise"): the rounds take the vanilla
Iskander-K cruise round 219 guidance and flight (path 200, no seeker, no laser, TargetType 1; speed/burn/turn equal the old HJ-10 values) and the
launchers stay Type 82 (cruise). No laser homing: no vanilla cruise round is laser guided.
Laser (Osama 21:3x "this is fine but now the missile doesn't follow the laser"): LaserGuided True on top of the Iskander-K guidance, and nlos.json
laser_hold lists the rounds: NlosTrait.LaserHoldAfter puts a round back on the cruise path when the game's laser handover (path 600) finds no
laser target, so Fire Position still dives on the spot and a lased unit is followed. No fire hook, no target picking.
Vanilla laser (Osama 21:4x "is that how lasers work in vanilla?"): no. In the game (LaserSeekerActivationSystem.InternalUpdate, 1.2.2.1 0x822980) a
laser-guided round looks for allied laser spots (LaserDesignatorSystem.LaserSpots) inside its own seeker cone: half-angle SeekerAngle x 0.5, reach
MaxSeekerDistance (GroundRange when Seeker != 0), then ActivateLaserSeeker. The Iskander-K copy had SeekerAngle 0 / MaxSeekerDistance 0 = blind.
So each round keeps its own pre-change seeker cone (HJ-10 90 deg / 800, QN-502 and CH-901 90 / 700, CTL-181 90 / 900) and laser_hold and the
custom lock code are gone: pure vanilla laser guidance.
Undone (Osama 22:1x "the NLOS are flying away after being laser designated"): with a cone the game hands the round to its laser path
(600) with no target entity and it flies off (as in 0.9.5-dev.44). Back to cone 0/0 + laser_hold + the custom lock (c859f743), which locked at 21:4x.
Agility (Osama 21:5x "can we increase missile agility?"): RotationSpeed 45 -> 120 deg/s, the vanilla Hellfire 164 value."""
import json
from pathlib import Path
ROUNDS = {2009623: 'HJ-10', 2009651: 'QN-502', 2018321: 'CTL-181', 2018448: 'CH-901 (Blood Wolves)', 2019891: 'CH-901 (Type 100)'}
VANILLA = 219   # Missile Cruise IskanderK HE Guided
GUIDANCE = ('TrajectoryType', 'Seeker', 'SeekerAngle', 'MaxSeekerDistance', 'CanReaquire', 'LaserGuided', 'TargetType', 'MuzzleVelocity', 'MaxSpeed',
            'Acceleration', 'BurnTime', 'RotationSpeed', 'MainEngineIgnitionDelay')
LAUNCHERS = {2009619: 'HJ-10', 2009647: 'QN-502', 2018322: 'CTL-181', 2018447: 'CH-901 (Blood Wolves)', 2019885: 'CH-901 (Type 100, Lynx Swarm)'}
NLOS = Path(__file__).resolve().parents[2] / 'mod/source/UserData/FreedomArrow/nlos.json'


def apply(t, g, ok, rec):
    A = t['AmmunitionsJson']; v = A[VANILLA]
    ok(v['Name'] == 'Missile Cruise IskanderK HE Guided' and v['TrajectoryType'] == 200 and v['LaserGuided'] is False, 'vanilla Iskander-K cruise round 219')
    want = {k: v[k] for k in GUIDANCE}
    ok({k: want[k] for k in ('Seeker', 'LaserGuided', 'TargetType', 'MaxSpeed', 'CanReaquire')} == {'Seeker': 0, 'LaserGuided': False, 'TargetType': 1, 'MaxSpeed': 300.0, 'CanReaquire': False}, ('Iskander-K cruise guidance', want))
    want['LaserGuided'] = True   # follows a friendly laser (laser_hold in nlos.json keeps the cruise path when nothing is lased)
    # turn rate (Osama 24 Nov 21:5x "can we increase missile agility? it seems to lock but it doesn't follow"): the Iskander-K 45 deg/s turns a
    # 300 u/s round on a ~380 u radius, but the laser lock comes at ~400-600 u. 120 = the vanilla Hellfire 164 laser missile.
    want['RotationSpeed'] = 120.0
    W = t['WeaponsJson']; WA = t['WeaponAmmunitionsJson']
    for wid, name in LAUNCHERS.items():
        ok({r['AmmunitionId'] for r in WA.values() if r and r['WeaponId'] == wid} <= set(ROUNDS) and W[wid]['Type'] == 82, (name, wid, 'NLOS launcher, cruise type 82'))
        ok(W[wid]['IsVerticalLauncher'] is True, (name, 'vertical cruise launcher (Type 82, unchanged)'))
    before = {}
    for rid, name in ROUNDS.items():
        a = A[rid]
        ok(a['TrajectoryType'] in (200, 300), (name, rid, 'cruise path before'))
        before[rid] = {k: a[k] for k in GUIDANCE}
        rest = {k: x for k, x in a.items() if k not in GUIDANCE}
        g.put('AmmunitionsJson', rid, want)
        ok({k: A[rid][k] for k in GUIDANCE} == want and {k: x for k, x in A[rid].items() if k not in GUIDANCE} == rest, (name, 'Iskander-K cruise guidance and flight, damage/range/everything else unchanged'))
    n = json.loads(NLOS.read_text())
    ok(sorted(n['ammunition']) == sorted(ROUNDS) or n['ammunition'] == [], ('nlos.json rounds', n['ammunition']))
    if n['ammunition']:
        n.update(version='0.9.7', ammunition=[], fire_weapons=[], fire_units=[], weapons=[], units={},
                 note='0.9.7 (Osama 24 Nov 2026 "it should just act like a cruise missile"): no NLOS rounds or units. The HJ-10, QN-502, CTL-181 and '
                      'CH-901 rounds use vanilla Iskander-K cruise guidance (Fire Position only) (tools/pla-specs/nlos_cruise_1124.py); with an empty list NlosTrait.cs installs no hooks.')
        n.pop('type100_ch901', None)
        NLOS.write_text(json.dumps(n, indent=2, ensure_ascii=False) + '\n')
    n = json.loads(NLOS.read_text())
    if sorted(n.get('laser_hold', [])) != sorted(ROUNDS):
        n['laser_hold'] = sorted(ROUNDS)
        n['note'] += ' 21:3x: laser_hold = these rounds (LaserGuided; NlosTrait.LaserHoldAfter keeps the cruise path when no laser target is locked).'
        NLOS.write_text(json.dumps(n, indent=2, ensure_ascii=False) + '\n')
    n = json.loads(NLOS.read_text())
    ok(n['ammunition'] == [] and n['fire_units'] == [] and sorted(n['laser_hold']) == sorted(ROUNDS), 'nlos.json: no NLOS rounds, laser_hold = the 5 rounds')
    rec['nlos_cruise_1124'] = {'rounds': ROUNDS, 'before': before, 'guidance': want}
    print('NLOS ISKANDER-K CRUISE', {r: before[r] for r in ROUNDS})

"""NLOS missiles act like vanilla cruise missiles (Osama 24 Nov 2026 17:1x-17:2x PST, bugs thread 1573561286803980289: "HJ-10 is still bugged, now it
seeks targets on its own even if it doesn't see", "they shouldn't track", "it should just act like a cruise missile, why is that so hard?").
His 0.9.6 log (17:08-17:13): all 20 NLOS launches were at a ground spot, and NlosTrait.cs then locked each missile on the enemy nearest that spot
(1-58 away) with no visibility check, and held the lock. Fix = vanilla cruise guidance, the Iskander-K 219 / Tomahawk 35 pattern:
Seeker 0, SeekerAngle 0, MaxSeekerDistance 0, CanReaquire False, LaserGuided False, TargetType 1 (ground position only: fired with Fire Position,
flies to the spot and dives, no auto fire, no tracking). Damage, penetration, range, speed and flight stay. nlos.json lists no rounds, units or
launchers any more, so NlosTrait.cs installs no hooks (empty list)."""
import json
from pathlib import Path
ROUNDS = {2009623: 'HJ-10', 2009651: 'QN-502', 2018321: 'CTL-181', 2018448: 'CH-901 (Blood Wolves)', 2019891: 'CH-901 (Type 100)'}
VANILLA = 219   # Missile Cruise IskanderK HE Guided
GUIDANCE = ('Seeker', 'SeekerAngle', 'MaxSeekerDistance', 'CanReaquire', 'LaserGuided', 'TargetType')
NLOS = Path(__file__).resolve().parents[2] / 'mod/source/UserData/FreedomArrow/nlos.json'


def apply(t, g, ok, rec):
    A = t['AmmunitionsJson']; v = A[VANILLA]
    ok(v['Name'] == 'Missile Cruise IskanderK HE Guided' and v['TrajectoryType'] == 200, 'vanilla Iskander-K cruise round 219')
    want = {k: v[k] for k in GUIDANCE}
    ok(want == {'Seeker': 0, 'SeekerAngle': 0.0, 'MaxSeekerDistance': 0.0, 'CanReaquire': False, 'LaserGuided': False, 'TargetType': 1}, ('vanilla cruise guidance', want))
    before = {}
    for rid, name in ROUNDS.items():
        a = A[rid]
        ok(a['TrajectoryType'] == 200, (name, rid, 'cruise path'))
        before[rid] = {k: a[k] for k in GUIDANCE}
        rest = {k: x for k, x in a.items() if k not in GUIDANCE}
        g.put('AmmunitionsJson', rid, want)
        ok({k: A[rid][k] for k in GUIDANCE} == want and {k: x for k, x in A[rid].items() if k not in GUIDANCE} == rest, (name, 'vanilla cruise guidance, everything else unchanged'))
    n = json.loads(NLOS.read_text())
    ok(sorted(n['ammunition']) == sorted(ROUNDS) or n['ammunition'] == [], ('nlos.json rounds', n['ammunition']))
    if n['ammunition']:
        n.update(version='0.9.7', ammunition=[], fire_weapons=[], fire_units=[], weapons=[], units={},
                 note='0.9.7 (Osama 24 Nov 2026 "it should just act like a cruise missile"): no NLOS rounds or units. The HJ-10, QN-502, CTL-181 and '
                      'CH-901 rounds use vanilla cruise guidance (tools/pla-specs/nlos_cruise_1124.py); with an empty list NlosTrait.cs installs no hooks.')
        n.pop('type100_ch901', None)
        NLOS.write_text(json.dumps(n, indent=2, ensure_ascii=False) + '\n')
    ok(json.loads(NLOS.read_text())['ammunition'] == [] and json.loads(NLOS.read_text())['fire_units'] == [], 'nlos.json empty')
    rec['nlos_cruise_1124'] = {'rounds': ROUNDS, 'before': before, 'guidance': want}
    print('NLOS CRUISE', {r: before[r] for r in ROUNDS})

"""Helicopter ATGMs turn at least 160 deg/s (Osama 27 Nov 2026 16:1x PST, bugs thread 1573561286803980289: "Our current solution is to make all
helo atgms 160 degrees/second at least").
Why: Bay of Winds 3v3, 26 Nov 21:55 PST (match 9926322): a Z-10K fired 6 AKD-10 at a moving M1A2 SEP; the guidance roll was 100 % for each
and the SEP stayed at 14 HP. AKD-10 is an exact copy of the vanilla AGM-114K Hellfire (top-attack path 110, semi-active seeker, 120 deg/s),
so this is vanilla missile behaviour, not a mod bug. The vanilla AGM-114L / JAGM already turn at 160.
Every guided anti-vehicle round (Seeker set, HEAT, can hit vehicles, damage >= 5, penetration >= 300) that a helicopter carries gets
RotationSpeed max(current, 160). Kh-31P (anti-radiation, 150) is not an ATGM and is left alone. Shared rows change for every user:
AKD-10 and AKD-9 are also on the Wing Loong drone."""
FLOOR = 160.0
EXPECT = {80: '9M114M', 123: '9M120M', 131: '9M133M-2', 2017077: 'HJ-8', 733: 'Kh-25M', 2000454: 'TOW-2A', 83: 'Vikhr',
          164: 'AGM-114K Hellfire', 2017053: 'AKD-10', 2019088: 'AKD-11', 2017071: 'AKD-9'}
SKIP = {400}   # Kh-31P anti-radiation


def apply(t, g, ok, rec):
    U, A = t['Units'], t['AmmunitionsJson']
    users = {}
    for r in t['WeaponAmmunitionsJson'].values():
        if r and U.get(r['UnitId']) and U[r['UnitId']].get('DisplayInArmory'): users.setdefault(r['AmmunitionId'], set()).add(r['UnitId'])
    found = {}
    for a, us in users.items():
        x = A.get(a)
        if not x or not x.get('Seeker') or x.get('ArmorTargeted') != 2 or not (int(x.get('TargetType') or 0) & 4): continue
        if x.get('Damage', 0) < 5 or x.get('PenetrationAtMinRange', 0) < 300: continue
        if not any(U[u]['Type'] == 8 for u in us) or a in SKIP: continue
        if float(x.get('RotationSpeed') or 0) < FLOOR: found[a] = x['HUDName'].strip()
    ok(found == EXPECT, ('helicopter ATGMs below 160', found))
    out = {}
    for a, name in EXPECT.items():
        out[name] = [A[a]['RotationSpeed'], FLOOR]
        g.put('AmmunitionsJson', a, {'RotationSpeed': FLOOR})
        ok(A[a]['RotationSpeed'] == FLOOR, (name, 'turn 160'))
    rec['heli_atgm_turn_1127'] = out
    print('HELI ATGM TURN', out)

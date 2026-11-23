"""PL-15C removed: every PL-15C becomes a PL-15 (Osama 23 Nov 2026 01:5x-02:0x PST, thread 1567745029781454889: "I want to get rid of all PL-15C.
We should replace them with PL-15 and remove overlapping loadouts ... whereever we replace PL-15C's with PL-15's we want to increase their price";
on the proposal Doc 1kNAPyBk0vK8DRY8JY3JhS3VXlJvAuWzoZUQKojZlgPA: "Make these changes and yes call it heavy cap").
The PL-15C round 2016390 is the PL-15 round 2016398 with 4000 m range instead of 4500 (only Name, HUDName, HUDIcon and the two ranges differ).
- The 11 WeaponAmmunitions rows with 2016390 (J-36, J-50, J-35, J-31, MD-22, FH-97A) take 2016398. Their launcher weapons take the PL-15 HUD name and icon.
- Each loadout that keeps a swapped missile costs +5 per missile (the PL-12 -> PL-15 step on these planes: Light CAP 70 -> 90 for 4).
- "Heavy CAP (PL-15C)" is renamed "Heavy CAP (PL-15)" on the J-35, J-31 and J-50.
- MD-22 31012 and FH-97A 31033 "Heavy CAP (PL-15C)" become exact copies of their "Light CAP (PL-15)" (31009, 31030) and are removed."""
import collections

C, P = 2016390, 2016398
PER_MISSILE = 5
# option: (unit, UIName before, Cost before, PL-15C missiles, UIName after)
KEEP = {24599: (921, 'Heavy CAP (PL-15C)', 105, 4, 'Heavy CAP (PL-15)'),
        24603: (1251, 'Heavy CAP (PL-15C)', 105, 4, 'Heavy CAP (PL-15)'),
        24608: (929, 'Anti-armor', 0, 4, None),
        31028: (929, 'Heavy strike', 55, 4, None),
        24395: (944, 'Heavy CAP (PL-15C)', 170, 8, 'Heavy CAP (PL-15)'),
        24611: (944, 'Light strike (4x LS-6 500kg)', 125, 2, None),
        24609: (944, 'Light strike (2x LS-6 500kg)', 135, 4, None)}
DROP = {31012: (976, 31009), 31033: (1253, 31030)}   # removed option: (unit, kept twin)


def apply(t, g, ok, rec):
    A, W, TW, WA, O, M = (t[k] for k in ('AmmunitionsJson', 'WeaponsJson', 'TurretWeaponsJson', 'WeaponAmmunitionsJson', 'OptionsJson', 'ModificationsJson'))
    diff = {k for k in set(A[C]) | set(A[P]) if A[C].get(k) != A[P].get(k)}
    ok(diff == {'Id', 'Name', 'HUDName', 'HUDIcon', 'LowAltRange', 'HighAltRange'} and A[C]['HighAltRange'] == 4000.0 and A[P]['HighAltRange'] == 4500.0,
       ('PL-15C = PL-15 with 4000 m range', sorted(diff)))
    rows = [r for r in WA.values() if r and r.get('AmmunitionId') == C]
    ok(len(rows) == 11 and {r['UnitId'] for r in rows} == {929, 944, 921, 1251, 976, 1253}, ('PL-15C rows', len(rows)))
    tw = collections.defaultdict(list)
    for r in TW.values():
        if r: tw[r['TurretId']].append(r['WeaponId'])

    def content(o):
        uid, out = M[o['ModificationId']]['UnitId'], collections.Counter()
        for i in range(21):
            for w in tw.get(o.get(f'Turret{i}Id') or 0, []):
                for r in WA.values():
                    if r and r['UnitId'] == uid and r['WeaponId'] == w: out[r['AmmunitionId']] += r['Quantity']
        return out
    before = {oid: content(O[oid]) for oid in [*KEEP, *DROP]}
    with_c = sorted(o['Id'] for o in O.values() if o and o['ModificationId'] in M and M[o['ModificationId']]['UnitId'] in {r['UnitId'] for r in rows} and content(o)[C])
    ok(with_c == sorted([*KEEP, *DROP]), ('loadouts with PL-15C', with_c))
    for oid, (uid, name, cost, n, _) in KEEP.items():
        ok(M[O[oid]['ModificationId']]['UnitId'] == uid and O[oid]['UIName'] == name and O[oid]['Cost'] == cost and before[oid][C] == n, (oid, name, 'before'))
    weapons = sorted({r['WeaponId'] for r in rows})
    ok(all(W[w]['HUDName'] == 'PL-15C' for w in weapons) and W[2016396]['HUDName'] == 'PL-15', ('PL-15C launchers', weapons))
    for r in rows: g.put('WeaponAmmunitionsJson', r['Id'], {'AmmunitionId': P})
    for w in weapons: g.put('WeaponsJson', w, {'HUDName': W[2016396]['HUDName'], 'HUDIcon': W[2016396]['HUDIcon']})
    for oid, (uid, name, cost, n, new) in KEEP.items():
        g.put('OptionsJson', oid, {'Cost': cost + PER_MISSILE * n, **({'UIName': new} if new else {})})
    for oid, (uid, twin) in DROP.items():
        ok(M[O[oid]['ModificationId']]['UnitId'] == uid and O[twin]['ModificationId'] == O[oid]['ModificationId'] and not O[oid]['IsDefault']
           and content(O[oid]) == content(O[twin]) == collections.Counter({P: 4}) and O[twin]['UIName'] == 'Light CAP (PL-15)' and O[twin]['Cost'] == 90,
           (oid, 'exact copy of', twin))
        g.remove('OptionsJson', oid)
    ok(not any(r and r.get('AmmunitionId') == C for r in WA.values()) and not any(O.get(o) for o in DROP), 'no PL-15C rows, duplicates gone')
    ok(not any(W[r['WeaponId']]['HUDName'] == 'PL-15C' for r in WA.values() if r), 'no PL-15C launcher name on any unit')
    for oid, (uid, name, cost, n, new) in KEEP.items():
        want = collections.Counter(before[oid]); want[P] += want.pop(C)
        ok(content(O[oid]) == want and O[oid]['Cost'] == cost + PER_MISSILE * n and O[oid]['UIName'] == (new or name), (oid, 'after'))
    for mid in {O[o]['ModificationId'] for o in KEEP}:
        opts = [o for o in O.values() if o and o['ModificationId'] == mid]
        sets = [tuple(sorted(content(o).items())) for o in opts]
        ok(len(sets) == len(set(sets)) and len({o['UIName'] for o in opts}) == len(opts), (M[mid]['UnitId'], 'weapon package: no duplicate loadouts or names'))
    rec['pl15c_to_pl15'] = {'rows': len(rows), 'weapons': weapons, 'prices': {o: [v[2], v[2] + PER_MISSILE * v[3]] for o, v in KEEP.items()},
                            'renamed': {o: v[4] for o, v in KEEP.items() if v[4]}, 'removed': DROP}
    print('PL-15C -> PL-15', rec['pl15c_to_pl15'])

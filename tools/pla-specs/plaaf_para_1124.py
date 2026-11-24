"""PLAAF infantry can parachute (SmallWD report, posted by Osama 24 Nov 2026 01:3x PST, bugs thread 1573561286803980289: "These chinese PLAAF
infantry units should have PARA tag"). Air-drop is Mobility.IsAirDroppable, as on the vanilla Airborne's 'Infantry 18kmh Airdrop' (190).
The six squads below each move on their own mobility row with the flag off; Thunder Gods (1143) already has it."""
SQUADS = ('PLA Airborne Riflemen MobilityJson', 'PLA Airborne HJ-12 Team MobilityJson', 'PLA Airborne PF-98 Fire Support MobilityJson',
          'PLA Airborne QLU-11 Precision Team MobilityJson', 'PLA Airborne HN-6 Patrol MobilityJson', 'PLA Air Assault Raiders MobilityJson')


def apply(t, g, ok, rec):
    M, UP = t['MobilityJson'], t['UnitPropulsionsJson']
    rows = {n: [i for i, m in M.items() if m and m.get('Name') == n] for n in SQUADS}
    ok(all(len(v) == 1 for v in rows.values()), ('PLAAF infantry mobility rows', {n: len(v) for n, v in rows.items()}))
    ok(M[190].get('IsAirDroppable') is True, 'vanilla Infantry 18kmh Airdrop is air-droppable')
    out = {}
    for n, (mid,) in rows.items():
        users = sorted({r['UnitId'] for r in UP.values() if r and r['MobilityId'] == mid})
        ok(len(users) == 1, (n, 'used by one squad only', users))
        g.put('MobilityJson', mid, {'IsAirDroppable': True})
        ok(M[mid]['IsAirDroppable'] is True, (n, 'air-droppable'))
        out[mid] = users[0]
    rec['plaaf_para_1124'] = out
    print('PLAAF PARA', out)

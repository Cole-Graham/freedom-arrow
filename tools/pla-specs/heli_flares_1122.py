"""Lateralus 22 Nov 2026 19:4x PST, thread 1568104480459722894: "queue the fix for helicopters that only have 10 flares intead of 15".
Called from apply_0_9_4_dev1.py.
Freedom Arrow gives helicopter flare rows 15 decoys (vanilla 10). Three helicopters still linked FA copies that kept 10:
- Z-10K Recon (1130) and Z-10 Recon (1131): row 2011655 "PLA Z-10K Recon AbilitiesJson".
- Mi-8 Cargo (1227): row 2014588 "ECM Heli 10 Default".
Each copy is the same as an existing 15-flare row in every field except DecoyQuantity, so the links move to those rows (ability-row-reuse rule):
2011655 -> 2000770 "ECM Heli 20 Default + Laser" (ECM 0.8, laser 1500), 2014588 -> 22 "ECM Heli 10 Default" (ECM 0.9). No option of these units sets
an ability. The old rows stay in the table, unused."""

IGNORE = {'Id', 'Name'}


def apply(t, g, ok, rec):
    U, AB, UAB = t['Units'], t['AbilitiesJson'], t['UnitAbilitiesJson']
    O, M = t['OptionsJson'], t['ModificationsJson']
    moves = ((2011655, 2000770, (1130, 1131)), (2014588, 22, (1227,)))
    for old, new, units in moves:
        a, b = AB[old], AB[new]
        diff = {k for k in set(a) | set(b) if k not in IGNORE and a.get(k) != b.get(k)}
        ok(diff == {'DecoyQuantity'} and a['DecoyQuantity'] == 10 and b['DecoyQuantity'] == 15 and b.get('IsDecoy'), (old, new, 'differ only in flares 10 -> 15', sorted(diff)))
        links = [r for r in UAB.values() if r and r.get('AbilityId') == old]
        ok(sorted(r['UnitId'] for r in links) == sorted(units), (old, 'linked by', sorted(r['UnitId'] for r in links)))
        mods = {m['Id'] for m in M.values() if m and m.get('UnitId') in units}
        ok(not any(o.get(f'Ability{i}Id') for o in O.values() if o and o.get('ModificationId') in mods for i in (1, 2, 3)), (units, 'no option sets an ability'))
        for r in links:
            g.put('UnitAbilitiesJson', r['Id'], {'AbilityId': new})
    ok([U[u]['HUDName'].strip() for u in (1130, 1131, 1227)] == ['Z-10K Recon', 'Z-10 Recon', 'Mi-8 Cargo'], 'unit names')
    # Guard: every helicopter (Units.Type 8) with a flare row now has 15 flares.
    heli = {i for i, u in U.items() if u and u.get('Type') == 8}
    short = sorted({(r['UnitId'], AB[r['AbilityId']]['DecoyQuantity']) for r in UAB.values()
                    if r and r.get('UnitId') in heli and AB.get(r['AbilityId'], {}).get('IsDecoy') and AB[r['AbilityId']].get('DecoyQuantity') != 15})
    ok(not short, ('helicopters with a flare count other than 15', short))
    rec['heli_flares_1122'] = {'Z-10K Recon 1130, Z-10 Recon 1131': [2011655, 2000770], 'Mi-8 Cargo 1227': [2014588, 22], 'flares': [10, 15]}

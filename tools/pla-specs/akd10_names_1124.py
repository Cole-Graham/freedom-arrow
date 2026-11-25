"""Air-launched HJ-10 shown as AKD-10 (Osama 24 Nov 2026 16:0x PST, thread "China cosmetic work": "Helicopters HJ-10 renamed akd-10").
The helicopter and Wing Loong launchers are already AKD-10 rows by Name ('PLA air AKD-10 x4', 'PLA Z-20 AKD-10 611', ...), but the
unit card shows HUDName 'HJ-10'. HUDName 'HJ-10' -> 'AKD-10' on every weapon whose Name has 'AKD-10', and on the round 'PLA air AKD-10'
(one row shared by the helicopters and the Wing Loong). Ground HJ-10 rows (HJ-10 NLOS/FNF unit, AFT-10) keep their name. Names only."""
OLD, NEW = 'HJ-10', 'AKD-10'


def apply(t, g, ok, rec):
    W, A, WA, U = t['WeaponsJson'], t['AmmunitionsJson'], t['WeaponAmmunitionsJson'], t['Units']
    ws = sorted(i for i, r in W.items() if r and 'AKD-10' in (r.get('Name') or '') and r.get('HUDName') == OLD)
    am = sorted(i for i, r in A.items() if r and r.get('Name') == 'PLA air AKD-10' and r.get('HUDName') == OLD)
    ok(len(ws) == 10 and len(am) == 1, ('AKD-10 rows shown as HJ-10: 10 launchers + 1 round', ws, am))
    users = sorted({r['UnitId'] for r in WA.values() if r and (r['WeaponId'] in ws or r['AmmunitionId'] in am)})
    ok(all(U[u].get('Type') in (8, 16) for u in users), ('only helicopters (8) and the Wing Loong (16) use them', users))
    for i in ws: g.put('WeaponsJson', i, {'HUDName': NEW})
    for i in am: g.put('AmmunitionsJson', i, {'HUDName': NEW})
    ok(all(W[i]['HUDName'] == NEW for i in ws) and all(A[i]['HUDName'] == NEW for i in am), 'renamed AKD-10')
    ground = [i for i, r in list(W.items()) + list(A.items()) if r and (r.get('HUDName') or '').startswith(OLD)]
    ok(all(not any(U.get(r['UnitId'], {}).get('Type') in (8, 16) for r in WA.values() if r and (r['WeaponId'] == i or r['AmmunitionId'] == i)) for i in ground),
       'no air unit still shows HJ-10')
    rec['akd10_names_1124'] = {'weapons': ws, 'round': am, 'units': [(u, U[u]['Name']) for u in users]}
    print('AKD-10 NAMES', rec['akd10_names_1124'])

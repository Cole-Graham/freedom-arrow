"""QN-202 (Osama 25 Nov 2026 00:4x PST, thread "blue dragons": "QN-202 should use javelin model, and should have 7 damage and 70mm
penetration and 18 rounds"). Weapon 2014236 'PLA infantry QN-202': ModelFileName Konkurs -> Javelin (the vanilla Javelin row 62 model, same
weapon type 80). Round 2014237: Damage -> 7, every Penetration* field -> 70. Carried rounds: every WeaponAmmunitions row of 2014236 -> 18."""


def apply(t, g, ok, rec):
    W, A, WA = t['WeaponsJson'], t['AmmunitionsJson'], t['WeaponAmmunitionsJson']
    WID, AID = 2014236, 2014237
    ok(W[62]['ModelFileName'] == 'Javelin' and W[62]['Type'] == W[WID]['Type'] == 80, 'vanilla Javelin 62 model, same type as QN-202')
    ammo = sorted({r['AmmunitionId'] for r in WA.values() if r and r['WeaponId'] == WID})
    ok(W[WID]['HUDName'] == 'QN-202' and ammo == [AID] and A[AID]['Name'].startswith('PLA infantry QN-202'), ('QN-202 rows', W[WID]['HUDName'], ammo, A[AID]['Name']))
    pen = sorted(k for k in A[AID] if k.startswith('Penetration'))
    before = {'model': W[WID]['ModelFileName'], 'damage': A[AID]['Damage'], 'pen': {k: A[AID][k] for k in pen},
              'rounds': sorted({r['Quantity'] for r in WA.values() if r and r['WeaponId'] == WID})}
    g.put('WeaponsJson', WID, {'ModelFileName': 'Javelin'})
    g.put('AmmunitionsJson', AID, {'Damage': 7.0, **{k: 70.0 for k in pen}})
    rows = sorted(i for i, r in WA.items() if r and r['WeaponId'] == WID)
    for i in rows: g.put('WeaponAmmunitionsJson', i, {'Quantity': 18})
    ok(rows and all(WA[i]['Quantity'] == 18 for i in rows) and A[AID]['Damage'] == 7.0 and all(A[AID][k] == 70.0 for k in pen), 'QN-202 7 dmg / 70 pen / 18 rounds')
    rec['qn202_javelin'] = {'before': before, 'units_rows': len(rows), 'pen_fields': pen}
    print('QN-202', rec['qn202_javelin'])

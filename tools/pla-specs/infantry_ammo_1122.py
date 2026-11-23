"""China infantry ammunition (Lateralus 22 Nov 2026 17:1x PST, thread 1572962048705429598: "QCW-05 is a Submachine gun and it only has 120 rounds,
it should have the same amount of ammunition as the MP5SD6", "QBU-191 should be increased from 60 -> 100 rounds").
WeaponAmmunitions.Quantity is the per-soldier amount (vanilla rifles keep one value for 1-7 carriers; FA doubled the vanilla infantry rows).
The MP5SD6 on the only fielded card that carries it (528 DLC2 KNT) is 160 (vanilla 80 x 2); the QCW-05 rows (weapon 2013349, 6 units) were 20,
the vanilla pilot/crew MP5SD6 value. QBU-191 (weapon 2004000, 43 rows) 60 -> 100. Called from apply_0_9_4_dev1.py."""


def apply(t, g, ok, rec):
    W, WA = t['WeaponsJson'], t['WeaponAmmunitionsJson']
    ok(W[508]['HUDName'].strip() == 'MP5SD6' and W[2013349]['HUDName'].strip() == 'QCW-05' and W[2004000]['HUDName'].strip() == 'QBU-191', 'MP5SD6 / QCW-05 / QBU-191 weapon ids')
    mp5 = WA[3034]
    ok(mp5['UnitId'] == 528 and mp5['WeaponId'] == 508 and mp5['Quantity'] == 160, ('KNT MP5SD6 row', mp5))
    out = {}
    for wid, old, new in ((2013349, 20, mp5['Quantity']), (2004000, 60, 100)):
        rows = [r for r in WA.values() if r and r['WeaponId'] == wid]
        ok(rows and all(r['Quantity'] == old for r in rows), (wid, 'rows all at', old, sorted({r['Quantity'] for r in rows})))
        for r in rows:g.put('WeaponAmmunitionsJson', r['Id'], {'Quantity': new})
        out[W[wid]['HUDName'].strip()] = {'rows': len(rows), 'quantity': [old, new]}
    ok(out['QCW-05']['rows'] == 6 and out['QBU-191']['rows'] == 43, ('row counts', out))
    rec['infantry_ammo_1122'] = out

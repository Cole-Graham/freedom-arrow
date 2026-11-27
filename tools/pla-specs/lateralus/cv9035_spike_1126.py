"""CV-9035 Mk.IV: Spike LR ammunition 2 -> 4 (Lateralus 26 Nov 2026 20:3x PST, thread 1572962048705429598, "queue it up").
The Mk.IV modernisation option (2196, +50) of CV-9035 card 498 mounts the Spike LR launcher (weapon 714); its ammo row is WeaponAmmunitions 3083,
the only Spike row on the unit. Vehicle weapon: Quantity is the vehicle's missile count. Existing rows only: no ID moves."""

CV9035, SPIKE_LR, WA_ROW = 498, 714, 3083


def apply(t, g, ok, rec):
    U, W, WA = t['Units'], t['WeaponsJson'], t['WeaponAmmunitionsJson']
    r = WA[WA_ROW]
    ok(U[CV9035]['HUDName'].strip() == 'CV-9035' and W[SPIKE_LR]['HUDName'] == 'Spike LR', 'CV-9035 Spike LR rows')
    ok(r['UnitId'] == CV9035 and r['WeaponId'] == SPIKE_LR and r['Quantity'] == 2, ('CV-9035 Spike LR ammo before', r))
    ok([x['Id'] for x in WA.values() if x and x['UnitId'] == CV9035 and 'Spike' in W[x['WeaponId']]['HUDName']] == [WA_ROW], 'one Spike row on CV-9035')
    g.put('WeaponAmmunitionsJson', WA_ROW, {'Quantity': 4})
    ok(WA[WA_ROW]['Quantity'] == 4, 'CV-9035 Mk.IV Spike LR 4')
    rec['cv9035_spike_1126'] = {'CV-9035 Mk.IV Spike LR ammo': '2 -> 4'}

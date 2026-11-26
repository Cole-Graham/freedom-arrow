"""Russian infantry prices and VDV PKP launcher ammo (Lateralus 26 Nov 2026 15:1x PST, thread 1572962048705429598, "queue it up").
- Gvardii Motostrelki (133): 60 -> 65 points. Motopekhota (60): 55 -> 60. Shturmoviki (401): 50 -> 55. None of them has a loadout option.
- VDV PKP (108): RPG-7D3 (weapon 143) ammunition 4 -> 6 (WeaponAmmunitions 4129). Unit 114, the other RPG-7D3 squad, is unchanged.
Existing rows only: no row is made, so no ID moves."""

PRICES = {133: ('Gvardii Motostrelki', 60, 65), 60: ('Motopekhota', 55, 60), 401: ('Shturmoviki', 50, 55)}
VDV_PKP, RPG7D3, WA_ROW = 108, 143, 4129


def apply(t, g, ok, rec):
    U, WA = t['Units'], t['WeaponAmmunitionsJson']
    for u, (name, old, new) in PRICES.items():
        ok(U[u]['HUDName'].strip() == name and U[u]['Cost'] == old and not U[u].get('OriginalCost'), ('price before', u, U[u]['HUDName'], U[u]['Cost']))
        g.put('Units', u, {'Cost': new})
    r = WA[WA_ROW]
    ok(r['UnitId'] == VDV_PKP and r['WeaponId'] == RPG7D3 and r['Quantity'] == 4, ('VDV PKP RPG-7D3 row', r))
    g.put('WeaponAmmunitionsJson', WA_ROW, {'Quantity': 6})
    ok(all(U[u]['Cost'] == new for u, (_, _, new) in PRICES.items()) and WA[WA_ROW]['Quantity'] == 6, 'infantry prices 1126 applied')
    rec['infantry_prices_1126'] = {**{name: f'{old} -> {new}' for name, old, new in PRICES.values()}, 'VDV PKP RPG-7D3 ammo': '4 -> 6'}
    print('INFANTRY PRICES', rec['infantry_prices_1126'])

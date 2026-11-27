"""Lynx 81mm Mortar HEAT supply weight (Osama 27 Nov 2026 04:0x PST, thread 1567745029781454889: "supply weight 30kg for all rounds").
The Lynx 81mm Mortar (1434)'s direct-fire round is the vanilla 82mm HEAT (135, 14 kg), which the MT-LB and CS/VP16B Mortar also fire.
No existing row is the 82mm HEAT at 30 kg, so the Lynx gets a copy of 135 with SupplyCost 30 and its weapon-ammo row 2021327 points at it.
Everything else is vanilla's. In the plb ID block (new rows are refused after the reserved-ID scope); the last plb section."""
MORTAR, WA_ROW, HEAT = 1434, 2021327, 135


def apply(t, g, ok, rec):
    U, A, WA = t['Units'], t['AmmunitionsJson'], t['WeaponAmmunitionsJson']
    ok(U[MORTAR]['HUDName'] == 'Lynx 81mm Mortar' and WA[WA_ROW]['UnitId'] == MORTAR and WA[WA_ROW]['AmmunitionId'] == HEAT and A[HEAT]['SupplyCost'] == 14.0,
       ('Lynx 81mm HEAT row on vanilla 135', WA[WA_ROW]['AmmunitionId'], A[HEAT].get('SupplyCost')))
    ok(not any(a and a.get('HUDName') == A[HEAT]['HUDName'] and a.get('SupplyCost') == 30.0 for a in A.values()), 'no 82mm HEAT at 30 kg to reuse')
    n = g.add('AmmunitionsJson', A[HEAT], {'Name': 'PLA Lynx 81mm Mortar 82mm HEAT', 'SupplyCost': 30.0})
    g.put('WeaponAmmunitionsJson', WA_ROW, {'AmmunitionId': n})
    ok(A[HEAT]['SupplyCost'] == 14.0 and {r['UnitId'] for r in WA.values() if r and r['AmmunitionId'] == HEAT} and MORTAR not in {r['UnitId'] for r in WA.values() if r and r['AmmunitionId'] == HEAT},
       'vanilla 135 unchanged, still used by the other units, Lynx off it')
    rec['pla_light_brigade_lynx81_heat_1127'] = {'round': n, 'supply': [14, 30]}
    print('LYNX 81 HEAT', rec['pla_light_brigade_lynx81_heat_1127'])

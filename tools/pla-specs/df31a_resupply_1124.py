"""DF-31A nuclear warhead resupply time 600 -> 6000 (Osama 24 Nov 2026 11:4x PST, thread 1567745029781454889: "DF-31A resupply time 6000 (you have
to buy a new one, not rearm)"). Ammo 2010399 'DF-31A nuclear warhead', used only by the DF-31A Nuclear card (unit 1032, 1 round). SupplyCost
(30000) and everything else unchanged."""
AMMO = 2010399


def apply(t, g, ok, rec):
    A, WA, U = t['AmmunitionsJson'], t['WeaponAmmunitionsJson'], t['Units']
    users = sorted({U[r['UnitId']]['HUDName'] for r in WA.values() if r and r['AmmunitionId'] == AMMO})
    ok(A[AMMO]['HUDName'] == 'DF-31A nuclear warhead' and A[AMMO]['ResupplyTime'] == 600.0 and users == ['DF-31A Nuclear'], ('DF-31A warhead', users))
    g.put('AmmunitionsJson', AMMO, {'ResupplyTime': 6000.0})
    ok(A[AMMO]['ResupplyTime'] == 6000.0, 'DF-31A resupply 6000')
    rec['df31a_resupply_1124'] = {'resupply_time': [600.0, 6000.0]}
    print('DF-31A RESUPPLY', rec['df31a_resupply_1124'])

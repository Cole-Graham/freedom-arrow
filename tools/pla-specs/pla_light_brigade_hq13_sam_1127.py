"""HQ-13 SHORAD missile (Osama 27 Nov 2026 04:4x PST, thread 1567745029781454889: "HQ-13 SHORAD, it should be 12 missiles that are stat clone of the
FK-2000 SAM called HQ-13 and it should be 170 points").
- New weapon 'HQ-13' and round 'HQ-13 ammunition' = stat copies (first of the FK-2000 SAM; now of the HHQ-10, see the last point),
  so the source rows are not touched. Own rows because the name differs (same pattern as the QJY-201 = Mk.48 copy).
- HQ-13 SHORAD (6008): its turret's FB-10 (the PGL-625's row, shared) -> HQ-13 on the same point 0; weapon-ammo row 3000054 -> HQ-13 round, 8 -> 12.
  The PGL-625 keeps the FB-10.
- Price 130 -> 170. In the plb ID block; the last plb section. Not yet tested in a game.
- Source changed 27 Nov 21:2x (Osama: "it should be a HHQ-10 clone but with 12 ammo stat wise. but call it HQ-13 ... I'm talking about weapon
  stats"): weapon and round are now copies of the HHQ-10 (weapon 2019357, round 2019358), weapon MagazineSize 18 -> 12, 12 missiles."""
HQ13, TURRET, WA_ROW, FB10, FB10_A, FK_W, FK_A = 6008, 3000000, 3000054, 2009371, 2009373, 2019357, 2019358   # FK_* = the HHQ-10 rows (source)


def apply(t, g, ok, rec):
    U, W, A, WA, TW = t['Units'], t['WeaponsJson'], t['AmmunitionsJson'], t['WeaponAmmunitionsJson'], t['TurretWeaponsJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok(U[HQ13]['HUDName'] == 'HQ-13 SHORAD' and U[HQ13]['Cost'] == 130 and not U[HQ13].get('OriginalCost'), ('HQ-13 SHORAD 130', U[HQ13]['Cost']))
    ok([r['UnitId'] for r in rows('TurretUnitsJson', TurretId=TURRET)] == [HQ13], 'HQ-13 owns its turret')
    tw = rows('TurretWeaponsJson', TurretId=TURRET)
    ok([(x['Order'], x['WeaponId']) for x in tw] == [(0, FB10)] and WA[WA_ROW]['UnitId'] == HQ13 and (WA[WA_ROW]['WeaponId'], WA[WA_ROW]['AmmunitionId'], WA[WA_ROW]['Quantity']) == (FB10, FB10_A, 8),
       ('HQ-13 turret FB-10 x8', [(x['Order'], x['WeaponId']) for x in tw], WA[WA_ROW]))
    ok(W[FK_W]['HUDName'] == 'HHQ-10' and W[FK_W]['MagazineSize'] == 18 and A[FK_A]['HUDName'] == 'HHQ-10', 'HHQ-10 rows')
    ok(not any(w and w.get('HUDName') == 'HQ-13' for w in W.values()), 'HQ-13 weapon name free')
    print('HQ-13 SOURCE HHQ-10 round', {k: A[FK_A].get(k) for k in ('GroundRange', 'LowAltRange', 'HighAltRange', 'Damage', 'Speed', 'TargetType')})
    w = g.add('WeaponsJson', W[FK_W], {'Name': 'PLA HQ-13 SHORAD HQ-13', 'HUDName': 'HQ-13', 'MagazineSize': 12})
    a = g.add('AmmunitionsJson', A[FK_A], {'Name': 'PLA HQ-13 SHORAD HQ-13 ammunition', 'HUDName': 'HQ-13 ammunition'})
    g.put('TurretWeaponsJson', tw[0]['Id'], {'WeaponId': w})
    g.put('WeaponAmmunitionsJson', WA_ROW, {'WeaponId': w, 'AmmunitionId': a, 'Quantity': 12})
    g.put('Units', HQ13, {'Cost': 170})
    same = lambda x, y, skip: all(x.get(k) == y.get(k) for k in set(x) | set(y) if k not in skip)
    ok(same(W[w], W[FK_W], ('Id', 'Name', 'HUDName', 'MagazineSize')) and W[w]['MagazineSize'] == 12 and same(A[a], A[FK_A], ('Id', 'Name', 'HUDName')), 'HQ-13 = HHQ-10 stats, 12 missiles')
    ok({r['UnitId'] for r in WA.values() if r and r['WeaponId'] == FB10} == {920} and {r['UnitId'] for r in WA.values() if r and r['WeaponId'] == FK_W} == {1273},
       'PGL-625 keeps the FB-10; HHQ-10 rows unchanged')
    rec['pla_light_brigade_hq13_sam_1127'] = {'weapon': w, 'round': a, 'missiles': WA[WA_ROW]['Quantity'], 'cost': [130, U[HQ13]['Cost']]}
    print('HQ-13 SAM', rec['pla_light_brigade_hq13_sam_1127'])

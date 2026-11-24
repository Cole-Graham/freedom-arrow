"""ZSL-191 stats (Osama 23 Nov 2026 21:5x PST, thread 1567745029781454889): "the ZSL-191 should be a 30 point unit, it should have 12 hp too, it only
has 10 right now. and no autocannon only mg. It shares the hull with the ZBL-191 ... should be same armor as the ZBL-191."
mk_china_1123.py made the ZSL-191 (transport for PLAGF Motorized infantry) a copy of the ZSL-92 family APC (35 pts, 10 HP, 30 mm + MG).
- Cost 35 -> 30.
- Armour: links the ZBL-191's own armour row 2010315 (12 HP; KE 80/60/30/20, HEAT 450/300/130/20), now shared by both on purpose;
  its copied ZSL-92 armour row is removed.
- MG only: one turret, a copy of the ZSL-92 mount 0 turret carrying the Type 86 7.62 mm in slot 0 (400 rounds, as before). The 30 mm turret,
  the separate MG mount and the 30 mm ammunition rows leave the ZSL-191, so the only weapon sits at Order 0 (no empty weapon slot)."""
ZBL_ARMOR, M0, M1 = 2010315, 2011272, 2011280


def apply(t, g, ok, rec):
    U, UAR, AR, T, TW, TU, WA, W = (t[k] for k in ('Units', 'UnitArmorsJson', 'ArmorsJson', 'TurretsJson', 'TurretWeaponsJson', 'TurretUnitsJson',
                                                    'WeaponAmmunitionsJson', 'WeaponsJson'))
    zsl = [i for i, u in U.items() if u and u.get('Name') == 'PLA ZSL-191']
    ok(len(zsl) == 1 and U[zsl[0]]['Cost'] == 35, 'ZSL-191 card 35 pts'); u = zsl[0]
    ok(AR[ZBL_ARMOR]['Name'] == 'PLA ZBL-191 ArmorsJson' and AR[ZBL_ARMOR]['MaxHealthPoints'] == 12, 'ZBL-191 armour row, 12 HP')
    arm = [r for r in UAR.values() if r and r['UnitId'] == u]
    ok(len(arm) == 1 and AR[arm[0]['ArmorId']]['MaxHealthPoints'] == 10, 'ZSL-191: one armour row, 10 HP'); old_arm = arm[0]['ArmorId']
    g.put('UnitArmorsJson', arm[0]['Id'], {'ArmorId': ZBL_ARMOR})
    if not any(r and r['ArmorId'] == old_arm for r in UAR.values()): g.remove('ArmorsJson', old_arm)
    tu = sorted([r for r in TU.values() if r and r['UnitId'] == u], key=lambda r: r['Order'])
    ok([r['TurretId'] for r in tu] == [M0, M1], ('ZSL-191 turrets = ZSL-92 mounts', [r['TurretId'] for r in tu]))
    mg = [r for r in TW.values() if r and r['TurretId'] == M1]
    ok(len(mg) == 1 and W[mg[0]['WeaponId']]['HUDName'] == 'Type 86 7.62 mm', 'mount 1 = Type 86 MG')
    tid = g.add('TurretsJson', T[M0], {'Name': 'PLA ZSL-191 mount 0 MG'})
    g.add('TurretWeaponsJson', mg[0], {'TurretId': tid, 'Order': 0, 'WeaponPriority': 0})
    g.put('TurretUnitsJson', tu[0]['Id'], {'TurretId': tid}); g.remove('TurretUnitsJson', tu[1]['Id'])
    for r in [r for r in WA.values() if r and r['UnitId'] == u and r['WeaponId'] != mg[0]['WeaponId']]: g.remove('WeaponAmmunitionsJson', r['Id'])
    g.put('Units', u, {'Cost': 30})
    w = [(W[r['WeaponId']]['HUDName'], r['Quantity']) for r in WA.values() if r and r['UnitId'] == u]
    ok(w == [('Type 86 7.62 mm', 400)] and [r['TurretId'] for r in TU.values() if r and r['UnitId'] == u] == [tid]
       and [(x['Order'], W[x['WeaponId']]['HUDName']) for x in TW.values() if x and x['TurretId'] == tid] == [(0, 'Type 86 7.62 mm')], ('ZSL-191 MG only', w))
    ok(U[u]['Cost'] == 30 and [AR[r['ArmorId']]['MaxHealthPoints'] for r in UAR.values() if r and r['UnitId'] == u] == [12], 'ZSL-191 30 pts, 12 HP')
    ok(sorted(U[r['UnitId']]['Name'] for r in UAR.values() if r and r['ArmorId'] == ZBL_ARMOR) == ['PLA ZBL-191', 'PLA ZSL-191'], 'armour shared by ZBL-191 and ZSL-191')
    rec['zsl191_stats'] = {'unit': u, 'cost': [35, 30], 'armor': [old_arm, ZBL_ARMOR], 'turret': tid, 'weapons': w}
    print('ZSL-191 STATS', rec['zsl191_stats'])

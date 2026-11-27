"""PLA Light Brigade build, Airborne QBU-202 (Osama 26 Nov 2026 18:3x PST, thread 1567745029781454889: "Airborne swap QBU-10 to QBU-203" / "sorry I
mean QBU-202"). Branch codex/batch/osama/pla-light-brigade only; the last plb section.
- Airborne 空降兵 (1136): the QBU-10 sniper (2012054, 40 rounds) -> the QBU-202 (Mk 22 ASR copy, Type 3 marksman; the back-pocket weapon the Marine
  Scouts carry), 40 rounds (the Marine Scouts' row). Same soldier, death priority 2 and list slot 4 (after the QBU-191, before the PF-98, the
  vanilla order of pla_light_brigade_order_1126). The QBU-10 stays on every other squad."""
AIRBORNE, QBU10 = 1136, 2012054


def apply(t, g, ok, rec):
    U, W, A = t['Units'], t['WeaponsJson'], t['AmmunitionsJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    qb = rec['backpocket_weapons_1125']['QBU-202']; Q, QA = qb['weapon'], qb['ammo']
    ok(U[AIRBORNE]['HUDName'] == 'Airborne 空降兵' and W[QBU10]['HUDName'] == 'QBU-10' and W[Q]['HUDName'] == 'QBU-202' and W[Q]['Type'] == 3, 'Airborne, QBU-10, QBU-202')
    (m,) = [m for m in rows('SquadMembersJson', UnitId=AIRBORNE) if m['PrimaryWeaponId'] == QBU10]
    (sw,) = rows('SquadWeaponsJson', UnitId=AIRBORNE, WeaponId=QBU10); (wa,) = rows('WeaponAmmunitionsJson', UnitId=AIRBORNE, WeaponId=QBU10)
    g.put('SquadMembersJson', m['Id'], {'PrimaryWeaponId': Q})
    g.put('SquadWeaponsJson', sw['Id'], {'WeaponId': Q})
    g.put('WeaponAmmunitionsJson', wa['Id'], {'WeaponId': Q, 'AmmunitionId': QA, 'Quantity': 40})
    # checks after
    men = rows('SquadMembersJson', UnitId=AIRBORNE)
    carried = {x for m in men for x in (m['PrimaryWeaponId'], m.get('SpecialWeaponId')) if x}
    ok({r['WeaponId'] for r in rows('SquadWeaponsJson', UnitId=AIRBORNE)} == carried == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=AIRBORNE)} and QBU10 not in carried, 'Airborne: card + ammo = carried, no QBU-10')
    order = [W[r['WeaponId']]['HUDName'] for r in sorted(rows('SquadWeaponsJson', UnitId=AIRBORNE), key=lambda r: r['Order'])]
    ok(order == ['QMK', 'QJS-161', 'QBU-191', 'QBU-202', 'PF-98'], ('Airborne order', order))
    ok(rows('SquadWeaponsJson', WeaponId=QBU10), 'QBU-10 still used elsewhere')
    rec['pla_light_brigade_late4_1126'] = {'airborne': order, 'qbu202_rounds': 40}
    print('PLA LIGHT BRIGADE LATE4', rec['pla_light_brigade_late4_1126'])

"""PLA Light Brigade build, late changes 3 (Osama 26 Nov 2026 18:3x PST, thread 1567745029781454889: "QLU-11 team to 65 points. Tank Hunters lose
Thermo round. set to 55 points. 8 ammo. Rifles switched to QMK."). Branch codex/batch/osama/pla-light-brigade only; the last plb section.
- QLU-11 Team (1140, PLAAF): 60 -> 65 pts.
- Tank Hunters 坦克杀手 (1139, PLAAF): 75 -> 55 pts; the leader's PF-98A loses its DZT-98 thermobaric round (ammo row removed) and its HEAT round goes
  6 -> 8 per carrier; the 5 QBZ-191 riflemen and the leader's rifle -> QMK (2019300, round 2019301, 160 per carrier as every QMK row). Men, death
  priority and cards unchanged. The Marines PF-98 (the PLAN copy) keeps its kit."""
QLU_TEAM, TH, QBZ191, QMK, QMK_A, DZT98 = 1140, 1139, 2003998, 2019300, 2019301, 2016058


def apply(t, g, ok, rec):
    U, W, A = t['Units'], t['WeaponsJson'], t['AmmunitionsJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok(U[QLU_TEAM]['HUDName'] == 'QLU-11 Team' and U[QLU_TEAM]['Cost'] == 60, 'QLU-11 Team 60 pts')
    g.put('Units', QLU_TEAM, {'Cost': 65})
    (pf98a,) = [i for i, w in W.items() if w and w.get('HUDName') == 'PF-98A']
    ok(U[TH]['HUDName'] == 'Tank Hunters 坦克杀手' and U[TH]['Cost'] == 75 and W[QMK]['HUDName'] == 'QMK' and A[QMK_A]['HUDName'] == 'QMK ammunition', 'Tank Hunters 75, QMK')
    wa = rows('WeaponAmmunitionsJson', UnitId=TH, WeaponId=pf98a)
    ok(sorted(A[r['AmmunitionId']]['HUDName'] for r in wa) == ['DZT-98 thermobaric (analog)', 'PF-98A ammunition'], 'PF-98A: HEAT + DZT-98')
    for r in wa:
        if r['AmmunitionId'] == DZT98: g.remove('WeaponAmmunitionsJson', r['Id'])
        else: g.put('WeaponAmmunitionsJson', r['Id'], {'Quantity': 8})
    men = rows('SquadMembersJson', UnitId=TH)
    ok(sum(m['PrimaryWeaponId'] == QBZ191 for m in men) == len(men) == 6, 'Tank Hunters: 6 men with QBZ-191')
    for m in men: g.put('SquadMembersJson', m['Id'], {'PrimaryWeaponId': QMK})
    (sw,) = rows('SquadWeaponsJson', UnitId=TH, WeaponId=QBZ191); g.put('SquadWeaponsJson', sw['Id'], {'WeaponId': QMK})
    (qa,) = rows('WeaponAmmunitionsJson', UnitId=TH, WeaponId=QBZ191); g.put('WeaponAmmunitionsJson', qa['Id'], {'WeaponId': QMK, 'AmmunitionId': QMK_A, 'Quantity': 160})
    g.put('Units', TH, {'Cost': 55})
    # checks after
    men = rows('SquadMembersJson', UnitId=TH)
    carried = {x for m in men for x in (m['PrimaryWeaponId'], m.get('SpecialWeaponId')) if x}
    ok({r['WeaponId'] for r in rows('SquadWeaponsJson', UnitId=TH)} == carried == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=TH)} == {QMK, pf98a}, 'Tank Hunters: QMK + PF-98A, card + ammo = carried')
    kit = [(A[r['AmmunitionId']]['HUDName'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=TH)]
    ok(sorted(kit) == [('PF-98A ammunition', 8), ('QMK ammunition', 160)] and U[TH]['Cost'] == 55 and U[QLU_TEAM]['Cost'] == 65, ('Tank Hunters kit', kit))
    rec['pla_light_brigade_late3_1126'] = {'qlu11_team': 65, 'tank_hunters': {'cost': 55, 'ammo': kit}}
    print('PLA LIGHT BRIGADE LATE3', rec['pla_light_brigade_late3_1126'])

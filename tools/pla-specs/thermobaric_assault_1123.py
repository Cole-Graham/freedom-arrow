"""Lateralus 23 Nov 2026 15:3x PST, thread 1568104480459722894: "Thermobaric Assault: QBS-09 2 -> 3, QBZ-191 7 -> 6, Armor 6 -> 8, Price 60 -> 70".
Called from batch_0_9_5b.py, after infantry_order_1122.py and thermobaric_pf97_1123.py.
Thermobaric Assault 温压突击 (1209, 9 men, no loadout options, OriginalCost 0):
- QBS-09 2 -> 3, QBZ-191 7 -> 6: plain rifleman 2015624 (QBZ-191, no special weapon, DeathPriority 4) gets the QBS-09 (2012131) instead, and the
  squad's shotgun death priority 2 (death-order rule: shotguns are tier B). Men stay 9; the 3 PF-97 carriers are unchanged. Ammo pools follow the
  carriers (Quantity x carriers), so QBS-09 ammo goes up by half and QBZ-191 ammo down by a seventh.
- Armour 6 -> 8: link 2013931 row 2013930 (6 / 45, this unit only) -> vanilla 277 "Armor Infantry Shock 9Men" (8 / 45), same row except armour.
- Price 60 -> 70 (Units.Cost)."""


def apply(t, g, ok, rec):
    U, SM, UA, AR, O, M = t['Units'], t['SquadMembersJson'], t['UnitArmorsJson'], t['ArmorsJson'], t['OptionsJson'], t['ModificationsJson']
    QBZ, QBS, PF97 = 2003998, 2012131, 2012515
    u = U[1209]
    ok(u['HUDName'].strip().startswith('Thermobaric Assault') and u['Cost'] == 60 and not u.get('OriginalCost'), ('Thermobaric Assault 1209 at 60', u['Cost']))
    mods = {m['Id'] for m in M.values() if m and m.get('UnitId') == 1209}
    ok(not any(o for o in O.values() if o and (o.get('ModificationId') in mods or o.get('ReplaceUnitId') == 1209)), 'no loadout options or swaps on 1209')
    men = lambda: [m for m in SM.values() if m and m.get('UnitId') == 1209]
    cnt = lambda w, f='PrimaryWeaponId': sum(1 for m in men() if m.get(f) == w)
    ok(len(men()) == 9 and cnt(QBS) == 2 and cnt(QBZ) == 7 and cnt(PF97, 'SpecialWeaponId') == 3, ('9 men, 2 QBS-09, 7 QBZ-191, 3 PF-97', len(men()), cnt(QBS), cnt(QBZ)))
    r = SM[2015624]
    ok(r['UnitId'] == 1209 and r['PrimaryWeaponId'] == QBZ and not r.get('SpecialWeaponId') and r['DeathPriority'] == 4, ('2015624 is a plain rifleman, priority 4', r))
    ok(all(m['DeathPriority'] == 2 for m in men() if m['PrimaryWeaponId'] == QBS), 'the QBS-09 men have death priority 2')
    g.put('SquadMembersJson', 2015624, {'PrimaryWeaponId': QBS, 'DeathPriority': 2})
    ok(len(men()) == 9 and cnt(QBS) == 3 and cnt(QBZ) == 6 and cnt(PF97, 'SpecialWeaponId') == 3, '9 men, 3 QBS-09, 6 QBZ-191, 3 PF-97')
    ign = {'Id', 'Name'}
    diff = lambda a, b: {k for k in set(a) | set(b) if k not in ign and a.get(k) != b.get(k)}
    ok(UA[2013931]['UnitId'] == 1209 and UA[2013931]['ArmorId'] == 2013930 and AR[2013930]['ArmorValue'] == 6, 'armour link 2013931 -> 2013930 (6)')
    ok(diff(AR[2013930], AR[277]) == {'ArmorValue'} and (AR[277]['ArmorValue'], AR[277]['MaxHealthPoints']) == (8, 45), 'row 277 = 2013930 with armour 8')
    g.put('UnitArmorsJson', 2013931, {'ArmorId': 277})
    g.put('Units', 1209, {'Cost': 70})
    rec['thermobaric_assault_1123'] = {'unit': 1209, 'qbs09': [2, 3], 'qbz191': [7, 6], 'member_2015624': ['QBZ-191 p4', 'QBS-09 p2'], 'armor': [2013930, 277], 'cost': [60, 70]}

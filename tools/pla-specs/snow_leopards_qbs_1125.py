"""PAP Snow Leopards 雪豹 (1182, PLAN Special Forces, 70 pts): one QCQ-171 -> QBS-09 (Osama 25 Nov 2026 18:3x PST, bugs thread 1573561286803980289:
"PAP Snow leopards swap 1 QCQ for QBS-09 (keep an eye on the balance of this unit)"). The plain QCQ-171 man (2015311, no launcher) carries the
QBS-09, death priority 2 like the other two QBS-09 men; the four QCQ-171 + DZJ-08 men stay. Card row and ammo row (QBS-09 96 per carrier) exist
already. Kit after: 3 QBS-09, 4 QCQ-171 (all with DZJ-08), 1 LG4. 8 men, 70 pts unchanged. The hidden copy 1189 (no card) is not changed."""
UID, QCQ, QBS, MAN = 1182, 2013349, 2012131, 2015311


def apply(t, g, ok, rec):
    W, SM, SW, WA = t['WeaponsJson'], t['SquadMembersJson'], t['SquadWeaponsJson'], t['WeaponAmmunitionsJson']
    men = lambda: [r for r in SM.values() if r and r['UnitId'] == UID]
    ok(SM[MAN]['UnitId'] == UID and SM[MAN]['PrimaryWeaponId'] == QCQ and not SM[MAN]['SpecialWeaponId'], 'Snow Leopards plain QCQ-171 man')
    ok(W[QBS]['HUDName'] == 'QBS-09' and sum(m['PrimaryWeaponId'] == QBS for m in men()) == 2, 'QBS-09, 2 carriers before')
    g.put('SquadMembersJson', MAN, {'PrimaryWeaponId': QBS, 'DeathPriority': 2})
    ms = men()
    kit = sorted((W[m['PrimaryWeaponId']]['HUDName'], W[m['SpecialWeaponId']]['HUDName'] if m['SpecialWeaponId'] else '') for m in ms)
    ok(len(ms) == 8 and sum(m['PrimaryWeaponId'] == QBS for m in ms) == 3 and sum(m['PrimaryWeaponId'] == QCQ for m in ms) == 4, ('Snow Leopards 3 QBS-09, 4 QCQ-171', kit))
    carried = {w for m in ms for w in (m['PrimaryWeaponId'], m['SpecialWeaponId']) if w}
    ok({r['WeaponId'] for r in SW.values() if r and r['UnitId'] == UID} == carried == {r['WeaponId'] for r in WA.values() if r and r['UnitId'] == UID}, 'card + ammo = carried weapons')
    rec['snow_leopards_qbs_1125'] = {'member': MAN, 'kit': kit}
    print('SNOW LEOPARDS QBS', rec['snow_leopards_qbs_1125'])

"""Thunder Gods 雷神 (1143): a second QJS-161 (Osama 25 Nov 2026 18:2x PST, bugs thread 1573561286803980289: "Thunder gods, remove 1 QBZ-192 and
replace with another QJS-161"). One plain QBZ-192 rifleman (no special weapon; the FHJ-02 man 2014922 stays a rifleman) carries the QJS-161,
death priority 2 like the first gunner. 9 men, 80 pts unchanged. Ammo row unchanged (QJS-161 400 per carrier; the pool is Quantity x carriers).
Kit after: 4 QBZ-192 (one with FHJ-02), 3 QCQ-171, 2 QJS-161. After thunder_gods_1124.py."""
UID, QBZ, QJS, FHJ_MAN = 1143, 2013087, 2011922, 2014922


def apply(t, g, ok, rec):
    W, SM = t['WeaponsJson'], t['SquadMembersJson']
    men = lambda: sorted([r for r in SM.values() if r and r['UnitId'] == UID], key=lambda r: r['Id'])
    plain = [m for m in men() if m['PrimaryWeaponId'] == QBZ and not m['SpecialWeaponId'] and m['Id'] != FHJ_MAN]
    ok(len(men()) == 9 and sum(m['PrimaryWeaponId'] == QJS for m in men()) == 1 and len(plain) == 4, ('Thunder Gods before: 9 men, 1 QJS-161, 4 plain QBZ-192', len(plain)))
    pick = plain[0]['Id']
    g.put('SquadMembersJson', pick, {'PrimaryWeaponId': QJS, 'DeathPriority': 2})
    ms = men()
    kit = sorted((W[m['PrimaryWeaponId']]['HUDName'], W[m['SpecialWeaponId']]['HUDName'] if m['SpecialWeaponId'] else '', m['DeathPriority']) for m in ms)
    ok(len(ms) == 9 and sum(m['PrimaryWeaponId'] == QJS for m in ms) == 2 and sum(m['PrimaryWeaponId'] == QBZ for m in ms) == 4
      , ('Thunder Gods 4 QBZ-192, 3 QCQ-171, 2 QJS-161', kit))
    rec['thunder_gods_qjs2_1125'] = {'member': pick, 'kit': kit}
    print('THUNDER GODS QJS2', rec['thunder_gods_qjs2_1125'])

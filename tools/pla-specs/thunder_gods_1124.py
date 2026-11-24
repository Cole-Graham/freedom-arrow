"""Thunder Gods 雷神 (1143) kit (Osama 24 Nov 2026 02:4x PST, thread "China cosmetic work": "Thunder gods QTS both replaced with QCW (now the
qcq-171) for total 3 QCQ-171. 2x QBZ-192 turns into 2xQJS-161"; 02:5x after the DPM comparison: "we should give them only 1 mg then"). The two
QTS-11 + QTS-11 grenade launcher men carry the QCQ-171 (no special weapon), one plain QBZ-192 rifleman carries the QJS-161 (400 rounds each, as on Sea Dragons / Marines / Assault Raiders). Card order QBZ-192,
QJS-161, QCQ-171, FHJ-02. Death priorities and the 80 pts are unchanged."""
UID = 1143
QBZ, QTS, GL, QCQ, QJS, FHJ = 2013087, 2004004, 2019270, 2013349, 2011922, 2013057
QJS_AMMO = 2011923
TO_QCQ, TO_QJS = (2014919, 2014920), (2014923,)


def apply(t, g, ok, rec):
    U, W, SM, SW, WA = (t[k] for k in ('Units', 'WeaponsJson', 'SquadMembersJson', 'SquadWeaponsJson', 'WeaponAmmunitionsJson'))
    rows = lambda tab: sorted([r for r in t[tab].values() if r and r['UnitId'] == UID], key=lambda r: r['Id'])
    ok(U[UID]['HUDName'].startswith('Thunder Gods'), 'Thunder Gods 1143')
    ok([(SM[i]['PrimaryWeaponId'], SM[i]['SpecialWeaponId']) for i in TO_QCQ] == [(QTS, GL)] * 2, 'the two QTS-11 + GL men')
    ok([(SM[i]['PrimaryWeaponId'], SM[i]['SpecialWeaponId']) for i in TO_QJS] == [(QBZ, 0)], 'one plain QBZ-192 rifleman')
    ok([W[w]['HUDName'] for w in (QCQ, QJS)] == ['QCQ-171', 'QJS-161'], 'QCQ-171 / QJS-161 weapon rows')
    for i in TO_QCQ: g.put('SquadMembersJson', i, {'PrimaryWeaponId': QCQ, 'SpecialWeaponId': 0})
    for i in TO_QJS: g.put('SquadMembersJson', i, {'PrimaryWeaponId': QJS})
    sw = {r['WeaponId']: r for r in rows('SquadWeaponsJson')}
    tpl = sw[QTS]
    for w in (QTS, GL): g.remove('SquadWeaponsJson', sw[w]['Id'])
    g.add('SquadWeaponsJson', tpl, {'WeaponId': QJS})
    for r in rows('SquadWeaponsJson'): g.put('SquadWeaponsJson', r['Id'], {'Order': {QBZ: 1, QJS: 2, QCQ: 3, FHJ: 4}[r['WeaponId']]})
    wa = {r['WeaponId']: r for r in rows('WeaponAmmunitionsJson')}
    for w in (QTS, GL): g.remove('WeaponAmmunitionsJson', wa[w]['Id'])
    g.add('WeaponAmmunitionsJson', wa[QBZ], {'WeaponId': QJS, 'AmmunitionId': QJS_AMMO, 'Quantity': 400})
    men = rows('SquadMembersJson'); carried = {w for m in men for w in (m['PrimaryWeaponId'], m['SpecialWeaponId']) if w}
    kit = sorted((W[m['PrimaryWeaponId']]['HUDName'], W[m['SpecialWeaponId']]['HUDName'] if m['SpecialWeaponId'] else '') for m in men)
    ok(sum(m['PrimaryWeaponId'] == QCQ for m in men) == 3 and sum(m['PrimaryWeaponId'] == QJS for m in men) == 1 and sum(m['PrimaryWeaponId'] == QBZ for m in men) == 5,
       ('Thunder Gods 3 QCQ-171, 1 QJS-161, 5 QBZ-192', kit))
    ok({r['WeaponId'] for r in rows('SquadWeaponsJson')} == carried == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson')}, 'card + ammo = carried weapons')
    ok([W[r['WeaponId']]['HUDName'] for r in sorted(rows('SquadWeaponsJson'), key=lambda r: r['Order'])] == ['QBZ-192', 'QJS-161', 'QCQ-171', 'FHJ-02'], 'card order')
    rec['thunder_gods_1124'] = {'kit': kit}
    print('THUNDER GODS', kit)

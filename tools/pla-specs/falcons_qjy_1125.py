"""Falcons (1185): 6 -> 4 QMK, 2 x QJY-201, still 8 men (Osama 25 Nov 2026 02:3x PST, thread 1567745029781454889: "Falcons
replace 1 QMK with QJY-201. I think we have an extra QMK so remove 2 total so we have 4"; corrected 10:2x: "it should still be 8 man, you just
had an extra primary rifle. and it should be total 2x QJY-201").
- Squad member 2015348 had the QMK as primary and the QJY-201 as special weapon, the only squad that carried the QJY-201 that way; it now has
  the QJY-201 as primary and no special weapon, as the 23 other QJY-201 gunners.
- Plain QMK rifleman 2015355 (the last member) gets the QJY-201 as primary too. The squad is QMK x4 (one with PF-98), QJY-201 x2, QLU-11, QBU-201.
  8 men and 40 HP as before. Price (75) and the ammo rows are unchanged; FAModels weapon rules are by weapon id, not by soldier index, so the models still match."""
FALCONS, GUNNER, EXTRA, QMK, QJY = 1185, 2015348, 2015355, 2019300, 2012411


def apply(t, g, ok, rec):
    U, SM, W = t['Units'], t['SquadMembersJson'], t['WeaponsJson']
    ms = lambda: sorted([m for m in SM.values() if m and m['UnitId'] == FALCONS], key=lambda m: m['Id'])
    ok(U[FALCONS]['HUDName'] == 'Falcons 猎鹰' and W[QMK]['HUDName'] == 'QMK' and W[QJY]['HUDName'] == 'QJY-201', 'Falcons / QMK / QJY-201')
    before = [(m['Id'], m['PrimaryWeaponId'], m.get('SpecialWeaponId') or 0) for m in ms()]
    ok(len(before) == 8 and sum(p == QMK for _, p, _ in before) == 6 and SM[GUNNER]['PrimaryWeaponId'] == QMK and SM[GUNNER]['SpecialWeaponId'] == QJY
       and SM[EXTRA]['PrimaryWeaponId'] == QMK and not SM[EXTRA].get('SpecialWeaponId') and before[-1][0] == EXTRA, ('Falcons 8 men, 6 QMK', before))
    g.put('SquadMembersJson', GUNNER, {'PrimaryWeaponId': QJY, 'SpecialWeaponId': 0})
    g.put('SquadMembersJson', EXTRA, {'PrimaryWeaponId': QJY})
    after = [(m['Id'], m['PrimaryWeaponId'], m.get('SpecialWeaponId') or 0) for m in ms()]
    ok(len(after) == 8 and sum(p == QMK for _, p, _ in after) == 4 and sum(p == QJY for _, p, _ in after) == 2 and not any(s == QJY for _, _, s in after),
       ('Falcons 8 men, 4 QMK, 2 QJY-201', after))
    ua = [r for r in t['UnitArmorsJson'].values() if r and r['UnitId'] == FALCONS]
    ok(len(ua) == 1 and t['ArmorsJson'][ua[0]['ArmorId']]['MaxHealthPoints'] == 40
       and [r['UnitId'] for r in t['UnitArmorsJson'].values() if r and r['ArmorId'] == ua[0]['ArmorId']] == [FALCONS], ('Falcons own armour row, 40 HP', ua))
    ok(t['ArmorsJson'][ua[0]['ArmorId']]['MaxHealthPoints'] == 5 * len(after), 'Falcons 40 HP = 5 x 8 men')
    rec['falcons_qjy_1125'] = {'before': before, 'after': after}
    print('FALCONS', rec['falcons_qjy_1125'])

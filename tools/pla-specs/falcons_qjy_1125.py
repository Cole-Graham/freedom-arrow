"""Falcons (1185): 6 -> 4 QMK, the QJY-201 gunner carries it as his own gun (Osama 25 Nov 2026 02:3x PST, thread 1567745029781454889: "Falcons
replace 1 QMK with QJY-201. I think we have an extra QMK so remove 2 total so we have 4").
- Squad member 2015348 had the QMK as primary and the QJY-201 as special weapon, the only squad that carried the QJY-201 that way; it now has
  the QJY-201 as primary and no special weapon, as the 23 other QJY-201 gunners.
- One plain QMK rifleman (2015355, the last member) leaves: 8 -> 7 men. The squad is QMK x4 (one with PF-98), QJY-201, QLU-11, QBU-201.
  Health 40 -> 35 HP on its own armour row 2013216 (5 HP per soldier, check_squad_hp.py). Price (75) and the ammo rows are unchanged; FAModels weapon rules are by weapon id, not by soldier index, so the models still match."""
FALCONS, GUNNER, EXTRA, QMK, QJY = 1185, 2015348, 2015355, 2019300, 2012411


def apply(t, g, ok, rec):
    U, SM, W = t['Units'], t['SquadMembersJson'], t['WeaponsJson']
    ms = lambda: sorted([m for m in SM.values() if m and m['UnitId'] == FALCONS], key=lambda m: m['Id'])
    ok(U[FALCONS]['HUDName'] == 'Falcons 猎鹰' and W[QMK]['HUDName'] == 'QMK' and W[QJY]['HUDName'] == 'QJY-201', 'Falcons / QMK / QJY-201')
    before = [(m['Id'], m['PrimaryWeaponId'], m.get('SpecialWeaponId') or 0) for m in ms()]
    ok(len(before) == 8 and sum(p == QMK for _, p, _ in before) == 6 and SM[GUNNER]['PrimaryWeaponId'] == QMK and SM[GUNNER]['SpecialWeaponId'] == QJY
       and SM[EXTRA]['PrimaryWeaponId'] == QMK and not SM[EXTRA].get('SpecialWeaponId') and before[-1][0] == EXTRA, ('Falcons 8 men, 6 QMK', before))
    g.put('SquadMembersJson', GUNNER, {'PrimaryWeaponId': QJY, 'SpecialWeaponId': 0})
    g.remove('SquadMembersJson', EXTRA)
    after = [(m['Id'], m['PrimaryWeaponId'], m.get('SpecialWeaponId') or 0) for m in ms()]
    ok(len(after) == 7 and sum(p == QMK for _, p, _ in after) == 4 and sum(p == QJY for _, p, _ in after) == 1 and not any(s == QJY for _, _, s in after),
       ('Falcons 7 men, 4 QMK, 1 QJY-201', after))
    ua = [r for r in t['UnitArmorsJson'].values() if r and r['UnitId'] == FALCONS]
    ok(len(ua) == 1 and t['ArmorsJson'][ua[0]['ArmorId']]['MaxHealthPoints'] == 40
       and [r['UnitId'] for r in t['UnitArmorsJson'].values() if r and r['ArmorId'] == ua[0]['ArmorId']] == [FALCONS], ('Falcons own armour row, 40 HP', ua))
    g.put('ArmorsJson', ua[0]['ArmorId'], {'MaxHealthPoints': 35})
    ok(t['ArmorsJson'][ua[0]['ArmorId']]['MaxHealthPoints'] == 5 * len(after), 'Falcons 35 HP = 5 x 7 men')
    rec['falcons_qjy_1125'] = {'before': before, 'after': after}
    print('FALCONS', rec['falcons_qjy_1125'])

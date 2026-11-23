"""J-8D health = J-7IIH, J-6W and J-5 (Osama 23 Nov 2026 12:5x PST, thread 1567745029781454889: "we need to make sure the J-8 has the same health as
the J-7 and 6 and 5"). The J-8D (975) used the vanilla MiG-29 armour row 238 (20 HP, shared with MiG-35/MiG-29SMT/MiG-29K/MiG-29S). The J-7IIH (1092)
uses 2019311, the same row with 10 HP; the J-5 (1089) and J-6W (1091) use 2019294 (10 HP). The J-8D now links 2019311, so the MiG-29s keep 238."""

J8, J7, J6, J5, OLD, NEW = 975, 1092, 1091, 1089, 238, 2019311


def apply(t, g, ok, rec):
    U, AR, UA, O, M = t['Units'], t['ArmorsJson'], t['UnitArmorsJson'], t['OptionsJson'], t['ModificationsJson']
    arm = lambda uid: [r for r in UA.values() if r and r.get('UnitId') == uid]
    hp = lambda uid: sorted({AR[r['ArmorId']]['MaxHealthPoints'] for r in arm(uid)})
    ok([U[u]['HUDName'] for u in (J8, J7)] == ['J-8D', 'J-7IIH'] and U[J6]['HUDName'].startswith('J-6W') and U[J5]['HUDName'].startswith('J-5'), 'PLARF planes')
    ok(hp(J7) == hp(J6) == hp(J5) == [10] and hp(J8) == [20], ('health before', hp(J8), hp(J7), hp(J6), hp(J5)))
    ok({k: v for k, v in AR[OLD].items() if k not in ('Id', 'MaxHealthPoints')} == {k: v for k, v in AR[NEW].items() if k not in ('Id', 'MaxHealthPoints')},
       '2019311 = armour 238 with 10 HP')
    ok(not any(o.get('ArmorId') for o in O.values() if o and M.get(o['ModificationId'], {}).get('UnitId') == J8), 'no J-8D option changes the armour')
    rows = arm(J8)
    ok(len(rows) == 1 and rows[0]['ArmorId'] == OLD, ('J-8D armour row', rows))
    g.put('UnitArmorsJson', rows[0]['Id'], {'ArmorId': NEW})
    ok(hp(J8) == hp(J7) == hp(J6) == hp(J5) == [10] and AR[OLD]['MaxHealthPoints'] == 20 and all(r['ArmorId'] == OLD for u in (309, 310, 311, 744) for r in arm(u)),
       'J-8D 10 HP like J-7IIH/J-6W/J-5; MiG-29s keep 20')
    rec['j8_health'] = {'unit': J8, 'armour': [OLD, NEW], 'hp': [20, 10]}
    print('J-8D health', rec['j8_health'])

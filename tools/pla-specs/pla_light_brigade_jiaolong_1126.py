"""PLA Light Brigade build, Jiaolong CQC (Osama 26 Nov 2026 02:0x PST, thread 1567745029781454889: "Jiaolong get the new QBZ URGI, it's a Mk 18 CQBR
clone (0.65 dps). This is their loadout, Jiaolong CQC 2 availability at 65 points and 8 man", with his DPM visualizer custom unit: 8 men, 40 HP, Armor
Infantry Elite (10); 2x M1014, 2x Mk18 CQBR, 2x QJS-161, 6x PF-97, 2x QCQ-05). Branch codex/batch/osama/pla-light-brigade only; after the Test SF copy.
- QBZ URGI: new weapon, exact copy of the Mk18 CQBR (67, 'Rifle MK18 CQBR T2') and its round (143) under the China name '5.8 mm ammunition';
  Mk18 icon until one is drawn. Rows from the 'plb' reserved block.
- Sea Dragons 蛟龙 (1191, PLAN) = the CQC kit: 2 QBS-09 (the China M1014: identical stats), 2 QBZ URGI, 2 QJS-161, 2 QCQ-05; PF-97 on the URGI, QJS-161
  and QCQ-05 men (6). Death priority: leader (URGI) 1, QJS-161 gunners 2, others 3, one QCQ-05 man 4. Ammo per carrier as their other China rows
  (QBS-09 96, QJS-161 400, QCQ-05 20, PF-97 1); URGI 240 (the Mk18's). 55 -> 65 pts, 3 -> 2 cards, armour 'Armor Infantry Elite 8Men' (272: 10, 40 HP).
  The Stand-off loadout comes later. 26 Nov 10:4x "Sea Dragons 70 points": 65 -> 70."""
SEA, MK18, MK18_AMMO, ELITE8 = 1191, 67, 143, 272
QBS, QBS_A, QJS, QJS_A, QCQ, QCQ_A, PF97, PF97_A = 2012131, 2012132, 2011922, 2011923, 2012924, 2012925, 2012515, 2012516
MEN = [2015385, 2015386, 2015387, 2015388, 2015389, 2015390, 2015391, 2015392]


def apply(t, g, ok, rec):
    U, W, A, SM, SW, WA, UA, AR, SA = (t[k] for k in ('Units', 'WeaponsJson', 'AmmunitionsJson', 'SquadMembersJson', 'SquadWeaponsJson', 'WeaponAmmunitionsJson',
                                                      'UnitArmorsJson', 'ArmorsJson', 'SpecializationAvailabilitiesJson'))
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    wn = lambda i: W[i]['HUDName'] if i else ''
    ok(U[SEA]['HUDName'] == 'Sea Dragons 蛟龙' and U[SEA]['Cost'] == 55 and [r['Id'] for r in rows('SquadMembersJson', UnitId=SEA)] == MEN, 'Sea Dragons 1191, 8 men')
    ok(W[MK18]['HUDName'] == 'Mk18 CQBR' and A[MK18_AMMO]['HUDName'] == '5.56x45mm' and [wn(w) for w in (QBS, QJS, QCQ, PF97)] == ['QBS-09', 'QJS-161', 'QCQ-05', 'PF-97'], 'weapons')
    ok(AR[ELITE8]['Name'] == 'Armor Infantry Elite 8Men' and AR[ELITE8]['ArmorValue'] == 10 and AR[ELITE8]['MaxHealthPoints'] == 40, 'Elite 8-man armour')
    ok(not any(w and w.get('HUDName') == 'QBZ URGI' for w in W.values()), 'QBZ URGI name free')
    urgi = g.add('WeaponsJson', W[MK18], {'Name': 'PLA infantry QBZ URGI', 'HUDName': 'QBZ URGI'})
    urgi_a = g.add('AmmunitionsJson', A[MK18_AMMO], {'Name': 'PLA infantry QBZ URGI ammunition', 'HUDName': '5.8 mm ammunition'})
    kit = [(QBS, 0, 3), (QBS, 0, 3), (urgi, PF97, 1), (urgi, PF97, 3), (QJS, PF97, 2), (QJS, PF97, 2), (QCQ, PF97, 3), (QCQ, PF97, 4)]
    for m, (p, s, dp) in zip(MEN, kit): g.put('SquadMembersJson', m, {'PrimaryWeaponId': p, 'SpecialWeaponId': s, 'DeathPriority': dp})
    ammo = [(QBS, QBS_A, 96), (urgi, urgi_a, 240), (QJS, QJS_A, 400), (QCQ, QCQ_A, 20), (PF97, PF97_A, 1)]
    sw, wa = rows('SquadWeaponsJson', UnitId=SEA), rows('WeaponAmmunitionsJson', UnitId=SEA)
    ok(len(sw) == 4 and len(wa) == 4, ('Sea Dragons card / ammo rows', len(sw), len(wa)))
    for i, (w, a, q) in enumerate(ammo):
        if i < 4: g.put('SquadWeaponsJson', sw[i]['Id'], {'WeaponId': w}); g.put('WeaponAmmunitionsJson', wa[i]['Id'], {'WeaponId': w, 'AmmunitionId': a, 'Quantity': q})
        else: g.add('SquadWeaponsJson', sw[0], {'WeaponId': w}); g.add('WeaponAmmunitionsJson', wa[0], {'WeaponId': w, 'AmmunitionId': a, 'Quantity': q})
    ua = rows('UnitArmorsJson', UnitId=SEA); ok(len(ua) == 1, 'one armour row'); g.put('UnitArmorsJson', ua[0]['Id'], {'ArmorId': ELITE8})
    g.put('Units', SEA, {'Cost': 70})   # 10:4x 'Sea Dragons 70 points' (was 65)
    card = rows('SpecializationAvailabilitiesJson', UnitId=SEA); ok(len(card) == 1 and card[0]['MaxAvailabilityXp0'] == 3, 'one card row, 3 cards')
    g.put('SpecializationAvailabilitiesJson', card[0]['Id'], {'MaxAvailabilityXp0': 2})
    # checks after
    men = rows('SquadMembersJson', UnitId=SEA)
    carried = {w for r in men for w in (r['PrimaryWeaponId'], r['SpecialWeaponId']) if w}
    ok({r['WeaponId'] for r in rows('SquadWeaponsJson', UnitId=SEA)} == carried == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=SEA)}, 'card + ammo = carried')
    same = lambda x, y, skip: all(x.get(k) == y[k] for k in y if k not in skip)
    ok(same(W[urgi], W[MK18], ('Id', 'Name', 'HUDName')) and same(A[urgi_a], A[MK18_AMMO], ('Id', 'Name', 'HUDName')), 'QBZ URGI = Mk18 CQBR stats')
    ok(len(men) == 8 and sum(r['SpecialWeaponId'] == PF97 for r in men) == 6, '8 men, 6 PF-97')
    got = sorted((wn(r['PrimaryWeaponId']), wn(r['SpecialWeaponId']), r['DeathPriority']) for r in men)
    rec['pla_light_brigade_jiaolong_1126'] = {'urgi': urgi, 'urgi_ammo': urgi_a, 'kit': got, 'cost': 70, 'cards': 2}
    print('PLA LIGHT BRIGADE JIAOLONG', rec['pla_light_brigade_jiaolong_1126'])

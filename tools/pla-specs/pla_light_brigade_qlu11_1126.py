"""PLA Light Brigade build, PLAAF QLU-11 Team (Osama 26 Nov 2026 02:1x PST, thread 1567745029781454889: "PLAAF QLU-11 Team regains 1 more man(4 total)
and second QLU-11. 60 points"). Branch codex/batch/osama/pla-light-brigade only.
- QLU-11 Team (1140, PLAAF): 3 -> 4 men; the new man carries a second QLU-11 (death priority 2, like the CAAT's QLU-11 gunner), copied from the
  QLU-11 gunner's row; his member row comes from the 'plb' reserved block. Ammo per carrier unchanged (QLU-11 120), so the team carries twice the
  QLU-11 rounds. Armour 'Armor Infantry 3Men' (79: 6, 15 HP) -> vanilla 'Armor Infantry 4Men' (80: 6, 20 HP). 45 -> 60 pts."""
TEAM, GUNNER, ARM3, ARM4 = 1140, 2014895, 79, 80


def apply(t, g, ok, rec):
    U, W, SM, AR = t['Units'], t['WeaponsJson'], t['SquadMembersJson'], t['ArmorsJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    wn = lambda i: W[i]['HUDName'] if i else ''
    men = rows('SquadMembersJson', UnitId=TEAM)
    ok(U[TEAM]['HUDName'] == 'QLU-11 Team' and U[TEAM]['Cost'] == 45 and len(men) == 3 and wn(SM[GUNNER]['PrimaryWeaponId']) == 'QLU-11', 'QLU-11 Team: 3 men, 45 pts')
    ok((AR[ARM3]['Name'], AR[ARM3]['MaxHealthPoints'], AR[ARM4]['Name'], AR[ARM4]['ArmorValue'], AR[ARM4]['MaxHealthPoints']) == ('Armor Infantry 3Men', 15, 'Armor Infantry 4Men', 6, 20)
       and AR[ARM3]['ArmorValue'] == 6, 'armour rows 3 / 4 men')
    g.add('SquadMembersJson', SM[GUNNER], {'DeathPriority': 2})
    ua = rows('UnitArmorsJson', UnitId=TEAM); ok(len(ua) == 1 and ua[0]['ArmorId'] == ARM3, 'one armour row (3 men)')
    g.put('UnitArmorsJson', ua[0]['Id'], {'ArmorId': ARM4})
    g.put('Units', TEAM, {'Cost': 60})
    men = rows('SquadMembersJson', UnitId=TEAM)
    kit = sorted((wn(r['PrimaryWeaponId']), wn(r['SpecialWeaponId']), r['DeathPriority']) for r in men)
    ok(len(men) == 4 and sum(wn(r['PrimaryWeaponId']) == 'QLU-11' for r in men) == 2, ('4 men, 2 QLU-11', kit))
    rec['pla_light_brigade_qlu11_1126'] = {'kit': kit, 'cost': 60, 'armour': ARM4}
    print('PLA LIGHT BRIGADE QLU-11 TEAM', rec['pla_light_brigade_qlu11_1126'])

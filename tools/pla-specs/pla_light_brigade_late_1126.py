"""PLA Light Brigade build, late requests (Osama 26 Nov 2026 04:0x PST, thread 1567745029781454889). Branch codex/batch/osama/pla-light-brigade only;
inside g.scope('plb'), after the PAP and ZSL-92 sections.
- "PAP Patrol renamed (高寒山地特战分队(Mountaineers))" / "Rifle patrol, change to Mountaineers": PAP Rifle Patrol (1196) card name ->
  'Mountaineers 高寒山地特战分队' (Osama gave both names). Kit, price, cards unchanged; the PAP AA Patrol keeps its name.
- "base ZBD-04 given to the PLAN": the plain ZBD-04 row 1308 (card name 'ZBD-04', 65 pts, 7 seats, the ZBD-04 model; its only card is in the hidden
  test spec 26) gets a PLAN Vehicles-tab card, a copy of that row (2 cards). The ZBD-04A stays a transport.
- "猛虎旅 this is Tiger Brigade's name": Tiger Brigade (the new Marines assault squad) card name -> 'Tiger Brigade 猛虎旅'.
- "Jiutian moved to light CAB": Jiutian UAV (1095) card row 2008949 (4 cards) PLAN -> Light CAB.
- 04:1x "for the time being, the QLZ-87 uses the QLU-11 model": the squads that carry a QLZ-87 (Falcons, Tiger Brigade) get a squad copy of the
  QLZ-87 (same stats and name) whose 3D model is the QLU-11's ('M32'; was 'AGS30', the tripod), and that soldier uses the squad's normal body in
  place of the AGS crew body. The QLZ-87 Teams keep the tripod QLZ-87 (04:2x: "the QLZ-87 team for the rocket reservists use a tripod version,
  this is seperate from all of our new ones. The new ones are the hand held version that have the QLU-11 model for now").
- 04:2x "Qirborne, QJY-88 replaced with QJB-161": Airborne 空降兵 (1136, PLAAF): its QJY-88 gunner carries the QJS-161 (2011922, the 5.8 mm LMG;
  there is no QJB-161 row, read as the QJS-161), 400 rounds as its other China rows. Card + ammo rows follow.
- 04:5x "FK-3000 given to light CAB": FK-3000 (1447) gets a Light CAB card, a copy of its Medium CAB row (4 cards); the Medium CAB keeps it
  ("given", as the Z-20 / Z-18 cards).
- 04:5x "Taishan eagles 3x QJs-161, remove QTS and 2x QBu-191": Taishan Eagles 泰山雄鹰 (1203, Medium CAB): the QTS-11 man (and his QTS-11
  grenade launcher) and the 2 QBU-191 men carry the QJS-161 (400 rounds each, death priority 2); the PF-89 stays with its carrier. 6 men stay."""
PATROL, ZBD04, PLAN = 1196, 1308, 20
JIUTIAN, JIUTIAN_ROW = 1095, 2008949
QLZ87, QLU11 = 2012157, 2004002
AIRBORNE, QJS161, QJS161_A = 1136, 2011922, 2011923
FK3000 = 1447
TAISHAN = 1203


def apply(t, g, ok, rec):
    U, S = t['Units'], t['SpecializationsJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok(U[PATROL]['HUDName'] == 'PAP Rifle Patrol' and not any(u and u.get('HUDName', '').startswith('Mountaineers') for u in U.values()), 'PAP Rifle Patrol; name free')
    g.put('Units', PATROL, {'HUDName': 'Mountaineers 高寒山地特战分队'})
    ok(U[ZBD04]['HUDName'] == 'ZBD-04' and U[ZBD04]['Name'] == 'PLA ZBD-04 Rocket Force' and U[ZBD04].get('CategoryType') == 2, 'plain ZBD-04 row 1308 (Vehicles tab)')
    src = rows('SpecializationAvailabilitiesJson', UnitId=ZBD04)
    ok(len(src) == 1 and src[0]['SpecializationId'] == 26 and S[PLAN]['UIName'].startswith('PLAN Naval'), ('ZBD-04: one card row in hidden spec 26', src))
    g.add('SpecializationAvailabilitiesJson', src[0], {'SpecializationId': PLAN}); g.put('Units', ZBD04, {'DisplayInArmory': True})
    ok(rows('SpecializationAvailabilitiesJson', UnitId=ZBD04, SpecializationId=PLAN), 'ZBD-04 card in PLAN')
    tb = [i for i, u in U.items() if u and u.get('HUDName') == 'Tiger Brigade']
    ok(len(tb) == 1 and U[tb[0]]['Name'] == 'PLA Tiger Brigade', 'Tiger Brigade row'); g.put('Units', tb[0], {'HUDName': 'Tiger Brigade 猛虎旅'})
    light = next(s['Id'] for s in S.values() if s and s.get('UIName', '').startswith('PLAGF Light Combined Arms Brigade'))
    SA = t['SpecializationAvailabilitiesJson']
    ok(U[JIUTIAN]['HUDName'] == 'Jiutian UAV' and SA[JIUTIAN_ROW]['UnitId'] == JIUTIAN and SA[JIUTIAN_ROW]['SpecializationId'] == PLAN and len(rows('SpecializationAvailabilitiesJson', UnitId=JIUTIAN)) == 1, 'Jiutian: one PLAN card row')
    g.put('SpecializationAvailabilitiesJson', JIUTIAN_ROW, {'SpecializationId': light})
    W = t['WeaponsJson']
    ok(W[QLZ87]['ModelFileName'] == 'AGS30' and W[QLU11]['HUDName'] == 'QLU-11', 'QLZ-87 tripod model, QLU-11')
    sq = g.add('WeaponsJson', W[QLZ87], {'Name': 'PLA infantry QLZ-87 squad (QLU-11 model)', 'ModelFileName': W[QLU11]['ModelFileName'], 'HUDIcon': 'FA_PLA_WP_QLZ87'})
    squads = [1185] + [i for i, u in U.items() if u and u.get('Name') == 'PLA Tiger Brigade']
    for u in squads:
        men = rows('SquadMembersJson', UnitId=u); body = next(r['ModelFileName'] for r in men if r['PrimaryWeaponId'] != QLZ87)
        q = [r for r in men if r['PrimaryWeaponId'] == QLZ87]; ok(len(q) == 1, ('one QLZ-87 man', u))
        g.put('SquadMembersJson', q[0]['Id'], {'PrimaryWeaponId': sq, 'ModelFileName': body})
        for tab in ('SquadWeaponsJson', 'WeaponAmmunitionsJson'):
            for r in rows(tab, UnitId=u, WeaponId=QLZ87): g.put(tab, r['Id'], {'WeaponId': sq})
        ok(not rows('WeaponAmmunitionsJson', UnitId=u, WeaponId=QLZ87) and rows('WeaponAmmunitionsJson', UnitId=u, WeaponId=sq), ('QLZ-87 squad copy rows', u))
    q88 = rec['backpocket_weapons_1125']['QJY-88']['weapon']
    am = rows('SquadMembersJson', UnitId=AIRBORNE); g88 = [r for r in am if r['PrimaryWeaponId'] == q88]
    ok(U[AIRBORNE]['HUDName'] == 'Airborne 空降兵' and len(g88) == 1 and W[QJS161]['HUDName'] == 'QJS-161', ('Airborne: one QJY-88 gunner', len(g88)))
    g.put('SquadMembersJson', g88[0]['Id'], {'PrimaryWeaponId': QJS161})
    for r in rows('SquadWeaponsJson', UnitId=AIRBORNE, WeaponId=q88): g.put('SquadWeaponsJson', r['Id'], {'WeaponId': QJS161})
    for r in rows('WeaponAmmunitionsJson', UnitId=AIRBORNE, WeaponId=q88): g.put('WeaponAmmunitionsJson', r['Id'], {'WeaponId': QJS161, 'AmmunitionId': QJS161_A, 'Quantity': 400})
    carried = {w for r in rows('SquadMembersJson', UnitId=AIRBORNE) for w in (r['PrimaryWeaponId'], r['SpecialWeaponId']) if w}
    ok({r['WeaponId'] for r in rows('SquadWeaponsJson', UnitId=AIRBORNE)} == carried == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=AIRBORNE)} and q88 not in carried, 'Airborne: card + ammo = carried, no QJY-88')
    fk = rows('SpecializationAvailabilitiesJson', UnitId=FK3000)
    ok(U[FK3000]['HUDName'] == 'FK-3000' and len(fk) == 1 and fk[0]['SpecializationId'] == 21, 'FK-3000: one Medium CAB card row')
    g.add('SpecializationAvailabilitiesJson', fk[0], {'SpecializationId': light})
    tm = rows('SquadMembersJson', UnitId=TAISHAN)
    sw = [r for r in tm if W[r['PrimaryWeaponId']]['HUDName'] in ('QTS-11', 'QBU-191')]
    ok(U[TAISHAN]['HUDName'] == 'Taishan Eagles 泰山雄鹰' and len(tm) == 6 and len(sw) == 3, ('Taishan Eagles: 1 QTS-11 + 2 QBU-191', len(sw)))
    for r in sw:
        g.put('SquadMembersJson', r['Id'], {'PrimaryWeaponId': QJS161, 'DeathPriority': 2, **({'SpecialWeaponId': 0} if W[r['SpecialWeaponId']]['HUDName'] == 'QTS-11 grenade launcher' else {})} if r['SpecialWeaponId'] else {'PrimaryWeaponId': QJS161, 'DeathPriority': 2})
    carried = {w for r in rows('SquadMembersJson', UnitId=TAISHAN) for w in (r['PrimaryWeaponId'], r['SpecialWeaponId']) if w}
    tw, ta = rows('SquadWeaponsJson', UnitId=TAISHAN), rows('WeaponAmmunitionsJson', UnitId=TAISHAN)
    for r in tw:
        if r['WeaponId'] not in carried: g.remove('SquadWeaponsJson', r['Id'])
    for r in ta:
        if r['WeaponId'] not in carried: g.remove('WeaponAmmunitionsJson', r['Id'])
    g.add('SquadWeaponsJson', tw[0], {'WeaponId': QJS161, 'Order': max(r['Order'] for r in tw) + 1})
    g.add('WeaponAmmunitionsJson', ta[0], {'WeaponId': QJS161, 'AmmunitionId': QJS161_A, 'Quantity': 400})
    ok({r['WeaponId'] for r in rows('SquadWeaponsJson', UnitId=TAISHAN)} == carried == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=TAISHAN)}
       and sum(r['PrimaryWeaponId'] == QJS161 for r in rows('SquadMembersJson', UnitId=TAISHAN)) == 3, 'Taishan Eagles: 3 QJS-161, card + ammo = carried')
    # 26 Nov 10:5x "zzzc-06 moved to PLAN Navy": ZZC-06 (1420, Recon tab) card row 2018376 (4 cards) Heavy CAB (18) -> PLAN.
    ok(U[1420]['HUDName'] == 'ZZC-06' and SA[2018376]['UnitId'] == 1420 and SA[2018376]['SpecializationId'] == 18 and len(rows('SpecializationAvailabilitiesJson', UnitId=1420)) == 1, 'ZZC-06: one Heavy CAB card row')
    g.put('SpecializationAvailabilitiesJson', 2018376, {'SpecializationId': PLAN})
    rec['pla_light_brigade_late_1126'] = {'mountaineers': PATROL, 'zbd04_plan_cards': src[0]['MaxAvailabilityXp0']}
    print('PLA LIGHT BRIGADE LATE', rec['pla_light_brigade_late_1126'])

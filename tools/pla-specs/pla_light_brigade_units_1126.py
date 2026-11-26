"""PLA Light Brigade build, new and returning cards (Osama 26 Nov 2026 01:4x PST, thread 1567745029781454889: "HQ-22 (we have the model) which is a
clone of the HQ-9A goes to Marines" / "leave in the notes I'm gonna chip away a bit at its range"; "J-50 reactivated for PLAN Air tab"; "Light CAB gets
access to SX2121"; roadmap 25 Nov: "split SOF off from PLAN to make PLAGF light CAB"). Branch codex/batch/osama/pla-light-brigade only.
All new rows take IDs from the 'plb' block in mod/id-reservations.json (run inside g.scope('plb')), so they never collide with live rows at merge.
- HQ-22: full copy of the HQ-9A (1233: 145 pts, armour and missile loadouts) with its own unit, armour and mobility rows; 2 cards (the HQ-9A's count) in
  PLAN Naval/Special Forces (spec 20, the China marines). Stats are the HQ-9A's until Osama cuts its range. Model: models.json key 'PLA HQ-22' = the
  HQ-9A's HQ-22 model (m_hq22g, already in Assets), added in the model stage at build time.
- J-50 (944, 300 pts, no card since before 0.9.2): back in PLAN Naval/Special Forces (air tab by unit type), 2 cards like the J-35 / J-36 there.
- PLAGF Light Combined Arms Brigade 陆军轻型合成旅: new China spec, slots and points copied from the Medium CAB (21) until set. First card: Shaanxi SX2121
  (1269), 4 cards as in its other specs (01:4x "Light CAB gets access to SX2121").
- Moves into the Light CAB, each card row keeping its count; the deck tab comes from the unit's CategoryType, unchanged (01:4x-01:5x):
  from the Medium CAB "SR-5, HQ-7B, PCL-181, PLL-05, and HQ-11 moved away from medium cab"; from PLAN "LY-1 goes to Light CAB" and "Beijing Swords,
  Mountain Leopards, Whistling Arrows, WZ-8 go to Light CAB Recon" (all four are Recon-tab units).
- FK-2000: Medium CAB -> PLAN ("FK-2000 goes to PLAN").
- 01:5x "Blood Wolves, falcons, godswords, PAP snow leopards go to Light CAB, Sea Dragons currently will get swapped for another kit, but they are copied to
  Light cab but call the new one (test SF). Sea Draongs will be made into SF stand off and cqc": the four squads move PLAN -> Light CAB; Test SF = a copy
  of Sea Dragons 蛟龙 (1191: squad, card count 3 and its 4 transports) in the Light CAB. Sea Dragons stay in PLAN until their SF Stand-off / CQC kits."""
HQ9A, J50, SX2121, PLAN, MEDIUM = 1233, 944, 1269, 20, 21
LIGHT = 'light'
MOVES = [  # (card row, unit, HUDName, from spec, to spec)
    (2014522, 934, 'SR-5', MEDIUM, LIGHT), (2008208, 925, 'HQ-7B', MEDIUM, LIGHT), (2021476, 1034, 'PCL-181', MEDIUM, LIGHT),
    (2008210, 926, 'PLL-05', MEDIUM, LIGHT), (2008891, 1046, 'HQ-11', MEDIUM, LIGHT), (2019451, 1275, 'LY-1', PLAN, LIGHT),
    (2013297, 1187, 'Beijing Swords 蓝剑', PLAN, LIGHT), (2013270, 1186, 'Mountain Leopards 高原雪豹', PLAN, LIGHT),
    (2013204, 1184, 'Whistling Arrows 响箭', PLAN, LIGHT), (2008264, 1252, 'WZ-8', PLAN, LIGHT), (2008222, 935, 'FK-2000', MEDIUM, PLAN),
    (2013175, 1183, 'Blood Wolves 朱日和之狼', PLAN, LIGHT), (2013239, 1185, 'Falcons 猎鹰', PLAN, LIGHT), (2013107, 1181, 'Godswords 东方神剑', PLAN, LIGHT),
    (2013140, 1182, 'PAP Snow Leopards 雪豹', PLAN, LIGHT)]
SEA_DRAGONS = 1191
LIGHT_UI = 'PLAGF Light Combined Arms Brigade 陆军轻型合成旅'


def apply(t, g, ok, rec):
    U, S, SA = t['Units'], t['SpecializationsJson'], t['SpecializationAvailabilitiesJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok(U[HQ9A]['HUDName'] == 'HQ-9A' and U[HQ9A]['Cost'] == 145 and U[J50]['Name'] == 'PLA J-50' and U[SX2121]['HUDName'].strip() == 'Shaanxi SX2121',
       ('HQ-9A, J-50, SX2121 rows', U[HQ9A]['Name'], U[HQ9A]['Cost'], U[J50]['Name'], U[SX2121]['HUDName']))
    ok(S[PLAN]['UIName'].startswith('PLAN Naval') and S[MEDIUM]['UIName'].startswith('PLAGF Medium'), 'specs 20 / 21')
    # HQ-22 = HQ-9A copy
    ok(not any(u and 'HQ-22' in (u.get('Name', ''), u.get('HUDName', '')) for u in U.values()), 'HQ-22 name free')
    uid = g.add('Units', U[HQ9A], {'Name': 'PLA HQ-22', 'HUDName': 'HQ-22', 'OriginalCost': 0, 'Description': None, 'OriginalName': None, 'DisplayInArmory': True})
    for tab, field, target in (('UnitArmorsJson', 'ArmorId', 'ArmorsJson'), ('UnitPropulsionsJson', 'MobilityId', 'MobilityJson')):
        for r in rows(tab, UnitId=HQ9A):
            g.add(tab, r, {'UnitId': uid, field: g.add(target, t[target][r[field]], {'Name': f'{t[target][r[field]]["Name"]} HQ-22'})})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson'):
        for r in rows(tab, UnitId=HQ9A): g.add(tab, r, {'UnitId': uid})
    for m in rows('ModificationsJson', UnitId=HQ9A):
        nm = g.add('ModificationsJson', m, {'UnitId': uid, 'Name': m['Name'].replace('HQ-9A', 'HQ-22')})
        for o in rows('OptionsJson', ModificationId=m['Id']): g.add('OptionsJson', o, {'ModificationId': nm, 'Name': o['Name'].replace('HQ-9A', 'HQ-22')})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitArmorsJson', 'UnitPropulsionsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson', 'ModificationsJson'):
        ok(len(rows(tab, UnitId=uid)) == len(rows(tab, UnitId=HQ9A)), ('HQ-22', tab, 'copied'))
    hq9a_card = rows('SpecializationAvailabilitiesJson', UnitId=HQ9A)
    ok(len(hq9a_card) == 1 and hq9a_card[0]['MaxAvailabilityXp0'] == 2, 'HQ-9A: one card row, 2 cards')
    g.add('SpecializationAvailabilitiesJson', hq9a_card[0], {'UnitId': uid, 'SpecializationId': PLAN})
    # J-50 back in PLAN
    j35 = [r for r in rows('SpecializationAvailabilitiesJson', SpecializationId=PLAN) if U[r['UnitId']]['HUDName'] == 'J-35']
    ok(len(j35) == 1 and j35[0]['MaxAvailabilityXp0'] == 2 and not rows('SpecializationAvailabilitiesJson', UnitId=J50), 'J-35 PLAN row (2 cards); J-50 has no card')
    g.add('SpecializationAvailabilitiesJson', j35[0], {'UnitId': J50})
    g.put('Units', J50, {'DisplayInArmory': True})
    # PLAGF Light CAB + SX2121
    ok(not any(s and s.get('UIName') == LIGHT_UI for s in S.values()), 'Light CAB not there yet')
    light = g.add('SpecializationsJson', S[MEDIUM], {'Name': 'PLA PLAGF Light', 'UIName': LIGHT_UI})
    sx = [r for r in rows('SpecializationAvailabilitiesJson', UnitId=SX2121) if r['SpecializationId'] == PLAN]
    ok(len(sx) == 1, 'SX2121 PLAN row')
    g.add('SpecializationAvailabilitiesJson', sx[0], {'SpecializationId': light})
    moved = []
    for row, unit, hud, frm, to in MOVES:
        to = light if to == LIGHT else to
        r = SA[row]
        ok(r['UnitId'] == unit and U[unit]['HUDName'].strip() == hud and r['SpecializationId'] == frm, ('card row before', hud, row, r['SpecializationId']))
        ok(not [x for x in SA.values() if x and x['UnitId'] == unit and x['SpecializationId'] == to], (hud, 'already in spec', to))
        g.put('SpecializationAvailabilitiesJson', row, {'SpecializationId': to})
        moved.append((hud, frm, to, r['MaxAvailabilityXp0'], U[unit].get('CategoryType', 0)))
    ok(all(c == 0 for h, f, to, n, c in moved if h.startswith(('Beijing', 'Mountain', 'Whistling', 'WZ-8'))), ('Recon-tab units', moved))
    # Test SF = copy of Sea Dragons in the Light CAB
    sd = U[SEA_DRAGONS]; ok(sd['HUDName'] == 'Sea Dragons 蛟龙' and not rows('ModificationsJson', UnitId=SEA_DRAGONS), 'Sea Dragons 1191, no loadouts')
    ok(not any(u and 'Test SF' in (u.get('Name', ''), u.get('HUDName', '')) for u in U.values()), 'Test SF name free')
    tsf = g.add('Units', sd, {'Name': 'PLA Test SF', 'HUDName': 'Test SF', 'OriginalCost': 0, 'Description': None, 'OriginalName': None})
    for tab in ('SquadMembersJson', 'SquadWeaponsJson', 'WeaponAmmunitionsJson', 'UnitArmorsJson', 'UnitPropulsionsJson', 'UnitAbilitiesJson', 'SensorUnitsJson'):
        for r in rows(tab, UnitId=SEA_DRAGONS): g.add(tab, r, {'UnitId': tsf})
        ok(len(rows(tab, UnitId=tsf)) == len(rows(tab, UnitId=SEA_DRAGONS)), ('Test SF', tab, 'copied'))
    sdc = rows('SpecializationAvailabilitiesJson', UnitId=SEA_DRAGONS); ok(len(sdc) == 1 and sdc[0]['SpecializationId'] == PLAN, 'Sea Dragons: one PLAN card row')
    nc = g.add('SpecializationAvailabilitiesJson', sdc[0], {'UnitId': tsf, 'SpecializationId': light})
    for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=sdc[0]['Id']): g.add('TransportAvailabilitiesJson', r, {'SpecializationAvailabilityId': nc})
    ok(sorted(r['UnitId'] for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=nc)) == sorted(r['UnitId'] for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=sdc[0]['Id'])),
       'Test SF transports = Sea Dragons')
    got = {U[r['UnitId']]['HUDName']: (r['SpecializationId'], r['MaxAvailabilityXp0']) for r in rows('SpecializationAvailabilitiesJson')
           if r['UnitId'] in (uid, J50, SX2121, tsf) and r['SpecializationId'] in (PLAN, light)}
    ok(got.get('HQ-22') == (PLAN, 2) and got.get('J-50') == (PLAN, 2) and SA and any(r['UnitId'] == SX2121 and r['SpecializationId'] == light for r in rows('SpecializationAvailabilitiesJson')),
       ('cards placed', got))
    rec['pla_light_brigade_units_1126'] = {'hq22': uid, 'test_sf': tsf, 'light_cab_spec': light, 'cards': got, 'moved': moved}
    print('PLA LIGHT BRIGADE UNITS', rec['pla_light_brigade_units_1126'])

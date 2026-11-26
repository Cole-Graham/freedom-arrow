"""PLA Light Brigade build, late requests (Osama 26 Nov 2026 04:0x PST, thread 1567745029781454889). Branch codex/batch/osama/pla-light-brigade only;
inside g.scope('plb'), after the PAP and ZSL-92 sections.
- "PAP Patrol renamed (高寒山地特战分队(Mountaineers))" / "Rifle patrol, change to Mountaineers": PAP Rifle Patrol (1196) card name ->
  'Mountaineers 高寒山地特战分队' (Osama gave both names). Kit, price, cards unchanged; the PAP AA Patrol keeps its name.
- "base ZBD-04 given to the PLAN": the plain ZBD-04 row 1308 (card name 'ZBD-04', 65 pts, 7 seats, the ZBD-04 model; its only card is in the hidden
  test spec 26) gets a PLAN Vehicles-tab card, a copy of that row (2 cards). The ZBD-04A stays a transport.
- "猛虎旅 this is Tiger Brigade's name": Tiger Brigade (the new Marines assault squad) card name -> 'Tiger Brigade 猛虎旅'.
- "Jiutian moved to light CAB": Jiutian UAV (1095) card row 2008949 (4 cards) PLAN -> Light CAB."""
PATROL, ZBD04, PLAN = 1196, 1308, 20
JIUTIAN, JIUTIAN_ROW = 1095, 2008949


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
    rec['pla_light_brigade_late_1126'] = {'mountaineers': PATROL, 'zbd04_plan_cards': src[0]['MaxAvailabilityXp0']}
    print('PLA LIGHT BRIGADE LATE', rec['pla_light_brigade_late_1126'])

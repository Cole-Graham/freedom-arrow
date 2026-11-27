"""PLA Light Brigade build, Moto. Riflemen and transports (Osama 26 Nov 2026 02:2x PST, thread 1567745029781454889: "Moto Riflemen moved to Light CAB.";
"ZBL-08 also available for PLAN"; "WZ-551 for Light cab"). Branch codex/batch/osama/pla-light-brigade only; after the Light CAB spec exists.
- Moto. Riflemen 摩步班 (1196, card row 2013580): Medium CAB (21) -> Light CAB, with its transports.
- ZBL-08 (903, transport only): offered as a transport on every PLAN (20) infantry card that offers the ZBD-05 (copy of that row).
- WZ-551 (962, unused before): offered as a transport on every Light CAB infantry card that already rides a ground vehicle (copy of that card's
  first ground-vehicle row). New rows come from the 'plb' reserved block.
- Z-10U (1270, card row 2019264): PLAN (20) -> Light CAB ("Z-10U goes to Light CAB", 02:2x).
- 02:3x "Z-20 given to light CAB and Z-18": Light CAB cards for the Z-20 (1244, as its Heavy CAB row: 2 cards) and the Z-18 (1271, as its PLAN row:
  2 cards); both keep their current cards. Light CAB infantry already ride the Z-20J.
- 02:4x "Z-11WB copied to light CAB, Z-19 recon moved to Light cab recon tab. CSK-131 recon given to Light cab (*this is available for everyone). Z-20J
  and Z-20T are both copied to Light CAB": Light CAB cards (copies of an existing card row, same count) for Z-11WB (942, 4), CSK-131 Recon (1265, 4),
  Z-20J (1238, 2), Z-20T (1245, 2). Z-19 Recon (1134 'PLA Recon Z-19', Recon tab, 75 pts) had no card in any 0.9 build: it gets a Light CAB card
  with the Z-19's count (2, copy of the Z-19 1103 row) and DisplayInArmory on; the Medium CAB attack Z-19 card stays."""
MOTO, MOTO_ROW, ZBL08, WZ551, PLAN, MEDIUM, Z10U, Z10U_ROW = 1196, 2013580, 903, 962, 20, 21, 1270, 2019264


def apply(t, g, ok, rec):
    U, SA, TA, S = t['Units'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson'], t['SpecializationsJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    light = next(s['Id'] for s in S.values() if s and s.get('UIName', '').startswith('PLAGF Light Combined Arms Brigade'))
    ok(U[MOTO]['HUDName'].startswith('Moto. Riflemen') and SA[MOTO_ROW]['UnitId'] == MOTO and SA[MOTO_ROW]['SpecializationId'] == MEDIUM, 'Moto. Riflemen card in Medium CAB')
    g.put('SpecializationAvailabilitiesJson', MOTO_ROW, {'SpecializationId': light})
    ok(U[Z10U]['HUDName'] == 'Z-10U' and SA[Z10U_ROW]['UnitId'] == Z10U and SA[Z10U_ROW]['SpecializationId'] == PLAN, 'Z-10U card in PLAN')
    g.put('SpecializationAvailabilitiesJson', Z10U_ROW, {'SpecializationId': light})
    ok(U[ZBL08]['HUDName'] == 'ZBL-08' and U[WZ551]['HUDName'] == 'WZ-551' and not rows('TransportAvailabilitiesJson', UnitId=WZ551), 'ZBL-08, WZ-551 (no transport rows yet)')
    zbd05 = next(i for i, u in U.items() if u and u.get('HUDName') == 'ZBD-05' and rows('TransportAvailabilitiesJson', UnitId=i))
    card = lambda r: SA[r['SpecializationAvailabilityId']]
    plan = [r for r in rows('TransportAvailabilitiesJson', UnitId=zbd05) if card(r)['SpecializationId'] == PLAN]
    ok(plan, 'PLAN infantry cards with the ZBD-05')
    zbl_cards = []
    for r in plan:
        if not rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=r['SpecializationAvailabilityId'], UnitId=ZBL08):
            g.add('TransportAvailabilitiesJson', r, {'UnitId': ZBL08}); zbl_cards.append(U[card(r)['UnitId']]['HUDName'])
    ground = lambda uid: U[uid].get('Type') == 4   # ground vehicle (not helicopter / plane)
    wz_cards = []
    for c in rows('SpecializationAvailabilitiesJson', SpecializationId=light):
        if U[c['UnitId']].get('CategoryType', 0) != 1: continue   # infantry tab
        tr = [r for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=c['Id']) if ground(r['UnitId'])]
        if tr and not any(r['UnitId'] == WZ551 for r in tr):
            g.add('TransportAvailabilitiesJson', tr[0], {'UnitId': WZ551}); wz_cards.append(U[c['UnitId']]['HUDName'])
    ok(zbl_cards and wz_cards, ('transports added', zbl_cards, wz_cards))
    heli = []
    for uid, hud, frm in ((1244, 'Z-20', 18), (1271, 'Z-18', PLAN)):
        src = rows('SpecializationAvailabilitiesJson', UnitId=uid)
        ok(U[uid]['HUDName'] == hud and len(src) == 1 and src[0]['SpecializationId'] == frm, (hud, 'one card row in', frm))
        g.add('SpecializationAvailabilitiesJson', src[0], {'SpecializationId': light}); heli.append((hud, src[0]['MaxAvailabilityXp0']))
    for uid, hud, frm in ((942, 'Z-11WB', MEDIUM), (1265, 'CSK-131 Recon', PLAN), (1238, 'Z-20J', PLAN), (1245, 'Z-20T', PLAN)):
        src = [r for r in rows('SpecializationAvailabilitiesJson', UnitId=uid) if r['SpecializationId'] == frm]
        ok(U[uid]['HUDName'] == hud and len(src) == 1 and not rows('SpecializationAvailabilitiesJson', UnitId=uid, SpecializationId=light), (hud, 'card in', frm))
        g.add('SpecializationAvailabilitiesJson', src[0], {'SpecializationId': light}); heli.append((hud, src[0]['MaxAvailabilityXp0']))
    z19 = rows('SpecializationAvailabilitiesJson', UnitId=1103)
    ok(U[1134]['HUDName'] == 'Z-19 Recon' and U[1134].get('CategoryType', 0) == 0 and not rows('SpecializationAvailabilitiesJson', UnitId=1134) and len(z19) == 1,
       'Z-19 Recon 1134 (Recon tab, no card), Z-19 1103 card')
    g.add('SpecializationAvailabilitiesJson', z19[0], {'UnitId': 1134, 'SpecializationId': light}); g.put('Units', 1134, {'DisplayInArmory': True})
    heli.append(('Z-19 Recon', z19[0]['MaxAvailabilityXp0']))
    rec['pla_light_brigade_transports_1126'] = {'moto_riflemen_spec': light, 'zbl08_plan': zbl_cards, 'wz551_light_cab': wz_cards, 'light_cab_helicopters': heli}
    print('PLA LIGHT BRIGADE TRANSPORTS', rec['pla_light_brigade_transports_1126'])

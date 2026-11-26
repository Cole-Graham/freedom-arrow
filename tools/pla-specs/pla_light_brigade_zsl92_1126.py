"""PLA Light Brigade build, ZSL-92 transports, HQ-17A and PHL-03 (Osama 26 Nov 2026 03:5x PST, thread 1567745029781454889). Branch
codex/batch/osama/pla-light-brigade only; inside g.scope('plb'), after every Light CAB infantry card exists.
- "ZSL-92 transport, basically a BTR with a 50 cal and 8 seats) / ZSL-92B transport, basically a BTR with autocannon and 8 seats. add to light CAB":
  both rows exist (8 infantry seats each, models in Assets 0.2.104 under their Names, which stay):
  - ZSL-92 = 1232 'PLA ZSL-92 MG' (QJC-88 12.7 mm, 25 pts), card name 'ZSL-92' (unchanged).
  - ZSL-92B = 1079 'PLA Catalogue ZSL-92 family' (30 mm autocannon + Type 86 7.62 mm, 35 pts): card name 'ZSL-92' -> 'ZSL-92B'.
  Both are new transport choices on every Light CAB infantry-tab card that rides a ground vehicle (copies of that card's first ground row), and are
  shown in the Armory. 1079 keeps its hidden test-spec card.
- "HQ-17A moved to Light CAB": card row 2018728 (4 cards) Medium CAB -> Light CAB. "PHL-03 moved to Light CAB": 2008171 (2 cards) Heavy CAB -> Light CAB.
- "weapons squad moved to Marines": Weapons Squad 火力班 (1199) card row 2013658 (4 cards) Medium CAB -> PLAN (the China marines), keeping its transports."""
ZSL92, ZSL92B = 1232, 1079
MOVES = [(2018728, 1049, 'HQ-17A', 21, 'light'), (2008171, 908, 'PHL-03', 18, 'light'), (2013658, 1199, 'Weapons Squad 火力班', 21, 20)]


def apply(t, g, ok, rec):
    U, SA, S = t['Units'], t['SpecializationAvailabilitiesJson'], t['SpecializationsJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    light = next(s['Id'] for s in S.values() if s and s.get('UIName', '').startswith('PLAGF Light Combined Arms Brigade'))
    ok(U[ZSL92]['Name'] == 'PLA ZSL-92 MG' and U[ZSL92B]['Name'] == 'PLA Catalogue ZSL-92 family' and U[ZSL92]['HUDName'] == U[ZSL92B]['HUDName'] == 'ZSL-92'
       and U[ZSL92]['InfantrySlots'] == U[ZSL92B]['InfantrySlots'] == 8 and not rows('TransportAvailabilitiesJson', UnitId=ZSL92) and not rows('TransportAvailabilitiesJson', UnitId=ZSL92B),
       'ZSL-92 MG / family rows, 8 seats, no transport rows yet')
    g.put('Units', ZSL92B, {'HUDName': 'ZSL-92B', 'DisplayInArmory': True}); g.put('Units', ZSL92, {'DisplayInArmory': True})
    ground = lambda uid: U[uid].get('Type') == 4
    added = []
    for c in rows('SpecializationAvailabilitiesJson', SpecializationId=light):
        if U[c['UnitId']].get('CategoryType', 0) != 1: continue
        tr = [r for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=c['Id']) if ground(r['UnitId'])]
        if not tr: continue
        for v in (ZSL92, ZSL92B): g.add('TransportAvailabilitiesJson', tr[0], {'UnitId': v})
        added.append(U[c['UnitId']]['HUDName'])
    for row, unit, hud, frm, to in MOVES:
        ok(U[unit]['HUDName'] == hud and SA[row]['UnitId'] == unit and SA[row]['SpecializationId'] == frm and len(rows('SpecializationAvailabilitiesJson', UnitId=unit)) == 1, (hud, 'one card row in', frm))
        g.put('SpecializationAvailabilitiesJson', row, {'SpecializationId': light if to == 'light' else to})
    ok(added and all(rows('TransportAvailabilitiesJson', UnitId=v) for v in (ZSL92, ZSL92B)), ('ZSL-92 / 92B on Light CAB cards', added))
    rec['pla_light_brigade_zsl92_1126'] = {'zsl92_on': added, 'moved': [m[2] for m in MOVES]}
    print('PLA LIGHT BRIGADE ZSL-92', rec['pla_light_brigade_zsl92_1126'])

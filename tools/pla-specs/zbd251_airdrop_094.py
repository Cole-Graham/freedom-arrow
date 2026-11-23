"""ZBD-251 air-droppable (Osama 21 Nov 2026 21:3x PST, thread 1572407822849810463: "ZBD-251 next patch should be air droppable"). Air drop is the
mobility row's IsAirDroppable flag (vanilla: BMD-4M "Tracks BMD4M", BMD-2 "Tracks BMD2 BTRD"; China ZBD-03 already true). ZBD-251 (1056) has its own row
2010729 "PLA ZBD-251 MobilityJson", used by no other unit, so it is set in place. Speed, armour, price and specs are unchanged. Called from batch_0_9_5b.py."""
def apply(t, g, ok, rec):
    U, UP, MO = t['Units'], t['UnitPropulsionsJson'], t['MobilityJson']
    ok((U[1056].get('HUDName') or '').strip() == 'ZBD-251', ('ZBD-251 card', U[1056].get('HUDName')))
    rows = sorted({p['MobilityId'] for p in UP.values() if p and p.get('UnitId') == 1056})
    ok(rows == [2010729] and MO[2010729].get('IsAirDroppable') is False, ('ZBD-251 mobility', rows))
    ok(sorted(p['UnitId'] for p in UP.values() if p and p.get('MobilityId') == 2010729) == [1056], 'mobility 2010729 is ZBD-251 only')
    g.put('MobilityJson', 2010729, {'IsAirDroppable': True})
    rec['zbd251_airdrop'] = {'unit': 1056, 'mobility': 2010729, 'IsAirDroppable': [False, True]}

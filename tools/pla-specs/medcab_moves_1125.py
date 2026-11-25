"""HQ-7B and PLL-05 to the Medium CAB, CSK-131 9 seats (Osama 25 Nov 2026 00:3x PST, thread "China cosmetic work": "HQ-7B moved to medium
cab, CSK131 should have 9 seats now. PLL-05 moved to medium cab").
- HQ-7B (925, row 2008208, 4 cards) and PLL-05 (926, row 2008210, 3 cards): PLAAF Air Force spec 17 -> PLAGF Medium Combined Arms Brigade 21,
  same card counts (the row moves; no copy stays in 17).
- CSK-131 (1266 'PLA CSK-181 4x4', the transport card): InfantrySlots 8 -> 9. The CSK-131 Recon (1265) is not changed. Changes rows only."""
MOVES = {925: ('HQ-7B', 2008208, 4), 926: ('PLL-05', 2008210, 3)}
AIRBORNE, MEDIUM, CSK = 17, 21, 1266


def apply(t, g, ok, rec):
    U, SA, S = t['Units'], t['SpecializationAvailabilitiesJson'], t['SpecializationsJson']
    ok(S[MEDIUM]['UIName'].startswith('PLAGF Medium Combined Arms Brigade') and S[AIRBORNE]['UIName'].startswith('PLAAF Air Force'), 'specs 17 / 21')
    out = {}
    for u, (hud, row, n) in MOVES.items():
        rows = sorted((r['Id'], r['SpecializationId'], r['MaxAvailabilityXp0']) for r in SA.values() if r and r['UnitId'] == u)
        ok(U[u]['HUDName'] == hud and rows == [(row, AIRBORNE, n)], (hud, 'one airborne row', rows))
        g.put('SpecializationAvailabilitiesJson', row, {'SpecializationId': MEDIUM})
        out[hud] = sorted((r['SpecializationId'], r['MaxAvailabilityXp0']) for r in SA.values() if r and r['UnitId'] == u)
        ok(out[hud] == [(MEDIUM, n)], (hud, 'in the Medium CAB', out[hud]))
    ok(U[CSK]['HUDName'] == 'CSK-131' and U[CSK]['InfantrySlots'] == 8, ('CSK-131 transport 8 seats', U[CSK]['InfantrySlots']))
    g.put('Units', CSK, {'InfantrySlots': 9})
    rec['medcab_moves_1125'] = {**out, 'CSK-131 seats': [8, U[CSK]['InfantrySlots']]}
    print('MEDCAB MOVES', rec['medcab_moves_1125'])

"""Osama's evening fixes (26 Nov 2026 20:2x PST, thread 1567745029781454889). Live section on codex/development; edits existing rows only.
- "remove the Type-74": the two Blue Dragon (Preview) Type 74 cards (Type 74 STB-2 1282: row 2019673; Type 74 (G) 1285: row 2019695; 4 cards each,
  no transports) are removed. The unit rows stay, so no other ID moves; without a card they are not in the Arsenal.
- "Leopard 2A8 PSO is missing its APS (2 charges)": the 0.9.3 base put a non-APS copy of the Trophy (2000207, IsAPS off) on the Leopard 2A8 (503,
  DLC2) and both armour options keep slot 2 empty, as in vanilla. The PSO option (2116, +5) now fills slot 2 with the vanilla Trophy row 93 (APS,
  2 charges since aps_two_charges_1125; the M1A1 FEP's Trophy option uses the same row), and the unit's ability row 1062 lists 93 again in place of
  2000207. The base option (2115) stays without APS."""
TYPE74 = {1282: 2019673, 1285: 2019695}
LEO, PSO, BASE, UA_ROW, TROPHY, NOAPS = 503, 2116, 2115, 1062, 93, 2000207


def apply(t, g, ok, rec):
    U, SA, O, AB, UA = t['Units'], t['SpecializationAvailabilitiesJson'], t['OptionsJson'], t['AbilitiesJson'], t['UnitAbilitiesJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    for u, c in TYPE74.items():
        ok(U[u]['HUDName'].startswith('Type 74') and SA[c]['UnitId'] == u and len(rows('SpecializationAvailabilitiesJson', UnitId=u)) == 1, (u, 'one Type 74 card'))
        for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=c): g.remove('TransportAvailabilitiesJson', r['Id'])
        g.remove('SpecializationAvailabilitiesJson', c)
    ok(not any(rows('SpecializationAvailabilitiesJson', UnitId=u) for u in TYPE74), 'Type 74 cards gone')
    ok(U[LEO]['HUDName'] == 'Leopard 2A8' and O[PSO]['Name'] == 'Armor Leopard2A8 PSO' and O[PSO].get('Ability2Id') == 4 and O[BASE].get('Ability2Id') == 4, 'Leopard 2A8 options, slot 2 empty')
    ok(AB[TROPHY].get('IsAPS') and AB[TROPHY]['APSQuantity'] == 2 and not AB[NOAPS].get('IsAPS'), 'Trophy 93 APS x2; 2000207 not APS')
    ok(UA[UA_ROW]['UnitId'] == LEO and UA[UA_ROW]['AbilityId'] == NOAPS, 'unit ability row 1062 = 2000207')
    g.put('OptionsJson', PSO, {'Ability2Id': TROPHY})
    g.put('UnitAbilitiesJson', UA_ROW, {'AbilityId': TROPHY})
    ok(O[PSO]['Ability2Id'] == TROPHY and TROPHY in {r['AbilityId'] for r in rows('UnitAbilitiesJson', UnitId=LEO)}, 'Leopard 2A8 PSO: Trophy APS x2')
    rec['osama_fixes_1126'] = {'type74_cards_removed': list(TYPE74.values()), 'leopard2a8_pso_aps': 'Trophy 93, 2 charges'}
    print('OSAMA FIXES 1126', rec['osama_fixes_1126'])

"""M1A1 FEP Trophy: 2 APS charges, not 4 (Osama 25 Nov 2026 12:1x PST, bugs thread 1573561286803980289: "US Marines FEP Abrams seems to have extra
APS charges ... It has four currently but it should be two"). Its Trophy option uses vanilla row 93 'APS US Heavy Model Trophy' (APSQuantity 4, FA
cooldown 10), shared with the DLC2 Leopard 2A8, which keeps it. The FEP's Trophy options link an identical row with APSQuantity 2 (ability-row
reuse: an existing identical row if there is one, else a copy of 93)."""
FEP, TROPHY = 'M1A1 FEP', 93


def apply(t, g, ok, rec):
    U, AB, O, M = t['Units'], t['AbilitiesJson'], t['OptionsJson'], t['ModificationsJson']
    (fep,) = [i for i, u in U.items() if u and u.get('Name') == FEP]
    ok(AB[TROPHY]['IsAPS'] and AB[TROPHY]['APSQuantity'] == 4, ('Trophy row 93: 4 charges before', AB[TROPHY]['APSQuantity']))
    want = dict(AB[TROPHY], APSQuantity=2)
    same = [i for i, a in AB.items() if a and i != TROPHY and all(a.get(k) == v for k, v in want.items() if k not in ('Id', 'Name'))]
    row = same[0] if same else g.add('AbilitiesJson', AB[TROPHY], {'Name': 'APS US Heavy Model Trophy x2', 'APSQuantity': 2})
    slots = ('Ability1Id', 'Ability2Id', 'Ability3Id')
    opts = [(i, k) for i, o in O.items() if o and M.get(o['ModificationId'], {}).get('UnitId') == fep for k in slots if o.get(k) == TROPHY]
    ok(len(opts) >= 1, ('M1A1 FEP Trophy options', opts))
    for i, k in opts: g.put('OptionsJson', i, {k: row})
    links = [r for r in t['UnitAbilitiesJson'].values() if r and r['UnitId'] == fep and r['AbilityId'] == TROPHY]
    for r in links: g.put('UnitAbilitiesJson', r['Id'], {'AbilityId': row})
    left = [(i, k) for i, o in O.items() if o and M.get(o['ModificationId'], {}).get('UnitId') == fep for k in slots if o.get(k) == TROPHY]
    ok(not left and AB[row]['APSQuantity'] == 2 and AB[TROPHY]['APSQuantity'] == 4, 'M1A1 FEP Trophy = 2 charges; row 93 unchanged for the Leopard 2A8')
    rec['fep_aps_1125'] = {'unit': fep, 'row': row, 'options': opts, 'unit_links': [r['Id'] for r in links]}
    print('FEP APS', rec['fep_aps_1125'])

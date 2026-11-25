"""HJ-10 NLOS range = the HJ-10 FNF's (Osama 25 Nov 2026 10:1x PST, bugs thread 1573561286803980289: "HJ-10 NLOS should be 1600 meters",
"same as the FN version"). NLOS round 2009623 GroundRange 1000 -> 800, the FNF round 2019706's (card 1600 m; the card shows GroundRange x2).
MinimalRange stays 100. The option label '(laser, 2000 m)' follows.
Price (Osama 10:1x "and the NLOS should be +40 points"): option +20 -> +40; a swap row, if the option has one, = base + 40.
Supply (Osama 25 Nov 11:3x, thread 1567745029781454889: "HJ-10 NLOS should be 150kg each missile"): SupplyCost 75 -> 150, the FNF round's."""
NLOS, FNF = 2009623, 2019706


def apply(t, g, ok, rec):
    A, O = t['AmmunitionsJson'], t['OptionsJson']
    ok(A[NLOS]['Name'] == 'PLA HJ-10 HJ-10 guided missile' and A[FNF]['Name'] == 'PLA HJ-10 HJ-10 FNF missile', 'HJ-10 NLOS and FNF rounds')
    before = A[NLOS]['GroundRange']
    g.put('AmmunitionsJson', NLOS, {'GroundRange': A[FNF]['GroundRange']})
    (opt,) = [i for i, o in O.items() if o and o.get('UIName') == 'HJ-10 NLOS (laser, 2000 m)']
    g.put('OptionsJson', opt, {'UIName': 'HJ-10 NLOS (laser, 1600 m)'})
    U = t['Units']; o = O[opt]; ok(o['Cost'] == 20, ('HJ-10 NLOS option +20 before', o['Cost']))
    g.put('OptionsJson', opt, {'Cost': 40})
    r = o.get('ReplaceUnitId')
    base = t['ModificationsJson'][o['ModificationId']]['UnitId']
    if r and r != base:
        g.put('Units', r, {'Cost': U[base]['Cost'] + 40})
        ok(U[r]['Cost'] == U[base]['Cost'] + 40, 'HJ-10 NLOS swap row = base + 40')
    ok(O[opt]['Cost'] == 40, 'HJ-10 NLOS option +40')
    ok(A[NLOS]['SupplyCost'] == 75.0 and A[FNF]['SupplyCost'] == 150.0, ('HJ-10 NLOS supply 75, FNF 150 before', A[NLOS]['SupplyCost'], A[FNF]['SupplyCost']))
    g.put('AmmunitionsJson', NLOS, {'SupplyCost': 150.0})
    ok(A[NLOS]['SupplyCost'] == 150.0, 'HJ-10 NLOS 150 kg per missile')
    ok(A[NLOS]['GroundRange'] == A[FNF]['GroundRange'] == 800.0 and O[opt]['UIName'] == 'HJ-10 NLOS (laser, 1600 m)', 'HJ-10 NLOS range = FNF 800 (1600 m)')
    rec['hj10_nlos_range_1125'] = {'GroundRange': [before, A[NLOS]['GroundRange']], 'option': opt, 'cost': [20, 40], 'supply': [75.0, 150.0], 'swap_row': r if r != base else None, 'base_cost': U[base]['Cost']}
    print('HJ-10 NLOS RANGE', rec['hj10_nlos_range_1125'])

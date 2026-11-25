"""HJ-10 NLOS range = the HJ-10 FNF's (Osama 25 Nov 2026 10:1x PST, bugs thread 1573561286803980289: "HJ-10 NLOS should be 1600 meters",
"same as the FN version"). NLOS round 2009623 GroundRange 1000 -> 800, the FNF round 2019706's (card 1600 m; the card shows GroundRange x2).
MinimalRange stays 100. The option label '(laser, 2000 m)' follows.
Price (Osama 10:1x "and the NLOS should be +40 points"): option +20 -> +40; a swap row, if the option has one, = base + 40."""
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
    ok(A[NLOS]['GroundRange'] == A[FNF]['GroundRange'] == 800.0 and O[opt]['UIName'] == 'HJ-10 NLOS (laser, 1600 m)', 'HJ-10 NLOS range = FNF 800 (1600 m)')
    rec['hj10_nlos_range_1125'] = {'GroundRange': [before, A[NLOS]['GroundRange']], 'option': opt, 'cost': [20, 40], 'swap_row': r if r != base else None, 'base_cost': U[base]['Cost']}
    print('HJ-10 NLOS RANGE', rec['hj10_nlos_range_1125'])

"""Delta Force prices and default loadout (Lateralus 24 Nov 2026 14:5x PST, thread 1572962048705429598): "increase Delta Force Standoff loadout to
100 points. Set default loadout of Delta Force to Close Quarters, and set their base cost to 95. Then set Delta Force Standoff loadout to +5. So
Delta Force Close Quarters becomes 95 points, Standoff loadout becomes 100 points."
Card unit 150 'Delta Force' (USMC/SOF spec 13, 3 cards) is the Close Quarters squad; slot 518 has Close Quarters 1849 (keeps 150, +10) and Standoff
1850 (-> loadout row 411, +0). Base 85 -> 95; Close Quarters +10 -> +0 and IsDefault (it is also Order 0 and keeps the card unit, the vanilla
default pattern); Standoff +0 -> +5; loadout row 411 Cost 85 -> 100 (= base + option, audit_swap_prices). Close Quarters 95 -> 95, Standoff 85 -> 100."""


def apply(t, g, ok, rec):
    U, O, M = t['Units'], t['OptionsJson'], t['ModificationsJson']
    ok(U[150]['HUDName'] == 'Delta Force' and U[150]['Cost'] == 85 and not U[150].get('OriginalCost') and not U[150].get('IsUnitModification'), 'Delta Force card 150 at 85')
    ok(U[411]['HUDName'].strip() == 'Delta Force' and U[411]['Cost'] == 85 and U[411].get('IsUnitModification'), 'Standoff loadout row 411 at 85')
    opts = sorted((o for o in O.values() if o and o.get('ModificationId') == 518), key=lambda o: o['Id'])
    ok(M[518]['UnitId'] == 150 and [(o['Id'], o['UIName'], o['Cost'], o['ReplaceUnitId'], o.get('Order') or 0) for o in opts] ==
       [(1849, 'Custom_Option_Closequarters', 10, 150, 0), (1850, 'Custom_Option_Standoff', 0, 411, 1)], ('slot 518', opts))
    ok(not [o for o in O.values() if o and o.get('ReplaceUnitId') in (150, 411) and o.get('ModificationId') != 518], 'only slot 518 reaches 150 / 411')
    g.put('Units', 150, {'Cost': 95});g.put('OptionsJson', 1849, {'Cost': 0, 'IsDefault': True})
    g.put('OptionsJson', 1850, {'Cost': 5});g.put('Units', 411, {'Cost': 100})
    ok(U[150]['Cost'] + O[1849]['Cost'] == 95 and U[150]['Cost'] + O[1850]['Cost'] == U[411]['Cost'] == 100, 'Close Quarters 95, Standoff 100')
    rec['delta_force_1124'] = {'base': [85, 95], 'close_quarters': {'option': [10, 0], 'default': True, 'total': [95, 95]}, 'standoff': {'option': [0, 5], 'total': [85, 100]}}
    print('DELTA FORCE', rec['delta_force_1124'])

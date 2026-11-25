"""Every APS has 2 charges (Osama 25 Nov 2026 12:1x PST, bugs thread 1573561286803980289: "Can you make sure all APS is only two charges on the fa
model"). Every ability row with IsAPS and APSQuantity above 2 goes to 2 (vanilla Trophy 93 / Trophy NoModel 2, Arena 14, T-14 17, T-15 117,
Smoke x2 APS Default 64 ...). Laser defences (APSQuantity 999: LSDW, LY-1, Lynx Laser) are not charge-based and stay.
Replaces fep_aps_1125.py (the FEP-only 2-charge copy of row 93), which is no longer needed."""
LASER = 999


def apply(t, g, ok, rec):
    AB = t['AbilitiesJson']
    changed = {i: (a['Name'], a['APSQuantity']) for i, a in AB.items() if a and a.get('IsAPS') and 2 < a.get('APSQuantity', 0) < LASER}
    for i in changed: g.put('AbilitiesJson', i, {'APSQuantity': 2})
    left = {i: a['APSQuantity'] for i, a in AB.items() if a and a.get('IsAPS') and a.get('APSQuantity') not in (2, LASER) and a.get('APSQuantity', 0) > 2}
    ok(not left, ('APS rows above 2 charges left', left))
    lasers = {i: a['Name'] for i, a in AB.items() if a and a.get('IsAPS') and a.get('APSQuantity') == LASER}
    rec['aps_two_charges_1125'] = {'changed': changed, 'lasers_kept': lasers}
    print('APS 2 CHARGES', rec['aps_two_charges_1125'])

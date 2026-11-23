"""Vanilla icons on the HQ-9 cards and the HJ-10 NLOS loadout (Osama 22 Nov 2026 17:5x PST, thread 1572407822849810463: "Can you please stop using
these shitty weapon icons just use the default here. Same with HJ-16 it should be a spike nlos").
- HQ-9 weapons and loadout pictures: our placeholder FA_PLA_WP_SAM -> the icons of the vanilla units they copy: HQ-9B (S-400 40N6 profile) = S-400
  launcher S300_FAVORIT / option MOD_S400_X4; HQ-9C 8x (PAC-3 MSE round) = MSE_X8 / MSE_X8-OptIcon; HQ-9A (Patriot PAC-2) = PAC2_X2 / PAC2_X4 and
  PAC2_X2-OptIcon / PAC2_X4-OptIcon.
- HJ-10 NLOS loadout picture FA_PLA_HJ10 -> VEH_SPIKE_LR, the vanilla vehicle Spike picture the HJ-16 loadouts already use (the game has no Spike NLOS
  picture). The HJ-10 weapon icon itself stays FA_PLA_HJ10 (Osama's dev.45 request, pinned in check_model_carry.py)."""


def apply(t, g, ok, rec):
    W, O, M, U = t['WeaponsJson'], t['OptionsJson'], t['ModificationsJson'], t['Units']
    hq = rec['hq9_rework_1122']
    sam = [i for i, w in W.items() if w and w['HUDIcon'] == 'FA_PLA_WP_SAM']
    ok(all(W[i]['HUDName'] in ('HQ-9B missile', 'HQ-9C missile', 'HQ-9A missile') for i in sam) and len(sam) == 5, ('FA_PLA_WP_SAM = the 5 HQ-9 launchers', sam))
    for i in sam:
        w = W[i]
        icon = {'HQ-9B missile': 'S300_FAVORIT', 'HQ-9C missile': 'MSE_X8'}.get(w['HUDName']) or ('PAC2_X2' if w['MagazineSize'] == 2 else 'PAC2_X4')
        g.put('WeaponsJson', i, {'HUDIcon': icon})
    pics = {o: p for o, p in zip(hq['options'], ('MOD_S400_X4', 'MSE_X8-OptIcon'))}
    for o in [o for o in O.values() if o and o['OptionPicture'] == 'FA_PLA_WP_SAM']:
        if o['Id'] not in pics:
            ok(M[o['ModificationId']]['UnitId'] == hq['hq9a_card'], ('HQ-9A option', o['Id']))
            pics[o['Id']] = {'Custom_Option_2xMissiles': 'PAC2_X2-OptIcon', 'Custom_Option_4xMissiles': 'PAC2_X4-OptIcon'}[o['UIName']]
    for o, p in pics.items():
        g.put('OptionsJson', o, {'OptionPicture': p})
    nl = [o for o in O.values() if o and o['OptionPicture'] == 'FA_PLA_HJ10']
    ok(len(nl) == 1 and nl[0]['Name'] == 'PLA loadout HJ-10 NLOS', 'one HJ-10 NLOS option picture')
    g.put('OptionsJson', nl[0]['Id'], {'OptionPicture': 'VEH_SPIKE_LR'})
    ok(not any(w and w['HUDIcon'] == 'FA_PLA_WP_SAM' for w in W.values()) and not any(o and o['OptionPicture'] in ('FA_PLA_WP_SAM', 'FA_PLA_HJ10') for o in O.values()),
       'no FA_PLA_WP_SAM weapon icon, no FA_PLA_WP_SAM / FA_PLA_HJ10 option picture left')
    rec['vanilla_icons_1122'] = {'weapons': {i: W[i]['HUDIcon'] for i in sam}, 'options': {**pics, nl[0]['Id']: 'VEH_SPIKE_LR'}}
    print('ICONS', rec['vanilla_icons_1122'])

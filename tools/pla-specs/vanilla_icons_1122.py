"""Vanilla icons on the HQ-9 cards and the HJ-10 NLOS loadout (Osama 22 Nov 2026 17:5x PST, thread 1572407822849810463: "Can you please stop using
these shitty weapon icons just use the default here. Same with HJ-16 it should be a spike nlos").
- HQ-9 weapons and loadout pictures: our placeholder FA_PLA_WP_SAM -> the icons of the vanilla units they copy: HQ-9B (S-400 40N6 profile) = S-400
  launcher S300_FAVORIT / option MOD_S400_X4; HQ-9C 8x (PAC-3 MSE round) = MSE_X8 / MSE_X8-OptIcon; HQ-9A (Patriot PAC-2) = PAC2_X2 / PAC2_X4 and
  PAC2_X2-OptIcon / PAC2_X4-OptIcon.
- HJ-10 NLOS loadout picture FA_PLA_HJ10 -> VEH_SPIKE_LR, the vanilla vehicle Spike picture the HJ-16 loadouts already use (the game has no Spike NLOS
  picture). The HJ-10 weapon icon itself stays FA_PLA_HJ10 (Osama's dev.45 request, pinned in check_model_carry.py).
- 18:0x (Osama: "Honestly just change it all to something that's not the placeholder because the placeholder looks terrible"): every round still on a
  generic FA_PLA_AMMO_* placeholder (54 in use, mostly China infantry; section 10 already did the 279 vehicle rounds) and the last generic weapon
  placeholder (FA_PLA_WP_MG, ZSL-92 QJC-88 12.7 mm) get the icon of the matching vanilla round / weapon. Vanilla puts AMMO_BULLET_SHORT on every
  rifle, MG, sniper, SMG and shotgun round. Our drawn weapon pictures (QBZ-191, PF-98, HJ-10, unit thumbnails) are not placeholders and stay."""
import re
# (regex on the round's HUDName, vanilla icon); first match wins. Fallback by placeholder kind below.
NAMED = [(r'^QN-202', 'AMMO_GRIFFIN'), (r'^CH-901', 'AMMO_GRIFFIN'), (r'^TL-4', 'AMMO_METIS_M'), (r'^GAM-102LR', 'AMMO_JAVELIN'), (r'^HJ-12', 'AMMO_JAVELIN'),
         (r'^HJ-8', 'AMMO_TOW_2A'), (r'^HJ-73', 'AMMO_KONKURS_M'), (r'^(HN-6|QW-|FN-6)', 'AMMO_STINGER'), (r'^(35 mm|LG\d)', 'AMMO_GRENADES'),
         (r'thermobaric \(analog\)', 'AMMO_TBG'), (r'^PF-97|^FHJ-02', 'AMMO_RPO'), (r'^PF-98', 'AMMO_CG_M3'), (r'^PF-89', 'AMMO_AT4'), (r'^DZJ-08', 'AMMO_SMAW_HEDP')]
BULLET = ('FA_PLA_AMMO_MG', 'FA_PLA_AMMO_RIFLE', 'FA_PLA_AMMO_SNIPER', 'FA_PLA_AMMO_SMG', 'FA_PLA_AMMO_SHOTGUN')


def ammo_icon(a):
    for p, ic in NAMED:
        if re.search(p, (a.get('HUDName') or '').strip()):
            return ic
    if a['HUDIcon'] in BULLET:
        return 'AMMO_BULLET_SHORT'
    raise KeyError((a['Id'], a['HUDIcon'], a.get('HUDName')))


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
    # every placeholder round in use and the FA_PLA_WP_MG weapon -> vanilla icons
    A, WA, native = t['AmmunitionsJson'], t['WeaponAmmunitionsJson'], rec['_native_icons']
    used = {r['AmmunitionId'] for r in WA.values() if r}
    ph = sorted(i for i in used if i in A and (A[i]['HUDIcon'] or '').startswith('FA_PLA_AMMO_'))
    ok(all(U[r['UnitId']]['CountryId'] == 4 for r in WA.values() if r and r['AmmunitionId'] in ph), 'placeholder rounds are China-only')
    am = {i: (A[i]['HUDIcon'], ammo_icon(A[i])) for i in ph}
    ok(all(n in native['ammo'] for _, n in am.values()), ('vanilla ammo icons only', {i: v for i, v in am.items() if v[1] not in native['ammo']}))
    for i, (_, n) in am.items():
        g.put('AmmunitionsJson', i, {'HUDIcon': n})
    mg = [i for i, w in W.items() if w and w['HUDIcon'] == 'FA_PLA_WP_MG']
    ok(len(mg) == 1 and W[mg[0]]['HUDName'] == 'QJC-88 12.7 mm' and 'Kord' in native['weapons'], ('one FA_PLA_WP_MG weapon (ZSL-92)', mg))
    g.put('WeaponsJson', mg[0], {'HUDIcon': 'Kord'})
    gen = ('FA_PLA_WP_ATGM', 'FA_PLA_WP_AUTOCANNON', 'FA_PLA_WP_BOMB', 'FA_PLA_WP_CANNON', 'FA_PLA_WP_GRENADE', 'FA_PLA_WP_HOWITZER', 'FA_PLA_WP_MG', 'FA_PLA_WP_MISSILE',
           'FA_PLA_WP_MORTAR', 'FA_PLA_WP_RIFLE', 'FA_PLA_WP_ROCKET', 'FA_PLA_WP_SAM', 'FA_PLA_WP_SHOTGUN', 'FA_PLA_WP_SMG', 'FA_PLA_WP_SNIPER')
    ok(not any(A[i]['HUDIcon'].startswith('FA_PLA_AMMO_') for i in used if i in A) and not any(w and w['HUDIcon'] in gen for w in W.values() if w and w['Id'] in {r['WeaponId'] for r in WA.values() if r}),
       'no round or weapon in use on a generic placeholder icon')
    rec['vanilla_icons_1122'] = {'weapons': {i: W[i]['HUDIcon'] for i in sam + mg}, 'options': {**pics, nl[0]['Id']: 'VEH_SPIKE_LR'},
                                 'ammo': {str(i): {'name': A[i].get('HUDName'), 'before': b, 'after': n} for i, (b, n) in am.items()}}
    print('ICONS', len(rec['vanilla_icons_1122']['ammo']), 'rounds', rec['vanilla_icons_1122']['weapons'])

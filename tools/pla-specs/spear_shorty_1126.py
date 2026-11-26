"""Sig Spear Shorty, back pocket (Osama 26 Nov 2026 01:5x PST, thread "China cosmetic work": "This is the new Sig Spear Shorty, add a suppressor to
it in front, it's a Sig Spear stat clone", with a photo). A copy of vanilla weapon 208 'Rifle XM7 T2' (M7 Spear), so every stat is the M7's;
only the names and the HUD icon change: FA_US_WP_SPEAR_SHORTY (tools/icons-src/make_spear_shorty.py: traced from the photo, suppressor added at the
muzzle). Carried by no squad yet. When a squad gets it, link it to the M7's round (the WeaponAmmunitions row of 208's carriers)."""
import os
DONOR, ICON = 208, 'FA_US_WP_SPEAR_SHORTY'
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'mod', 'source', 'runtime-qa', 'icons')


def apply(t, g, ok, rec):
    W, SM = t['WeaponsJson'], t['SquadMembersJson']
    ok(W[DONOR]['Name'] == 'Rifle XM7 T2' and W[DONOR]['HUDName'] == 'M7 Spear', ('donor M7 Spear 208', W[DONOR]['Name'], W[DONOR]['HUDName']))
    ok(not any(w and w.get('HUDName') == 'Sig Spear Shorty' for w in W.values()), 'Sig Spear Shorty name free')
    ok(all(os.path.isfile(os.path.join(DIR, ICON + s + '.png')) for s in ('', '_OUTLINE')), ICON + ' + outline in runtime-qa/icons')
    nw = g.add('WeaponsJson', W[DONOR], {'Name': 'Rifle Sig Spear Shorty T2', 'HUDName': 'Sig Spear Shorty', 'HUDIcon': ICON})
    used = [r['UnitId'] for r in SM.values() if r and nw in (r.get('PrimaryWeaponId'), r.get('SpecialWeaponId'))]
    same = {k: v for k, v in W[nw].items() if k not in ('Id', 'Name', 'HUDName', 'HUDIcon')} == {k: v for k, v in W[DONOR].items() if k not in ('Id', 'Name', 'HUDName', 'HUDIcon')}
    ok(same and not used, ('Sig Spear Shorty = M7 stats, no squad', nw, used))
    rec['spear_shorty_1126'] = {'weapon': nw, 'copy_of': DONOR, 'icon': ICON}
    print('SPEAR SHORTY', rec['spear_shorty_1126'])

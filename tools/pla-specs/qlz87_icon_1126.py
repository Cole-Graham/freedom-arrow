"""QLZ-87 icon (Osama 26 Nov 2026 02:2x PST, thread "China cosmetic work": "this is the new QLZ-87, it's a stat clone of the QLZ-04 but it has a 25m
minimum range (need to discuss this with lat, add it to the current light brigade sheet)", with a photo).
- The QLZ-87 (weapon 2012157, QLZ-87 Team and Airborne QLZ-87 Team) is already an exact stat copy of the QLZ-04 (2012312): only the names differ,
  and both rounds already have MinimalRange 25 (as the vanilla AGS-17/30/40). Checked here, not changed. The minimum range is on the patch log for
  Lateralus.
- New HUD icon FA_PLA_WP_QLZ87 (tools/icons-src/make_qlz87.py, traced from the photo, bipod left out); it was the vanilla AGS-30 icon."""
import os
QLZ87, QLZ04, ICON = 2012157, 2012312, 'FA_PLA_WP_QLZ87'
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'mod', 'source', 'runtime-qa', 'icons')


def apply(t, g, ok, rec):
    W, A, WA = t['WeaponsJson'], t['AmmunitionsJson'], t['WeaponAmmunitionsJson']
    ok(W[QLZ87]['HUDName'] == 'QLZ-87' and W[QLZ04]['HUDName'] == 'QLZ-04', 'QLZ-87 / QLZ-04 rows')
    skip = ('Id', 'Name', 'HUDName', 'HUDIcon')
    ok({k: v for k, v in W[QLZ87].items() if k not in skip} == {k: v for k, v in W[QLZ04].items() if k not in skip}, 'QLZ-87 = QLZ-04 stats')
    am = {w: sorted({r['AmmunitionId'] for r in WA.values() if r and r['WeaponId'] == w}) for w in (QLZ87, QLZ04)}
    ok(len(am[QLZ87]) == 1 and len(am[QLZ04]) == 1 and A[am[QLZ87][0]]['MinimalRange'] == A[am[QLZ04][0]]['MinimalRange'] == 25.0, ('min range 25 on both', am))
    ok(all(os.path.isfile(os.path.join(DIR, ICON + s + '.png')) for s in ('', '_OUTLINE')), ICON + ' + outline in runtime-qa/icons')
    before = W[QLZ87]['HUDIcon']; g.put('WeaponsJson', QLZ87, {'HUDIcon': ICON})
    rec['qlz87_icon_1126'] = {'weapon': QLZ87, 'icon_before': before, 'icon': ICON, 'min_range': 25.0}
    print('QLZ-87 ICON', rec['qlz87_icon_1126'])

"""XM25 Punisher shown as the MTL-30 (Osama 25 Nov 2026 19:4x PST, bugs thread 1573561286803980289: "Create this as the MTL-30 and it replaces the
XM-25 punisher cosmetically", with a photo of the Barrett squad support rifle). Cosmetic only: vanilla weapon 365 'MGL 25 XM25' gets the card name
MTL-30 and the icon FA_US_WP_MTL30 (traced from the photo, tools/icons-src/make_mtl30.py). Stats, rounds and the soldiers' 3D weapon model
(still the XM25's; no MTL-30 model yet) are unchanged."""
import os
XM25, ICON = 365, 'FA_US_WP_MTL30'
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'mod', 'source', 'runtime-qa', 'icons')


def apply(t, g, ok, rec):
    W, U, SM = t['WeaponsJson'], t['Units'], t['SquadMembersJson']
    ok(W[XM25]['Name'] == 'MGL 25 XM25' and W[XM25]['HUDName'] == 'XM25 Punisher' and W[XM25]['HUDIcon'] == 'INF_XM25', 'XM25 Punisher row 365')
    ok(all(os.path.isfile(os.path.join(DIR, ICON + s + '.png')) for s in ('', '_OUTLINE')), ICON + ' + outline in runtime-qa/icons')
    g.put('WeaponsJson', XM25, {'HUDName': 'MTL-30', 'HUDIcon': ICON})
    users = sorted({U[m['UnitId']].get('HUDName') or U[m['UnitId']]['Name'] for m in SM.values() if m and XM25 in (m['PrimaryWeaponId'], m['SpecialWeaponId'])})
    ok(W[XM25]['HUDName'] == 'MTL-30' and W[XM25]['HUDIcon'] == ICON, 'XM25 shown as MTL-30')
    rec['mtl30_1125'] = {'weapon': XM25, 'users': users}
    print('MTL-30', rec['mtl30_1125'])

"""QJB-201 weapon HUD icon (Osama 24 Nov 2026 02:3x PST, thread "China cosmetic work": "use this to make a weapon icon for the QJB-201", with a
photo of the LMG). FA_PLA_WP_QJB201 (+ _OUTLINE) in mod/source/runtime-qa/icons, made by work/qjb201-icon/make_icon.py in the QBU-10 style, muzzle
right; ChinaUi registers every FA_PLA_* resource. Set on every weapon row whose HUDName is 'QJB-201'."""
import os
ICON = 'FA_PLA_WP_QJB201'
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'mod', 'source', 'runtime-qa', 'icons')


def apply(t, g, ok, rec):
    W = t['WeaponsJson']
    ok(all(os.path.isfile(os.path.join(DIR, ICON + s + '.png')) for s in ('', '_OUTLINE')), ICON + ' + outline in runtime-qa/icons')
    ids = sorted(i for i, w in W.items() if w and w.get('HUDName') == 'QJB-201')
    ok(1 <= len(ids) <= 6, ('QJB-201 weapon rows', ids))
    before = {i: W[i].get('HUDIcon') for i in ids}
    for i in ids: g.put('WeaponsJson', i, {'HUDIcon': ICON})
    ok(all(W[i]['HUDIcon'] == ICON for i in ids), 'QJB-201 icon set')
    users = sorted({t['Units'][r['UnitId']]['HUDName'] for r in t['SquadWeaponsJson'].values() if r and r['WeaponId'] in ids and t['Units'].get(r['UnitId'])})
    rec['qjb201_icon_1124'] = {'icon': ICON, 'before': before, 'squads': users}
    print('QJB-201 ICON', rec['qjb201_icon_1124'])

"""QBU-10 weapon HUD icon (Osama 24 Nov 2026 02:0x PST, thread "blue dragons": "can we make this the QBU-10 icon", with a side photo of the rifle).
FA_PLA_WP_QBU10 (+ _OUTLINE) in mod/source/runtime-qa/icons, made by work/qbu10-icon/make_icon.py from that photo in the QBU-191/QBU-88 style.
It replaces the native stand-in INF_ASVK on both QBU-10 weapon rows (infantry 2012054, prototype 2005018)."""
import os
ICON, IDS = 'FA_PLA_WP_QBU10', (2012054, 2005018)
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'mod', 'source', 'runtime-qa', 'icons')


def apply(t, g, ok, rec):
    W = t['WeaponsJson']
    ok(all(os.path.isfile(os.path.join(DIR, ICON + s + '.png')) for s in ('', '_OUTLINE')), ICON + ' + outline in runtime-qa/icons')
    ok([W[i]['HUDName'] for i in IDS] == ['QBU-10', 'QBU-10'], 'QBU-10 weapon rows 2012054, 2005018')
    ok(sorted(w['Id'] for w in W.values() if w and w.get('HUDName') == 'QBU-10') == sorted(IDS), 'no other QBU-10 weapon row')
    before = {i: W[i].get('HUDIcon') for i in IDS}
    for i in IDS: g.put('WeaponsJson', i, {'HUDIcon': ICON})
    ok(all(W[i]['HUDIcon'] == ICON for i in IDS), 'QBU-10 icon set')
    rec['qbu10_icon_1124'] = {'icon': ICON, 'before': before}
    print('QBU-10 ICON', rec['qbu10_icon_1124'])

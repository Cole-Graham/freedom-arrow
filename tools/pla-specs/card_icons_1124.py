"""Unit icons (card silhouettes) for the new China vehicles (Osama 24 Nov 2026 01:1x PST, thread "China cosmetic work": "where are the unit
icons"). White side-view labels rendered from each card's own model (dev.18 battle mesh) by work/pla-unit-icons-20261114/do_icon2.py
(sil.py + style.py, the 14 Nov China icon style): mod/source/runtime-qa/icons/FA_PLA_VEH_<KEY>.png + _OUTLINE.png, registered by
ChinaUi (every FA_PLA_* resource). ZZC-06 rendered from work/c5-cn-1123/out3 (not in dev.18). Sets ThumbnailFileName on the card and its own loadout rows (Name = card name + ' ...')."""
import os
ICONS = {'PLA ZTD-05': 'ZTD05', 'PLA ZSD-05': 'ZSD05', 'PLA ZRZ-100': 'ZRZ100', 'PLA ZBD-05': 'ZBD05', 'PLA VN-3': 'VN3', 'PLA PLZ-25': 'PLZ25',
         'PLA PLZ-10': 'PLZ10', 'PLA ZBL-08 Recon': 'ZBL08R', 'PLA ZSL-191': 'ZSL191', 'PLA PLL-05': 'PLL05',
         'PLA ZZC-06': 'ZZC06'}
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'mod', 'source', 'runtime-qa', 'icons')


def apply(t, g, ok, rec):
    U = t['Units']; out = {}
    for name, key in ICONS.items():
        addr = 'FA_PLA_VEH_' + key
        ok(all(os.path.isfile(os.path.join(DIR, addr + s + '.png')) for s in ('', '_OUTLINE')), addr + ' + outline in runtime-qa/icons')
        ids = sorted(i for i, u in U.items() if u and (u.get('Name') == name or (u.get('Name') or '').startswith(name + ' '))
                     and '(old' not in u['Name'] and 'Catalogue' not in u['Name'])
        ok(any(U[i]['Name'] == name for i in ids), name + ' card exists')
        out[name] = {i: U[i].get('ThumbnailFileName') for i in ids}
        for i in ids: g.put('Units', i, {'ThumbnailFileName': addr})
    ok(all(U[i]['ThumbnailFileName'] == 'FA_PLA_VEH_' + ICONS[n] for n, d in out.items() for i in d), 'icons set')
    rec['card_icons_1124'] = out
    print('CARD ICONS (before)', out)

"""Lynx Cargo icon (Osama 25 Nov 2026 10:0x PST, thread "China cosmetic work": "lynx cargo make icon (try to remove the person)").
White side view rendered from the card's own model (work/lynx-1124/conv/cargo8_c.glb) with the seated crewman deleted first (his material,
Material__333185 = the soldier atlas, 7,146 faces; work/lynx-cargo-icon-1125/nocrew_fam.py), then work/pla-unit-icons-20261114 sil.py + style.py:
FA_PLA_VEH_LYNXCARGO + _OUTLINE in mod/source/runtime-qa/icons, registered by ChinaUi (every FA_PLA_* resource). Was US_LMTV-Label."""
import os
CARGO, ICON = 1432, 'FA_PLA_VEH_LYNXCARGO'
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'mod', 'source', 'runtime-qa', 'icons')


def apply(t, g, ok, rec):
    U = t['Units']
    ok(U[CARGO]['HUDName'] == 'Lynx Cargo', ('Lynx Cargo', U[CARGO]['HUDName']))
    ok(all(os.path.isfile(os.path.join(DIR, ICON + s + '.png')) for s in ('', '_OUTLINE')), 'Lynx Cargo icon + outline in runtime-qa/icons')
    before = U[CARGO].get('ThumbnailFileName')
    g.put('Units', CARGO, {'ThumbnailFileName': ICON})
    rec['lynx_cargo_icon_1125'] = {'unit': CARGO, 'icon_before': before, 'icon': ICON}
    print('LYNX CARGO ICON', rec['lynx_cargo_icon_1125'])

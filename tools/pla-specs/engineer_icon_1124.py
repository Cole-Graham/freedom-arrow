"""Combat Engineers unit icon (Osama 24 Nov 2026 19:1x PST, #Website: "can you make this the new unit icon for Combat engineers?",
"turn it into a unit icon and then add it"). His black shield emblem (shovel, pickaxe, star, blast, mine, bridge truss) made white on
transparent, 256x160, emblem 140 px high, like the other FA_PLA_INF_* emblems: mod/source/runtime-qa/icons/FA_PLA_INF_ENGINEER(_OUTLINE).png,
registered by ChinaUi (every FA_PLA_* resource). Source + script: work/eng-icon-20261124 (make.py). Sets ThumbnailFileName on China
Combat Engineers 1156 only (was RU_SAPERI-Label). Its Thermobaric loadout row 1162 (option 24354) keeps RU_FLAMETHROWER-Label, as vanilla
loadouts show their own weapon icon."""
import os
ADDR = 'FA_PLA_INF_ENGINEER'
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'mod', 'source', 'runtime-qa', 'icons')


def apply(t, g, ok, rec):
    U, O = t['Units'], t['OptionsJson']
    ok(all(os.path.isfile(os.path.join(DIR, ADDR + s + '.png')) for s in ('', '_OUTLINE')), ADDR + ' + outline in runtime-qa/icons')
    ok(U[1156]['HUDName'].strip().startswith('Combat Engineers') and U[1162]['HUDName'].strip().startswith('Thermobaric Breachers')
       and O[24354]['ReplaceUnitId'] == 1162, 'China Combat Engineers 1156 and its Thermobaric loadout 1162')
    before = {i: U[i].get('ThumbnailFileName') for i in (1156,)}
    for i in before: g.put('Units', i, {'ThumbnailFileName': ADDR})
    ok(all(U[i]['ThumbnailFileName'] == ADDR for i in before), 'engineer icon set')
    rec['engineer_icon_1124'] = {'icon': ADDR, 'before': before}
    print('ENGINEER ICON (before)', before)

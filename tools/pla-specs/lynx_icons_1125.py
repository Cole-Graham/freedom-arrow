"""Lynx unit icons and the Lynx Laser weapon name (Osama 25 Nov 2026 00:1x PST, thread "China cosmetic work": "lets make icons: lynx ATV ...",
"Lynx howitzer (goes to support tab)", "Lynx Laser (weapon renamed 50kw laser) sent to support tab").
- Icons: white side views rendered from each card's own battle model (work/lynx-1124/out3) by work/pla-unit-icons-20261114 sil.py + style.py,
  the China icon style: FA_PLA_VEH_LYNXHOW (m_mh120), FA_PLA_VEH_LYNXLAS (m_796017), FA_PLA_VEH_LYNXATV (m_315224, the armed Troop Carrier /
  Lynx ATV model in his picture) + _OUTLINE, in mod/source/runtime-qa/icons, registered by ChinaUi (every FA_PLA_* resource).
  Howitzer 1436 and Laser 1446 get theirs; the ATV icon is on the existing Lynx ATV transport (1228, was US_M1297-Label).
- Support tab: Howitzer and Laser are CategoryType 3 (Support) already; checked, not changed.
- Laser weapon: the Lynx mount fires the LY-1 unit's weapon row 2019445, so a Lynx-only copy named '50 kW laser' replaces it on the Lynx mount
  and ammo rows (the LY-1 card keeps 'LY-1 laser'); its own pulse round 'LY-1 laser pulse' -> '50 kW laser pulse'. Names only.
Creates one weapon row: after every other row-creating section."""
ICON = {1436: 'FA_PLA_VEH_LYNXHOW', 1446: 'FA_PLA_VEH_LYNXLAS', 1228: 'FA_PLA_VEH_LYNXATV'}
LY1_WEAPON, NEW = 2019445, '50 kW laser'
import os
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'mod', 'source', 'runtime-qa', 'icons')


def apply(t, g, ok, rec):
    U, W, A, WA, TW, TU = t['Units'], t['WeaponsJson'], t['AmmunitionsJson'], t['WeaponAmmunitionsJson'], t['TurretWeaponsJson'], t['TurretUnitsJson']
    ok([U[i]['HUDName'] for i in ICON] == ['Lynx Howitzer', 'Lynx Laser', 'Lynx ATV'], ('Lynx Howitzer / Laser / ATV', [U[i]['HUDName'] for i in ICON]))
    ok(all(os.path.isfile(os.path.join(DIR, a + s + '.png')) for a in ICON.values() for s in ('', '_OUTLINE')), 'Lynx icons + outlines in runtime-qa/icons')
    ok(U[1436]['CategoryType'] == 3 and U[1446]['CategoryType'] == 3, 'Howitzer and Laser in the Support tab (CategoryType 3)')
    before = {i: U[i].get('ThumbnailFileName') for i in ICON}
    for i, a in ICON.items(): g.put('Units', i, {'ThumbnailFileName': a})
    lz = 1446
    mounts = [r['TurretId'] for r in TU.values() if r and r['UnitId'] == lz]
    tw = [r for r in TW.values() if r and r['TurretId'] in mounts and r['WeaponId'] == LY1_WEAPON]
    wa = [r for r in WA.values() if r and r['UnitId'] == lz and r['WeaponId'] == LY1_WEAPON]
    ok(len(mounts) == 1 and len(tw) == 1 and len(wa) == 1 and W[LY1_WEAPON]['HUDName'] == 'LY-1 laser', ('Lynx Laser: one mount, LY-1 weapon', mounts, tw, wa))
    others = sorted({r['UnitId'] for r in WA.values() if r and r['WeaponId'] == LY1_WEAPON} - {lz})
    nw = g.add('WeaponsJson', W[LY1_WEAPON], {'Name': 'PLA Lynx 50 kW laser', 'HUDName': NEW})
    g.put('TurretWeaponsJson', tw[0]['Id'], {'WeaponId': nw}); g.put('WeaponAmmunitionsJson', wa[0]['Id'], {'WeaponId': nw})
    pulse = wa[0]['AmmunitionId']
    ok(A[pulse]['Name'] == 'PLA Lynx Laser pulse' and not any(r and r['AmmunitionId'] == pulse and r['UnitId'] != lz for r in WA.values()), 'pulse round is the Lynx own')
    g.put('AmmunitionsJson', pulse, {'HUDName': NEW + ' pulse'})
    ok(W[LY1_WEAPON]['HUDName'] == 'LY-1 laser' and all(r['WeaponId'] == LY1_WEAPON for r in WA.values() if r and r['UnitId'] in others)
       and {k: v for k, v in W[nw].items() if k not in ('Id', 'Name', 'HUDName')} == {k: v for k, v in W[LY1_WEAPON].items() if k not in ('Id', 'Name', 'HUDName')},
       ('LY-1 users keep LY-1 laser; the copy differs only by name', others))
    rec['lynx_icons_1125'] = {'icons_before': before, 'laser_weapon': nw, 'pulse': pulse, 'ly1_users_kept': others}
    print('LYNX ICONS', rec['lynx_icons_1125'])

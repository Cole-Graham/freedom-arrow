"""China weapons kept in the back pocket: placeholders with vanilla stats, carried by no squad yet (Osama 25 Nov 2026 13:3x PST, thread
blue dragons). Batch branch codex/batch/osama/backpocket-weapons (kept out of the 0.9.7 release candidate). Each new weapon is a copy of a
vanilla weapon of the same kind and tier, so every stat is that weapon's; only the names and the HUD icon change.
- QJY-88 (Type 88 GPMG): "make icon for a t1 762 machine gun ... keep it on our back pocket" -> copy of the PKM T1 (158, 7.62x54 mm).
  Icon FA_PLA_WP_QJY88 (work/qjy88-icon/make_qjy88.py, from Osama's photo, bipod left out). The real QJY-88 fires 5.8 mm.
- QBZ-192 MLOK: "Put this weapon in the game as a T4 rifle as a place holder. Copy maybe any of the SF rifles" -> copy of the HK416A5 T3
  (767). Icon FA_PLA_WP_QBZ192_MLOK (work/qbz192-mlok-icon/make_mlok.py: MLOK handguard, LPVO, laser box, no bipod).
- VQX191: "Qbz-192 with suppressor, call it VQX191 and the icon is the QBZ-192 but add a short suppressor" -> copy of the suppressed
  HK416 D10RS T3 (210). Icon FA_PLA_WP_VQX191 (work/vqx191-icon/make_vqx191.py: the approved QBZ-192 icon with a short can).
- QBU-202 (8.6 mm .338 sniper): "there's a 338 ... sniper in the game ... maybe the mk22. Just copy a vanilla weapon" -> copy of the
  MK 22 ASR (674, .338 LM). Keeps the MK 22's icon until we draw one.
When a squad gets one, give it the donor's ammunition row (PKM 75 7.62x54mm, HK416A5 358 / D10RS 469 5.56x45mm, MK 22 389 .338 LM) or a
China-named copy, as the QBU-201 did."""
import os
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'mod', 'source', 'runtime-qa', 'icons')
NEW = [  # (donor, donor HUDName, Name, HUDName, icon or None)
    (158, 'PKM', 'PLA infantry QJY-88 T1', 'QJY-88', 'FA_PLA_WP_QJY88'),
    (767, 'HK 416A5', 'PLA infantry QBZ-192 MLOK T4', 'QBZ-192 MLOK', 'FA_PLA_WP_QBZ192_MLOK'),
    (210, 'HK 416 D10RS', 'PLA infantry QBZ-192 VQX191 T4', 'VQX191', 'FA_PLA_WP_VQX191'),
    (674, 'MK 22 ASR', 'PLA infantry QBU-202 T3', 'QBU-202', None),
]


def apply(t, g, ok, rec):
    W, SM = t['WeaponsJson'], t['SquadMembersJson']
    out = {}
    for donor, dname, name, hud, icon in NEW:
        ok(W[donor]['HUDName'] == dname, ('donor', donor, W[donor]['HUDName']))
        ok(not any(w and w.get('HUDName') == hud for w in W.values()), (hud, 'name free'))
        if icon: ok(all(os.path.isfile(os.path.join(DIR, icon + s + '.png')) for s in ('', '_OUTLINE')), icon + ' + outline in runtime-qa/icons')
        nw = g.add('WeaponsJson', W[donor], {'Name': name, 'HUDName': hud, **({'HUDIcon': icon} if icon else {})})
        used = [r['UnitId'] for r in SM.values() if r and nw in (r.get('PrimaryWeaponId'), r.get('SpecialWeaponId'))]
        ok(W[nw]['HUDName'] == hud and not used, (hud, 'added, carried by no squad', nw, used))
        out[hud] = {'weapon': nw, 'copy_of': donor, 'icon': icon or W[donor]['HUDIcon']}
    rec['backpocket_weapons_1125'] = out
    print('BACKPOCKET', out)

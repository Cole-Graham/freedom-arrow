"""QTS-11 grenade launcher as an under-barrel weapon (Osama 25 Nov 2026 00:0x PST, thread "blue dragons": "can we please make sure not every
QTS-11 is counted twice? I see each solder holding one in their hands and one on their back?" + screenshot).
The QTS-11's 20 mm launcher is its own weapon row (copied from the standalone XM25, IsUnderbarrel false) with the M203 rifle model M4A1_m203,
so the game gives every soldier a second, slung gun for it (FAModels draws w_qts11 on both). Every vanilla rifle grenade launcher
(M203 58 on M4A1_m203, GP-34 31, M320 117, AG36 639 ...) is IsUnderbarrel true and shows as one gun. Sets IsUnderbarrel true on every
'QTS-11 grenade launcher' row; nothing else changes (rate of fire, rounds, ammo, squads unchanged)."""


def apply(t, g, ok, rec):
    W = t['WeaponsJson']
    ok(W[58]['HUDName'] == 'M203' and W[58]['ModelFileName'] == 'M4A1_m203' and W[58]['IsUnderbarrel'] is True, 'vanilla M203 58 is under-barrel')
    rows = sorted(i for i, w in W.items() if w and w.get('HUDName') == 'QTS-11 grenade launcher')
    ok(len(rows) >= 2 and all(W[i]['Type'] == 60 for i in rows), ('QTS-11 grenade launcher rows', rows))
    changed = []
    for i in rows:
        if W[i].get('IsUnderbarrel') is not True: g.put('WeaponsJson', i, {'IsUnderbarrel': True}); changed.append(i)
    ok(all(W[i]['IsUnderbarrel'] is True for i in rows), 'every QTS-11 grenade launcher is under-barrel')
    rec['qts11_underbarrel'] = {'rows': rows, 'changed': changed, 'names': [W[i]['Name'] for i in rows]}
    print('QTS-11 UNDERBARREL', rec['qts11_underbarrel'])

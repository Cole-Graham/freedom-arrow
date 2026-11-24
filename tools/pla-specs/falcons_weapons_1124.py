"""Falcons 猎鹰 weapons (Osama 24 Nov 2026 02:2x PST, thread 1567745029781454889: "Falcon's QJZ-171 replaced with QJY-201, QBU-10 replaced with
QBU-201 (use this image as an icon), make it a stat clone of the M40A5").
- Falcons (unit 1185, PLAN Special Forces): the QJZ-171 12.7 mm HMG (2011972) -> the infantry QJY-201 7.62 mm GPMG (2012411) with its usual 400 rounds
  of '7.62 mm ammunition' (2012412), as on the GPMG Riflemen, AT Riflemen and 14 other China squads.
- QBU-10 (2012054) -> new weapon QBU-201: a copy of the M40A5 (weapon 64, 'Sniper 7.62 M40A5 T2') and its round (369 '7.62x51mm'), so every stat
  is the M40A5's (5-round magazine, aim 4-6 s, 3.6 damage, 500 m). Only names and the icon differ: 'QBU-201', round '7.62 mm precision
  ammunition' (the China naming of the QBU-10's '12.7 mm precision ammunition'), HUD icon FA_PLA_WP_QBU201 (work/qbu201-icon/make_icon.py from
  Osama's image). 60 rounds, the M40A5's count on the Scout Snipers. The soldier keeps the M40A5 3D model (no QBU-201 model).
- The QJZ-171 and QBU-10 rows stay for the other squads."""
import os
FALCONS, QJZ, QJY, QJY_AMMO, QBU10, M40, M40_AMMO = 1185, 2011972, 2012411, 2012412, 2012054, 64, 369
ICON = 'FA_PLA_WP_QBU201'
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'mod', 'source', 'runtime-qa', 'icons')


def apply(t, g, ok, rec):
    U, W, A, SM, SW, WA = (t[k] for k in ('Units', 'WeaponsJson', 'AmmunitionsJson', 'SquadMembersJson', 'SquadWeaponsJson', 'WeaponAmmunitionsJson'))
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok(U[FALCONS]['HUDName'].startswith('Falcons') and W[QJZ]['HUDName'] == 'QJZ-171' and W[QJY]['HUDName'] == 'QJY-201' and W[QBU10]['HUDName'] == 'QBU-10'
       and W[M40]['HUDName'] == 'M40A5' and A[M40_AMMO]['HUDName'] == '7.62x51mm', 'Falcons, QJZ-171, QJY-201, QBU-10, M40A5 rows')
    ok(all(os.path.isfile(os.path.join(DIR, ICON + s + '.png')) for s in ('', '_OUTLINE')), ICON + ' + outline in runtime-qa/icons')
    ok(not any(w and w.get('HUDName') == 'QBU-201' for w in W.values()), 'QBU-201 name free')
    m40wa = [r for r in rows('WeaponAmmunitionsJson', WeaponId=M40)]
    ok([(r['AmmunitionId'], r['Quantity']) for r in m40wa] == [(M40_AMMO, 60)], 'M40A5: one ammo row, 60 rounds')
    qjy_q = {r['Quantity'] for r in rows('WeaponAmmunitionsJson', WeaponId=QJY) if r['AmmunitionId'] == QJY_AMMO}
    ok(qjy_q == {400}, ('QJY-201 squads carry 400 rounds', qjy_q))
    nw = g.add('WeaponsJson', W[M40], {'Name': 'PLA infantry QBU-201', 'HUDName': 'QBU-201', 'HUDIcon': ICON})
    na = g.add('AmmunitionsJson', A[M40_AMMO], {'Name': 'PLA QBU-201 7.62 mm precision', 'HUDName': '7.62 mm precision ammunition'})
    swaps = {QJZ: (QJY, QJY_AMMO, 400), QBU10: (nw, na, 60)}
    for old, (w, a, q) in swaps.items():
        sm = [r for r in rows('SquadMembersJson', UnitId=FALCONS) if old in (r['PrimaryWeaponId'], r['SpecialWeaponId'])]
        sw = rows('SquadWeaponsJson', UnitId=FALCONS, WeaponId=old); wa = rows('WeaponAmmunitionsJson', UnitId=FALCONS, WeaponId=old)
        ok(len(sm) == 1 and len(sw) == 1 and len(wa) == 1, ('Falcons rows for', W[old]['HUDName'], len(sm), len(sw), len(wa)))
        f = 'PrimaryWeaponId' if sm[0]['PrimaryWeaponId'] == old else 'SpecialWeaponId'
        g.put('SquadMembersJson', sm[0]['Id'], {f: w}); g.put('SquadWeaponsJson', sw[0]['Id'], {'WeaponId': w})
        g.put('WeaponAmmunitionsJson', wa[0]['Id'], {'WeaponId': w, 'AmmunitionId': a, 'Quantity': q})
    same = lambda x, y, skip: all(x[k] == y[k] for k in x if k not in skip)
    ok(same(W[nw], W[M40], ('Id', 'Name', 'HUDName', 'HUDIcon')) and same(A[na], A[M40_AMMO], ('Id', 'Name', 'HUDName')), 'QBU-201 = M40A5 stats')
    got = sorted((W[r['WeaponId']]['HUDName'], A[r['AmmunitionId']]['HUDName'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=FALCONS))
    ok(not any(n in ('QJZ-171', 'QBU-10') for n, _, _ in got) and ('QJY-201', '7.62 mm ammunition', 400) in got and ('QBU-201', '7.62 mm precision ammunition', 60) in got,
       ('Falcons loadout', got))
    ok(rows('WeaponAmmunitionsJson', WeaponId=QJZ) and rows('WeaponAmmunitionsJson', WeaponId=QBU10), 'QJZ-171 / QBU-10 still on other squads')
    rec['falcons_weapons_1124'] = {'qbu201_weapon': nw, 'qbu201_ammo': na, 'loadout': got}
    print('FALCONS', rec['falcons_weapons_1124'])

"""Infantry AT team swaps (Osama 23 Nov 2026 18:2x PST, thread 1567745029781454889): "Marine HJ-8H renamed to Marine HJ-12 team, They get the
HJ-12 instead and go to 105 points (4 ammo). GAM-102LR in motorized replaced with HJ-8H and rename the team name too. 6x HJ-8H. 65 points".
- Marine HJ-8H Team (1193, PLAN SF): card 'Marine HJ-12 Team'; its launcher soldier (2015422) carries the HJ-12 (weapon 2011864, the PLAAF HJ-12
  Team's launcher) with 4 HJ-12 rounds (2011865); 85 -> 105 pts. Squad, rifles and QJY-201 unchanged.
- GAM-102LR Team (1221, PLAGF Motorized): card 'HJ-8H Team'; its launcher soldier (2015735) carries the HJ-8H (weapon 2018801, the Marine team's
  launcher) with 6 HJ-8H rounds (2018802); 110 -> 65 pts.
Existing weapon and ammunition rows only; each team's own WeaponAmmunitions and SquadWeapons rows are re-pointed."""

HJ12_W, HJ12_A, HJ8H_W, HJ8H_A, GAM_W = 2011864, 2011865, 2018801, 2018802, 2014292
TEAMS = {1193: ('Marine HJ-8H Team', 'Marine HJ-12 Team', 2015422, HJ8H_W, HJ12_W, HJ12_A, 4, 85, 105),
         1221: ('GAM-102LR Team', 'HJ-8H Team', 2015735, GAM_W, HJ8H_W, HJ8H_A, 6, 110, 65)}


def apply(t, g, ok, rec):
    U, W, A, SM, WA, SW = (t[k] for k in ('Units', 'WeaponsJson', 'AmmunitionsJson', 'SquadMembersJson', 'WeaponAmmunitionsJson', 'SquadWeaponsJson'))
    ok((W[HJ12_W]['HUDName'], A[HJ12_A]['HUDName'], W[HJ8H_W]['HUDName'], A[HJ8H_A]['HUDName']) == ('HJ-12', 'HJ-12 ammunition', 'HJ-8H', 'HJ-8H'), 'HJ-12 / HJ-8H rows')
    out = {}
    for uid, (old, new, carrier, w0, w1, a1, qty, c0, c1) in TEAMS.items():
        ok(U[uid]['HUDName'] == old and U[uid]['Cost'] == c0 and SM[carrier]['UnitId'] == uid and SM[carrier]['SpecialWeaponId'] == w0, (old, 'team, price, launcher soldier'))
        ok(not any(u and u.get('HUDName') == new and u.get('DisplayInArmory') for u in U.values()), (new, 'name free'))
        wa = [r for r in WA.values() if r and r['UnitId'] == uid and r['WeaponId'] == w0]; sw = [r for r in SW.values() if r and r['UnitId'] == uid and r['WeaponId'] == w0]
        ok(len(wa) == 1 and len(sw) == 1 and sum(1 for m in SM.values() if m and m['UnitId'] == uid and m.get('SpecialWeaponId') == w0) == 1, (old, 'one launcher row'))
        g.put('SquadMembersJson', carrier, {'SpecialWeaponId': w1})
        g.put('WeaponAmmunitionsJson', wa[0]['Id'], {'WeaponId': w1, 'AmmunitionId': a1, 'Quantity': qty})
        g.put('SquadWeaponsJson', sw[0]['Id'], {'WeaponId': w1})
        g.put('Units', uid, {'HUDName': new, 'Cost': c1})
        ok(U[uid]['HUDName'] == new and U[uid]['Cost'] == c1 and not any(r and r['UnitId'] == uid and r['WeaponId'] == w0 for r in list(WA.values()) + list(SW.values()))
           and [(r['AmmunitionId'], r['Quantity']) for r in WA.values() if r and r['UnitId'] == uid and r['WeaponId'] == w1] == [(a1, qty)], (new, 'after'))
        out[new] = {'unit': uid, 'was': old, 'launcher': W[w1]['HUDName'], 'rounds': qty, 'cost': [c0, c1]}
    # Osama 23 Nov 2026 19:5x (thread 1573561286803980289): "change the icon of the Marine HJ-12 team to a javelin, and the new HJ-8H in medium cab to
    # a kornet". Card label icon (ThumbnailFileName) = the vanilla Javelin team / Kornet team label.
    for uid, (before, after) in {1193: ('RU_KORNET-Label', 'US_JAVELIN-Label'), 1221: ('DLC2_SPIKE_LR-label', 'RU_KORNET-Label')}.items():
        ok(U[uid].get('ThumbnailFileName') == before, (uid, 'label icon before', U[uid].get('ThumbnailFileName')))
        g.put('Units', uid, {'ThumbnailFileName': after})
        ok(U[uid]['ThumbnailFileName'] == after, (uid, 'label icon after'))
        out[U[uid]['HUDName']]['label_icon'] = [before, after]
    rec['hj_teams_1123'] = out
    print('HJ TEAMS', out)

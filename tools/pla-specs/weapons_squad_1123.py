"""Weapons Squad 火力班 (Osama 23 Nov 2026 21:3x PST, thread 1567745029781454889: "weapons squad was supposed to go to 65 points and lose one
QJZ-171"). Earlier: 21 Nov 01:27 "QLU 11 and Weapons squad are over performing. If I remove one of the QJZ machine guns ..." (the
calculated answer then was 55 pts; nothing was queued).
- Unit 1199: the second QJZ-171 carrier (squad member 2015517) keeps his QBZ-191 and loses the QJZ-171 (SpecialWeaponId 0). 8 men stay;
  the QJZ-171 ammunition row (400 per carrier) is unchanged, so the squad carries 400 instead of 800.
- Cost 45 -> 60 (Osama 21:3x "60 points seems fine actually now that I compare"; OriginalCost 0, so the card price is Cost)."""
UNIT, MEMBER, QJZ, QBZ = 1199, 2015517, 2011972, 2003998


def apply(t, g, ok, rec):
    U, SM, W = t['Units'], t['SquadMembersJson'], t['WeaponsJson']
    ok(U[UNIT]['HUDName'] == 'Weapons Squad 火力班' and U[UNIT]['Cost'] == 45 and not U[UNIT].get('OriginalCost'), 'Weapons Squad 45 pts')
    carriers = sorted(r['Id'] for r in SM.values() if r and r['UnitId'] == UNIT and r['SpecialWeaponId'] == QJZ)
    ok(W[QJZ]['HUDName'] == 'QJZ-171' and carriers == [2015516, MEMBER] and SM[MEMBER]['PrimaryWeaponId'] == QBZ, ('two QJZ-171 carriers', carriers))
    g.put('SquadMembersJson', MEMBER, {'SpecialWeaponId': 0})
    g.put('Units', UNIT, {'Cost': 60})
    men = [r for r in SM.values() if r and r['UnitId'] == UNIT]
    ok(len(men) == 8 and [r['Id'] for r in men if r['SpecialWeaponId'] == QJZ] == [2015516] and U[UNIT]['Cost'] == 60, 'one QJZ-171, 8 men, 60 pts')
    rec['weapons_squad'] = {'unit': UNIT, 'qjz171_carriers': [2, 1], 'cost': [45, 60]}
    print('WEAPONS SQUAD', rec['weapons_squad'])

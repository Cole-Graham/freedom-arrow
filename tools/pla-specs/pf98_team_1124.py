"""PF-98 Team (PLARF, unit 1172) rounds (Osama 24 Nov 2026 11:4x PST, thread 1567745029781454889: "PF98 team (rocket force) HE remove ignore
cover. AT ammunition to 600m range instead of 800m"). Both rounds are used only by this card's PF-98 (tripod), weapon 2016259.
- DZD98A HE (2016261): IgnoreCover 0.25 -> 0.
- PF-98 ammunition, the AT round (2016260): GroundRange 400 -> 300 (card 800 m -> 600 m). The other range fields and penetration unchanged."""
HE, AT = 2016261, 2016260


def apply(t, g, ok, rec):
    A, WA, U = t['AmmunitionsJson'], t['WeaponAmmunitionsJson'], t['Units']
    for a, name in ((HE, 'DZD98A HE'), (AT, 'PF-98 ammunition')):
        users = sorted({U[r['UnitId']]['HUDName'] for r in WA.values() if r and r['AmmunitionId'] == a})
        ok(A[a]['HUDName'] == name and users == ['PF-98 Team'], (name, 'only on the PF-98 Team', users))
    ok(A[HE]['IgnoreCover'] == 0.25 and A[AT]['GroundRange'] == 400.0, ('before', A[HE]['IgnoreCover'], A[AT]['GroundRange']))
    g.put('AmmunitionsJson', HE, {'IgnoreCover': 0.0})
    g.put('AmmunitionsJson', AT, {'GroundRange': 300.0})
    ok(A[HE]['IgnoreCover'] == 0.0 and A[AT]['GroundRange'] == 300.0 and A[AT]['MinimalRange'] < 300.0, 'PF-98 Team HE no ignore cover; AT 600 m card')
    rec['pf98_team_1124'] = {'he_ignore_cover': [0.25, 0.0], 'at_card_range_m': [800, 600]}
    print('PF-98 TEAM', rec['pf98_team_1124'])

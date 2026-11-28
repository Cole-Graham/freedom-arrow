"""Osama 27 Nov 2026 21:4x PST, thread 1567745029781454889: "flying tigers don't shoot their smoke launcher when I fire position" / "or force fire" /
"the non lethal round isnt working either" / "they have no pen on them" / "thats maybe it?". Both ARWEN 37 rounds were made with penetration 20 -> 0
(pla_light_brigade_sf_1126, so the less-lethal round could not hurt), and the smoke round copies it. The game only uses a round when its damage
against the target comes out above 0 (docs/engine/target-and-ammo-selection.md: a round must do more than 0 damage; an attack order checks the
damage formula), so 0 penetration likely made both rounds unusable. Both go back to the vanilla 40 mm grenade value (M320 / GP-25: 20 / 20).
Damage stays 0.1 (less-lethal) and 0.01 (smoke), so neither becomes a killing round. Put-only: after the plb scope. Not yet tested in a game."""


def apply(t, g, ok, rec):
    A = t['AmmunitionsJson']
    rounds = {k: a for k, a in A.items() if a and a.get('HUDName') in ('37 mm less-lethal', '37 mm smoke') and (a.get('Name') or '').startswith('PLA infantry ARWEN 37')}
    ok(sorted(a['HUDName'] for a in rounds.values()) == ['37 mm less-lethal', '37 mm smoke'], ('ARWEN rounds', sorted(rounds)))
    out = {}
    for k, a in rounds.items():
        ok(a['PenetrationAtMinRange'] == 0 and a['PenetrationAtGroundRange'] == 0 and a['Damage'] in (0.1, 0.01), (k, 'pen 0 / 0 before', a['Damage']))
        g.put('AmmunitionsJson', k, {'PenetrationAtMinRange': 20.0, 'PenetrationAtGroundRange': 20.0})
        out[a['HUDName']] = {'id': k, 'pen': [0, 20], 'damage': a['Damage']}
    rec['osama_arwen_pen_1127'] = out
    print('ARWEN PEN', out)

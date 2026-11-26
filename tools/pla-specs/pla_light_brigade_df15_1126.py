"""PLA Light Brigade build, DF-15 range (Osama 26 Nov 2026 15:5x PST, thread 1567745029781454889: "Df-15 range reduced to 8000 to match Tochka").
Branch codex/batch/osama/pla-light-brigade only; the last plb section. The DF-15 round (2010363, only the DF-15 fires it) GroundRange 5000 -> 4000
(card 10000 -> 8000 m), the Tochka-U's (rounds 439 / 440: 4000, card 8000). Nothing else changes."""
DF15, DF15_A, TOCHKA_A = 1029, 2010363, 439


def apply(t, g, ok, rec):
    U, A, WA = t['Units'], t['AmmunitionsJson'], t['WeaponAmmunitionsJson']
    ok(U[DF15]['HUDName'] == 'DF-15' and A[DF15_A]['GroundRange'] == 5000.0 and A[TOCHKA_A]['GroundRange'] == 4000.0, 'DF-15 5000, Tochka-U 4000')
    ok({U[r['UnitId']]['HUDName'] for r in WA.values() if r and r['AmmunitionId'] == DF15_A} == {'DF-15'}, 'only the DF-15 fires its round')
    g.put('AmmunitionsJson', DF15_A, {'GroundRange': 4000.0})
    rec['pla_light_brigade_df15_1126'] = {'round': DF15_A, 'card_range_m': 8000}
    print('PLA LIGHT BRIGADE DF-15', rec['pla_light_brigade_df15_1126'])

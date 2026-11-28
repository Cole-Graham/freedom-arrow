"""HJ-10 (Osama 27 Nov 2026 17:3x-17:4x PST, thread 1567745029781454889: "HJ-10 to 4 availability" / "HJ-10 FNF goes to 130 pts. Both FNF and NLOS
get 1800m range ( armory )").
- Card 2008223 (Heavy CAB): 8 -> 4.
- Price 120 -> 130 (the FNF loadout is the default, +0); NLOS stays +60 over it (osama_tanks_1127), so 180 -> 190.
- Range 1,600 -> 1,800 card m: GroundRange 800 -> 900 on the FNF round 2019706 and the NLOS round 2009623. Both rows are shared with the
  ZSD-05 HJ-10 (6006, same launcher), which gets the same range. FNF straight-line reach ~926 (missile-flight.md formula), so 900 is reachable.
- NLOS option label '(laser, 1600 m)' -> '(laser, 1800 m)'."""
HJ10, CARD, FNF_A, NLOS_A, NLOS_OPT = 936, 2008223, 2019706, 2009623, 31107


def apply(t, g, ok, rec):
    U, SA, A, O = t['Units'], t['SpecializationAvailabilitiesJson'], t['AmmunitionsJson'], t['OptionsJson']
    ok(U[HJ10]['Cost'] == 120 and SA[CARD]['UnitId'] == HJ10 and SA[CARD]['MaxAvailabilityXp0'] == 8, ('HJ-10 as read', U[HJ10]['Cost'], SA[CARD]['MaxAvailabilityXp0']))
    ok(A[FNF_A]['GroundRange'] == A[NLOS_A]['GroundRange'] == 800.0 and O[NLOS_OPT]['UIName'] == 'HJ-10 NLOS (laser, 1600 m)' and O[NLOS_OPT]['Cost'] == 60, 'HJ-10 rounds 800, NLOS +60')
    g.put('SpecializationAvailabilitiesJson', CARD, {'MaxAvailabilityXp0': 4})
    g.put('Units', HJ10, {'Cost': 130})
    for a in (FNF_A, NLOS_A): g.put('AmmunitionsJson', a, {'GroundRange': 900.0})
    g.put('OptionsJson', NLOS_OPT, {'UIName': 'HJ-10 NLOS (laser, 1800 m)'})
    rec['osama_hj10_1127'] = {'availability': [8, 4], 'cost': [120, 130], 'nlos_total': [180, 190], 'range_m': [1600, 1800], 'also': 'ZSD-05 HJ-10 rounds'}
    print('HJ-10 1127', rec['osama_hj10_1127'])

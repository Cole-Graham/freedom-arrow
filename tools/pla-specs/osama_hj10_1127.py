"""HJ-10 (Osama 27 Nov 2026 17:3x-17:4x PST, thread 1567745029781454889: "HJ-10 to 4 availability" / "HJ-10 FNF goes to 130 pts. Both FNF and NLOS
get 1800m range ( armory )" / 17:4x "Actually HJ-10 bring it back to 120. MAKE SURE THE 05 MARINE VERSION ALSO GETS THESE CHANGES").
- HJ-10 (936, Heavy CAB) and ZSD-05 HJ-10 (6006, PLAN): cards 8 -> 4 (rows 2008223, 3000016). Prices stay: HJ-10 120, ZSD-05 HJ-10 140.
- NLOS loadout +60 on both (HJ-10 already +60 since osama_tanks_1127; ZSD-05 HJ-10 option 29015 +40 -> +60).
- Range 1,600 -> 1,800 card m: GroundRange 800 -> 900 on the FNF round 2019706 and the NLOS round 2009623, which both vehicles fire.
  FNF straight-line reach ~926 (missile-flight.md formula), so 900 is reachable. NLOS option labels '(laser, 1600 m)' -> '(laser, 1800 m)'."""
CARDS = {936: 2008223, 6006: 3000016}
NLOS_OPTS = {936: 31107, 6006: 29015}
FNF_A, NLOS_A = 2019706, 2009623


def apply(t, g, ok, rec):
    U, SA, A, O = t['Units'], t['SpecializationAvailabilitiesJson'], t['AmmunitionsJson'], t['OptionsJson']
    ok(A[FNF_A]['GroundRange'] == A[NLOS_A]['GroundRange'] == 800.0, 'HJ-10 rounds 800')
    out = {}
    for u, card in CARDS.items():
        o = NLOS_OPTS[u]
        ok(SA[card]['UnitId'] == u and SA[card]['MaxAvailabilityXp0'] == 8 and O[o]['UIName'] == 'HJ-10 NLOS (laser, 1600 m)' and O[o]['Cost'] in (40, 60),
           (U[u]['HUDName'], SA[card]['MaxAvailabilityXp0'], O[o]['UIName'], O[o]['Cost']))
        out[U[u]['HUDName']] = {'cards': [8, 4], 'nlos_option': [O[o]['Cost'], 60], 'price': U[u]['Cost']}
        g.put('SpecializationAvailabilitiesJson', card, {'MaxAvailabilityXp0': 4})
        g.put('OptionsJson', o, {'Cost': 60, 'UIName': 'HJ-10 NLOS (laser, 1800 m)'})
    for a in (FNF_A, NLOS_A): g.put('AmmunitionsJson', a, {'GroundRange': 900.0})
    ok(U[936]['Cost'] == 120 and U[6006]['Cost'] == 140, 'prices unchanged')
    out['range_m'] = [1600, 1800]
    rec['osama_hj10_1127'] = out
    print('HJ-10 1127', out)

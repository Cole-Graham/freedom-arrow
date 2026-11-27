"""Osama 27 Nov 2026 00:0x PST, thread 1567745029781454889: "ZTZ-99A to 6 availability. ZTZ-96B to 85 forward speed. ZTZ-96A and B both armor
to 650/700. ZTZ-96A to 125 points. ZTZ-96B to 145." / "ztz-96 each have 8 availability" / "HJ-10 to 120, but the loadout is +60 for the nlos" /
"SEPV2 to 220". Each row below is used only by the unit named (checked).
- ZTZ-99A (904) card 2008164 (Heavy CAB): availability 2 -> 6.
- ZTZ-96 cards, availability 6 -> 8: ZTZ-96B (905) 2008165, ZTZ-96A (1082) 2008936, ZTZ-96 (949) 2020390.
- ZTZ-96B mobility 2009093: MaxSpeedRoad (the card's "Forward speed") 80 -> 85. Off-road 62.9 and reverse 40 unchanged.
- Front armour KE / HEAT 600 / 600 -> 650 / 700: ZTZ-96A row 2011345, ZTZ-96B row 2009091. Sides, rear, top, HP unchanged.
- Price: ZTZ-96A 105 -> 125, ZTZ-96B 195 -> 145, HJ-10 (936) 140 -> 120, M1A2 SEP v2 (243) 215 -> 220. OriginalCost is 0 on all four.
- HJ-10 'HJ-10 NLOS (laser, 1600 m)' loadout option 31107: +40 -> +60, so the NLOS HJ-10 stays 180 in total (140 + 40 -> 120 + 60); the FNF HJ-10 drops 140 -> 120. No swap rows (ReplaceUnitId 0).
Not yet tested in a game."""
CARDS = {2008164: (904, 2, 6), 2008165: (905, 6, 8), 2008936: (1082, 6, 8), 2020390: (949, 6, 8)}
MOB96B, ARMORS = 2009093, {2011345: 1082, 2009091: 905}
COSTS = {1082: (105, 125), 905: (195, 145), 936: (140, 120), 243: (215, 220)}
NLOS_OPT = 31107


def apply(t, g, ok, rec):
    U, SA, MO, AR, O = t['Units'], t['SpecializationAvailabilitiesJson'], t['MobilityJson'], t['ArmorsJson'], t['OptionsJson']
    only = lambda tab, key, i: sorted({r['UnitId'] for r in t[tab].values() if r and r[key] == i})
    out = {}
    for c, (u, a, b) in CARDS.items():
        ok(SA[c]['UnitId'] == u and SA[c]['MaxAvailabilityXp0'] == a, (U[u]['HUDName'], 'card', c, SA[c]['MaxAvailabilityXp0']))
        g.put('SpecializationAvailabilitiesJson', c, {'MaxAvailabilityXp0': b}); out[U[u]['HUDName'] + ' availability'] = [a, b]
    ok(only('UnitPropulsionsJson', 'MobilityId', MOB96B) == [905] and MO[MOB96B]['MaxSpeedRoad'] == 80.0, ('ZTZ-96B mobility', MO[MOB96B]['MaxSpeedRoad']))
    g.put('MobilityJson', MOB96B, {'MaxSpeedRoad': 85.0}); out['ZTZ-96B forward speed'] = [80, 85]
    for r, u in ARMORS.items():
        ok(only('UnitArmorsJson', 'ArmorId', r) == [u] and (AR[r]['KinArmorFront'], AR[r]['HeatArmorFront']) == (600, 600), (U[u]['HUDName'], 'armour', r))
        g.put('ArmorsJson', r, {'KinArmorFront': 650, 'HeatArmorFront': 700}); out[U[u]['HUDName'] + ' front KE/HEAT'] = ['600/600', '650/700']
    for u, (a, b) in COSTS.items():
        ok(U[u]['Cost'] == a and not U[u].get('OriginalCost'), (U[u]['HUDName'], 'cost', U[u]['Cost']))
        g.put('Units', u, {'Cost': b}); out[U[u]['HUDName'] + ' cost'] = [a, b]
    o = O[NLOS_OPT]; m = t['ModificationsJson'][o['ModificationId']]
    ok(m['UnitId'] == 936 and o['UIName'].startswith('HJ-10 NLOS') and o['Cost'] == 40 and not o.get('ReplaceUnitId'), ('HJ-10 NLOS option', o['Cost']))
    g.put('OptionsJson', NLOS_OPT, {'Cost': 60}); out['HJ-10 NLOS loadout'] = ['+40', '+60']
    ok(U[936]['HUDName'] == 'HJ-10' and U[243]['HUDName'] == 'M1A2 SEP v2', 'unit names')
    rec['osama_tanks_1127'] = out
    print('OSAMA TANKS 1127', out)

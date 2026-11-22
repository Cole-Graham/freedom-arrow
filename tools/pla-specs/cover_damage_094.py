"""Infantry cover and damage (Osama 21 Nov 2026, thread 1573561286803980289 "bug fixes"; decided 19:08-19:43 PST, "you can push this into the build"
19:51). Proposal and full before/after list: Doc "Balance notes and calculations" 1if0iWzQ, section "Infantry cover and damage proposal (21 November)".
Called from apply_0_9_4_dev1.py (section 22). Buildings 30 % is game-config.json (BuildingDamageFloor 0.18 -> 0.3), not a table row.
- Tank guns (Weapons.Type 110), autocannons (114) and HMGs (28) only. Anti-infantry rounds x0.8: tank guns to the nearest 0.5, autocannons 0.2, HMGs 0.1
  ("20% reduction ... for those 3 classes", 19:08; 0.1 HMG 19:19; 0.2 autocannon 19:24). Every HMG on every unit, SPAAGs and helicopter door guns
  included ("Every HMG needs to be changed across the board", 19:43). Helicopter rotary cannons (GAU-19B, YakB) are not HMGs here (19:28).
- Ignore Cover -> 0 on every round of those weapons ("we're removing ignore cover from those categories", 19:08).
- Tank HEAT = the same gun's HE after the cut; guns with no HE take the HE of the same calibre ("Change the HEAT rounds to match equivalent HE round
  damage", 19:28). HEAT is also the anti-vehicle round: see the Doc for the hits-to-kill side effect.
- SPAAG main guns keep their values (Derivatsiya 211, M6 Linebacker 27, Unimog 538, Ural-4320 ZU-23 222), except the JRVG-1 (952), which takes the cut
  (19:28 "SPAAGs do not get changed", 19:43 "when I say SPAAG I was talking about main gun", "JRVG most certainly needs to be affected").
  57x348mm HE (491) is shared by the Ural and the BMOP Toros (450): the Toros gets a cut copy; 491 stays with the Ural."""
WT = (110, 114, 28)
SPAAG_MAIN = (211, 27, 538, 222)
SHARED = 491; SHARED_KEEP = 222; SHARED_CUT = 450
# ammo id: (class, name, damage before, after) -- anti-infantry rounds
DAMAGE = {
    7: ('Tank guns', '100mm 3UOF19', 10.0, 8.0),
    19: ('HMGs', '12.7x99mm', 1.0, 0.8),
    24: ('Tank guns', 'M393A1 HESH', 11.0, 9.0),
    36: ('Autocannons', '30x113mm HEDP', 2.25, 1.8),
    49: ('Tank guns', '125mm HE Telnik', 13.0, 10.5),
    53: ('Autocannons', '30x173mm HEI-T', 3.0, 2.4),
    54: ('Tank guns', '125mm HE', 13.0, 10.5),
    70: ('HMGs', '12.7x108mm', 1.0, 0.8),
    126: ('Tank guns', '125mm HE', 13.0, 10.5),
    140: ('Tank guns', '125mm HE', 13.0, 10.5),
    142: ('Tank guns', '125mm HE', 13.0, 10.5),
    161: ('Autocannons', '23x115mm', 1.75, 1.4),
    163: ('HMGs', '14.5x114mm', 1.25, 1.0),
    169: ('Tank guns', '152mm HE', 15.0, 12.0),
    171: ('Tank guns', 'M393A1 HESH', 11.0, 9.0),
    177: ('Autocannons', '30x165mm HE', 3.0, 2.4),
    204: ('Autocannons', '30x165mm HE', 3.0, 2.4),
    207: ('Autocannons', '30x165mm HE', 3.0, 2.4),
    222: ('Autocannons', '57x348mm', 4.3, 3.4),
    224: ('Tank guns', '76mm HE', 8.0, 6.5),
    240: ('Tank guns', '125mm HE', 13.0, 10.5),
    241: ('Tank guns', '125mm HE Telnik', 13.0, 10.5),
    243: ('Tank guns', '125mm HE Telnik', 13.0, 10.5),
    247: ('Tank guns', '125mm HE', 13.0, 10.5),
    249: ('Tank guns', '125mm HE', 13.0, 10.5),
    259: ('Tank guns', 'Mk324 HE', 12.0, 9.5),
    265: ('Tank guns', '125mm HE', 13.0, 10.5),
    267: ('Autocannons', '57x348mm', 4.3, 3.4),
    277: ('Autocannons', '25x137mm HEIT', 2.5, 2.0),
    436: ('Tank guns', '73mm HE', 7.5, 6.0),
    488: ('HMGs', '12.7x108mm', 1.0, 0.8),
    491: ('Autocannons', '57x348mm', 4.3, 3.4),
    493: ('Tank guns', '165mm HESH', 17.0, 13.5),
    500: ('Tank guns', '100mm HE', 10.0, 8.0),
    504: ('Tank guns', 'M393A1 HESH', 11.0, 9.0),
    507: ('Autocannons', '50x228mm', 3.8, 3.0),
    540: ('Tank guns', 'M1147 HE', 12.0, 9.5),
    546: ('Autocannons', '30x165mm HE', 4.5, 3.6),
    567: ('Autocannons', '30x170mm HEI-T', 3.0, 2.4),
    576: ('Tank guns', 'DM11', 12.0, 9.5),
    577: ('Tank guns', 'DM12A1', 11.0, 9.0),
    716: ('Tank guns', '115mm HE', 12.0, 9.5),
    717: ('Tank guns', '115mm HE', 12.0, 9.5),
    2005006: ('HMGs', 'QJZ-171 (prototype)', 1.0, 0.8),
    2005009: ('HMGs', 'QJZ-171 (prototype)', 1.0, 0.8),
    2009005: ('HMGs', 'QJZ-89 12.7 mm RWS ammunition', 1.0, 0.8),
    2009023: ('Tank guns', '100 mm gun / HJ-9 launcher HE', 10.0, 8.0),
    2009031: ('Autocannons', 'ZPT-99 30 mm HE', 3.0, 2.4),
    2009077: ('Tank guns', 'ZPT-98 125 mm HE', 13.0, 10.5),
    2009089: ('HMGs', 'QJC-88 12.7 mm ammunition', 1.0, 0.8),
    2009105: ('Tank guns', '125 mm tank gun HE', 13.0, 10.5),
    2009117: ('HMGs', 'QJC-88 12.7 mm ammunition', 1.0, 0.8),
    2009133: ('Tank guns', '105 mm rifled gun HE', 11.0, 9.0),
    2009145: ('HMGs', 'QJC-88 12.7 mm ammunition', 1.0, 0.8),
    2009639: ('Autocannons', '30 mm autocannon HE', 3.0, 2.4),
    2009671: ('Tank guns', '105 mm rifled gun HE', 11.0, 9.0),
    2009683: ('HMGs', 'QJC-88 12.7 mm ammunition', 1.0, 0.8),
    2009925: ('HMGs', 'QJC-88 12.7 mm ammunition', 1.0, 0.8),
    2009953: ('Autocannons', '76 mm HE (proximity)', 8.0, 6.4),
    2010197: ('Tank guns', 'Prototype 105 mm gun HE', 13.0, 10.5),
    2010209: ('HMGs', 'QJC-88 12.7 mm ammunition', 1.0, 0.8),
    2010797: ('Tank guns', '100 mm rifled gun HE', 10.0, 8.0),
    2010809: ('HMGs', 'QJC-88 12.7 mm ammunition', 1.0, 0.8),
    2010825: ('Tank guns', '100 mm rifled tank gun HE', 10.0, 8.0),
    2010837: ('HMGs', 'QJC-88 12.7 mm ammunition', 1.0, 0.8),
    2010853: ('Tank guns', '105 mm rifled tank gun HE', 10.0, 8.0),
    2010865: ('HMGs', 'QJC-88 12.7 mm ammunition', 1.0, 0.8),
    2011145: ('Autocannons', '30 mm autocannon HE', 3.0, 2.4),
    2011303: ('Tank guns', '105 mm rifled gun HE', 11.0, 9.0),
    2011315: ('HMGs', 'QJC-88 12.7 mm ammunition', 1.0, 0.8),
    2011359: ('Tank guns', '125 mm tank gun HE', 13.0, 10.5),
    2011371: ('HMGs', 'QJC-88 12.7 mm ammunition', 1.0, 0.8),
    2011387: ('Tank guns', 'ZPT-98 125 mm HE', 13.0, 10.5),
    2011399: ('HMGs', 'QJC-88 12.7 mm ammunition', 1.0, 0.8),
    2011973: ('HMGs', '12.7 mm ammunition', 1.0, 0.8),
    2012388: ('HMGs', '12.7 mm ammunition', 1.0, 0.8),
    2018754: ('HMGs', 'QJC-88 12.7 mm ammunition', 1.0, 0.8),
    2019460: ('Tank guns', '120 mm HE', 13.0, 10.5),
    2019545: ('Tank guns', 'Type 75 HESH', 11.0, 9.0),
}
# ammo id: (class, name, damage before, after) -- tank HEAT matched to HE
HEAT = {
    2: ('Tank guns', 'M830A1 HEAT', 11.5, 9.5),
    170: ('Tank guns', '152mm HEAT', 14.0, 12.0),
    173: ('Tank guns', 'M830A1 HEAT', 11.5, 9.5),
    244: ('Tank guns', '125mm HEAT', 11.0, 10.5),
    251: ('Tank guns', 'M830A1 HEAT', 11.5, 9.5),
    252: ('Tank guns', 'M830A1 HEAT', 11.5, 9.5),
    253: ('Tank guns', 'M830 HEAT', 11.0, 9.5),
    260: ('Tank guns', 'M830 HEAT', 11.0, 9.5),
    356: ('Tank guns', '125mm HEAT', 11.0, 10.5),
    435: ('Tank guns', '73mm HEAT', 7.0, 6.0),
    499: ('Tank guns', '3BK16M HEAT', 9.5, 8.0),
    532: ('Tank guns', '125mm HEAT', 11.0, 10.5),
    541: ('Tank guns', '125mm HEAT', 11.0, 10.5),
    714: ('Tank guns', '115mm HEAT', 10.0, 9.5),
    715: ('Tank guns', '115mm HEAT', 10.0, 9.5),
    2009079: ('Tank guns', 'ZPT-98 125 mm HEAT', 11.0, 10.5),
    2009107: ('Tank guns', '125 mm tank gun HEAT', 11.0, 10.5),
    2010199: ('Tank guns', 'Prototype 105 mm gun HEAT', 11.0, 10.5),
    2011361: ('Tank guns', '125 mm tank gun HEAT', 11.0, 10.5),
    2011389: ('Tank guns', 'ZPT-98 125 mm HEAT', 11.0, 10.5),
    2019461: ('Tank guns', '120 mm HEAT', 11.0, 10.5),
    2019492: ('Tank guns', 'JM12A1 HEAT', 11.0, 9.5),
    2019539: ('Tank guns', 'K280 HEAT-MP', 11.0, 9.5),
    2019540: ('Tank guns', 'K277 HEAT-MP', 11.0, 9.5),
    2019542: ('Tank guns', 'KM456A2 HEAT', 11.0, 9.0),
    2019544: ('Tank guns', 'Type 91 HEAT', 11.0, 9.0),
}
# ammo id: (name, Ignore Cover before) -> 0
IGNORE_COVER = {
    2: ('M830A1 HEAT', 0.2),
    7: ('100mm 3UOF19', 0.1),
    24: ('M393A1 HESH', 0.1),
    36: ('30x113mm HEDP', 0.25),
    49: ('125mm HE Telnik', 0.25),
    53: ('30x173mm HEI-T', 0.25),
    54: ('125mm HE', 0.25),
    126: ('125mm HE', 0.25),
    140: ('125mm HE', 0.25),
    142: ('125mm HE', 0.25),
    169: ('152mm HE', 0.4),
    171: ('M393A1 HESH', 0.1),
    173: ('M830A1 HEAT', 0.2),
    177: ('30x165mm HE', 0.25),
    204: ('30x165mm HE', 0.25),
    207: ('30x165mm HE', 0.25),
    222: ('57x348mm', 0.25),
    240: ('125mm HE', 0.25),
    241: ('125mm HE Telnik', 0.25),
    243: ('125mm HE Telnik', 0.25),
    247: ('125mm HE', 0.25),
    249: ('125mm HE', 0.25),
    251: ('M830A1 HEAT', 0.2),
    252: ('M830A1 HEAT', 0.2),
    253: ('M830 HEAT', 0.2),
    259: ('Mk324 HE', 0.25),
    260: ('M830 HEAT', 0.2),
    265: ('125mm HE', 0.25),
    267: ('57x348mm', 0.25),
    277: ('25x137mm HEIT', 0.25),
    491: ('57x348mm', 0.25),
    493: ('165mm HESH', 0.5),
    499: ('3BK16M HEAT', 0.1),
    500: ('100mm HE', 0.1),
    504: ('M393A1 HESH', 0.1),
    507: ('50x228mm', 0.125),
    540: ('M1147 HE', 0.25),
    546: ('30x165mm HE', 0.25),
    567: ('30x170mm HEI-T', 0.25),
    576: ('DM11', 0.25),
    577: ('DM12A1', 0.2),
    716: ('115mm HE', 0.25),
    717: ('115mm HE', 0.25),
    2009023: ('100 mm gun / HJ-9 launcher HE', 0.1),
    2009031: ('ZPT-99 30 mm HE', 0.25),
    2009077: ('ZPT-98 125 mm HE', 0.25),
    2009105: ('125 mm tank gun HE', 0.25),
    2009133: ('105 mm rifled gun HE', 0.1),
    2009639: ('30 mm autocannon HE', 0.25),
    2009671: ('105 mm rifled gun HE', 0.1),
    2009953: ('76 mm HE (proximity)', 0.342),
    2010197: ('Prototype 105 mm gun HE', 0.25),
    2010797: ('100 mm rifled gun HE', 0.1),
    2010825: ('100 mm rifled tank gun HE', 0.1),
    2010853: ('105 mm rifled tank gun HE', 0.1),
    2011145: ('30 mm autocannon HE', 0.25),
    2011303: ('105 mm rifled gun HE', 0.1),
    2011359: ('125 mm tank gun HE', 0.25),
    2011387: ('ZPT-98 125 mm HE', 0.25),
    2019460: ('120 mm HE', 0.25),
    2019492: ('JM12A1 HEAT', 0.2),
    2019539: ('K280 HEAT-MP', 0.2),
    2019540: ('K277 HEAT-MP', 0.2),
    2019542: ('KM456A2 HEAT', 0.2),
    2019544: ('Type 91 HEAT', 0.2),
    2019545: ('Type 75 HESH', 0.1),
}


def apply(t, g, ok, rec, heli):
    A, WA, W, U = t['AmmunitionsJson'], t['WeaponAmmunitionsJson'], t['WeaponsJson'], t['Units']
    nm = lambda aid: (A[aid].get('HUDName') or A[aid].get('Name') or '').strip()
    users = lambda aid: [r for r in WA.values() if r and r.get('AmmunitionId') == aid]
    rows = set(DAMAGE) | set(HEAT) | set(IGNORE_COVER)
    for aid in sorted(rows):
        for r in users(aid):
            w = W[r['WeaponId']]
            ok(w.get('Type') in WT, (aid, nm(aid), 'fired only by tank guns, autocannons and HMGs', r['UnitId'], w.get('HUDName'), w.get('Type')))
            ok(r['UnitId'] not in SPAAG_MAIN or aid == SHARED, (aid, 'SPAAG main gun keeps its values', r['UnitId']))
    for aid, (c, n, b, a) in list(DAMAGE.items()) + list(HEAT.items()):
        ok(nm(aid) == n and A[aid].get('Damage') == b, (aid, n, 'damage before', A[aid].get('Damage'), b))
    for aid, (n, b) in IGNORE_COVER.items():
        ok(nm(aid) == n and round(A[aid].get('IgnoreCover') or 0, 3) == b, (aid, n, 'Ignore Cover before', A[aid].get('IgnoreCover'), b))
    ok({r['UnitId'] for r in users(SHARED)} == {SHARED_KEEP, SHARED_CUT}, ('57x348mm HE users', {r['UnitId'] for r in users(SHARED)}))
    ok(str(SHARED) in heli['ammo'], 'helicopter range entry for 491')
    copy = g.add('AmmunitionsJson', A[SHARED])
    for r in users(SHARED):
        if r['UnitId'] == SHARED_CUT: g.put('WeaponAmmunitionsJson', r['Id'], {'AmmunitionId': copy})
    heli['ammo'][str(copy)] = heli['ammo'][str(SHARED)]
    ok({r['UnitId'] for r in users(SHARED)} == {SHARED_KEEP} and {r['UnitId'] for r in users(copy)} == {SHARED_CUT}, '491 Ural only, copy Toros only')
    for aid, (c, n, b, a) in list(DAMAGE.items()) + list(HEAT.items()):
        tgt = copy if aid == SHARED else aid
        ok(aid != SHARED or SHARED_CUT in [r['UnitId'] for r in users(copy)], 'shared row cut on the copy')
        g.put('AmmunitionsJson', tgt, {'Damage': a})
    for aid in IGNORE_COVER:
        g.put('AmmunitionsJson', copy if aid == SHARED else aid, {'IgnoreCover': 0})
    ok(A[SHARED]['Damage'] == 4.3 and A[SHARED]['IgnoreCover'] == 0.25 and A[copy]['Damage'] == 3.4 and A[copy]['IgnoreCover'] == 0, 'Ural 491 unchanged, Toros copy cut')
    # step and ratio checks
    step = {'Tank guns': 0.5, 'Autocannons': 0.2, 'HMGs': 0.1}
    for aid, (c, n, b, a) in DAMAGE.items():
        s = step[c]
        ok(abs(a / s - round(a / s)) < 1e-9 and abs(a - b * 0.8) <= s / 2 + 1e-9 and a < b, (aid, n, c, b, a, 'x0.8 to the nearest', s))
    he_after = {a for aid, (c, n, b, a) in DAMAGE.items() if c == 'Tank guns'}
    for aid, (c, n, b, a) in HEAT.items():
        ok(c == 'Tank guns' and a in he_after and a < b, (aid, n, 'HEAT matches a tank HE value', b, a))
    rec['cover_damage_094'] = {'building_damage_floor': [0.18, 0.3], 'damage': {str(k): [v[2], v[3]] for k, v in DAMAGE.items()},
                               'heat': {str(k): [v[2], v[3]] for k, v in HEAT.items()}, 'ignore_cover_to_0': sorted(IGNORE_COVER),
                               'toros_57mm_copy': copy, 'spaag_main_unchanged': list(SPAAG_MAIN)}
    return copy

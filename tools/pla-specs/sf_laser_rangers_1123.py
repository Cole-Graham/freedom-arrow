"""Lateralus 23 Nov 2026 15:2x PST, thread 1568104480459722894: "Rangers RRC Standoff loadout price +0 -> +5" and "The following units are missing
their laser ability: Taishan Eagles, Beijing Swords, Mountain Leopards, Sharp Swords, Whistling Arrows (make sure we are still re-using ability rows
and not creating new ability rows, unless we are asking for a new combination of abilities)". Called from batch_0_9_5b.py (after
sf_recon_armor_1123, which moves Taishan Eagles to row 11).
- Rangers RRC (77): option 1481 Custom_Option_Standoff +0 -> +5; its swap unit Rangers RRC (338) 65 -> 70 (swap price = base 65 + option).
- Laser: each unit's only ability link moves to the existing row that equals its current row plus the laser (1200 m), so smoke, sprint and the rest
  stay as they are. No new rows.
  Taishan Eagles 1203 and Whistling Arrows 1184: row 11 "Sprint Smoke" -> 28 "Sprint Smoke Laser" (vanilla).
  Sharp Swords 1174: row 81 "Sprint30 Smoke x4" -> 2000611 "Sprint30 Smoke x4 Laser".
  Mountain Leopards 1186: row 2000198 "Sprint Smoke" (no sprint) -> 2000210 "Sprint Smoke Laser" (no sprint).
  Beijing Swords 1187 already links 2000611 (laser 1200 m) in 0.9.5b and in this batch: checked, not changed."""

LASER = {'IsLaserDesignator', 'LaserMaxRange', 'LaserUsableInMove'}
MOVES = ((1203, 2013760, 11, 28), (1184, 2013190, 11, 28), (1174, 2012854, 81, 2000611), (1186, 2013254, 2000198, 2000210))


def apply(t, g, ok, rec):
    U, UAB, AB, O, M = t['Units'], t['UnitAbilitiesJson'], t['AbilitiesJson'], t['OptionsJson'], t['ModificationsJson']
    ign = {'Id', 'Name'}
    diff = lambda a, b: {k for k in set(a) | set(b) if k not in ign and a.get(k) != b.get(k)}
    # Rangers RRC Standoff +0 -> +5
    o = O[1481]
    ok(o['UIName'] == 'Custom_Option_Standoff' and not o.get('Cost') and o['ReplaceUnitId'] == 338 and M[o['ModificationId']]['UnitId'] == 77, 'Rangers RRC Standoff option 1481 at +0 -> unit 338')
    ok(U[77]['Cost'] == 65 and U[338]['Cost'] == 65 and U[77]['HUDName'].strip() == 'Rangers RRC', ('Rangers RRC 65 / swap 65', U[77]['Cost'], U[338]['Cost']))
    g.put('OptionsJson', 1481, {'Cost': 5});g.put('Units', 338, {'Cost': 70})
    ok(U[338]['Cost'] == U[77]['Cost'] + O[1481]['Cost'], 'swap price = base + option')
    # lasers
    for uid, link, old, new in MOVES:
        ls = [r for r in UAB.values() if r and r.get('UnitId') == uid]
        ok([r['Id'] for r in ls] == [link] and UAB[link]['AbilityId'] == old and not AB[old].get('IsLaserDesignator'), (U[uid]['HUDName'], 'one link', link, 'to row', old, 'without laser', [(r['Id'], r['AbilityId']) for r in ls]))
        ok(AB[new].get('IsLaserDesignator') and AB[new].get('LaserMaxRange') == 1200 and diff(AB[old], AB[new]) <= LASER, (U[uid]['HUDName'], 'row', new, '= row', old, '+ laser 1200', sorted(diff(AB[old], AB[new]))))
        g.put('UnitAbilitiesJson', link, {'AbilityId': new})
    ok([r['AbilityId'] for r in UAB.values() if r and r.get('UnitId') == 1187] == [2000611] and AB[2000611]['IsLaserDesignator'], 'Beijing Swords already has the laser row 2000611')
    mods = {m['Id'] for m in M.values() if m and m.get('UnitId') in (1203, 1184, 1174, 1186, 1187)}
    ok(not any(o.get(f'Ability{i}Id') for o in O.values() if o and o.get('ModificationId') in mods for i in (1, 2, 3)), 'no loadout option sets an ability on these units')
    rec['sf_laser_rangers_1123'] = {'rangers_rrc_standoff': [0, 5], 'unit_338': [65, 70], 'laser_rows': {U[u]['HUDName'].strip(): [o2, n] for u, _, o2, n in MOVES}, 'beijing_swords': 'already 2000611'}

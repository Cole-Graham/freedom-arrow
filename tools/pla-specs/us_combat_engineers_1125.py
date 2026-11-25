"""US Combat Engineers 449 (Lateralus 25 Nov 2026 11:5x, thread 1572962048705429598: "US Combat Engineers: M-25 CDTE quantity 2 -> 1, M4A1 quantity 5 -> 6,
Price 75 -> 70, queue it up").
- M-25 CDTE 2 -> 1: member 934 (M4A1 + M-25) loses the M-25 and keeps his M4A1; member 933 keeps the M-25. The M-25 ammo row stays 120 per carrier, so
  the squad's M-25 pool is 240 -> 120. Head count 9 and HP unchanged.
- Price 75 -> 70.
- M4A1 5 -> 6 is NOT applied here: the 5 M4A1 already include both M-25 men (933, 934 carry M4A1 + M-25), so a 6th M4A1 needs another man's
  weapon changed (asked in the thread)."""
UNIT, KEEP, DROP, M25, M4 = 449, 933, 934, 2002020, 50


def apply(t, g, ok, rec):
    U, SM, SW, WA, O = t['Units'], t['SquadMembersJson'], t['SquadWeaponsJson'], t['WeaponAmmunitionsJson'], t['OptionsJson']
    mem = {m['Id']: m for m in SM.values() if m and m['UnitId'] == UNIT}
    count = lambda w: sum((m.get('PrimaryWeaponId') == w) + (m.get('SpecialWeaponId') == w) for m in mem.values())
    ok(U[UNIT]['HUDName'] == 'Combat Engineers' and U[UNIT]['CountryId'] == 2 and U[UNIT]['Cost'] == 75, 'US Combat Engineers 449, 75 pts')
    ok(len(mem) == 9 and count(M25) == 2 and count(M4) == 5 and mem[DROP]['PrimaryWeaponId'] == M4 and mem[DROP]['SpecialWeaponId'] == M25
       and mem[KEEP]['SpecialWeaponId'] == M25, ('449 before: 9 men, M-25 x2 (933, 934), M4A1 x5', count(M25), count(M4)))
    ok(not [o for o in O.values() if o and o.get('ReplaceUnitId') == UNIT], '449 has no loadout swap rows (no swap price to keep in step)')
    g.put('SquadMembersJson', DROP, {'SpecialWeaponId': 0})
    g.put('Units', UNIT, {'Cost': 70})
    mem = {m['Id']: m for m in SM.values() if m and m['UnitId'] == UNIT}
    ok(len(mem) == 9 and count(M25) == 1 and count(M4) == 5 and U[UNIT]['Cost'] == 70, ('449 after: 9 men, M-25 x1, M4A1 x5, 70 pts', count(M25), count(M4)))
    ok(any(r['UnitId'] == UNIT and r['WeaponId'] == M25 for r in SW.values() if r) and any(r['UnitId'] == UNIT and r['WeaponId'] == M25 for r in WA.values() if r),
       '449 keeps its M-25 weapon and ammo rows for the remaining carrier')
    rec['us_combat_engineers_1125'] = {'unit': UNIT, 'm25_removed_from': DROP, 'cost': [75, 70]}
    print('US COMBAT ENGINEERS 1125', rec['us_combat_engineers_1125'])

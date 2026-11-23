"""Lateralus 23 Nov 2026 14:5x PST, thread 1568104480459722894: "Chinese Combat Engineers Thermobaric Rocket loadout: Smoke 1 -> 4,
Armor 8 -> 10, 8 -> 7 men, 40 -> 35 HP, QBZ-191 5 -> 4 quantity"; then "actually, both of their loadouts should only have 1 smoke".
Called from batch_0_9_5b.py.
The loadout is option 24354 (Custom_Option_Thermobaric_launcher, +10) on Combat Engineers 工兵班 (1156); it swaps the card to unit 1162
Thermobaric Breachers 温压工兵. Changes on 1162, reusing existing rows (ability-row-reuse rule):
- Smoke: both loadouts have 1 smoke. 1162 already links row 11 "Sprint Smoke" (x1); Combat Engineers (1156, the Multipurpose loadout) moves from
  row 81 "Sprint30 Smoke x4" to row 11, the same row except smoke 1 (link 2012356).
- Armour/HP: armour link 2012509 row 2012508 (ArmorValue 8, MaxHealthPoints 40, used by 1162 only) -> vanilla row 273 "Armor Infantry Elite
  7Men" (10 / 35), the same row except those two values (Combat Engineers' own). Row 2012508 stays in the table, unused.
- Men 8 -> 7 and QBZ-191 5 -> 4: squad member 2015093 (QBZ-191 + PF-97, death priority 3) is removed. Each QBZ-191 man also carries a PF-97, so the
  squad's PF-97 launchers (and rockets, 1 each) go 5 -> 4 as well. The keeper (2015089, priority 1) and the three HAWK 97-2 men stay.
Price unchanged (1162 = 60 = Combat Engineers 50 + option 10)."""


def apply(t, g, ok, rec):
    U, SM, UAB, UA, AB, AR = t['Units'], t['SquadMembersJson'], t['UnitAbilitiesJson'], t['UnitArmorsJson'], t['AbilitiesJson'], t['ArmorsJson']
    O, M = t['OptionsJson'], t['ModificationsJson']
    ok(U[1162]['HUDName'].strip().startswith('Thermobaric Breachers') and U[1156]['HUDName'].strip().startswith('Combat Engineers'), 'units 1162 / 1156')
    ok(O[24354]['ReplaceUnitId'] == 1162 and M[O[24354]['ModificationId']]['UnitId'] == 1156, 'option 24354 swaps Combat Engineers to 1162')
    ign = {'Id', 'Name'}
    diff = lambda a, b: {k for k in set(a) | set(b) if k not in ign and a.get(k) != b.get(k)}
    # smoke: 1 on both loadouts (1162 stays on row 11; 1156 row 81 x4 -> row 11 x1)
    ok(UAB[2012513]['UnitId'] == 1162 and UAB[2012513]['AbilityId'] == 11 and AB[11]['SmokeAmmunitionQuantity'] == 1, 'Thermobaric loadout smoke link 2012513 -> row 11 (x1)')
    ok(UAB[2012356]['UnitId'] == 1156 and UAB[2012356]['AbilityId'] == 81, 'Combat Engineers smoke link 2012356 -> row 81 (x4)')
    ok(diff(AB[81], AB[11]) == {'SmokeAmmunitionQuantity'} and AB[11]['SmokeAmmunitionQuantity'] == 1, 'row 11 = row 81 with smoke 1')
    ok(not any(o.get(f'Ability{i}Id') for o in O.values() if o and o.get('ModificationId') in {m['Id'] for m in M.values() if m and m.get('UnitId') in (1156, 1162)} for i in (1, 2, 3)), 'no loadout option sets an ability')
    g.put('UnitAbilitiesJson', 2012356, {'AbilityId': 11})
    # armour 8 -> 10, HP 40 -> 35
    ok(UA[2012509]['UnitId'] == 1162 and UA[2012509]['ArmorId'] == 2012508 and (AR[2012508]['ArmorValue'], AR[2012508]['MaxHealthPoints']) == (8, 40), 'armour link 2012509 -> 2012508 (8 / 40)')
    ok(diff(AR[2012508], AR[273]) == {'ArmorValue', 'MaxHealthPoints'} and (AR[273]['ArmorValue'], AR[273]['MaxHealthPoints']) == (10, 35), 'row 273 = 2012508 with 10 / 35')
    g.put('UnitArmorsJson', 2012509, {'ArmorId': 273})
    # 8 -> 7 men, QBZ-191 5 -> 4
    men = [m for m in SM.values() if m and m.get('UnitId') == 1162]
    gone = SM[2015093]
    ok(len(men) == 8 and gone['UnitId'] == 1162 and gone['DeathPriority'] == 3 and gone['SpecialWeaponId'] == 2012515, ('8 men; 2015093 is a priority-3 PF-97 carrier', len(men)))
    rifle = gone['PrimaryWeaponId'];n_rifle = sum(1 for m in men if m.get('PrimaryWeaponId') == rifle)
    ok(n_rifle == 5, ('5 QBZ-191 men before', n_rifle))
    g.remove('SquadMembersJson', 2015093)
    men = [m for m in SM.values() if m and m.get('UnitId') == 1162]
    ok(len(men) == 7 and sum(1 for m in men if m.get('PrimaryWeaponId') == rifle) == 4 and sum(1 for m in men if m.get('SpecialWeaponId') == 2012515) == 4
       and any(m.get('DeathPriority') == 1 for m in men), '7 men, 4 QBZ-191, 4 PF-97, keeper kept')
    ok(U[1162]['Cost'] == U[1156]['Cost'] + O[24354]['Cost'], 'swap price = base + option')
    rec['thermobaric_breachers_1123'] = {'unit': 1162, 'smoke_1156': [81, 11], 'smoke_1162': 11, 'armor': [2012508, 273], 'men': [8, 7], 'qbz191': [5, 4], 'pf97': [5, 4], 'removed_member': 2015093}

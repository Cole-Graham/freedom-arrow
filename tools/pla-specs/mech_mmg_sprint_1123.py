"""Mech. Riflemen MMG sprint back (Lateralus 23 Nov 2026 19:5x PST, thread 1572962048705429598).
"Mech. Riflemen MMG should get sprint back, everything else is fine."
- Unit 370 links ability 2000198 'Sprint Smoke' through UnitAbilities row 595: an FA copy of vanilla 11 with IsInfantrySprint False
  (since 0.1, d420fd0b). Vanilla row 595 links 11. Row 595 -> 11 again (vanilla); 11 = 2000198 apart from the sprint flag.
- Unchanged: row 2000198 and its other units, and every other no-sprint loadout (Mech. Riflemen Dragon 638 included).
"""
UNIT, ROW, FA, VAN = 370, 595, 2000198, 11
DIFF = lambda a, b: {k: (a.get(k), b.get(k)) for k in set(a) | set(b) if k not in ('Id', 'Name') and a.get(k) != b.get(k)}


def apply(t, g, ok, rec):
    U, AB, UA = t['Units'], t['AbilitiesJson'], t['UnitAbilitiesJson']
    ok(U[UNIT]['HUDName'] == 'Mech. Riflemen MMG', (UNIT, U[UNIT]['HUDName']))
    ok([(r['Id'], r['AbilityId']) for r in UA.values() if r and r['UnitId'] == UNIT] == [(ROW, FA)], (UNIT, 'one ability row 595 -> 2000198'))
    ok(DIFF(AB[FA], AB[VAN]) == {'IsInfantrySprint': (False, True)}, ('11 = 2000198 apart from sprint', DIFF(AB[FA], AB[VAN])))
    fa_before, users = dict(AB[FA]), sorted(r['UnitId'] for r in UA.values() if r and r['AbilityId'] == FA and r['UnitId'] != UNIT)
    g.put('UnitAbilitiesJson', ROW, {'AbilityId': VAN})
    sprint = lambda u: any(AB[r['AbilityId']]['IsInfantrySprint'] for r in UA.values() if r and r['UnitId'] == u)
    ok(sprint(UNIT) and not sprint(638), '370 sprints; Mech. Riflemen Dragon 638 still does not')
    ok(dict(AB[FA]) == fa_before and users == sorted(r['UnitId'] for r in UA.values() if r and r['AbilityId'] == FA), '2000198 and its other units unchanged')
    rec['mech_mmg_sprint_1123'] = {'unit': UNIT, 'unit_ability_row': ROW, 'ability': [FA, VAN], 'other_2000198_units': users}
    print('MECH MMG SPRINT', rec['mech_mmg_sprint_1123'])

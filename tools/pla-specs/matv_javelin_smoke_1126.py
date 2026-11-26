"""M-ATV Javelin smoke, 1 charge (Osama 26 Nov 2026 13:4x PST, bugs thread 1573561286803980289: "Dev build, matv with javelin gets smoke 1 charge").
The M-ATV Javelin (vanilla unit 714) is already linked to the vanilla option smoke row 2000195 'Smoke x1 NoModel' (1 smoke charge, 5 s cooldown),
but no option turns it on, so it has no smoke (the plain M-ATV 467 is the same and is left alone). Vanilla pattern (Stryker ICV options 7 and 8):
both armour options carry Ability1Id 2000195. So the M-ATV Javelin's two armour options (Default, Uparmored) get Ability1Id 2000195; no new
ability row, price unchanged."""
UNIT = 714
SMOKE = 2000195


def apply(t, g, ok, rec):
    U, A, M, O, UA = t['Units'], t['AbilitiesJson'], t['ModificationsJson'], t['OptionsJson'], t['UnitAbilitiesJson']
    ok(U[UNIT]['Name'] == 'M-ATV Javelin', ('unit 714 is the M-ATV Javelin', U[UNIT]['Name']))
    a = A[SMOKE]
    ok(a['IsSmoke'] and a['SmokeAmmunitionQuantity'] == 1 and not a.get('IsDefault'), 'row 2000195 = option smoke x1')
    ok(any(r and r['UnitId'] == UNIT and r['AbilityId'] == SMOKE for r in UA.values()), 'M-ATV Javelin linked to 2000195')
    (arm,) = [m for m in M.values() if m and m['UnitId'] == UNIT and m['Type'] == 5]
    opts = sorted([o for o in O.values() if o and o['ModificationId'] == arm['Id']], key=lambda o: o['Order'])
    before = [(o['UIName'], o.get('Ability1Id', 0)) for o in opts]
    ok(len(opts) == 2 and all(not o.get('Ability1Id') for o in opts), ('M-ATV Javelin armour options, slot 1 free', before))
    for o in opts: g.put('OptionsJson', o['Id'], {'Ability1Id': SMOKE})
    after = [(O[o['Id']]['UIName'], O[o['Id']]['Ability1Id']) for o in opts]
    ok(all(x == SMOKE for _, x in after), ('M-ATV Javelin smoke on both armour options', after))
    rec['matv_javelin_smoke_1126'] = {'unit': UNIT, 'options_before': before, 'options_after': after}
    print('M-ATV JAVELIN SMOKE', rec['matv_javelin_smoke_1126'])

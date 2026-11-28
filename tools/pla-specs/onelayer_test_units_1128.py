"""One-layer TEST units (Osama 28 Nov 2026 01:1x, bugs thread 1573561286803980289: "add extra units in the next build called test units so I can flip
between the units. you can bake about 10 models"; 01:0x "we'll remove these after. Try different archetypes of ground units").
Each test unit is a full copy of a China ground card (same rows, turrets, loadouts, price, specs), named "<parent Name> TEST 1L" so FAModels draws
the one-layer copy of its Arsenal model (work/onelayer-test-1128, models.json entry added by model-rework-096/stage.py; battle files unchanged).
HUDName "TEST 1L <parent HUDName>". To remove: delete the import line in batch_0_9_5b.py and the stage.py ONE-LAYER TEST block."""
PARENTS = ['PLA ZTZ-99A', 'PLA ZTQ-15', 'PLA ZBD-04A', 'PLA ZBL-08', 'PLA ZTL-11', 'PLA PGZ-09', 'PLA PLZ-05', 'PLA PHL-03',
           'PLA Shaanxi Troop Truck', 'PLA CSK-181 4x4']


def apply(t, g, ok, rec):
    U = t['Units']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    out = []
    for pn in PARENTS:
        ids = [i for i, u in U.items() if u and u.get('Name') == pn]
        ok(len(ids) == 1, (pn, 'one unit with this Name', ids))
        if len(ids) != 1: continue
        p = ids[0]; name = pn + ' TEST 1L'; hud = 'TEST 1L ' + (U[p].get('HUDName') or pn.replace('PLA ', ''))
        ok(not any(u and u.get('Name') == name for u in U.values()), (name, 'name free'))
        uid = g.add('Units', U[p], {'Name': name, 'HUDName': hud})   # inside g.scope('plb'): the ID comes from the plb block
        for tab, field, target in (('UnitArmorsJson', 'ArmorId', 'ArmorsJson'), ('UnitPropulsionsJson', 'MobilityId', 'MobilityJson')):
            for r in rows(tab, UnitId=p):
                g.add(tab, r, {'UnitId': uid, field: g.add(target, t[target][r[field]], {'Name': f'{t[target][r[field]]["Name"]} {name}'})})
        for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson'):
            for r in rows(tab, UnitId=p): g.add(tab, r, {'UnitId': uid})
        for m in rows('ModificationsJson', UnitId=p):
            nm = g.add('ModificationsJson', m, {'UnitId': uid})
            for o in rows('OptionsJson', ModificationId=m['Id']): g.add('OptionsJson', o, {'ModificationId': nm})
        for r in rows('SpecializationAvailabilitiesJson', UnitId=p): g.add('SpecializationAvailabilitiesJson', r, {'UnitId': uid})
        if not rows('SpecializationAvailabilitiesJson', UnitId=p):
            # transport-only parents (ZBD-04A, ZBL-08, Shaanxi truck, CSK-131) have no card of their own: the test copy gets a card in the ZTZ-99A's
            # spec, on the ZTZ-99A's availability row, so it can be picked in the Arsenal next to the other test units.
            (tpl,) = rows('SpecializationAvailabilitiesJson', UnitId=next(i for i, u in U.items() if u and u.get('Name') == 'PLA ZTZ-99A'))
            g.add('SpecializationAvailabilitiesJson', tpl, {'UnitId': uid})
        for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitArmorsJson', 'UnitPropulsionsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson',
                    'ModificationsJson'):
            ok(len(rows(tab, UnitId=uid)) == len(rows(tab, UnitId=p)), (name, tab, 'copied'))
        po = [o for m in rows('ModificationsJson', UnitId=p) for o in rows('OptionsJson', ModificationId=m['Id'])]
        to = [o for m in rows('ModificationsJson', UnitId=uid) for o in rows('OptionsJson', ModificationId=m['Id'])]
        ok([o['Cost'] for o in to] == [o['Cost'] for o in po] and U[uid]['Cost'] == U[p]['Cost'], (name, 'same prices as parent'))
        out.append({'unit': uid, 'parent': p, 'name': name, 'hud': hud, 'cost': U[uid]['Cost'],
                    'specs': [r['SpecializationId'] for r in rows('SpecializationAvailabilitiesJson', UnitId=uid)]})
    ok(len(out) == len(PARENTS) and all(x['specs'] for x in out), ('all test units made, each with a card', out))
    rec['onelayer_test_units_1128'] = out
    print('ONELAYER TEST UNITS', [(x['unit'], x['hud'], x['specs']) for x in out])

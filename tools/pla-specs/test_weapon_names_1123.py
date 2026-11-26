"""RETIRED 26 Nov 2026 (Lateralus): no [TEST] labels and no copies; the module now only keeps the IDs the copies used to take.
Was: Blue Dragon and Euro preview weapons marked as test stand-ins (Osama 23 Nov 2026 23:5x PST, thread "China cosmetic work": "can you replace all the
BD and Euro weapons with TEST or something like Standin ... maybe add [TEST] in each weapon and ammo").
Scope: every unit in Blue Dragon (Testing Preview) 23, France (Preview) 24 and Germany (Preview) 25, plus the units their loadout options swap in
(ReplaceUnitId). Every weapon and round those units can show gets '[TEST] ' in front of its Name and HUDName:
- a weapon / round / turret used ONLY by these units is renamed in place;
- a weapon or turret also used by any other unit (the US parents these cards were copied from) gets an own copy for these units, so no US or other card
  changes; a round also used by other units is shared as it is (Lateralus 26 Nov 2026: no label-only round copies).
Turret copies keep their weapons' order and child-turret links; the units' turret links, option turret slots, ammunition rows and squad weapons
point at the copies. Runs LAST in the batch."""
SPECS = (23, 24, 25)
TAG = '[TEST] '


def apply(t, g, ok, rec):
    U, SA, O, M = t['Units'], t['SpecializationAvailabilitiesJson'], t['OptionsJson'], t['ModificationsJson']
    T, TU, TW, W, A, WA, SW, SM = (t[k] for k in ('TurretsJson', 'TurretUnitsJson', 'TurretWeaponsJson', 'WeaponsJson', 'AmmunitionsJson',
                                                  'WeaponAmmunitionsJson', 'SquadWeaponsJson', 'SquadMembersJson'))
    live = lambda tab: [r for r in t[tab].values() if r]
    tslots = lambda o: [k for k in o if k.startswith('Turret') and k.endswith('Id') and k[6:-2].isdigit() and o[k]]
    mod_unit = {m['Id']: m['UnitId'] for m in live('ModificationsJson')}
    # target units: the three specs + option ReplaceUnitId closure
    tgt = {r['UnitId'] for r in live('SpecializationAvailabilitiesJson') if r['SpecializationId'] in SPECS}
    while True:
        add = {o['ReplaceUnitId'] for o in live('OptionsJson') if o.get('ReplaceUnitId') and mod_unit.get(o['ModificationId']) in tgt} - tgt
        if not add: break
        tgt |= add
    ok(len(tgt) >= 32, ('BD + Euro units', len(tgt)))
    def shown(units):   # unit -> sorted weapon + round names it can show
        res = {}
        tu = {}
        for r in live('TurretUnitsJson'): tu.setdefault(r['UnitId'], set()).add(r['TurretId'])
        for o in live('OptionsJson'):
            u = mod_unit.get(o['ModificationId'])
            if u in units: tu.setdefault(u, set()).update(o[k] for k in tslots(o))
        kids = {}
        for tid, tr in T.items():
            if tr and tr.get('ParentTurretId'): kids.setdefault(tr['ParentTurretId'], set()).add(tid)
        tw = {}
        for r in live('TurretWeaponsJson'): tw.setdefault(r['TurretId'], []).append(r['WeaponId'])
        wa = {}
        for r in live('WeaponAmmunitionsJson'): wa.setdefault(r['UnitId'], []).append(r['AmmunitionId'])
        sw = {}
        for r in live('SquadWeaponsJson'): sw.setdefault(r['UnitId'], []).append(r['WeaponId'])
        for u in units:
            ts, todo = set(), list(tu.get(u, ()))
            while todo:
                x = todo.pop()
                if x in ts: continue
                ts.add(x); todo += kids.get(x, ())
            ws = [w for x in ts for w in tw.get(x, ())] + sw.get(u, [])
            res[u] = (sorted(W[w]['HUDName'] or '' for w in ws if W.get(w)), sorted(A[a]['HUDName'] or '' for a in wa.get(u, ()) if A.get(a)))
        return res
    others = [u for u, r in U.items() if r and u not in tgt]
    before = shown(others)
    tbefore = shown(tgt)
    # who uses what (unit sets)
    tur_users = {}
    for r in live('TurretUnitsJson'): tur_users.setdefault(r['TurretId'], set()).add(r['UnitId'])
    for o in live('OptionsJson'):
        for k in tslots(o): tur_users.setdefault(o[k], set()).add(mod_unit.get(o['ModificationId']))
    changed = True
    while changed:   # a child turret is used by whoever uses its parent
        changed = False
        for tid, tr in T.items():
            p = tr and tr.get('ParentTurretId')
            if p and p in tur_users and not tur_users[p] <= tur_users.setdefault(tid, set()):
                tur_users[tid] |= tur_users[p]; changed = True
    tgt_tur = {tid for tid, us in tur_users.items() if us & tgt}
    w_users = {}
    for r in live('TurretWeaponsJson'):
        for u in tur_users.get(r['TurretId'], ()): w_users.setdefault(r['WeaponId'], set()).add(u)
    for r in live('SquadWeaponsJson'): w_users.setdefault(r['WeaponId'], set()).add(r['UnitId'])
    for r in live('SquadMembersJson'):
        for k in ('PrimaryWeaponId', 'SpecialWeaponId'):
            if r.get(k): w_users.setdefault(r[k], set()).add(r['UnitId'])
    a_users = {}
    for r in live('WeaponAmmunitionsJson'): a_users.setdefault(r['AmmunitionId'], set()).add(r['UnitId'])
    tgt_w = {w for w, us in w_users.items() if us & tgt}
    tgt_a = {a for a, us in a_users.items() if us & tgt}
    # Lateralus 26 Nov 2026 (thread 1572962048705429598): "There is no need for the test label ... its a preview and everything is subject to
    # change" and, for the weapon and turret copies, "Yes do it". The preview units keep the shared weapons, rounds and turrets with their own
    # names; nothing is copied or renamed. The IDs the copies used to take stay unused (g.next advances by the same count), so every row the
    # batch makes later keeps its ID.
    w_copies = sum(1 for w in tgt_w if not w_users[w] <= tgt)
    a_copies = sum(1 for a in tgt_a if not a_users[a] <= tgt)
    t_copies = [tid for tid in tgt_tur if not tur_users[tid] <= tgt]
    tw_copies = sum(1 for r in live('TurretWeaponsJson') if r['TurretId'] in set(t_copies))
    g.next += w_copies + a_copies + len(t_copies) + tw_copies
    after = shown(others)
    ok(all(before[u] == after[u] for u in others), 'other units unchanged')
    ok(shown(tgt) == tbefore, 'BD/Euro units keep their weapons and rounds as they are')
    rec['test_weapon_names'] = {'units': len(tgt), 'ids_kept_unused': w_copies + a_copies + len(t_copies) + tw_copies,
                                'weapon_copies_not_made': w_copies, 'round_copies_not_made': a_copies, 'turret_copies_not_made': len(t_copies)}
    print('TEST NAMES (off)', rec['test_weapon_names'])

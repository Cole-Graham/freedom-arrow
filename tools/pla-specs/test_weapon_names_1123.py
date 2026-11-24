"""Blue Dragon and Euro preview weapons marked as test stand-ins (Osama 23 Nov 2026 23:5x PST, thread "China cosmetic work": "can you replace all the
BD and Euro weapons with TEST or something like Standin ... maybe add [TEST] in each weapon and ammo").
Scope: every unit in Blue Dragon (Testing Preview) 23, France (Preview) 24 and Germany (Preview) 25, plus the units their loadout options swap in
(ReplaceUnitId). Every weapon and round those units can show gets '[TEST] ' in front of its Name and HUDName:
- a weapon / round / turret used ONLY by these units is renamed in place;
- one also used by any other unit (the US parents these cards were copied from) gets an own copy for these units, so no US or other card changes.
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
    tag = lambda s: s if (s or '').startswith(TAG) else TAG + (s or '')
    wmap, amap, tmap, st = {}, {}, {}, {'w_renamed': 0, 'w_copied': 0, 'a_renamed': 0, 'a_copied': 0, 't_copied': 0}
    for w in sorted(tgt_w):
        new = {'Name': tag(W[w]['Name']), 'HUDName': tag(W[w].get('HUDName'))}
        if w_users[w] <= tgt: g.put('WeaponsJson', w, new); wmap[w] = w; st['w_renamed'] += 1
        else: wmap[w] = g.add('WeaponsJson', W[w], new); st['w_copied'] += 1
    for a in sorted(tgt_a):
        new = {'Name': tag(A[a]['Name']), 'HUDName': tag(A[a].get('HUDName'))}
        if a_users[a] <= tgt: g.put('AmmunitionsJson', a, new); amap[a] = a; st['a_renamed'] += 1
        else: amap[a] = g.add('AmmunitionsJson', A[a], new); st['a_copied'] += 1
    # turrets: shared with other units -> copy (its weapon links point at the [TEST] weapons); target-only -> relink weapons in place
    for tid in sorted(tgt_tur):
        if tur_users[tid] <= tgt: tmap[tid] = tid
        else: tmap[tid] = g.add('TurretsJson', T[tid], {'Name': (T[tid].get('Name') or '') + ' [TEST]'}); st['t_copied'] += 1
    for tid in sorted(tgt_tur):
        nt = tmap[tid]; p = T[tid].get('ParentTurretId')
        if nt != tid and p in tmap: g.put('TurretsJson', nt, {'ParentTurretId': tmap[p]})
        for r in sorted([r for r in live('TurretWeaponsJson') if r['TurretId'] == tid], key=lambda r: r['Id']):
            if nt == tid: g.put('TurretWeaponsJson', r['Id'], {'WeaponId': wmap[r['WeaponId']]})
            else: g.add('TurretWeaponsJson', r, {'TurretId': nt, 'WeaponId': wmap[r['WeaponId']]})
    for r in live('TurretUnitsJson'):
        if r['UnitId'] in tgt and tmap.get(r['TurretId'], r['TurretId']) != r['TurretId']: g.put('TurretUnitsJson', r['Id'], {'TurretId': tmap[r['TurretId']]})
    for o in live('OptionsJson'):
        if mod_unit.get(o['ModificationId']) in tgt:
            ch = {k: tmap[o[k]] for k in tslots(o) if tmap.get(o[k], o[k]) != o[k]}
            if ch: g.put('OptionsJson', o['Id'], ch)
    for r in live('WeaponAmmunitionsJson'):
        if r['UnitId'] in tgt: g.put('WeaponAmmunitionsJson', r['Id'], {'WeaponId': wmap.get(r['WeaponId'], r['WeaponId']), 'AmmunitionId': amap[r['AmmunitionId']]})
    for r in live('SquadWeaponsJson'):
        if r['UnitId'] in tgt: g.put('SquadWeaponsJson', r['Id'], {'WeaponId': wmap[r['WeaponId']]})
    for r in live('SquadMembersJson'):
        if r['UnitId'] in tgt:
            ch = {k: wmap[r[k]] for k in ('PrimaryWeaponId', 'SpecialWeaponId') if r.get(k)}
            if ch: g.put('SquadMembersJson', r['Id'], ch)
    # checks: every weapon/round a target unit shows is [TEST]; nothing a non-target unit shows changed
    shown_w = set()
    for u in tgt:
        tids = {r['TurretId'] for r in live('TurretUnitsJson') if r['UnitId'] == u} | {o[k] for o in live('OptionsJson') if mod_unit.get(o['ModificationId']) == u for k in tslots(o)}
        shown_w |= {r['WeaponId'] for r in live('TurretWeaponsJson') if r['TurretId'] in tids}
        shown_w |= {r['WeaponId'] for r in live('SquadWeaponsJson') if r['UnitId'] == u}
    shown_a = {r['AmmunitionId'] for r in live('WeaponAmmunitionsJson') if r['UnitId'] in tgt}
    ok(all(W[w]['HUDName'].startswith(TAG) for w in shown_w), 'all BD/Euro weapons [TEST]')
    ok(all(A[a]['HUDName'].startswith(TAG) for a in shown_a), 'all BD/Euro rounds [TEST]')
    other_w = {r['WeaponId'] for r in live('TurretWeaponsJson') if (tur_users.get(r['TurretId'], set()) - tgt)} - set(wmap.values())
    ok(not any(W[w]['HUDName'].startswith(TAG) for w in other_w if w in W and w not in tgt_w), 'no [TEST] on other units')
    after = shown(others)
    bad = [u for u in others if before[u] != after[u]]
    ok(not bad, ('other units unchanged', len(others), bad[:5]))
    tafter = shown(tgt)
    ok(all(len(tbefore[u][0]) == len(tafter[u][0]) and len(tbefore[u][1]) == len(tafter[u][1]) and all(x.startswith(TAG) for x in tafter[u][0] + tafter[u][1]) for u in tgt),
       'BD/Euro units keep the same weapon/round count, all [TEST]')
    ok(all([x[len(TAG):] if x.startswith(TAG) else x for x in tbefore[u][0]] == sorted(x[len(TAG):] for x in tafter[u][0]) for u in tgt), 'BD/Euro weapon names same after the tag')
    rec['test_weapon_names'] = {'units': len(tgt), **st, 'weapons_shown': len(shown_w), 'rounds_shown': len(shown_a)}
    print('TEST NAMES', rec['test_weapon_names'])

"""Radar only on loadouts with a radar weapon; HHQ-10 and SeaRAM on SA radar (Lateralus 25 Nov 2026 08:5x-09:1x PST, thread 1568104480459722894).
08:52 "remove the radar ability for loadouts that don't have any radar weapons"; 09:17 "1. Yes that is what I want [no radar optics/SEAD exposure on those
loadouts] 2. (a) [new static non-default IR row for the MML] 3. HHQ-10 should actually benefit from radar, and it should have SA radar. This is also true
for the RIM-116 (SeaRAM), it should benefit from radar and have SA radar."
The game gives a unit its one default ability row plus, per slot Ability1/2/3, the first chosen option's non-default row (UnitsInfoService.ApplyCurrentMods,
1.2.2.1; memory option-ability-slots). So a per-loadout radar moves from the unit's default row onto the turret options (the M6 Linebacker pattern):
- Stryker M-SHORAD (20): default radar 60 unlinked; 62 (SA, same values, non-default) in Ability3 of the Stinger pod / Fletcher / Hellfire turrets
  (slot 1 = armour/APS, slot 2 = Fletcher laser). The M2 + Stinger turret: no radar.
- Centurion C-RAM (250): default 2021461 unlinked; Phalanx -> 2021462 (IR, non-default), SeaRAM -> 62 (SA) in Ability1.
- MML (393): default 2021460 (IR static) unlinked; new row = its copy with IsDefault false (no such row exists: checked) on the AIM-9 and Hellfire
  turrets, Ability1. The Stinger turret: no radar.
- HHQ-10 (1273): 2021461 (IR) -> 60 (SA). RIM-116 560 and HHQ-10 2019358 use the radar (radar_weapons_1124.KEEP_IR).
Lateralus 25 Nov 2026 12:1x: "MML AIM-9 loadout should use SA radar ability (just for the AIM-9 loadout, the hellfire loadout should stay as IR)
Stryker M-SHORAD should use IR radar ability for all 3 of its radar-equipped loadouts (instead of SA)". So:
- MML AIM-9 turret (1819): new row = SA static (58) with IsDefault false (no such row exists: checked); the unit links it too. Hellfire keeps IR static.
- Stryker M-SHORAD: Stinger pod / Fletcher / Hellfire options and the unit link 62 (SA) -> 2021462 (IR, non-default).
Creates two ability rows and two unit-ability links: keep this section after every other row-creating section."""
SA_DEF, SA_OPT, IR_DEF, IR_OPT, IR_STATIC, SA_STATIC = 60, 62, 2021461, 2021462, 2021460, 58


def _same(a, b):
    return {k: v for k, v in a.items() if k not in ('Id', 'Name')} == {k: v for k, v in b.items() if k not in ('Id', 'Name')}


def apply(t, g, ok, rec, HR):
    AB, UA, O, M, U = (t[k] for k in ('AbilitiesJson', 'UnitAbilitiesJson', 'OptionsJson', 'ModificationsJson', 'Units'))
    for i, d in ((SA_DEF, True), (SA_OPT, False), (IR_DEF, True), (IR_OPT, False), (IR_STATIC, True)):
        ok(AB[i].get('IsRadar') and AB[i].get('IsDefault') == d, (i, 'radar row default flag'))
    ok(_same(dict(AB[SA_DEF], IsDefault=False), AB[SA_OPT]) and _same(dict(AB[IR_DEF], IsDefault=False), AB[IR_OPT]), 'non-default twins')
    cand = dict(AB[IR_STATIC], IsDefault=False)
    ok(not any(_same(cand, a) for a in AB.values() if a), 'no non-default static IR row yet')
    links = lambda u: {r['AbilityId']: r['Id'] for r in UA.values() if r and r['UnitId'] == u}
    opt = lambda i, name: ok(O[i]['Name'] == name, (i, O[i]['Name'], name)) or O[i]
    done = {}

    def repoint(u, old, ab):   # keeps the link row's ID
        l = links(u);ok(old in l and ab not in l, (u, old, ab, 'link to repoint'));g.put('UnitAbilitiesJson', l[old], {'AbilityId': ab})

    def link(u, ab):
        if ab not in links(u):g.add('UnitAbilitiesJson', {'UnitId': u, 'AbilityId': ab}, {})
    # Stryker M-SHORAD
    for i, n in ((1935, 'MainTurret StrykerSHORAD M2'), (1936, 'MainTurret StrykerSHORAD 8xStinger'), (1937, 'MainTurret StrykerSHORAD Fletcher'),
                 (1938, 'MainTurret StrykerSHORAD Hellfire')):opt(i, n)
    ok(not any((o.get('Ability3Id') or 0) for o in O.values() if o and M[o['ModificationId']]['UnitId'] == 20), 'Stryker M-SHORAD slot 3 free')
    repoint(20, SA_DEF, IR_OPT)   # Lateralus 25 Nov 12:1x: IR, not SA
    for i in (1936, 1937, 1938):g.put('OptionsJson', i, {'Ability3Id': IR_OPT})
    done[20] = 'Stinger pod / Fletcher / Hellfire: IR radar (2021462); M2 + Stinger: none'
    # Centurion C-RAM
    opt(2110, 'MainTurret Centurion Phalanx');opt(2111, 'MainTurret Centurion SeRAM')
    ok(not any((o.get('Ability1Id') or 0) for o in O.values() if o and M[o['ModificationId']]['UnitId'] == 250), 'C-RAM slot 1 free')
    repoint(250, IR_DEF, IR_OPT);link(250, SA_OPT)
    g.put('OptionsJson', 2110, {'Ability1Id': IR_OPT});g.put('OptionsJson', 2111, {'Ability1Id': SA_OPT})
    done[250] = 'Phalanx: IR radar (2021462); SeaRAM: SA radar (62)'
    # MML
    for i, n in ((1818, 'MainTurret MML 15xStinger'), (1819, 'MainTurret MML 15xAIM9'), (1821, 'MainTurret MML 15xHellfire')):opt(i, n)
    ok(not any((o.get('Ability1Id') or 0) for o in O.values() if o and M[o['ModificationId']]['UnitId'] == 393), 'MML slot 1 free')
    new = g.add('AbilitiesJson', AB[IR_STATIC], {'Name': 'Radar IR SHORAD Static Not Default', 'IsDefault': False})
    repoint(393, IR_STATIC, new)
    g.put('OptionsJson', 1821, {'Ability1Id': new})
    ok(AB[SA_STATIC].get('IsRadarStatic') and AB[SA_STATIC].get('IsDefault'), 'SA static row 58')
    cand = dict(AB[SA_STATIC], IsDefault=False)
    ok(not any(_same(cand, a) for a in AB.values() if a), 'no non-default static SA row yet')
    sa_st = g.add('AbilitiesJson', AB[SA_STATIC], {'Name': 'Radar SHORAD Static Not Default', 'IsDefault': False})   # Lateralus 25 Nov 12:1x: MML AIM-9 = SA
    link(393, sa_st);g.put('OptionsJson', 1819, {'Ability1Id': sa_st})
    done[393] = f'AIM-9: SA static radar ({sa_st}); Hellfire: IR static radar ({new}); Stinger: none'
    # HHQ-10
    repoint(1273, IR_DEF, SA_DEF)
    done[1273] = 'SA radar (60)'
    HR.EDIT[new] = dict(HR.EDIT[IR_STATIC]);HR.LABEL[new] = HR.LABEL[IR_STATIC]
    HR.EDIT[sa_st] = dict(HR.EDIT[SA_STATIC]);HR.LABEL[sa_st] = HR.LABEL[SA_STATIC]
    for u in done:ok(sum(1 for a in links(u) if AB[a].get('IsDefault')) <= 1, (u, 'at most one default ability row'))
    rec['radar_loadouts_1125'] = {'units': {u: str(U[u]['HUDName']).strip() + ': ' + s for u, s in done.items()}, 'new_ability': new, 'new_sa_static': sa_st}
    return rec['radar_loadouts_1125']


def check(t, ok, rec, radar_weapons):
    """Every radar loadout (default ability + first option per slot) carries a weapon in radar_weapons."""
    import itertools
    AB, UA, O, M, TU, TW, T = (t[k] for k in ('AbilitiesJson', 'UnitAbilitiesJson', 'OptionsJson', 'ModificationsJson', 'TurretUnitsJson',
                                              'TurretWeaponsJson', 'TurretsJson'))
    rw = set(radar_weapons);bad = []
    ua = {};tu = {};mods = {};opts = {}
    for r in UA.values():
        if r:ua.setdefault(r['UnitId'], []).append(r['AbilityId'])
    for r in TU.values():
        if r:tu.setdefault(r['UnitId'], []).append(r)
    for m in M.values():
        if m:mods.setdefault(m['UnitId'], []).append(m['Id'])
    for o in O.values():
        if o:opts.setdefault(o['ModificationId'], []).append(o)
    tw = {}
    for r in TW.values():
        if r:tw.setdefault(r['TurretId'], set()).add(r['WeaponId'])
    slots = ('Ability1Id', 'Ability2Id', 'Ability3Id')
    for u, abl in ua.items():
        sets = [s for s in (opts.get(m, []) for m in mods.get(u, [])) if any(o.get(f'Turret{i}Id') for o in s for i in range(21)) or any(o.get(k) for o in s for k in slots)]
        if not any(AB.get(a, {}).get('IsRadar') for a in abl):continue
        base = {}
        for r in sorted(tu.get(u, []), key=lambda r: (not T[r['TurretId']].get('IsDefault'), r['Id'])):base.setdefault(r['Order'], r['TurretId'])
        for c in itertools.islice(itertools.product(*sets), 400):
            ab = {a for a in abl if AB.get(a, {}).get('IsDefault')}
            for k in slots:
                v = next((o.get(k) for o in c if o.get(k)), 0)
                if v:ab.add(v)
            if not any(AB.get(a, {}).get('IsRadar') for a in ab):continue
            tur = dict(base)
            for o in c:
                for i in range(21):
                    if o.get(f'Turret{i}Id'):tur[i] = o[f'Turret{i}Id']
            ts = set(tur.values());ts |= {r['TurretId'] for r in tu.get(u, []) if T[r['TurretId']].get('ParentTurretId') in ts}
            if not any(w in rw for x in ts for w in tw.get(x, ())):bad.append((u, [o['Id'] for o in c]))
    ok(not bad, ('radar loadouts without a radar weapon (unit, options)', bad[:20]))
    rec['radar_loadout_check'] = {'radar_loadouts_without_radar_weapon': len(bad)}

"""SHORAD radar split (Lateralus 24 Nov 2026 15:5x-16:4x PST, thread 1568104480459722894; proposal work/shorad-15-20261124).
- "come up with a detailed proposal to increase SHORAD range and optics multipliers to 1.5 ... for low altitude"; decisions 16:07:
  "keep helicopters at 1.25", burn time option "B", "keep the x1.5 range". 16:12: "create a seperate radar ability for units that only have
  Guns and/or Infrared weapons. For the units which have a mix of semi-active radar guided missiles + infrared like SLAMRAAM, create seperate
  rounds for them". 16:17: gun/IR rows "Use x1.25". 16:37: "just use the IR SHORAD ability on the units which only have guns". 16:42 "queue up
  this proposal".
- SA SHORAD: radar rows 58/60/62 (users with a radar-guided missile, Seeker 50/100, that can target planes): Low weapon range and Low optics
  1.25 -> 1.5. High stays 1.0 range / 2.0 optics.
- IR SHORAD: every other user of 58/60/62 (guns and/or heat-seeking missiles only) moves to a copy of its row with Low range 1.25 (unchanged)
  and Low optics 1.5. The China gun rows 2009175 (PGZ-09, Type 87 AW, AFT-10; also holds their smoke), 2009943 (JRVG-1) and 2019443 (LY-1)
  take the same values (or are relinked to the IR copy when that makes them identical to it: no duplicate ability rows, Lateralus 19 Nov).
- The game applies a radar unit's bonus to every weapon on it (GetAmmoShootingDistance 0x7D6330 reads only the round's five range fields),
  so the heat-seeking rounds of SA units (SLAMRAAM/NASAMS AIM-9, M-SHORAD Stinger) get copies whose LowAltRange (and an absolute SEAD/non-SEAD
  override) is x1.25/1.5: with the x1.5 radar they reach what they reach today. Their helicopter range keeps today's value.
- Option B burn time: every radar-guided round of an SA unit burns longer so its catch range against a jet flying away at 225 grows by the same
  20% as the range (work/shorad-15-20261124/burn.py). Each round is used by SA units only (checked).
- Helicopters keep x1.25 range and optics on every SHORAD row (heli_range.EDIT); labels for the radar icon on the card (heli_range.LABEL).
  Lateralus 24 Nov 18:4x: "the SHORAD text labels are way too big ... maybe just use 'IR' and 'SA' and make the text smaller": SA / IR / LR."""
OLD = (1.25, 1.25, 1.25, 1.0, 2.0)  # low range, low optics, ..., high range, high optics: rows 58/60/62 today
SA_ROWS = (58, 60, 62)
CHINA_GUN_ROWS = (2009175, 2009943, 2019443)
LR_ROWS = (59, 123)
SA_LOW, IR_LOW_RANGE, IR_LOW_OPTICS, HELI = 1.5, 1.25, 1.5, 1.25
IR_SCALE = IR_LOW_RANGE / SA_LOW
# round id: (MaxSpeed, Acceleration, BurnTime, MainEngineIgnitionDelay, MuzzleVelocity) today -> new BurnTime (burn.py, 24 Nov)
BURN = {20: ((700, 350, 2, 0, 50), 2.7), 28: ((600, 300, 2, 0.15, 75), 2.65), 69: ((500, 225, 2, 0, 50), 2.5), 77: ((700, 350, 2, 0.15, 75), 2.7),
        232: ((600, 300, 2, 0, 50), 2.65), 233: ((600, 300, 2, 0, 50), 2.65), 234: ((700, 350, 2, 0, 50), 2.7), 452: ((550, 250, 2, 0, 50), 2.55),
        464: ((600, 300, 2, 0, 50), 2.65), 603: ((700, 350, 2, 0, 50), 2.7), 2009199: ((600, 300, 2, 0.15, 75), 2.65),
        2009449: ((500, 225, 2, 0, 50), 2.5), 2009607: ((700, 350, 2, 0, 50), 2.7), 2010125: ((500, 225, 2, 0, 50), 2.5),
        2010629: ((700, 350, 2, 0.15, 75), 2.7),
        2009373: ((600, 300, 2, 0, 50), 2.65)}   # FB-10 as the AMRAAM clone (fb10_amraam_1124.py runs first): PGL-625 / Lynx 66 SPAAG on SA (Lateralus 18:5x)
KEYS = ('RadarLowAltWeaponRangeModifier', 'RadarLowAltOpticsModifier', 'RadarLowAltWeaponRangeModifier', 'RadarHighAltWeaponRangeModifier',
        'RadarHighAltOpticsModifier')


def _vals(a):
    return (a['RadarLowAltWeaponRangeModifier'], a['RadarLowAltOpticsModifier'], a['RadarLowAltWeaponRangeModifier'],
            a['RadarHighAltWeaponRangeModifier'], a['RadarHighAltOpticsModifier'])


def _same(a, b):
    return {k: v for k, v in a.items() if k not in ('Id', 'Name')} == {k: v for k, v in b.items() if k not in ('Id', 'Name')}


def apply(t, g, ok, rec, HR, heli):
    AB, UA, WA, A, O, M, U = (t[k] for k in ('AbilitiesJson', 'UnitAbilitiesJson', 'WeaponAmmunitionsJson', 'AmmunitionsJson', 'OptionsJson',
                                             'ModificationsJson', 'Units'))
    for i in SA_ROWS + CHINA_GUN_ROWS:
        ok(AB[i].get('IsRadar') and _vals(AB[i]) == OLD, (i, 'SHORAD radar row before', _vals(AB[i])))
    # users of 58/60/62: unit rows and loadout options
    links = {}
    for r in UA.values():
        if r and r['AbilityId'] in SA_ROWS:links.setdefault(r['UnitId'], []).append(('UnitAbilitiesJson', r['Id'], 'AbilityId', r['AbilityId']))
    for o in O.values():
        if not o:continue
        for k in ('Ability1Id', 'Ability2Id', 'Ability3Id'):
            if o.get(k) in SA_ROWS:links.setdefault(M[o['ModificationId']]['UnitId'], []).append(('OptionsJson', o['Id'], k, o[k]))

    def air(u):
        out = set()
        for r in WA.values():
            if r and r.get('UnitId') == u:
                a = A[r['AmmunitionId']]
                if int(a.get('TargetType') or 0) & 16:out.add('radar' if a.get('Seeker') in (50, 100) else 'ir' if a.get('Seeker') == 10 else 'gun')
        return out
    sa = sorted(u for u in links if 'radar' in air(u))
    ir = sorted(u for u in links if u not in sa)
    ok(len(sa) == 16 and len(ir) == 12 and {920, 1439} <= set(sa) and {31, 12, 389, 508, 20} <= set(sa) and {188, 221, 27, 393, 250, 1273} <= set(ir), ('SA / IR split', sa, ir))
    # IR SHORAD copies of the rows the IR units use
    new = {}
    for i in sorted({l[3] for u in ir for l in links[u]}):
        name = {58: 'Radar IR SHORAD Static', 60: 'Radar IR SHORAD', 62: 'Radar IR SHORAD Not Default'}[i]
        new[i] = g.add('AbilitiesJson', AB[i], {'Name': name, 'RadarLowAltWeaponRangeModifier': IR_LOW_RANGE, 'RadarLowAltOpticsModifier': IR_LOW_OPTICS})
    moved = []
    for u in ir:
        for tab, rid, field, old in links[u]:
            g.put(tab, rid, {field: new[old]});moved.append((u, tab, rid, old, new[old]))
    ir60 = AB[new[60]]
    china = {}
    for i in CHINA_GUN_ROWS:
        users = [r for r in UA.values() if r and r['AbilityId'] == i]
        ok(all('radar' not in air(r['UnitId']) for r in users), (i, 'China gun radar row: no radar-guided missiles on its units'))
        cand = dict(AB[i], RadarLowAltOpticsModifier=IR_LOW_OPTICS)
        twin = next((j for j in [new[60]] + [k for k, v in china.items() if v[0] == 'IR values'] if _same(cand, AB[j])), None)
        if twin:
            for r in users:g.put('UnitAbilitiesJson', r['Id'], {'AbilityId': twin})
            china[i] = ('relinked', twin, [r['UnitId'] for r in users])
        else:
            g.put('AbilitiesJson', i, {'RadarLowAltOpticsModifier': IR_LOW_OPTICS});china[i] = ('IR values', i, [r['UnitId'] for r in users])
    for i in SA_ROWS:g.put('AbilitiesJson', i, {'RadarLowAltWeaponRangeModifier': SA_LOW, 'RadarLowAltOpticsModifier': SA_LOW})
    # no duplicate ability rows (Lateralus 19 Nov)
    rows = [a for a in AB.values() if a]
    for a in rows:
        if a['Id'] in set(new.values()) | set(SA_ROWS) | {k for k, v in china.items() if v[0] == 'IR values'}:
            ok(not any(b['Id'] != a['Id'] and _same(a, b) for b in rows), (a['Id'], a['Name'], 'radar row has no identical twin'))
    # heat-seeking rounds on SA units: copies that do not gain from the x1.5 radar
    copies, heli_ammo = {}, {}
    for u in sa:
        for r in [r for r in WA.values() if r and r.get('UnitId') == u]:
            a = A[r['AmmunitionId']]
            if not (int(a.get('TargetType') or 0) & 16 and a.get('Seeker') == 10):continue
            if a['Id'] not in copies:
                f = {'Name': a['Name'] + ' SA-radar unit', 'LowAltRange': round(a['LowAltRange'] * IR_SCALE, 2)}
                for k in ('SeadProjectileRangeOverride', 'NonSeadProjectileRangeOverride'):
                    if (a.get(k) or 0) >= 100:f[k] = round(a[k] * IR_SCALE, 2)
                ok(a.get('LowAltRange', 0) > 0, (a['Id'], 'IR round has a Low range'))
                c = g.add('AmmunitionsJson', a, f);copies[a['Id']] = c
                heli_ammo[c] = heli['ammo'].get(str(a['Id']), a['LowAltRange'])
                HR.AMMO[c] = heli_ammo[c]
            g.put('WeaponAmmunitionsJson', r['Id'], {'AmmunitionId': copies[a['Id']]})
    ok(set(copies) == {465, 18}, ('IR rounds on SA units', sorted(copies)))
    # option B burn times
    burned = {}
    for u in sa:
        for r in [r for r in WA.values() if r and r.get('UnitId') == u]:
            a = A[r['AmmunitionId']]
            if int(a.get('TargetType') or 0) & 16 and a.get('Seeker') in (50, 100) and a.get('BurnTime'):
                ok(a['Id'] in BURN, (a['Id'], a['Name'], 'radar-guided SA round has a burn-time entry'))
                burned[a['Id']] = a['Name']
    for aid, (motor, nb) in BURN.items():
        a = A[aid]
        ok((a['MaxSpeed'], a['Acceleration'], a['BurnTime'], a.get('MainEngineIgnitionDelay') or 0, a.get('MuzzleVelocity') or 0) == motor, (aid, 'motor', motor))
        users = {r['UnitId'] for r in WA.values() if r and r['AmmunitionId'] == aid}
        ok(users <= set(sa), (aid, 'round used by SA units only', sorted(users - set(sa))))
        g.put('AmmunitionsJson', aid, {'BurnTime': nb})
    ok(set(burned) == set(BURN), ('burn table = radar-guided rounds of SA units', sorted(set(burned) ^ set(BURN))))
    # helicopters stay x1.25; labels for the card radar icon
    for i in SA_ROWS + CHINA_GUN_ROWS + tuple(new.values()):HR.EDIT[i] = {'helicopterRangeMultiplier': HELI, 'helicopterOpticsMultiplier': HELI}
    for i in SA_ROWS:HR.LABEL[i] = 'SA'
    for i in CHINA_GUN_ROWS + tuple(new.values()):HR.LABEL[i] = 'IR'
    for i in LR_ROWS:HR.LABEL[i] = 'LR'
    out = {'sa_units': {u: str(U[u].get('HUDName')).strip() for u in sa}, 'ir_units': {u: str(U[u].get('HUDName')).strip() for u in ir},
           'ir_rows': new, 'moved': moved, 'china_rows': china, 'ir_round_copies': copies, 'heli_ammo': heli_ammo,
           'burn': {k: v[1] for k, v in BURN.items()}}
    rec['shorad_radar_1124'] = out
    return out

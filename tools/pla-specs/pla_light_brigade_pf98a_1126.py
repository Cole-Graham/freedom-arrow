"""PLA Light Brigade build, PF-98 merge, PF-98A, Tank Hunters and Marines PF-98 (Osama 26 Nov 2026 12:5x-13:0x PST, thread 1567745029781454889).
Branch codex/batch/osama/pla-light-brigade only; the last plb section (after the smoke section), so no earlier row id moves.
- 12:5x "My plan is to give tank hunters the new PF-98A. The new PF-98A should be 700m." / 13:0x "And the new one is the A variant": PF-98A = the
  long-range PF-98 of the Sky Wolf Commandos (pla_light_brigade_skywolf_1126: Osama 03:48 "PF-98A, PF-98 clone copy but 800m range"): card name
  'PF-98' -> 'PF-98A', round 'PF-98A ammunition', GroundRange 400 -> 350 (card 800 -> 700 m). Internal Name stays 'PLA infantry PF-98 long range'
  (plb_infantry_rules.py finds its PF-98 model by that name). All other stats are the PF-98's. The Sky Wolf Commandos' launcher is 700 m too.
- 13:0x "All the old PF-98 and A (not tripod) are compressed to just PF-98": the four PF-98 launcher rows with identical weapon stats become one,
  the infantry PF-98 (2011832, round 2011833): 'PLA Prototype PF-98' (2004962, round 2004971: only the aim override 0 vs 0.2 and icon differ),
  'PLA infantry PF-98A mixed' (2011919, round 2011920) and 'PLA infantry PF-98A' (2013157, round 2013158). Every squad, soldier and ammo row moves
  to 2011832 / 2011833; second rounds on the old rows (the DZT-98 thermobaric) stay, now on 2011832. The old weapon and round rows are removed (the
  Lateralus rule: no identical copies). The PF-98 (tripod) (2016259) and the PF-98A stay separate.
- 12:5x "And the current tank hunters are rolled into the PLAN" / 13:0x "The new PF98 for marines just call Marines PF-98. The icon is the Marine sign
  with the SMAW icon in the bottom right corner": new unit 'Marines PF-98' = copy of the current Tank Hunters 坦克杀手 (1139: 6 men, 75 pts, the
  leader's PF-98 with 6 HEAT + 6 DZT-98) with its card row (4 cards) in PLAN and, by Osama's standing rule, the Marines' PLAN transports (ZBD-05,
  Z-20J, CTL-181, ZSD-05, ZBL-08). Card icon FA_PLA_INF_LINE_MARINE_PF98 (tools/icons-src/make_marines_pf98.py).
- Tank Hunters 坦克杀手 (1139) stay in PLAAF with their transports; the leader's PF-98 -> the PF-98A (6 HEAT at 700 m, the 6 DZT-98 stay).
Not yet tested in a game."""
TH, TH_CARD, PF98, PF98_A, DZT98, PLAAF, PLAN, MARINES = 1139, 2011937, 2011832, 2011833, 2016058, 17, 20, 1192
OLD = {2004962: 2004971, 2011919: 2011920, 2013157: 2013158}   # old PF-98 rows (weapon: its PF-98 round) merged into 2011832 / 2011833
ICON = 'FA_PLA_INF_LINE_MARINE_PF98'


def apply(t, g, ok, rec):
    U, W, A, SA = t['Units'], t['WeaponsJson'], t['AmmunitionsJson'], t['SpecializationAvailabilitiesJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    users = lambda w: sorted({U[r['UnitId']]['HUDName'] for r in rows('SquadWeaponsJson', WeaponId=w)})
    # PF-98A
    (lw,) = [i for i, w in W.items() if w and w.get('Name') == 'PLA infantry PF-98 long range']
    (lwa,) = rows('WeaponAmmunitionsJson', WeaponId=lw); la = lwa['AmmunitionId']
    ok(W[lw]['HUDName'] == 'PF-98' and A[la]['GroundRange'] == 400.0 and not any(w and w.get('HUDName') == 'PF-98A' for w in W.values()), 'long-range PF-98 (800 m), PF-98A name free')
    g.put('WeaponsJson', lw, {'HUDName': 'PF-98A'})
    g.put('AmmunitionsJson', la, {'HUDName': 'PF-98A ammunition', 'GroundRange': 350.0})
    # merge the old PF-98 rows
    same = lambda a, b, skip: all(a.get(k) == b.get(k) for k in set(a) | set(b) if k not in skip)
    for w, a in OLD.items():
        ok(same(W[w], W[PF98], ('Id', 'Name')), (w, W[w]['Name'], 'weapon stats = PF-98'))
        ok(same(A[a], A[PF98_A], ('Id', 'Name', 'HUDName', 'HUDIcon', 'AimTimeMinOverride', 'AimTimeMaxOverride')), (a, A[a]['Name'], 'round = PF-98 round'))
    before = {w: users(w) for w in OLD}
    for r in [r for r in t['SquadWeaponsJson'].values() if r and r['WeaponId'] in OLD]:
        ok(not rows('SquadWeaponsJson', UnitId=r['UnitId'], WeaponId=PF98), (r['UnitId'], 'has one PF-98 row only'))
        g.put('SquadWeaponsJson', r['Id'], {'WeaponId': PF98})
    for m in [m for m in t['SquadMembersJson'].values() if m and (m.get('PrimaryWeaponId') in OLD or m.get('SpecialWeaponId') in OLD)]:
        g.put('SquadMembersJson', m['Id'], {f: PF98 for f in ('PrimaryWeaponId', 'SpecialWeaponId') if m.get(f) in OLD})
    for r in [r for r in t['WeaponAmmunitionsJson'].values() if r and r['WeaponId'] in OLD]:
        g.put('WeaponAmmunitionsJson', r['Id'], {'WeaponId': PF98, **({'AmmunitionId': PF98_A} if r['AmmunitionId'] in OLD.values() else {})})
    refs = lambda i, key: [(tab, k) for tab, d in t.items() for k, r in d.items() if r for f, v in r.items() if f != 'Id' and key in f and v == i]
    for w, a in OLD.items():
        ok(not refs(w, 'Weapon') and not refs(a, 'Ammunition'), (w, a, 'no row uses the old PF-98 any more'))
        g.remove('WeaponsJson', w); g.remove('AmmunitionsJson', a)
    # Marines PF-98 = copy of the current Tank Hunters
    ok(U[TH]['HUDName'] == 'Tank Hunters 坦克杀手' and SA[TH_CARD]['UnitId'] == TH and SA[TH_CARD]['SpecializationId'] == PLAAF and len(rows('SpecializationAvailabilitiesJson', UnitId=TH)) == 1,
       'Tank Hunters: one PLAAF card row')
    ok(not any(u and 'Marines PF-98' in (u.get('Name', ''), u.get('HUDName', '')) for u in U.values()), 'Marines PF-98 name free')
    ok(not rows('ModificationsJson', UnitId=TH), 'Tank Hunters: no loadouts')
    mp = g.add('Units', U[TH], {'Name': 'PLA Marines PF-98', 'HUDName': 'Marines PF-98', 'ThumbnailFileName': ICON, 'Description': None, 'OriginalName': None})
    for tab in ('UnitArmorsJson', 'UnitPropulsionsJson', 'UnitAbilitiesJson', 'SensorUnitsJson', 'SquadMembersJson', 'SquadWeaponsJson', 'WeaponAmmunitionsJson'):
        for r in rows(tab, UnitId=TH): g.add(tab, r, {'UnitId': mp})
        ok(len(rows(tab, UnitId=mp)) == len(rows(tab, UnitId=TH)), ('Marines PF-98', tab, 'copied'))
    (mc,) = rows('SpecializationAvailabilitiesJson', UnitId=MARINES); ok(mc['SpecializationId'] == PLAN, 'Marines card in PLAN')
    nc = g.add('SpecializationAvailabilitiesJson', SA[TH_CARD], {'UnitId': mp, 'SpecializationId': PLAN})
    for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=mc['Id']): g.add('TransportAvailabilitiesJson', r, {'SpecializationAvailabilityId': nc})
    # Tank Hunters: PF-98 -> PF-98A
    (man,) = [m for m in rows('SquadMembersJson', UnitId=TH) if m.get('SpecialWeaponId') == PF98]
    (sw,) = rows('SquadWeaponsJson', UnitId=TH, WeaponId=PF98)
    wa = rows('WeaponAmmunitionsJson', UnitId=TH, WeaponId=PF98)
    ok(sorted(r['AmmunitionId'] for r in wa) == [PF98_A, DZT98], 'Tank Hunters PF-98: HEAT + DZT-98 rounds')
    g.put('SquadMembersJson', man['Id'], {'SpecialWeaponId': lw})
    g.put('SquadWeaponsJson', sw['Id'], {'WeaponId': lw})
    for r in wa: g.put('WeaponAmmunitionsJson', r['Id'], {'WeaponId': lw, **({'AmmunitionId': la} if r['AmmunitionId'] == PF98_A else {})})
    # checks after
    for u in (TH, mp):
        carried = {x for m in rows('SquadMembersJson', UnitId=u) for x in (m['PrimaryWeaponId'], m.get('SpecialWeaponId')) if x}
        ok({r['WeaponId'] for r in rows('SquadWeaponsJson', UnitId=u)} == carried == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=u)}, (U[u]['HUDName'], 'card + ammo = carried'))
    pf = [i for i, w in W.items() if w and w.get('HUDName', '').startswith('PF-98')]
    ok(sorted(W[i]['HUDName'] for i in pf) == ['PF-98', 'PF-98 (tripod)', 'PF-98A'], ('PF-98 rows left', [(i, W[i]['HUDName']) for i in pf]))
    ok(users(lw) == ['Sky Wolf Commandos 天狼突击队', 'Tank Hunters 坦克杀手'], ('PF-98A users', users(lw)))
    tr = [U[r['UnitId']]['HUDName'] for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=nc)]
    ok(SA[nc]['SpecializationId'] == PLAN and sorted(tr) == sorted(['ZBD-05', 'Z-20J', 'CTL-181', 'ZSD-05', 'ZBL-08']) and SA[TH_CARD]['SpecializationId'] == PLAAF, ('Marines PF-98 PLAN transports', tr))
    rnd = lambda u, w: [(A[r['AmmunitionId']]['HUDName'], r['Quantity'], 2 * A[r['AmmunitionId']]['GroundRange']) for r in rows('WeaponAmmunitionsJson', UnitId=u, WeaponId=w)]
    rec['pla_light_brigade_pf98a_1126'] = {'pf98a': lw, 'round': la, 'merged_into_pf98': {str(w): before[w] for w in OLD}, 'pf98_users': users(PF98),
                                           'marines_pf98': mp, 'marines_pf98_card': nc, 'marines_pf98_rounds': rnd(mp, PF98), 'transports': tr,
                                           'tank_hunters_rounds': rnd(TH, lw), 'pf98a_users': users(lw)}
    print('PLA LIGHT BRIGADE PF-98A', rec['pla_light_brigade_pf98a_1126'])

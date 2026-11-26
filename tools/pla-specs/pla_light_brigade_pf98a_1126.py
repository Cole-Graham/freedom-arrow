"""PLA Light Brigade build, PF-98A and Tank Hunters to PLAN (Osama 26 Nov 2026 12:5x PST, thread 1567745029781454889: "My plan is to give tank
hunters the new PF-98A. The new PF-98A should be 700m." / "And the current tank hunters are rolled into the PLAN"). Branch
codex/batch/osama/pla-light-brigade only; the last plb section (after the smoke section), so no earlier row id moves.
- PF-98A = the long-range PF-98 of the Sky Wolf Commandos (pla_light_brigade_skywolf_1126: Osama 03:48 "the PF-98A, PF-98 clone copy but 800m range"),
  one weapon for both squads: card name 'PF-98' -> 'PF-98A', round 'PF-98 ammunition' -> 'PF-98A ammunition', GroundRange 400 -> 350 (card 800 ->
  700 m). Its internal Name stays 'PLA infantry PF-98 long range' (plb_infantry_rules.py finds its PF-98 model by that name). All other stats are the
  PF-98's. The Sky Wolf Commandos' launcher is therefore 700 m too.
- Tank Hunters 坦克杀手 (1139): the leader's PF-98 (2011919, shared with PF-98 Fire Support, which keeps it) -> the PF-98A; its 2 rounds move with it:
  6 PF-98A HEAT (700 m) and the 6 DZT-98 thermobaric (2016058, its own range unchanged). Men, price, cards unchanged.
- The card (2011937, 4 cards) PLAAF -> PLAN, and by Osama's standing rule the transports follow the spec: the PLAAF set (Z-20KA, Z-9, ZBD-251, VN-3,
  Lynx Troop Carrier) -> the Marines' PLAN set (ZBD-05, Z-20J, CTL-181, ZSD-05, ZBL-08), as the Weapons Squad got. Not yet tested in a game."""
TH, TH_CARD, PF98_MIXED, PF98_A, DZT98, PLAAF, PLAN, MARINES = 1139, 2011937, 2011919, 2011920, 2016058, 17, 20, 1192


def apply(t, g, ok, rec):
    U, W, A, SA = t['Units'], t['WeaponsJson'], t['AmmunitionsJson'], t['SpecializationAvailabilitiesJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    (lw,) = [i for i, w in W.items() if w and w.get('Name') == 'PLA infantry PF-98 long range']
    (lwa,) = rows('WeaponAmmunitionsJson', WeaponId=lw); la = lwa['AmmunitionId']
    ok(W[lw]['HUDName'] == 'PF-98' and A[la]['GroundRange'] == 400.0 and A[la]['HUDName'] == 'PF-98 ammunition' and not any(w and w.get('HUDName') == 'PF-98A' for w in W.values()),
       'long-range PF-98 (800 m), PF-98A name free')
    g.put('WeaponsJson', lw, {'HUDName': 'PF-98A'})
    g.put('AmmunitionsJson', la, {'HUDName': 'PF-98A ammunition', 'GroundRange': 350.0})
    # Tank Hunters
    ok(U[TH]['HUDName'] == 'Tank Hunters 坦克杀手' and SA[TH_CARD]['UnitId'] == TH and SA[TH_CARD]['SpecializationId'] == PLAAF and len(rows('SpecializationAvailabilitiesJson', UnitId=TH)) == 1,
       'Tank Hunters: one PLAAF card row')
    (man,) = [m for m in rows('SquadMembersJson', UnitId=TH) if m.get('SpecialWeaponId') == PF98_MIXED]
    (sw,) = rows('SquadWeaponsJson', UnitId=TH, WeaponId=PF98_MIXED)
    wa = rows('WeaponAmmunitionsJson', UnitId=TH, WeaponId=PF98_MIXED)
    ok(sorted(r['AmmunitionId'] for r in wa) == [PF98_A, DZT98] and A[DZT98]['HUDName'].startswith('DZT-98'), 'Tank Hunters PF-98: HEAT + DZT-98 rounds')
    g.put('SquadMembersJson', man['Id'], {'SpecialWeaponId': lw})
    g.put('SquadWeaponsJson', sw['Id'], {'WeaponId': lw})
    for r in wa: g.put('WeaponAmmunitionsJson', r['Id'], {'WeaponId': lw, **({'AmmunitionId': la} if r['AmmunitionId'] == PF98_A else {})})
    # card to PLAN, transports follow
    (mc,) = rows('SpecializationAvailabilitiesJson', UnitId=MARINES); ok(mc['SpecializationId'] == PLAN, 'Marines card in PLAN')
    g.put('SpecializationAvailabilitiesJson', TH_CARD, {'SpecializationId': PLAN})
    for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=TH_CARD): g.remove('TransportAvailabilitiesJson', r['Id'])
    for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=mc['Id']): g.add('TransportAvailabilitiesJson', r, {'SpecializationAvailabilityId': TH_CARD})
    # checks after
    men = rows('SquadMembersJson', UnitId=TH)
    carried = {x for m in men for x in (m['PrimaryWeaponId'], m.get('SpecialWeaponId')) if x}
    ok({r['WeaponId'] for r in rows('SquadWeaponsJson', UnitId=TH)} == carried == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=TH)} and lw in carried and PF98_MIXED not in carried,
       'Tank Hunters: card + ammo = carried, PF-98A')
    ok(rows('SquadWeaponsJson', WeaponId=PF98_MIXED), 'PF-98 Fire Support keeps the PF-98')
    sky = sorted({U[r['UnitId']]['HUDName'] for r in rows('SquadWeaponsJson', WeaponId=lw)})
    ok(sky == ['Sky Wolf Commandos 天狼突击队', 'Tank Hunters 坦克杀手'], ('PF-98A users', sky))
    tr = [U[r['UnitId']]['HUDName'] for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=TH_CARD)]
    ok(SA[TH_CARD]['SpecializationId'] == PLAN and sorted(tr) == sorted(['ZBD-05', 'Z-20J', 'CTL-181', 'ZSD-05', 'ZBL-08']), ('Tank Hunters PLAN transports', tr))
    rec['pla_light_brigade_pf98a_1126'] = {'pf98a': lw, 'round': la, 'card_range_m': 700, 'users': sky, 'tank_hunters_rounds': [(A[r['AmmunitionId']]['HUDName'], r['Quantity'], 2 * A[r['AmmunitionId']]['GroundRange'])
                                           for r in rows('WeaponAmmunitionsJson', UnitId=TH, WeaponId=lw)], 'cards': SA[TH_CARD]['MaxAvailabilityXp0'], 'transports': tr}
    print('PLA LIGHT BRIGADE PF-98A', rec['pla_light_brigade_pf98a_1126'])

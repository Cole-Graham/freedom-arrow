"""PLA Light Brigade build, Tiger Brigade (Marines Assault), PTL-02 and Light CAB transports (Osama 26 Nov 2026 02:3x-02:4x PST, thread
1567745029781454889). Branch codex/batch/osama/pla-light-brigade only; inside g.scope('plb'), after the Light CAB spec and the MG section.
- 02:3x "New Marines Assault. QLZ-04 is renamed the QLZ-87, QBZ-191 basic, PKP-M is the QJY-201 ..." / "8 man 75 pts", then "Actually let's make the
  loadout like this" (DPM visualizer custom unit from Marines 1192: 8 men, 40 HP, Armor Infantry Shock (8); 1 QLZ-04, 4 QBZ-192, 2 PKP-M, 1 PF-98,
  1 QBU-201) and "80 points". New unit 'Tiger Brigade' = copy of Marines 陆战队 (1192: armour 'Armor Infantry Shock 8Men' 291, card row in PLAN with
  6 cards and its 5 transports), 80 pts. Kit: the QLZ-87 (2012157, the QLZ-04's stat copy) in place of the QLZ-04; the QJY-201 (2012411, PKP-M stats
  in this build) in place of the PKP-M. The PF-98 is the leader's special weapon (8 men carry 9 weapons). Death priority: leader 1, QJY-201 and QLZ-87
  men 2, others 3. Ammo per carrier as their China rows: QLZ-87 190, QBZ-192 160, QJY-201 400, PF-98 6, QBU-201 60.
- Name (02:4x "猛虎旅 we just call them Tiger Brigade actually"; 02:4x "No, the Marines assault is called Tiger Brigade, the PLAN spec is still the
  same"): card name 'Tiger Brigade' (Name 'PLA Tiger Brigade'). The PLAN spec name does not change.
- 02:4x "PTL-02 goes to loght CAB": card row 2008907 (6 cards) Medium CAB (21) -> Light CAB.
- 02:4x "CTL-181 NLOS, QN-506, ZRZ-100 should be moved to Light CAB": their one card row each, PLAN (20) -> Light CAB, same counts
  (CTL-181 NLOS 1054: 2, QN-506 937: 4, ZRZ-100 1410: 6).
- 02:4x "Light CAB gets CSK-131 and CSK-181 transports": CSK-131 (1266 'PLA CSK-181 4x4', card name CSK-131) and the CSK-181 transport (1230
  'PLA CSK-181 Transport', card name CTL-181 since the 25 Nov QQ fix) on every Light CAB infantry card that rides a ground vehicle, where missing."""
MARINES, SHOCK8, PLAN, MEDIUM = 1192, 291, 20, 21
QLZ87, QLZ87_A, QBZ192, QBZ192_A, QJY201, QJY201_A, PF98, PF98_A, QBU, QBU_A = 2012157, 2012158, 2013087, 2013088, 2012411, 2012412, 2011832, 2011833, 2020834, 2020835
PTL02, PTL02_ROW, CSK131, CSK181 = 1059, 2008907, 1266, 1230
PLAN_MOVES = [(2015785, 1054, 'CTL-181 NLOS', 2), (2014509, 937, 'QN-506', 4), (2020666, 1410, 'ZRZ-100', 6)]   # (card row, unit, HUDName, cards)
TIGER = 'Tiger Brigade'


def apply(t, g, ok, rec):
    U, W, A, SM, SA, S = (t[k] for k in ('Units', 'WeaponsJson', 'AmmunitionsJson', 'SquadMembersJson', 'SpecializationAvailabilitiesJson', 'SpecializationsJson'))
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    wn = lambda i: W[i]['HUDName'] if i else ''
    light = next(s['Id'] for s in S.values() if s and s.get('UIName', '').startswith('PLAGF Light Combined Arms Brigade'))
    # Tiger Brigade (Marines Assault)
    ok(U[MARINES]['HUDName'] == 'Marines 陆战队' and len(rows('SquadMembersJson', UnitId=MARINES)) == 8 and not rows('ModificationsJson', UnitId=MARINES), 'Marines 1192, 8 men, no loadouts')
    ok([wn(w) for w in (QLZ87, QBZ192, QJY201, PF98, QBU)] == ['QLZ-87', 'QBZ-192', 'QJY-201', 'PF-98', 'QBU-203'], 'weapons (QBU-201 shows as QBU-203)')
    ok([A[a]['HUDName'] for a in (QLZ87_A, QBZ192_A, QJY201_A, PF98_A, QBU_A)] == ['35 mm HE-fragmentation', '5.8 mm ammunition', '7.62 mm ammunition', 'PF-98 ammunition', '7.62 mm precision ammunition'], 'rounds')
    ok('pla_light_brigade_mg_1126' in rec, 'MG section first (QJY-201 = PKP-M stats)')
    ok(t['ArmorsJson'][SHOCK8]['Name'] == 'Armor Infantry Shock 8Men' and [r['ArmorId'] for r in rows('UnitArmorsJson', UnitId=MARINES)] == [SHOCK8], 'Marines: Shock 8Men armour')
    ok(not any(u and TIGER in (u.get('Name', ''), u.get('HUDName', '')) for u in U.values()), 'Tiger Brigade name free')
    ma = g.add('Units', U[MARINES], {'Name': 'PLA ' + TIGER, 'HUDName': TIGER, 'Cost': 80, 'OriginalCost': 0, 'Description': None, 'OriginalName': None,
                                    # 26 Nov 10:5x 'tiger brigade is SF': SF role, SF death timer (0, Marines -240) and SF sound preset, as Falcons
                                    'Role': 36, 'TimeModifierResurrect': 0.0, 'AudioPreset': 'UNIT_SOUND_PRESET_RU_SF_SSO'})
    for tab in ('UnitArmorsJson', 'UnitPropulsionsJson', 'UnitAbilitiesJson', 'SensorUnitsJson'):
        for r in rows(tab, UnitId=MARINES): g.add(tab, r, {'UnitId': ma})
        ok(len(rows(tab, UnitId=ma)) == len(rows(tab, UnitId=MARINES)), (TIGER, tab, 'copied'))
    man = rows('SquadMembersJson', UnitId=MARINES)[0]
    kit = [(QBZ192, PF98, 1), (QJY201, 0, 2), (QJY201, 0, 2), (QLZ87, 0, 2), (QBU, 0, 3), (QBZ192, 0, 3), (QBZ192, 0, 3), (QBZ192, 0, 3)]
    agl_body = rows('SquadMembersJson', PrimaryWeaponId=QLZ87)[0]['ModelFileName']
    for p, s, dp in kit:
        g.add('SquadMembersJson', man, {'UnitId': ma, 'PrimaryWeaponId': p, 'SpecialWeaponId': s, 'DeathPriority': dp,
                                        'ModelFileName': agl_body if p == QLZ87 else man['ModelFileName']})
    sw0, wa0 = rows('SquadWeaponsJson', UnitId=MARINES)[0], rows('WeaponAmmunitionsJson', UnitId=MARINES)[0]
    for n, (w, a, q) in enumerate([(QBZ192, QBZ192_A, 160), (QJY201, QJY201_A, 400), (QLZ87, QLZ87_A, 190), (QBU, QBU_A, 60), (PF98, PF98_A, 6)], 1):
        g.add('SquadWeaponsJson', sw0, {'UnitId': ma, 'WeaponId': w, 'Order': n})
        g.add('WeaponAmmunitionsJson', wa0, {'UnitId': ma, 'WeaponId': w, 'AmmunitionId': a, 'Quantity': q})
    mc = rows('SpecializationAvailabilitiesJson', UnitId=MARINES); ok(len(mc) == 1 and mc[0]['SpecializationId'] == PLAN, 'Marines: one PLAN card row')
    nc = g.add('SpecializationAvailabilitiesJson', mc[0], {'UnitId': ma})
    for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=mc[0]['Id']): g.add('TransportAvailabilitiesJson', r, {'SpecializationAvailabilityId': nc})
    # PTL-02
    ok(U[PTL02]['HUDName'] == 'PTL-02' and SA[PTL02_ROW]['UnitId'] == PTL02 and SA[PTL02_ROW]['SpecializationId'] == MEDIUM and len(rows('SpecializationAvailabilitiesJson', UnitId=PTL02)) == 1,
       'PTL-02: one card row, Medium CAB')
    g.put('SpecializationAvailabilitiesJson', PTL02_ROW, {'SpecializationId': light})
    for row, unit, hud, n in PLAN_MOVES:
        ok(U[unit]['HUDName'] == hud and SA[row]['UnitId'] == unit and SA[row]['SpecializationId'] == PLAN and SA[row]['MaxAvailabilityXp0'] == n
           and len(rows('SpecializationAvailabilitiesJson', UnitId=unit)) == 1, (hud, 'one PLAN card row'))
        g.put('SpecializationAvailabilitiesJson', row, {'SpecializationId': light})
    # CSK-131 + CSK-181 transports
    ok(U[CSK131]['HUDName'] == 'CSK-131' and U[CSK181]['Name'] == 'PLA CSK-181 Transport' and U[CSK181]['HUDName'] == 'CTL-181', 'CSK-131 (1266), CSK-181 transport (1230)')
    ground = lambda uid: U[uid].get('Type') == 4
    added = []
    for c in rows('SpecializationAvailabilitiesJson', SpecializationId=light):
        if U[c['UnitId']].get('CategoryType', 0) != 1: continue
        tr = [r for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=c['Id']) if ground(r['UnitId'])]
        for v in (CSK131, CSK181):
            if tr and not any(r['UnitId'] == v for r in tr):
                g.add('TransportAvailabilitiesJson', tr[0], {'UnitId': v}); added.append((U[c['UnitId']]['HUDName'], U[v]['HUDName']))
    # checks after
    men = rows('SquadMembersJson', UnitId=ma)
    carried = {w for r in men for w in (r['PrimaryWeaponId'], r['SpecialWeaponId']) if w}
    ok({r['WeaponId'] for r in rows('SquadWeaponsJson', UnitId=ma)} == carried == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=ma)}, 'card + ammo = carried')
    got = sorted((wn(r['PrimaryWeaponId']), wn(r['SpecialWeaponId']), r['DeathPriority']) for r in men)
    ok(len(men) == 8 and U[ma]['Cost'] == 80 and sum(r['PrimaryWeaponId'] == QBZ192 for r in men) == 4 and sum(r['PrimaryWeaponId'] == QJY201 for r in men) == 2, ('Tiger Brigade kit', got))
    lc = {r['UnitId'] for r in rows('SpecializationAvailabilitiesJson', SpecializationId=light)}
    ok(PTL02 in lc and all(u in lc for r, u, h, n in PLAN_MOVES) and S[PLAN]['UIName'].startswith('PLAN Naval/Special Forces') and added, ('PTL-02, PLAN name unchanged, CSK transports', added))
    rec['pla_light_brigade_tiger_1126'] = {'tiger_brigade': ma, 'kit': got, 'cost': 80, 'cards': mc[0]['MaxAvailabilityXp0'],
                                           'transports': [U[r['UnitId']]['HUDName'] for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=nc)],
                                           'ptl02': 'Light CAB', 'plan_to_light': [h for r, u, h, n in PLAN_MOVES], 'csk_added': added}
    print('PLA LIGHT BRIGADE TIGER', rec['pla_light_brigade_tiger_1126'])

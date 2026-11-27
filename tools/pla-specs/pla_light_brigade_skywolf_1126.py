"""PLA Light Brigade build, Sky Wolf Commandos, PF-98 names and J-11s (Osama 26 Nov 2026 03:4x PST, thread 1567745029781454889). Branch
codex/batch/osama/pla-light-brigade only; inside g.scope('plb'), after the PAP section.
- 03:48 "Test SF goes down to 6 people, 6x VQX181 (the HK416 D10 clone), and 4 shots for the PF-98A, PF-98 clone copy but 800m range. (by the way call
  all the PF-98's just the PF-98, we have some A's lingering around). and then 4 shots for the QW-12, 3 availability. Call them "Sky Wolf Commandos"
  (天狼突击队) and use the blood wolf icon 75 points". Test SF (6001, Light CAB):
  - card name 'Sky Wolf Commandos 天狼突击队' (Osama gave the Chinese name), 55 -> 75 pts, card icon FA_PLA_INF_BLOOD_WOLF, 3 cards (unchanged).
  - 8 -> 6 men, all with the VQX191 (2021547, the back-pocket exact copy of the HK 416 D10RS; Osama's "VQX181"), 160 rounds each (the D10RS's). The
    leader carries the new long-range PF-98 (4 rounds), one man the QW-12 (4 missiles). Armour 'PLA Jiaolong (8, 40 HP)' -> 'Armor Infantry Shock
    6Men' (289: 8, 30 HP), same armour value.
  - New long-range PF-98: exact copy of the infantry PF-98 (2011832) and its round (2011833) with GroundRange 300 -> 400 (card 600 -> 800).
- "call all the PF-98's just the PF-98": the two 'PF-98A' weapons (2011919, 2013157) -> 'PF-98'; the 'PF-98A ammunition' rounds (2011920, 2013158) ->
  'PF-98 ammunition'. Stats unchanged. ('PF-98 (tripod)' and 'PF-98 (prototype)' keep their names.)
- 03:4x "J-11 both moved to Light CAB" / "J-11BHG and J-11BS": card rows 2008206 (J-11BS, 2 cards) and 2016100 (J-11BHG, 2 cards) PLAAF -> Light CAB."""
TSF, PF98, PF98_A, QW12, QW12_A, SHOCK6, BLOOD_WOLF_ICON = 6001, 2011832, 2011833, 2016056, 2016057, 289, 'FA_PLA_INF_BLOOD_WOLF'
PF98A = [(2011919, 2011920), (2013157, 2013158)]
J11 = [(2008206, 923, 'J-11BS'), (2016100, 1241, 'J-11BHG')]
PLAAF = 17


def apply(t, g, ok, rec):
    U, W, A, AR, SA, S = (t[k] for k in ('Units', 'WeaponsJson', 'AmmunitionsJson', 'ArmorsJson', 'SpecializationAvailabilitiesJson', 'SpecializationsJson'))
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    wn = lambda i: W[i]['HUDName'] if i else ''
    light = next(s['Id'] for s in S.values() if s and s.get('UIName', '').startswith('PLAGF Light Combined Arms Brigade'))
    vq = rec['backpocket_weapons_1125']['VQX191']; VQX, VQX_A = vq['weapon'], vq['ammo']
    ok(wn(VQX) == 'VQX191' and all(W[VQX].get(k) == W[210][k] for k in W[210] if k not in ('Id', 'Name', 'HUDName', 'HUDIcon')), 'VQX191 = HK 416 D10RS copy')
    ok(wn(PF98) == 'PF-98' and A[PF98_A]['GroundRange'] == 300.0 and wn(QW12) == 'QW-12' and AR[SHOCK6]['Name'] == 'Armor Infantry Shock 6Men' and AR[SHOCK6]['ArmorValue'] == 8, 'PF-98, QW-12, Shock 6Men')
    # long-range PF-98
    lw = g.add('WeaponsJson', W[PF98], {'Name': 'PLA infantry PF-98 long range'})
    la = g.add('AmmunitionsJson', A[PF98_A], {'Name': 'PLA infantry PF-98 long range', 'GroundRange': 400.0})
    # Sky Wolf Commandos
    men = rows('SquadMembersJson', UnitId=TSF)
    ok(U[TSF]['HUDName'] == 'Test SF' and len(men) == 8 and [r['ArmorId'] for r in rows('UnitArmorsJson', UnitId=TSF)] == [2013404], 'Test SF: 8 men, Jiaolong armour')
    ok(not any(u and u.get('HUDName', '').startswith('Sky Wolf') for u in U.values()), 'name free')
    lead = next(r for r in men if r['SpecialWeaponId'] == PF98); qw = next(r for r in men if r['SpecialWeaponId'] == QW12)
    rest = [r for r in men if r['Id'] not in (lead['Id'], qw['Id'])]
    keep = [lead, qw] + rest[:4]
    for r in rest[4:]: g.remove('SquadMembersJson', r['Id'])
    for r in keep:
        g.put('SquadMembersJson', r['Id'], {'PrimaryWeaponId': VQX, 'SpecialWeaponId': lw if r is lead else (QW12 if r is qw else 0),
                                            'DeathPriority': 1 if r is lead else (2 if r is qw else 3)})
    sw0, wa0 = rows('SquadWeaponsJson', UnitId=TSF)[0], rows('WeaponAmmunitionsJson', UnitId=TSF)[0]
    for tab in ('SquadWeaponsJson', 'WeaponAmmunitionsJson'):
        for r in rows(tab, UnitId=TSF): g.remove(tab, r['Id'])
    for n, (w, a, q) in enumerate([(VQX, VQX_A, 160), (lw, la, 4), (QW12, QW12_A, 4)], 1):
        g.add('SquadWeaponsJson', sw0, {'UnitId': TSF, 'WeaponId': w, 'Order': n})
        g.add('WeaponAmmunitionsJson', wa0, {'UnitId': TSF, 'WeaponId': w, 'AmmunitionId': a, 'Quantity': q, 'Order': 0})
    (ua,) = rows('UnitArmorsJson', UnitId=TSF); g.put('UnitArmorsJson', ua['Id'], {'ArmorId': SHOCK6})
    g.put('Units', TSF, {'Name': 'PLA Sky Wolf Commandos', 'HUDName': 'Sky Wolf Commandos 天狼突击队', 'Cost': 75, 'ThumbnailFileName': BLOOD_WOLF_ICON})
    (card,) = rows('SpecializationAvailabilitiesJson', UnitId=TSF); ok(card['MaxAvailabilityXp0'] == 3 and card['SpecializationId'] == light, 'Light CAB, 3 cards')
    # PF-98A -> PF-98
    for w, a in PF98A:
        ok(wn(w) == 'PF-98A' and A[a]['HUDName'] == 'PF-98A ammunition', ('PF-98A rows', w, a))
        g.put('WeaponsJson', w, {'HUDName': 'PF-98'}); g.put('AmmunitionsJson', a, {'HUDName': 'PF-98 ammunition'})
    ok(not [w for w in W.values() if w and w.get('HUDName') == 'PF-98A'] and not [a for a in A.values() if a and a.get('HUDName') == 'PF-98A ammunition'], 'no PF-98A names left')
    # J-11s
    for row, unit, hud in J11:
        ok(U[unit]['HUDName'] == hud and SA[row]['UnitId'] == unit and SA[row]['SpecializationId'] == PLAAF and len(rows('SpecializationAvailabilitiesJson', UnitId=unit)) == 1, (hud, 'one PLAAF card row'))
        g.put('SpecializationAvailabilitiesJson', row, {'SpecializationId': light})
    # checks after
    men = rows('SquadMembersJson', UnitId=TSF); carried = {w for r in men for w in (r['PrimaryWeaponId'], r['SpecialWeaponId']) if w}
    ok(len(men) == 6 and {r['WeaponId'] for r in rows('SquadWeaponsJson', UnitId=TSF)} == carried == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=TSF)}, 'Sky Wolf: 6 men, card + ammo = carried')
    ok(all(W[lw].get(k) == W[PF98][k] for k in W[PF98] if k not in ('Id', 'Name')) and all(A[la].get(k) == A[PF98_A][k] for k in A[PF98_A] if k not in ('Id', 'Name', 'GroundRange')), 'long-range PF-98 = PF-98 but range')
    kit = sorted((wn(r['PrimaryWeaponId']), wn(r['SpecialWeaponId']), r['DeathPriority']) for r in men)
    rec['pla_light_brigade_skywolf_1126'] = {'unit': TSF, 'kit': kit, 'pf98_long_range': (lw, la, 400.0), 'renamed_pf98a': PF98A, 'j11_to_light': [h for r, u, h in J11]}
    print('PLA LIGHT BRIGADE SKY WOLF', rec['pla_light_brigade_skywolf_1126'])

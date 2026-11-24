"""Infantry launcher batch (Lateralus 24 Nov 2026 11:3x PST, thread 1572962048705429598).
"SRAW MPV: Max range 600 -> 700m, Ignore Cover 25 -> 50%, Penetration 75 -> 300mm. Change DZJ-08, SMAW-D 84mm HEDP, and C90-CR-AM 90mm dual
purpose to 0% ignore cover. Bur 62mm thermobaric: Damage 2.5 -> 4, Ignore cover 100 -> 75%. Chinese 'Thermobaric Assault': 70 -> 60 points, 9 -> 8
men, 45 -> 40 HP, QBZ-191 x6 -> QBZ-191 x5. Chinese 'Combat Engineers': Thermobaric Rockets loadout +10 -> +0. USA 'Mech Engineers': Close
Quarters loadout +10 -> +0. USA 'Combat Engineers': Make sure this unit's death priority and weapon order makes sense. 'Shturmoviki': 40 -> 50 points"
- Rounds (each row is the weapon's only round; every user follows): SRAW MPV 140mm blast-frag 392 GroundRange 300 -> 350 world (600 -> 700 card m),
  IgnoreCover 0.25 -> 0.5, penetration 75 -> 300 (min and ground). DZJ-08 2012025, SMAW-D 84mm HEDP 128 (vanilla 0), C90-CR-AM 593: IgnoreCover -> 0.
  Bur 62mm Thermobaric 103: Damage 2.5 -> 4.0, IgnoreCover 1.0 -> 0.75 (also VDV Spetsnaz, SSO, SF Assault, SF Recon).
- Thermobaric Assault 1209: rifleman 2015623 (QBZ-191 + PF-97, priority 3) removed, so QBZ-191 6 -> 5; shotgunner 2015616 gets that PF-97
  (Lateralus 11:4x "give the 6th to a QBS-09 man"), so PF-97 stays 6, one per carrier (disposable_launchers_1123.py); armour 277 'Shock 9Men' 8/45 -> vanilla 291 'Shock 8Men' 8/40 (same row except HP); Cost 70 -> 60.
- Loadouts +10 -> +0: China Combat Engineers 1156 option 24354 (Thermobaric launcher -> 1162 Thermobaric Breachers 60 -> 50) and US Mech. Engineers
  146 option 3348 (Close quarters -> 708 Mech. Engineers CQC 55 -> 45). Swap row price = base + option (audit_swap_prices).
- US Combat Engineers 449: weapon order already the vanilla pattern (M4A1, M-25 CDTE, M590A1, M249E3, SMAW-D HIT: rifle first, AT last); unchanged.
  Death priority by the tier rule (docs/engine/infantry-casualty-and-weapon-order.md 1.4): keeper 940 (M4A1 + SMAW-D HIT) 1; shotgun and MG men 2;
  riflemen with the M-25 or a SMAW-D HIT 3. The squad has no plain riflemen, so 934 (M-25) and 941 (SMAW-D HIT) 4 -> 3 like their equals.
- Shturmoviki 401: Cost 40 -> 50 (no loadout options point at it)."""
DIFF = lambda a, b: {k for k in set(a) | set(b) if k not in ('Id', 'Name') and a.get(k) != b.get(k)}


def apply(t, g, ok, rec):
    U, A, W, WA, SM, SW, UA, AR, O, M = (t[k] for k in ('Units', 'AmmunitionsJson', 'WeaponsJson', 'WeaponAmmunitionsJson', 'SquadMembersJson',
                                                       'SquadWeaponsJson', 'UnitArmorsJson', 'ArmorsJson', 'OptionsJson', 'ModificationsJson'))
    out = {}
    def ammo(aid, name, want, new):
        a = A[aid];ok(a.get('HUDName') == name and all((a.get(k) or 0) == v for k, v in want.items()), (aid, name, {k: a.get(k) for k in want}))
        g.put('AmmunitionsJson', aid, new);out[name] = {k: [want.get(k, a.get(k)), v] for k, v in new.items()}
    ammo(392, '140mm blast-frag', {'GroundRange': 300.0, 'IgnoreCover': 0.25, 'PenetrationAtMinRange': 75.0, 'PenetrationAtGroundRange': 75.0},
         {'GroundRange': 350.0, 'IgnoreCover': 0.5, 'PenetrationAtMinRange': 300.0, 'PenetrationAtGroundRange': 300.0})
    ammo(2012025, 'DZJ-08 ammunition', {'IgnoreCover': 0.25}, {'IgnoreCover': 0.0})
    ammo(128, '84mm HEDP', {'IgnoreCover': 0.25}, {'IgnoreCover': 0.0})
    ammo(593, '90mm dual purpose', {'IgnoreCover': 0.2}, {'IgnoreCover': 0.0})
    ammo(103, '62mm Thermobaric', {'Damage': 2.5, 'IgnoreCover': 1.0}, {'Damage': 4.0, 'IgnoreCover': 0.75})
    # Thermobaric Assault 1209
    men = lambda: sorted(m['Id'] for m in SM.values() if m and m.get('UnitId') == 1209)
    cnt = lambda f, w: sum(1 for m in SM.values() if m and m.get('UnitId') == 1209 and m.get(f) == w)
    ok(U[1209]['HUDName'].strip().startswith('Thermobaric Assault') and U[1209]['Cost'] == 70 and len(men()) == 9 and cnt('PrimaryWeaponId', 2003998) == 6
       and cnt('SpecialWeaponId', 2012515) == 6 and cnt('PrimaryWeaponId', 2012131) == 3, ('1209 before', U[1209]['Cost'], men()))
    r = SM[2015623];ok(r['UnitId'] == 1209 and r['PrimaryWeaponId'] == 2003998 and r['SpecialWeaponId'] == 2012515 and r['DeathPriority'] == 3, ('2015623', r))
    g.remove('SquadMembersJson', 2015623)
    # Lateralus 24 Nov 11:4x "yes give the 6th to a QBS-09 man": PF-97 stays 6 (one per carrier); shotgunner 2015616 keeps priority 2 (tier B),
    # as the Thermobaric Breachers' HAWK man with the 5th PF-97.
    q = SM[2015616];ok(q['UnitId'] == 1209 and q['PrimaryWeaponId'] == 2012131 and not q.get('SpecialWeaponId') and q['DeathPriority'] == 2, ('2015616', q))
    g.put('SquadMembersJson', 2015616, {'SpecialWeaponId': 2012515})
    ok(len(men()) == 8 and cnt('PrimaryWeaponId', 2003998) == 5 and cnt('SpecialWeaponId', 2012515) == 6, '1209: 8 men, QBZ-191 x5, PF-97 x6')
    ua = [x for x in UA.values() if x and x['UnitId'] == 1209];ok(len(ua) == 1 and ua[0]['ArmorId'] == 277, ('1209 armour row', ua))
    ok(DIFF(AR[277], AR[291]) == {'MaxHealthPoints'} and (AR[291]['ArmorValue'], AR[291]['MaxHealthPoints']) == (8, 40), 'row 291 = 277 with 40 HP')
    g.put('UnitArmorsJson', ua[0]['Id'], {'ArmorId': 291});g.put('Units', 1209, {'Cost': 60})
    # loadouts +10 -> +0 and their swap rows
    for opt, base, swap, name in ((24354, 1156, 1162, 'Thermobaric Breachers'), (3348, 146, 708, 'Mech. Engineers CQC')):
        o = O[opt];ok(o['Cost'] == 10 and o['ReplaceUnitId'] == swap and M[o['ModificationId']]['UnitId'] == base and U[swap]['Cost'] == U[base]['Cost'] + 10
                     and U[swap]['HUDName'].strip().startswith(name), (opt, o['Cost'], U[swap]['Cost'], U[base]['Cost']))
        g.put('OptionsJson', opt, {'Cost': 0});g.put('Units', swap, {'Cost': U[base]['Cost']})
    # US Combat Engineers 449
    order = [W[r['WeaponId']]['HUDName'] for r in sorted((r for r in SW.values() if r and r['UnitId'] == 449), key=lambda r: r['Order'])]
    ok(order == ['M4A1', 'M-25 CDTE', 'M590A1', 'M249E3', 'SMAW-D HIT'], ('449 weapon order', order))
    pr = {m['Id']: m['DeathPriority'] for m in SM.values() if m and m['UnitId'] == 449}
    ok(pr == {933: 3, 934: 4, 935: 2, 936: 2, 937: 2, 938: 2, 939: 3, 940: 1, 941: 4}, ('449 death priority', pr))
    for mid in (934, 941):g.put('SquadMembersJson', mid, {'DeathPriority': 3})
    # Shturmoviki
    ok(U[401]['HUDName'].strip() == 'Shturmoviki' and U[401]['Cost'] == 40 and not [o for o in O.values() if o and o.get('ReplaceUnitId') == 401], 'Shturmoviki 40')
    g.put('Units', 401, {'Cost': 50})
    rec['infantry_launchers_1124'] = {'rounds': out, 'thermobaric_assault': {'cost': [70, 60], 'men': [9, 8], 'hp': [45, 40], 'qbz191': [6, 5], 'pf97': [6, 6], 'pf97_to_qbs09': 2015616},
        'loadouts': {'China Combat Engineers Thermobaric launcher': [10, 0], 'Mech. Engineers Close quarters': [10, 0]},
        'us_combat_engineers_priority': {934: [4, 3], 941: [4, 3]}, 'shturmoviki': [40, 50]}
    print('INFANTRY LAUNCHERS', rec['infantry_launchers_1124'])

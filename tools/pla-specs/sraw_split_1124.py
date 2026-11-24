"""Assaultmen SRAW A / B (Lateralus 24 Nov 2026, thread 1572962048705429598).
12:5x "split off the SRAW loadout to its own unit (and remove the loadout from Assaultmen SMAW), and give it a second anti-tank loadout option,
the units would be named: Assaultmen SRAW A / Assaultmen SRAW B. The A would have the anti-tank loadout, with 700m range and ammunition called
'140mm HEAT' and the weapon would just be called 'SRAW'. It should top attack with 11 damage and 140mm penetration. The B would keep using the SRAW
MPV. Both loadouts would be the same cost (65 points). The unit icon for both loadouts should be the SRAW MPV weapon icon"; 13:2x "yes 4 cards and
remove the slot so the card shows no loadout picker. Queue it up" (preview work/sraw-split-20261124/sraw-proposal.png).
- New card unit 'Assaultmen SRAW A' = a copy of Assaultmen SRAW 332 (8 Marines, M16A4 + one disposable each; same ability, sensor, armour and
  mobility rows), not a loadout-only row. Its SRAW is a new weapon 'SRAW' (copy of SRAW MPV 534) firing a new round '140mm HEAT' (copy of the
  140mm blast-frag 392 for model, sound and flight): damage 11, penetration 140, TopArmorAttack (always the roof: 1.2.2.1
  BattleSystemHelpers.DoesAmmunitionUseTopArmorAttack returns true for the flag, otherwise only LoftAngle >= 30 rounds beyond a range share),
  range 350 world = 700 card m, vehicles only and the AT stress/blast of the SMAW 84mm anti-tank round 2000130 (TargetType 45, no ignore cover).
- 'Assaultmen SRAW B' = 332 renamed; keeps the SRAW MPV (values as queued in infantry_launchers_1124.py).
- Card A: USMC (spec 3) with 4 cards and the Assaultmen SMAW card's transports (ACV, AAVP-7A1); a squad loadout slot (copy of slot 399):
  'SRAW' -> A (+0) and 'SRAW MPV' -> B (+0). Both units 65 pts; both use the vanilla SRAW unit icon US_MARINE_SRAW-Label (the SRAW MPV silhouette).
- Assaultmen SMAW 63: its loadout slot 399 (SMAW 1472 / SRAW 1473) is removed, so the card has no loadout picker."""
SMAW, SRAW, SLOT, MPV_W, MPV_A, AT_A = 63, 332, 399, 534, 392, 2000130
A_NAME, B_NAME, ICON = 'Assaultmen SRAW A', 'Assaultmen SRAW B', 'US_MARINE_SRAW-Label'


def apply(t, g, ok, rec):
    U, W, A, O, M, SA, TA, SM, SW, WA = (t[k] for k in ('Units', 'WeaponsJson', 'AmmunitionsJson', 'OptionsJson', 'ModificationsJson',
        'SpecializationAvailabilitiesJson', 'TransportAvailabilitiesJson', 'SquadMembersJson', 'SquadWeaponsJson', 'WeaponAmmunitionsJson'))
    rows = lambda tab, **kw: sorted((r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())), key=lambda r: r['Id'])
    # before
    ok(U[SMAW]['HUDName'] == 'Assaultmen SMAW' and U[SRAW]['HUDName'] == 'Assaultmen SRAW' and U[SRAW]['IsUnitModification'] and U[SRAW]['Cost'] == 65
       and U[SMAW]['Cost'] == 65 and U[SRAW]['ThumbnailFileName'] == ICON, 'Assaultmen SMAW 63 card, Assaultmen SRAW 332 loadout row, both 65')
    ok([(o['Id'], o['ReplaceUnitId']) for o in rows('OptionsJson', ModificationId=SLOT)] == [(1472, SMAW), (1473, SRAW)] and M[SLOT]['UnitId'] == SMAW
       and M[SLOT]['UIName'] == 'Custom_Slot_Squad_loadout', 'SMAW slot 399: SMAW 1472 / SRAW 1473')
    ok(not [o for o in O.values() if o and o.get('ReplaceUnitId') == SRAW and o['Id'] != 1473], '332 reached only by option 1473')
    ok(W[MPV_W]['HUDName'] == 'SRAW MPV' and A[MPV_A]['HUDName'] == '140mm blast-frag' and A[AT_A]['HUDName'] == '84mm anti-tank', 'SRAW MPV / AT rows')
    ok([(r['WeaponId'], r['AmmunitionId'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=SRAW) if r['WeaponId'] == MPV_W] == [(MPV_W, MPV_A, 1)],
       '332 SRAW MPV row: 1 round per carrier')
    sa = rows('SpecializationAvailabilitiesJson', UnitId=SMAW);ok(len(sa) == 1 and sa[0]['SpecializationId'] == 3 and sa[0]['MaxAvailabilityXp0'] == 4, 'SMAW card: USMC, 4')
    ta = rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=sa[0]['Id'])
    # 1. round and weapon
    at = A[AT_A]
    na = g.add('AmmunitionsJson', A[MPV_A], {'Name': 'InfRocket 140 SRAW HEAT', 'HUDName': '140mm HEAT', 'Damage': 11.0, 'PenetrationAtMinRange': 140.0,
        'PenetrationAtGroundRange': 140.0, 'TopArmorAttack': True, 'GroundRange': 350.0, 'IgnoreCover': 0.0,
        **{k: at.get(k) for k in ('TargetType', 'StressDamage', 'HealthAOERadius', 'StressAOERadius', 'OverpressureRadius')}})
    nw = g.add('WeaponsJson', W[MPV_W], {'Name': 'RocketLauncher 140 SRAW HEAT Disposable', 'HUDName': 'SRAW'})
    # 2. unit A: a card copy of 332
    d = dict(U[SRAW]);d.pop('Id');d.update(Name=A_NAME, HUDName=A_NAME, IsUnitModification=U[SMAW]['IsUnitModification'])
    ua = g.put('Units', max(U) + 1, d)
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitArmorsJson', 'UnitPropulsionsJson'):
        for r in rows(tab, UnitId=SRAW):g.add(tab, r, {'UnitId': ua})
    for r in rows('SquadMembersJson', UnitId=SRAW):g.add('SquadMembersJson', r, {'UnitId': ua, **({'SpecialWeaponId': nw} if r.get('SpecialWeaponId') == MPV_W else {})})
    for r in rows('SquadWeaponsJson', UnitId=SRAW):g.add('SquadWeaponsJson', r, {'UnitId': ua, **({'WeaponId': nw} if r['WeaponId'] == MPV_W else {})})
    for r in rows('WeaponAmmunitionsJson', UnitId=SRAW):
        g.add('WeaponAmmunitionsJson', r, {'UnitId': ua, **({'WeaponId': nw, 'AmmunitionId': na} if r['WeaponId'] == MPV_W else {})})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitArmorsJson', 'UnitPropulsionsJson', 'SquadMembersJson', 'SquadWeaponsJson', 'WeaponAmmunitionsJson'):
        ok(len(rows(tab, UnitId=ua)) == len(rows(tab, UnitId=SRAW)), (A_NAME, tab, 'copied'))
    ok(sum(1 for m in rows('SquadMembersJson', UnitId=ua) if m.get('SpecialWeaponId') == nw) == 8 and not any(m.get('SpecialWeaponId') == MPV_W for m in rows('SquadMembersJson', UnitId=ua)),
       'A: 8 SRAW carriers, no SRAW MPV')
    # 3. B = 332 renamed
    g.put('Units', SRAW, {'Name': B_NAME, 'HUDName': B_NAME})
    # 4. card A in USMC with the SMAW card's transports, and its loadout slot
    nsa = g.add('SpecializationAvailabilitiesJson', sa[0], {'UnitId': ua})
    for r in ta:g.add('TransportAvailabilitiesJson', r, {'SpecializationAvailabilityId': nsa})
    nm = g.add('ModificationsJson', M[SLOT], {'UnitId': ua, 'Name': 'Assaultmen SRAW'})
    oa = g.add('OptionsJson', O[1473], {'ModificationId': nm, 'Order': 0, 'Name': 'Squad ' + A_NAME, 'UIName': 'SRAW', 'ReplaceUnitName': A_NAME, 'ReplaceUnitId': ua,
        'OptionPicture': 'INF_SRAW', 'ThumbnailOverride': ICON, 'Cost': 0})
    ob = g.add('OptionsJson', O[1473], {'ModificationId': nm, 'Order': 1, 'Name': 'Squad ' + B_NAME, 'UIName': 'SRAW MPV', 'ReplaceUnitName': B_NAME, 'ReplaceUnitId': SRAW,
        'OptionPicture': 'INF_SRAW', 'ThumbnailOverride': ICON, 'Cost': 0})
    # 5. SMAW card: no loadout slot
    for o in rows('OptionsJson', ModificationId=SLOT):g.remove('OptionsJson', o['Id'])
    g.remove('ModificationsJson', SLOT)
    ok(not rows('ModificationsJson', UnitId=SMAW) and not [o for o in O.values() if o and o.get('ReplaceUnitId') in (SMAW,) and M.get(o['ModificationId'], {}).get('UnitId') == SMAW],
       'SMAW card: no loadout slot')
    # after
    ok(U[ua]['Cost'] == U[SRAW]['Cost'] == 65 and U[ua]['ThumbnailFileName'] == U[SRAW]['ThumbnailFileName'] == ICON, 'A and B: 65 pts, SRAW unit icon')
    ok([(r['SpecializationId'], r['MaxAvailabilityXp0']) for r in rows('SpecializationAvailabilitiesJson', UnitId=ua)] == [(3, 4)], 'A: USMC, 4 cards')
    ok(sorted(r['UnitId'] for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=nsa)) == sorted(r['UnitId'] for r in ta), 'A: SMAW transports')
    ok([(o['ReplaceUnitId'], o['Cost']) for o in rows('OptionsJson', ModificationId=nm)] == [(ua, 0), (SRAW, 0)], 'A slot: A +0, B +0')
    a = A[na];ok((a['Damage'], a['PenetrationAtMinRange'], a['PenetrationAtGroundRange'], a['TopArmorAttack'], a['GroundRange'], a['TargetType']) == (11.0, 140.0, 140.0, True, 350.0, 45),
                 ('140mm HEAT', a))
    rec['sraw_split_1124'] = {'unit_a': ua, 'unit_b': SRAW, 'weapon_sraw': nw, 'round_140mm_heat': na, 'slot': nm, 'options': {'A': oa, 'B': ob},
                              'usmc_cards': 4, 'transports': [U[r['UnitId']]['HUDName'] for r in ta], 'smaw_slot_removed': [SLOT, 1472, 1473]}
    print('SRAW SPLIT', rec['sraw_split_1124'])

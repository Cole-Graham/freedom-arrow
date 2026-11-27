"""PLA Light Brigade build, J-50, PL-16, HQ-22 and Y-8 (Osama 26 Nov 2026 03:0x PST, thread 1567745029781454889). Branch
codex/batch/osama/pla-light-brigade only; inside g.scope('plb'), after the units section (HQ-22 copy, J-50 card).
- 03:02 "J-50 should be a J-20S clone but with 800 (raptor) turn radius. Except it gets 2.2 stealth. Bumped +20 points. 45% ecm. Make sure the PL-16
  has a large flare value so the J-50 can't stealth shoot. Same loadouts as the J-20S". J-50 (944) takes the J-20S (966) rows:
  - cost 255 + 20 = 275 (was 300); armour row 65 (Armor SU57, 20 HP; was 231 Armor F22, 20 HP); ability 2001399 (ECM 0.55 = 45%, laser designator;
    was 2001398, ECM 0.5 = 50%); sensor 6 (same).
  - mobility: new row = copy of the J-20S's 2019457 (900 km/h, loiter 360 s, afterburner 120 s) with the F-22 / Su-57 'turn800' flight preset 2002006.
  - Stealth 0.4545 (card 2.2 = 1 / 0.4545, the J-36's value; was 0.5 = 2.0).
  - loadouts: the J-50's own modification, 7 options, 24 turret links and 14 ammo rows go; it gets copies of the J-20S's (10 options, same names, costs
    and turrets).
- "large flare value": every PL-16 weapon (5 rows) FlashPerShot 1.0 -> 2.2 (3.5 until 26 Nov; 2.2 is the FA flash cap), the highest AAM value in the data (PL-17, PL-21, R-37, AIM-260). It changes
  every aircraft that carries the PL-16 in this build (J-20, J-20S, J-31, J-35, J-36, J-50, MD-22, FH-97A). How FlashPerShot reveals a firing plane
  is not yet read in game code: theoretical, not yet proven in a game.
- 03:0x "HQ-22 2200 (armory) range": the HQ-22 (6000) fires its own copy of the HQ-9B missile (2014535: Low/High-alt 1175, card 2350) with Low/High-alt
  1100 (card 2200). The HQ-9A keeps 1175. "and 125 points base, +70 for 4x missiles": HQ-22 145 -> 125 pts, 4x missiles option 80 -> 70.
- 03:0x "Y-8 moved to light CAB": card row 2008955 (2 cards) PLAN -> Light CAB."""
J50, J20S, ARMOR_J20S, ABIL_J20S, TURN800 = 944, 966, 65, 2001399, 2002006
HQ22, HQ9B_MISSILE, Y8, Y8_ROW, PLAN = 6000, 2014535, 1102, 2008955, 20
PL16_AMMO, FLASH = 2017953, 2.2  # was 3.5; 2.2 = the FA flash cap, as the other long-range AAMs (Lateralus 26 Nov 2026)


def apply(t, g, ok, rec):
    U, W, A, WA, SA, S, MO = (t[k] for k in ('Units', 'WeaponsJson', 'AmmunitionsJson', 'WeaponAmmunitionsJson', 'SpecializationAvailabilitiesJson', 'SpecializationsJson', 'MobilityJson'))
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    light = next(s['Id'] for s in S.values() if s and s.get('UIName', '').startswith('PLAGF Light Combined Arms Brigade'))
    # J-50 = J-20S clone
    ok(U[J50]['HUDName'] == 'J-50' and U[J20S]['HUDName'] == 'J-20S' and U[J20S]['Cost'] == 255 and U[J50]['Cost'] == 300, 'J-50 300 / J-20S 255')
    ok(t['FlyPresetsJson'][TURN800]['Name'] == 'FA F22 Su57 Su75 turn800' and t['AbilitiesJson'][ABIL_J20S]['ECMAccuracyMultiplier'] == 0.55, 'turn800 preset, J-20S ECM 0.55')
    ok([r['ArmorId'] for r in rows('UnitArmorsJson', UnitId=J20S)] == [ARMOR_J20S] and [r['AbilityId'] for r in rows('UnitAbilitiesJson', UnitId=J20S)] == [ABIL_J20S], 'J-20S armour / ability')
    ok([r['SensorId'] for r in rows('SensorUnitsJson', UnitId=J50)] == [r['SensorId'] for r in rows('SensorUnitsJson', UnitId=J20S)], 'same sensor')
    (ua,) = rows('UnitArmorsJson', UnitId=J50); g.put('UnitArmorsJson', ua['Id'], {'ArmorId': ARMOR_J20S})
    (ab,) = rows('UnitAbilitiesJson', UnitId=J50); g.put('UnitAbilitiesJson', ab['Id'], {'AbilityId': ABIL_J20S})
    (pj,) = rows('UnitPropulsionsJson', UnitId=J20S); (p50,) = rows('UnitPropulsionsJson', UnitId=J50)
    mob = g.add('MobilityJson', MO[pj['MobilityId']], {'Name': 'Plane J-50 J-20S turn800', 'FlyPresetId': TURN800})
    g.put('UnitPropulsionsJson', p50['Id'], {'MobilityId': mob})
    g.put('Units', J50, {'Cost': 275, 'Stealth': 0.4545, 'CurrentStealth': 0.4545})
    old = {'options': 0, 'turrets': len(rows('TurretUnitsJson', UnitId=J50)), 'ammo': len(rows('WeaponAmmunitionsJson', UnitId=J50))}
    for m in rows('ModificationsJson', UnitId=J50):
        for o in rows('OptionsJson', ModificationId=m['Id']): g.remove('OptionsJson', o['Id']); old['options'] += 1
        g.remove('ModificationsJson', m['Id'])
    for tab in ('TurretUnitsJson', 'WeaponAmmunitionsJson'):
        for r in rows(tab, UnitId=J50): g.remove(tab, r['Id'])
    for m in rows('ModificationsJson', UnitId=J20S):
        nm = g.add('ModificationsJson', m, {'UnitId': J50, 'Name': m['Name'].replace('J-20S', 'J-50')})
        for o in rows('OptionsJson', ModificationId=m['Id']): g.add('OptionsJson', o, {'ModificationId': nm, 'Name': o['Name'].replace('J-20S', 'J-50')})
    for tab in ('TurretUnitsJson', 'WeaponAmmunitionsJson'):
        for r in rows(tab, UnitId=J20S): g.add(tab, r, {'UnitId': J50})
    opt = lambda u: [(o['UIName'], o['Cost'], o['IsDefault'], tuple(o.get(f'Turret{i}Id') for i in range(21))) for m in rows('ModificationsJson', UnitId=u) for o in rows('OptionsJson', ModificationId=m['Id'])]
    ok(opt(J50) == opt(J20S) and len(opt(J50)) == 10, ('J-50 loadouts = J-20S', len(opt(J50)), len(opt(J20S))))
    for tab in ('TurretUnitsJson', 'WeaponAmmunitionsJson'):
        strip = lambda u: sorted(tuple(sorted((k, v) for k, v in r.items() if k not in ('Id', 'UnitId'))) for r in rows(tab, UnitId=u))
        ok(strip(J50) == strip(J20S), ('J-50 = J-20S', tab))
    m50 = MO[mob]; mj = MO[pj['MobilityId']]
    ok(all(m50[k] == mj[k] for k in mj if k not in ('Id', 'Name', 'FlyPresetId')) and m50['FlyPresetId'] == TURN800, 'mobility = J-20S + turn800')
    # PL-16 flash
    pl16 = sorted({r['WeaponId'] for r in WA.values() if r and r['AmmunitionId'] == PL16_AMMO})
    ok(len(pl16) == 5 and all(W[w]['HUDName'] == 'PL-16' and W[w]['FlashPerShot'] == 1.0 for w in pl16) and max(w.get('FlashPerShot', 0) for w in W.values() if w and w.get('Type') == 87) == FLASH,
       ('PL-16 weapons at 1.0; AAM max 2.2', pl16))
    for w in pl16: g.put('WeaponsJson', w, {'FlashPerShot': FLASH})
    carriers = sorted({U[r['UnitId']]['HUDName'] for r in WA.values() if r and r['WeaponId'] in pl16})
    # HQ-22
    ok(U[HQ22]['HUDName'] == 'HQ-22' and U[HQ22]['Cost'] == 145 and A[HQ9B_MISSILE]['LowAltRange'] == A[HQ9B_MISSILE]['HighAltRange'] == 1175.0, 'HQ-22 145, HQ-9B missile 1175')
    hw = rows('WeaponAmmunitionsJson', UnitId=HQ22); ok(len(hw) == 2 and all(r['AmmunitionId'] == HQ9B_MISSILE for r in hw), 'HQ-22 fires the HQ-9B missile (2 rows)')
    na = g.add('AmmunitionsJson', A[HQ9B_MISSILE], {'Name': 'PLA HQ-22 missile', 'LowAltRange': 1100.0, 'HighAltRange': 1100.0})
    for r in hw: g.put('WeaponAmmunitionsJson', r['Id'], {'AmmunitionId': na})
    o4 = [o for m in rows('ModificationsJson', UnitId=HQ22) for o in rows('OptionsJson', ModificationId=m['Id']) if o['UIName'] == 'Custom_Option_4xMissiles']
    ok(len(o4) == 1 and o4[0]['Cost'] == 80, 'HQ-22 4x missiles +80')
    g.put('OptionsJson', o4[0]['Id'], {'Cost': 70}); g.put('Units', HQ22, {'Cost': 125})
    ok(all(r['AmmunitionId'] == HQ9B_MISSILE for r in rows('WeaponAmmunitionsJson', UnitId=1233)) and A[HQ9B_MISSILE]['HighAltRange'] == 1175.0, 'HQ-9A unchanged')
    # Y-8
    ok(U[Y8]['HUDName'] == 'Y-8' and SA[Y8_ROW]['UnitId'] == Y8 and SA[Y8_ROW]['SpecializationId'] == PLAN and len(rows('SpecializationAvailabilitiesJson', UnitId=Y8)) == 1, 'Y-8: one PLAN card row')
    g.put('SpecializationAvailabilitiesJson', Y8_ROW, {'SpecializationId': light})
    rec['pla_light_brigade_j50_hq22_1126'] = {'j50': {'cost': 275, 'stealth_card': 2.2, 'ecm': 0.55, 'mobility': mob, 'loadouts': [o[0] for o in opt(J50)], 'removed': old},
                                              'pl16_flash': FLASH, 'pl16_carriers': carriers, 'hq22': {'ammo': na, 'range_data': 1100, 'cost': 125, 'x4': 70}, 'y8': 'Light CAB'}
    print('PLA LIGHT BRIGADE J-50 / HQ-22', rec['pla_light_brigade_j50_hq22_1126'])

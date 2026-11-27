"""PLA Light Brigade build, ZSD-05 HJ-10 for the Marines (Osama 26 Nov 2026 13:3x PST, thread 1572407822849810463 "China cosmetic work":
"Version A is perfect. We just copy the HJ-10 unit from armored and give it zsd-05 chassis and give it to marines").
Branch codex/batch/osama/pla-light-brigade only; the last plb section (after the PF-98A section), so no earlier row id moves.
- New unit 'PLA ZSD-05 HJ-10' = copy of the Heavy CAB (spec 18 'PLA PLAGF Armored Force') HJ-10 (936): its launcher turrets, rounds, the HJ-10
  FNF / NLOS loadout (same turret, weapon and ammunition rows, so the cruise and laser_hold rules apply unchanged), abilities, sensor, 140 pts,
  and its card row (8 cards), moved to PLAN (spec 20, the Marines).
- ZSD-05 chassis (1412): the ZSD-05's default armour row (2020686: HP 12, same armour values as the HJ-10's) and its amphibious tracks
  (2020692: 50/70 km/h, 50 km/h on water), linked, not copied (Lateralus: reuse rows); WaterDiveOffset and sound preset of the ZSD-05.
  The game body stays US_M6_Linebacker, the HJ-10's, because its turret points carry the HJ-10 launcher turrets.
- Model: version A of the Blender test (work/zsd05-hj10-1126): the ZSD-05 with the AFT-10's HJ-10 launcher in place of the MG cupola, launcher
  in the ZSD-05 digital camo. It needs a models build; until then the card shows the vanilla M6 Linebacker.
- The Heavy CAB HJ-10 is unchanged. Not yet tested in a game."""
HJ10, ZSD05, ARMORED, PLAN = 936, 1412, 18, 20
ZSD_ARMOR, ZSD_TRACKS = 2020686, 2020692
NAME, HUD = 'PLA ZSD-05 HJ-10', 'ZSD-05 HJ-10'


def apply(t, g, ok, rec):
    U, SA, AR, MO = t['Units'], t['SpecializationAvailabilitiesJson'], t['ArmorsJson'], t['MobilityJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    (card,) = rows('SpecializationAvailabilitiesJson', UnitId=HJ10)
    ok(U[HJ10]['Name'] == 'PLA HJ-10' and card['SpecializationId'] == ARMORED and U[ZSD05]['Name'] == 'PLA ZSD-05', 'HJ-10 in Heavy CAB; ZSD-05 row')
    ok(AR[ZSD_ARMOR]['IsDefault'] and {r['ArmorId'] for r in rows('UnitArmorsJson', UnitId=ZSD05)} >= {ZSD_ARMOR}
       and [r['MobilityId'] for r in rows('UnitPropulsionsJson', UnitId=ZSD05)] == [ZSD_TRACKS] and MO[ZSD_TRACKS]['IsAmphibious'], 'ZSD-05 default armour + amphibious tracks')
    ok(len(rows('UnitArmorsJson', UnitId=HJ10)) == 1 and len(rows('UnitPropulsionsJson', UnitId=HJ10)) == 1, 'HJ-10: one armour, one mobility row')
    ok(not any(u and NAME in (u.get('Name'), u.get('HUDName')) or u and u.get('HUDName') == HUD for u in U.values()), 'name free')
    uid = g.add('Units', U[HJ10], {'Name': NAME, 'HUDName': HUD, 'Description': None, 'OriginalName': None, 'OriginalCost': 0,
                                   'AudioPreset': U[ZSD05]['AudioPreset'], 'WaterDiveOffset': U[ZSD05]['WaterDiveOffset']})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson'):
        for r in rows(tab, UnitId=HJ10): g.add(tab, r, {'UnitId': uid})
        ok(len(rows(tab, UnitId=uid)) == len(rows(tab, UnitId=HJ10)), (HUD, tab, 'copied'))
    for m in rows('ModificationsJson', UnitId=HJ10):
        nm = g.add('ModificationsJson', m, {'UnitId': uid})
        for o in rows('OptionsJson', ModificationId=m['Id']): g.add('OptionsJson', o, {'ModificationId': nm})
    g.add('UnitArmorsJson', rows('UnitArmorsJson', UnitId=HJ10)[0], {'UnitId': uid, 'ArmorId': ZSD_ARMOR})
    g.add('UnitPropulsionsJson', rows('UnitPropulsionsJson', UnitId=HJ10)[0], {'UnitId': uid, 'MobilityId': ZSD_TRACKS})
    nc = g.add('SpecializationAvailabilitiesJson', card, {'UnitId': uid, 'SpecializationId': PLAN})
    opts = [(o['UIName'], o.get('Cost', 0), o['Turret0Id']) for m in rows('ModificationsJson', UnitId=uid) for o in rows('OptionsJson', ModificationId=m['Id'])]
    ok(opts == [(o['UIName'], o.get('Cost', 0), o['Turret0Id']) for m in rows('ModificationsJson', UnitId=HJ10) for o in rows('OptionsJson', ModificationId=m['Id'])]
       and len(opts) == 2, ('loadouts copied', opts))
    ok(SA[card['Id']]['SpecializationId'] == ARMORED and SA[nc]['SpecializationId'] == PLAN and SA[nc]['MaxAvailabilityXp0'] == card['MaxAvailabilityXp0'], 'cards: Heavy CAB kept, PLAN copy')
    ab = lambda u: [t['AbilitiesJson'][r['AbilityId']].get('Name') for r in rows('UnitAbilitiesJson', UnitId=u)] if 'AbilitiesJson' in t else [r['AbilityId'] for r in rows('UnitAbilitiesJson', UnitId=u)]
    rec['pla_light_brigade_zsd05hj10_1126'] = {'unit': uid, 'card': nc, 'cards': SA[nc]['MaxAvailabilityXp0'], 'cost': U[uid]['Cost'], 'body': U[uid]['ModelFileName'],
        'armour': {k: AR[ZSD_ARMOR][k] for k in ('MaxHealthPoints', 'KinArmorFront', 'KinArmorSides', 'KinArmorRear', 'KinArmorTop')},
        'hj10_armour_hp': AR[rows('UnitArmorsJson', UnitId=HJ10)[0]['ArmorId']]['MaxHealthPoints'],
        'tracks': {k: MO[ZSD_TRACKS][k] for k in ('MaxCrossCountrySpeed', 'MaxSpeedRoad', 'MaxSpeedWater', 'IsAmphibious')},
        'hj10_tracks': {k: MO[rows('UnitPropulsionsJson', UnitId=HJ10)[0]['MobilityId']].get(k) for k in ('MaxCrossCountrySpeed', 'MaxSpeedRoad', 'MaxSpeedWater', 'IsAmphibious')},
        'loadouts': opts, 'abilities': ab(uid), 'zsd05_abilities': ab(ZSD05)}
    print('PLA LIGHT BRIGADE ZSD-05 HJ-10', rec['pla_light_brigade_zsd05hj10_1126'])

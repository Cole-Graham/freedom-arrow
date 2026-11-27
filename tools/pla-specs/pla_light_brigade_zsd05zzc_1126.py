"""PLA Light Brigade build, ZZC-06 on the ZSD-05 chassis for PLAN (Osama 26 Nov 2026 13:37 PST "Can you do the same with the mechanized zzc and
it's radar mast?", 13:4x on the Blender preview "Perfect, add this as a zzc-06 but zsd-05 chassis"; thread 1572407822849810463).
Branch codex/batch/osama/pla-light-brigade only; the last plb section (after the ZSD-05 HJ-10 section), so no earlier row id moves.
- New unit 'PLA ZSD-05 ZZC' (card 'ZSD-05 ZZC') = copy of the ZZC-06 (1420, PLAN since 26 Nov 11:00): its ZPT-99 30 mm + Type 86 turret, rounds,
  Very Good Optics, smoke/supply ability, 45 pts and its card row (4 cards in PLAN). The ZZC-06 card stays as it is.
- ZSD-05 chassis (1412): the ZSD-05's default armour row (2020686: HP 12, sides 80 / rear 60 instead of the ZZC-06's 60 / 30) and its amphibious tracks
  (2020692: 50/70 km/h, 50 km/h on water), linked, not copied (Lateralus: reuse rows); WaterDiveOffset and sound preset of the ZSD-05.
  The game body stays RU_BMP3, the ZZC-06's, because its turret points carry the ZZC-06 turret.
- Model: work/zsd05-hj10-1126 build_zzc.py: the ZSD-05 with the ZZC-06's 30 mm turret and observation/radar mast in place of the MG cupola,
  in the ZSD-05 digital camo. It needs a models build; until then the card shows the BMP-3 body. Not yet tested in a game."""
HJ10, ZSD05, ARMORED, PLAN = 1420, 1412, 20, 20   # HJ10 = the source unit (here the ZZC-06; its card is in PLAN too)
ZSD_ARMOR, ZSD_TRACKS = 2020686, 2020692
NAME, HUD = 'PLA ZSD-05 ZZC', 'ZSD-05 ZZC'


def apply(t, g, ok, rec):
    U, SA, AR, MO = t['Units'], t['SpecializationAvailabilitiesJson'], t['ArmorsJson'], t['MobilityJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    (card,) = rows('SpecializationAvailabilitiesJson', UnitId=HJ10)
    ok(U[HJ10]['Name'] == 'PLA ZZC-06' and card['SpecializationId'] == ARMORED and U[ZSD05]['Name'] == 'PLA ZSD-05', 'ZZC-06 in PLAN; ZSD-05 row')
    ok(AR[ZSD_ARMOR]['IsDefault'] and {r['ArmorId'] for r in rows('UnitArmorsJson', UnitId=ZSD05)} >= {ZSD_ARMOR}
       and [r['MobilityId'] for r in rows('UnitPropulsionsJson', UnitId=ZSD05)] == [ZSD_TRACKS] and MO[ZSD_TRACKS]['IsAmphibious'], 'ZSD-05 default armour + amphibious tracks')
    ok(len(rows('UnitArmorsJson', UnitId=HJ10)) == 1 and len(rows('UnitPropulsionsJson', UnitId=HJ10)) == 1, 'ZZC-06: one armour, one mobility row')
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
       and len(opts) == 0, ('no loadouts', opts))
    ok(SA[card['Id']]['SpecializationId'] == PLAN and SA[nc]['SpecializationId'] == PLAN and SA[nc]['MaxAvailabilityXp0'] == card['MaxAvailabilityXp0'], 'cards: ZZC-06 kept, PLAN copy')
    ab = lambda u: [t['AbilitiesJson'][r['AbilityId']].get('Name') for r in rows('UnitAbilitiesJson', UnitId=u)] if 'AbilitiesJson' in t else [r['AbilityId'] for r in rows('UnitAbilitiesJson', UnitId=u)]
    rec['pla_light_brigade_zsd05zzc_1126'] = {'unit': uid, 'card': nc, 'cards': SA[nc]['MaxAvailabilityXp0'], 'cost': U[uid]['Cost'], 'body': U[uid]['ModelFileName'],
        'armour': {k: AR[ZSD_ARMOR][k] for k in ('MaxHealthPoints', 'KinArmorFront', 'KinArmorSides', 'KinArmorRear', 'KinArmorTop')},
        'zzc06_armour': {k: AR[rows('UnitArmorsJson', UnitId=HJ10)[0]['ArmorId']][k] for k in ('MaxHealthPoints', 'KinArmorFront', 'KinArmorSides', 'KinArmorRear', 'KinArmorTop')},
        'tracks': {k: MO[ZSD_TRACKS][k] for k in ('MaxCrossCountrySpeed', 'MaxSpeedRoad', 'MaxSpeedWater', 'IsAmphibious')},
        'zzc06_tracks': {k: MO[rows('UnitPropulsionsJson', UnitId=HJ10)[0]['MobilityId']].get(k) for k in ('MaxCrossCountrySpeed', 'MaxSpeedRoad', 'MaxSpeedWater', 'IsAmphibious')},
        'loadouts': opts, 'abilities': ab(uid), 'zsd05_abilities': ab(ZSD05)}
    print('PLA LIGHT BRIGADE ZSD-05 ZZC', rec['pla_light_brigade_zsd05zzc_1126'])

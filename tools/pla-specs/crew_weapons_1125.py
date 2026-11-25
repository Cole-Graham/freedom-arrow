"""China tripod weapons crewed like vanilla (Osama 25 Nov 2026 10:2x PST, thread "China cosmetic work": "PF-98 team in PLARF needs the
launcher to be rigger like an spg. same with heavy CAB QLZ-04 and HJ-8E, they're sticking out the back of the soldier instead of the soldier
kneeling next to the launcher on the ground ... We need this for all the tripod based weapons").
- Vanilla: every tripod weapon (AGS, SPG-9, Konkurs, Fagot, Kornet, TOW, M2 / Mk19 tripod) is the gunner's PRIMARY weapon on a crew soldier
  prefab (RU_VDV_AGS, RU_Morskaya_heavy, RU_Motostrelki_Konkurs, RU_VDV_Kornet, US_Army_TOW, US_Army_M2); the game then places the weapon on the
  ground and plays the kneeling crew animations. China squads carried them as the SPECIAL weapon of a rifleman, so they rode on his back.
- Every China squad member whose special weapon has a tripod model now carries it as primary (no special) on the vanilla crew prefab for that
  model. The gunner loses his rifle, as vanilla gunners have none; squad size, HP, price and ammo rows are unchanged.
- QJZ-89 / QJZ-171 (tripod 12.7 mm HMGs) drew the vanilla Kord bipod: their infantry rows now draw the M2 tripod (crew prefab US_Army_M2).
- The PF-98 (tripod) FAModels rule moves from the special to the primary slot in the model stage (work/model-rework-096/stage.py)."""
CREW = {'AGS30': 'RU_VDV_AGS', 'AGS17': 'RU_Motostrelki_AGS', 'AGS40': 'RU_GvMotostrelki_rifle_AGS', 'SPG9': 'RU_Morskaya_heavy',
        'Konkurs': 'RU_Morskaya_heavy', 'KonkursM': 'RU_Morskaya_heavy', 'Fagot': 'RU_Motostrelki_Konkurs', 'Kornet': 'RU_VDV_Kornet',
        'M220': 'US_Army_TOW', 'M220 1': 'US_Army_TOW', 'MK19_TRIPOD': 'US_Army_M2', 'M2_TRIPOD': 'US_Army_M2'}
HMG = {2012387: 'QJZ-89', 2011972: 'QJZ-171'}


def apply(t, g, ok, rec):
    U, SM, W, TW = t['Units'], t['SquadMembersJson'], t['WeaponsJson'], t['TurretWeaponsJson']
    for w, n in HMG.items():
        users = [m['UnitId'] for m in SM.values() if m and w in (m['PrimaryWeaponId'], m.get('SpecialWeaponId'))]
        ok(W[w]['HUDName'] == n and W[w]['ModelFileName'] == 'ModelPrefabs/Weapon/Kord_bipod' and not any(r and r['WeaponId'] == w for r in TW.values())
           and all(U[u]['CountryId'] == 4 and U[u]['Type'] == 2 for u in users), (n, 'infantry-only Kord bipod row', users))
        g.put('WeaponsJson', w, {'ModelFileName': 'M2_TRIPOD'})
    china = {int(k) for k, u in U.items() if u and u['CountryId'] == 4 and u['Type'] == 2}
    changed = []
    for m in sorted((m for m in SM.values() if m and m['UnitId'] in china and m.get('SpecialWeaponId')), key=lambda m: m['Id']):
        crew = CREW.get(W[m['SpecialWeaponId']]['ModelFileName'])
        if not crew: continue
        changed.append((m['UnitId'], U[m['UnitId']]['HUDName'], m['Id'], m['ModelFileName'], crew, W[m['SpecialWeaponId']]['HUDName']))
        g.put('SquadMembersJson', m['Id'], {'ModelFileName': crew, 'PrimaryWeaponId': m['SpecialWeaponId'], 'SpecialWeaponId': 0})
    left = [(m['UnitId'], W[m['SpecialWeaponId']]['HUDName']) for m in SM.values()
            if m and m['UnitId'] in china and m.get('SpecialWeaponId') and W[m['SpecialWeaponId']]['ModelFileName'] in CREW]
    ok(not left, ('no China tripod weapon left in a special slot', left))
    named = {u: n for u, n, *_ in changed}
    for u in (1172, 1154, 1152, 1171, 1221, 1168, 1173, 1170, 1199):
        ok(u in named, ('tripod team crewed', u, U[u]['HUDName']))
    rec['crew_weapons_1125'] = {'members': len(changed), 'units': sorted(named.items()), 'hmg_model': 'M2_TRIPOD'}
    print('CREW WEAPONS', len(changed), 'members on', len(named), 'squads')
    for c in changed: print('   ', c)

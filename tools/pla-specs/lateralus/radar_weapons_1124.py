"""Which weapons on a radar unit use the radar (Lateralus 24 Nov 2026 22:0x-22:2x PST, thread 1568104480459722894).
22:02 "Do you think it would be possible to individually control which weapons on a unit benefit from radar?"; 22:11 "the stingers, igla, and AIM-9
are all infrared and thus should not benefit from Radar"; 22:2x "actually, AIM-9 should benefit from radar and so should Hellfire. Fletcher should
not benefit from radar. Build it". Card: "plain radar icon" in the selected weapon's trait row (next to the static-to-fire icon).
- radarExempt: rounds that get no radar range bonus. Rule: every heat-seeking round (Seeker 10) fired by a radar unit, except the AIM-9 ground
  round (465), plus the Fletcher APKWS (501, laser). The runtime (HeliRange.RangeAfter) takes the bonus back out of GetAmmoShootingDistance while
  the shooter's radar is on; the search radius is not hooked (it only bounds the search; every candidate still passes the per-target range).
  Their SEAD / non-SEAD overrides must be 0 (global factor 1.0) or a fixed range >= 100 (HHQ-10: SEAD 1100); the runtime handles both (checked).
- radarAmmo: rounds that do use the radar and can engage air targets (helicopters, planes, SEAD / cruise / ballistic missiles) on radar units:
  the card shows the plain radar icon for a weapon carrying one of them.
- Lateralus 25 Nov 2026 07:5x ("-MGs should not benefit from radar / -HJ-10, AFT-1[0], and LY-1 should have radar / -SM-6 and M61 CIWS should have
  radar / build it"): machine-gun rounds (Weapons.Type 26-29: LMG, MMG, HMG, minigun) on radar units are exempt too (M2 19, M240 27 today).
- radarWeapons: weapon ids on radar units whose air rounds use the radar. The card decides per weapon from this list (dev.13 read
  WeaponListButton.TotalAmmoCount, which the game reuses across cards, so it held other weapons' rounds). No weapon on a radar unit may mix radar and
  exempt rounds (checked)."""
AIR = 8 | 16 | 256 | 512 | 1024
EXPECT = {18: 'Stinger', 127: 'Igla-S', 2010683: 'QW-2 (PGZ-95)', 2010649: 'QW-2 (PGZ-04)', 2009565: 'QW-2 (PGZ-04A)',
          501: 'Fletcher', 19: 'M2 12.7 mm (MG)', 27: 'M240 7.62 mm (MG)'}
MG = {26, 27, 28, 29}   # WeaponType LightMachineGun, MediumMachineGun, HeavyMachineGun, MiniGun (1.2.2.1)
# Lateralus' named weapons (thread 1568104480459722894, 25 Nov 07:3x / 07:5x): must use the radar / must not
WANT = {40: 'M230LF 30mm', 17: 'Hellfire (Stryker M-SHORAD)', 616: 'Hellfire (M6 M-SHORAD)', 345: 'M61 CIWS (C-RAM)', 2010673: 'Four 25 mm (PGZ-95)',
        2010625: 'HQ-17A', 2009599: '2x 30 mm (FK-2000/3000)', 2009605: 'FK-2000 SAM', 2009365: '625 six-barrel', 2010721: 'HJ-10 (AFT-10)',
        2019445: 'LY-1 laser', 599: 'SM-6', 706: 'M61 CIWS (ships)', 625: 'AIM-9 (MML)', 627: 'Hellfire (MML)', 732: 'RIM-116 (C-RAM SeaRAM)',
        2019357: 'HHQ-10'}
NOT = {654: 'Fletcher', 626: 'FIM-92K Stinger (MML)', 18: 'M2 Browning', 27: 'M240'}
KEEP_IR = {465, 560, 2019358}   # AIM-9 ground (Lateralus 24 Nov 22:2x); RIM-116 SeaRAM and HHQ-10 (25 Nov 09:17 "should benefit from radar")
ADD = {501}         # Fletcher APKWS: laser, no radar (Lateralus 22:2x)


def apply(t, ok, rec, heli):
    U, AB, UA, WA, A, O, M = (t[k] for k in ('Units', 'AbilitiesJson', 'UnitAbilitiesJson', 'WeaponAmmunitionsJson', 'AmmunitionsJson', 'OptionsJson',
                                             'ModificationsJson'))
    radar = {r['UnitId'] for r in UA.values() if r and AB.get(r['AbilityId'], {}).get('IsRadar')}
    for o in O.values():
        if o and any(AB.get(o.get(k), {}).get('IsRadar') for k in ('Ability1Id', 'Ability2Id', 'Ability3Id')):radar.add(M[o['ModificationId']]['UnitId'])
    rounds = {r['AmmunitionId'] for r in WA.values() if r and r.get('UnitId') in radar}
    air = {i for i in rounds if int(A[i].get('TargetType') or 0) & AIR}
    W = t['WeaponsJson']
    mg = {r['AmmunitionId'] for r in WA.values() if r and r.get('UnitId') in radar and W[r['WeaponId']].get('Type') in MG}
    exempt = ({i for i in air if A[i].get('Seeker') == 10} - KEEP_IR | ADD | (mg & air))
    ok(exempt == set(EXPECT), ('radar-exempt rounds', sorted(exempt), sorted(set(EXPECT))))
    for i in exempt:
        a = A[i]
        ok(all((a.get(k) or 0) == 0 or a[k] >= 100 for k in ('SeadProjectileRangeOverride', 'NonSeadProjectileRangeOverride')),
           (i, a['Name'], 'exempt round: anti-missile override 0 or a fixed range (>= 100), not a multiplier'))
    use = sorted(air - exempt)
    ok({465, 166, 28, 263} <= set(use), 'AIM-9, Hellfire SHORAD, Tor M1, PAC-3 use the radar')
    weapons = {}
    for r in WA.values():
        if r and r.get('UnitId') in radar and r['AmmunitionId'] in air:weapons.setdefault(r['WeaponId'], set()).add(r['AmmunitionId'] in exempt)
    ok(not [w for w, v in weapons.items() if len(v) > 1], ('weapon mixes radar and exempt rounds', [w for w, v in weapons.items() if len(v) > 1]))
    rw = sorted(w for w, v in weapons.items() if v == {False})
    ok(set(WANT) <= set(rw) and not set(NOT) & set(rw), ('named weapons', sorted(set(WANT) - set(rw)), sorted(set(NOT) & set(rw))))
    heli['radarWeapons'] = rw
    heli['radarExempt'] = sorted(exempt)
    heli['radarAmmo'] = use
    rec['radar_weapons_1124'] = {'exempt': {i: A[i]['Name'] for i in sorted(exempt)}, 'radar_units': len(radar), 'radar_rounds': len(use),
                                 'radar_weapons': len(rw)}
    return rec['radar_weapons_1124']

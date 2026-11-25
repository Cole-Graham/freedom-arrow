"""Which weapons on a radar unit use the radar (Lateralus 24 Nov 2026 22:0x-22:2x PST, thread 1568104480459722894).
22:02 "Do you think it would be possible to individually control which weapons on a unit benefit from radar?"; 22:11 "the stingers, igla, and AIM-9
are all infrared and thus should not benefit from Radar"; 22:2x "actually, AIM-9 should benefit from radar and so should Hellfire. Fletcher should
not benefit from radar. Build it". Card: "plain radar icon" in the selected weapon's trait row (next to the static-to-fire icon).
- radarExempt: rounds that get no radar range bonus. Rule: every heat-seeking round (Seeker 10) fired by a radar unit, except the AIM-9 ground
  round (465), plus the Fletcher APKWS (501, laser). The runtime (HeliRange.RangeAfter) takes the bonus back out of GetAmmoShootingDistance while
  the shooter's radar is on; the search radius is not hooked (it only bounds the search; every candidate still passes the per-target range).
  Their SEAD / non-SEAD overrides must be 0 (global factor 1.0) or a fixed range >= 100 (HHQ-10: SEAD 1100); the runtime handles both (checked).
- radarAmmo: rounds that do use the radar and can engage air targets (helicopters, planes, SEAD / cruise / ballistic missiles) on radar units:
  the card shows the plain radar icon for a weapon carrying one of them."""
AIR = 8 | 16 | 256 | 512 | 1024
EXPECT = {18: 'Stinger', 127: 'Igla-S', 2010683: 'QW-2 (PGZ-95)', 2010649: 'QW-2 (PGZ-04)', 2009565: 'QW-2 (PGZ-04A)', 560: 'RIM-116', 2019358: 'HHQ-10',
          501: 'Fletcher'}
KEEP_IR = {465}     # AIM-9 ground: uses the radar (Lateralus 22:2x)
ADD = {501}         # Fletcher APKWS: laser, no radar (Lateralus 22:2x)


def apply(t, ok, rec, heli):
    U, AB, UA, WA, A, O, M = (t[k] for k in ('Units', 'AbilitiesJson', 'UnitAbilitiesJson', 'WeaponAmmunitionsJson', 'AmmunitionsJson', 'OptionsJson',
                                             'ModificationsJson'))
    radar = {r['UnitId'] for r in UA.values() if r and AB.get(r['AbilityId'], {}).get('IsRadar')}
    for o in O.values():
        if o and any(AB.get(o.get(k), {}).get('IsRadar') for k in ('Ability1Id', 'Ability2Id', 'Ability3Id')):radar.add(M[o['ModificationId']]['UnitId'])
    rounds = {r['AmmunitionId'] for r in WA.values() if r and r.get('UnitId') in radar}
    air = {i for i in rounds if int(A[i].get('TargetType') or 0) & AIR}
    exempt = {i for i in air if A[i].get('Seeker') == 10} - KEEP_IR | ADD
    ok(exempt == set(EXPECT), ('radar-exempt rounds', sorted(exempt), sorted(set(EXPECT))))
    for i in exempt:
        a = A[i]
        ok(all((a.get(k) or 0) == 0 or a[k] >= 100 for k in ('SeadProjectileRangeOverride', 'NonSeadProjectileRangeOverride')),
           (i, a['Name'], 'exempt round: anti-missile override 0 or a fixed range (>= 100), not a multiplier'))
    use = sorted(air - exempt)
    ok({465, 166, 28, 263} <= set(use), 'AIM-9, Hellfire SHORAD, Tor M1, PAC-3 use the radar')
    heli['radarExempt'] = sorted(exempt)
    heli['radarAmmo'] = use
    rec['radar_weapons_1124'] = {'exempt': {i: A[i]['Name'] for i in sorted(exempt)}, 'radar_units': len(radar), 'radar_rounds': len(use)}
    return rec['radar_weapons_1124']

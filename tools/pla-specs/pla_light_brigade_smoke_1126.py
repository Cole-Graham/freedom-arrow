"""PLA Light Brigade build, Flying Tigers smoke launcher (Osama 26 Nov 2026 11:5x-12:0x PST, thread 1567745029781454889: "give the Hong Kong units
like a smoke launcher ... they can shoot tiny puffs of smoke let's say at around 200 m", "Ok a tiny smoke cloud that only lasts ten seconds", "And the
weapon only shoots once every ten seconds"). Branch codex/batch/osama/pla-light-brigade only; the last plb section, so no earlier row id moves.
- Weapon 'ARWEN 37 Smoke' = copy of the ARWEN 37 (Arbalet icon) firing one round, then a 10 s reload: magazine 1, burst 1, reload 10-10 s.
- Round '37 mm smoke' = copy of the ARWEN 37 round (direct-fire path, TrajectoryType 10, like every infantry grenade; no mortar arc):
  GenerateSmoke on, SmokeRadius 10, SmokeDuration 10, SmokeFadeDuration 1 (the size and time of vanilla's smallest cloud, 585 'Special SmokeScreen
  Zombie'); no stress, no blast; Damage 0.01 so an attack order can use it (a round must do more than 0 damage) while its score against any target
  stays below its time to hit, so the squad should not fire it by itself (docs/engine/target-and-ammo-selection.md); range 15-100 world = 30-200 m
  on the card. Smoke from a shell: ExplosionEventSystem.Update calls SmokeHelper.SpawnSmoke for any exploding shell (call scan of GameAssembly).
- Carrier: the Flying Tigers' plain SIG 516 man gets it as his special weapon, 6 rounds; weapon list after the ARWEN 37 (grenade launchers last),
  death priority 2 (a specialist, the vanilla rule of pla_light_brigade_order_1126). Not yet tested in a game."""
FT = 1187


def apply(t, g, ok, rec):
    U, W, A = t['Units'], t['WeaponsJson'], t['AmmunitionsJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    hud = lambda h: [i for i, w in W.items() if w and w.get('HUDName') == h]
    (sig,), (arwen,) = hud('SIG 516'), hud('ARWEN 37')
    ok(U[FT]['HUDName'] == 'Flying Tigers' and not hud('ARWEN 37 Smoke'), 'Flying Tigers, smoke launcher name free')
    (arwen_wa,) = rows('WeaponAmmunitionsJson', UnitId=FT, WeaponId=arwen)
    ar = A[arwen_wa['AmmunitionId']]
    ok(ar['HUDName'] == '37 mm less-lethal' and ar['TrajectoryType'] == 10 and not ar.get('GenerateSmoke'), 'ARWEN round: direct fire, no smoke')
    w = g.add('WeaponsJson', W[arwen], {'Name': 'PLA infantry ARWEN 37 Smoke', 'HUDName': 'ARWEN 37 Smoke', 'MagazineSize': 1, 'ShotsPerBurstMin': 1,
                                        'ShotsPerBurstMax': 1, 'TimeBetweenShotsInBurst': 0.0, 'TimeBetweenBurstsMin': 0.0, 'TimeBetweenBurstsMax': 0.0,
                                        'MagazineReloadTimeMin': 10.0, 'MagazineReloadTimeMax': 10.0})
    a = g.add('AmmunitionsJson', ar, {'Name': 'PLA infantry ARWEN 37 smoke', 'HUDName': '37 mm smoke', 'Damage': 0.01, 'StressDamage': 0.0,
                                      'StressAOERadius': 0.0, 'HealthAOERadius': 0.0, 'NoDamageFalloff': False, 'GenerateSmoke': True,
                                      'SmokeRadius': 10.0, 'SmokeDuration': 10.0, 'SmokeFadeDuration': 1.0, 'MinimalRange': 15.0, 'GroundRange': 100.0,
                                      'AudioPreset': 'AmmunitionSoundsPreset_SFX_SMK_80-105'})
    (man,) = [m for m in rows('SquadMembersJson', UnitId=FT) if m['PrimaryWeaponId'] == sig and not m.get('SpecialWeaponId')]
    g.put('SquadMembersJson', man['Id'], {'SpecialWeaponId': w, 'DeathPriority': 2})
    sw = rows('SquadWeaponsJson', UnitId=FT)
    g.add('SquadWeaponsJson', sw[0], {'UnitId': FT, 'WeaponId': w, 'Order': max(r['Order'] for r in sw) + 1})
    g.add('WeaponAmmunitionsJson', arwen_wa, {'WeaponId': w, 'AmmunitionId': a, 'Quantity': 6})
    # checks after
    men = rows('SquadMembersJson', UnitId=FT)
    carried = {x for m in men for x in (m['PrimaryWeaponId'], m.get('SpecialWeaponId')) if x}
    ok({r['WeaponId'] for r in rows('SquadWeaponsJson', UnitId=FT)} == carried == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=FT)}, 'card + ammo = carried')
    order = [W[r['WeaponId']]['HUDName'] for r in sorted(rows('SquadWeaponsJson', UnitId=FT), key=lambda r: r['Order'])]
    ok(order[-2:] == ['ARWEN 37', 'ARWEN 37 Smoke'] and sorted(r['Order'] for r in rows('SquadWeaponsJson', UnitId=FT)) == list(range(1, len(order) + 1)), ('order', order))
    ok(len(men) == 6 and sum(m['DeathPriority'] == 1 for m in men) == 1 and U[FT]['Cost'] == 55, 'Flying Tigers: 6 men, one keeper, 55 pts')
    rec['pla_light_brigade_smoke_1126'] = {'weapon': w, 'round': a, 'carrier': man['Id'], 'order': order,
                                           'death': sorted((m['DeathPriority'], W[m['PrimaryWeaponId']]['HUDName'] + (' + ' + W[m['SpecialWeaponId']]['HUDName'] if m.get('SpecialWeaponId') else '')) for m in men)}
    print('PLA LIGHT BRIGADE SMOKE', rec['pla_light_brigade_smoke_1126'])

"""NLOS cruise missiles without laser guidance; HJ-10 on a cruise-missile launcher (Osama 21 Nov 2026 23:3x PST, thread 1567745029781454889, testing
0.9.5-dev.1: "The HJ-10 still doesn't fire", "the blood wolves NLOS still goes haywire after lazing", "they seem to be chasing something off the
edge of the map").
- No vanilla round combines the cruise path (TrajectoryType 200) with LaserGuided: every vanilla laser-guided missile flies the Hellfire path (110).
  On 13 Nov (0.8.0-dev.25) the CTL-181 round on the cruise path went haywire when lased and LaserGuided False fixed it (Osama). 0.9.0-dev.35 put it
  back on the cruise path with LaserGuided still True; 0.9.4 section 14 gave the HJ-10 and QN-502 rounds the same mix (copied from the Blood
  Wolves' CH-901, which has had it since 0.8.0-dev.21). 0.9.5-dev.3 set LaserGuided False on all four (undone below). Path, seeker, speed, damage and
  interception are unchanged; the NLOS hook still fires them at spotted enemies and keeps the seeker on a moving target.
- HJ-10 launcher 2009619 was still an ATGM-HE launcher (Type 81, not vertical, no ground-attack bursts) firing a cruise round: test log
  23:26 "HJ-10 guided missile: shots 886, hits 0, mean gap 0.01 s" and no missile launched. Type 82 (CruiseMissile), vertical launch and the
  CH-901 / CTL-181 vertical angle and ground-attack bursts, like both working cruise launchers. Magazine, reload and range stay.
- HJ-10 still did not fire in 0.9.5-dev.3 (log 23:49: 14,719 shots, 0 hits, one per frame): its round kept LaunchMarginAngle 30 from the
  Hellfire path. A vertical launcher points up, so no target is ever within 30 degrees and every launch is refused. Every vanilla round on a
  vertical launcher (22) and the three working NLOS rounds use 180; set 180 on all four (no change for the other three).
- 0.9.5-dev.3 had LaserGuided False on all four: Osama 23:5x "the QN, blood wolves, and CTL-181 lost their NLOS ability", so the laser is how
  they reach targets without line of sight. LaserGuided is back to True on all four (as in 0.9.4); only the HJ-10 launch fixes stay. The
  off-map flight after lasing is still open: NlosTrait traces these four rounds (FREEDOM_ARROW_NLOS_TRACE) to show where they aim.
- dev.4 still no HJ-10 launch: 7,311 WeaponForceFire (fire at a point) calls; its round TargetType 36 lacks Ground (1). Now 37, as the CTL-181.
- dev.7 hits counted as Front (top-attack flag only works on the Hellfire path): OverpressureRadius on the three top-attack rounds -> roof hits
  (dev.8 0.1 m; dev.9 HJ-10 5 m, QN-502 and CH-901 2 m for near-miss leeway, Osama).
- dev.10: HJ-10 penetration 90 -> 130 (Osama). dev.12: TOW-2B stats (11 / 140) instead; FNF default launcher (aim 3-4 s) and NLOS option (+20, aim
  0.2 s, 2000 m) on a loadout option (Osama).
Called from apply_0_9_4_dev1.py."""
ROUNDS = {2009623: 'HJ-10', 2009651: 'QN-502', 2018321: 'CTL-181', 2018448: 'CH-901'}
HJ10_LAUNCHER = 2009619


def apply(t, g, ok, rec):
    A, W, WA = t['AmmunitionsJson'], t['WeaponsJson'], t['WeaponAmmunitionsJson']
    for i, name in ROUNDS.items():
        a = A[i]
        ok(a.get('TrajectoryType') == 200 and a.get('LaserGuided') is True and a.get('CanBeIntercepted') is False, (name, 'cruise + laser before', i))
        g.put('AmmunitionsJson', i, {'LaunchMarginAngle': 180.0})
        ok(A[i]['LaserGuided'] is True and A[i]['TrajectoryType'] == 200 and A[i]['LaunchMarginAngle'] == 180.0, (name, 'cruise, laser kept, vertical launch margin', i))
    w = W[HJ10_LAUNCHER]
    ok(w.get('HUDName') == 'HJ-10' and w.get('Type') == 81 and w.get('IsVerticalLauncher') is False, ('HJ-10 launcher before', w.get('Type')))
    ok(sorted({r['AmmunitionId'] for r in WA.values() if r and r.get('WeaponId') == HJ10_LAUNCHER}) == [2009623], 'HJ-10 launcher fires only the HJ-10 round')
    ch = W[2018447]
    new = {'Type': 82, 'IsVerticalLauncher': True, 'LowerVerticalAngle': ch['LowerVerticalAngle'],
           'ShortGroundAttackBurst': ch['ShortGroundAttackBurst'], 'NormalGroundAttackBurst': ch['NormalGroundAttackBurst'],
           'LongGroundAttackBurst': ch['LongGroundAttackBurst']}
    g.put('WeaponsJson', HJ10_LAUNCHER, new)
    ok(all(W[HJ10_LAUNCHER][k] == v for k, v in new.items()) and W[HJ10_LAUNCHER]['MagazineSize'] == 8, 'HJ-10 cruise launcher')
    # dev.5 (Osama 22 Nov 00:0x "HJ-10 can't fire"; dev.4 log: 7,311 WeaponForceFire calls, no missile): firing at a laser spot / position needs
    # the Ground bit (1) in the round's TargetType; HJ-10 had 36 (vehicle + ship). 37 as the CTL-181 (16 Nov fix); QN-502 / CH-901 have 1.
    ok(A[2009623]['TargetType'] == 36 and A[2018321]['TargetType'] == 37, 'HJ-10 target type before')
    g.put('AmmunitionsJson', 2009623, {'TargetType': 37})
    ok(A[2009623]['TargetType'] == 37, 'HJ-10 may fire at ground points (laser spot)')
    # dev.8 (Osama 22 Nov 00:3x "now they fly right but it doesn't seem to do damage?"; dev.7 shot log: every hit on the ZTZ-100 counted as
    # Front, HEAT 1075 vs penetration 30-90, 0.01-0.09 damage, forceTop false). IsTopArmorArmorAttack only works on the Hellfire path (110), as for
    # every vanilla top-attack missile; on the cruise path the side comes from the direction. Native rule (ShellHitSystem, 19 Nov): a direct hit by a
    # round with OverpressureRadius > 0 strikes the roof, with no distance check for the struck unit. 0.1 m on the three top-attack rounds; the
    # splash part only reaches units within 0.1 m of the struck one. CTL-181 is not top-attack (as in 0.9.3) and stays 0.
    TOP = (2009623, 2009651, 2018448)
    ok(all(A[i].get('IsTopArmorArmorAttack') is True and not A[i].get('OverpressureRadius') for i in TOP) and A[2018321].get('IsTopArmorArmorAttack') is False, 'top-attack NLOS rounds before')
    # dev.9 (Osama 22 Nov 00:4x "you can maybe make it a bit bigger for leeway?", "especially for the HJ-10 that should have big leeway"): the
    # struck unit gets the roof at any radius above 0; a near miss gives units within OverpressureRadius - unit radius a roof-armor splash (DealAOEDamage).
    OP = {2009623: 5.0, 2009651: 2.0, 2018448: 2.0}
    for i in TOP: g.put('AmmunitionsJson', i, {'OverpressureRadius': OP[i]})
    ok(all(A[i]['OverpressureRadius'] == OP[i] for i in TOP), 'top-attack NLOS rounds strike the roof on a direct hit; near-miss leeway')
    # dev.10 (Osama 22 Nov 00:5x "HJ-10 needs more penetration, about 130"). dev.9 shot log: roof hits work (forceTop, side Top); damage =
    # base x pen^2 / (pen^2 + armour^2): pen 90 on roof 100 (ZTZ-100, M1A2 SEP ...) 5.82 a hit, 3 to kill 14 HP; pen 130 8.17, 2 hits; roof 60 10.72.
    # dev.12 (Osama 22 Nov 01:0x "give the HJ-10 a 0.2 second aim time"; "a terminal guidance mode that turns the missiles into a FNF. And another
    # that uses the current mode that's NLOS"; "penetration and damage match the Tow-2b"; "so the FNF version has a long aim time but the NLOS is
    # 2000 range and 0.2 aim time (and +20)"). Aim time belongs to the launcher, so the two modes are two launchers on a loadout option, built like
    # the vanilla BTR-D weapon package (mod 88): both turrets linked at TurretUnits Order 1, Turrets.IsDefault picks the default, each option
    # sets Turret1Id. The existing launcher 2009619 / turret 2009620 / round 2009623 become the NLOS option (+20, aim 0.2 s, 2000 m), so nlos.json
    # stays as it is; a new launcher + turret + FNF round (Seeker 50 terminal guidance as the Javelin, no laser, units only) are the default
    # (aim 3-4 s, 0 points). Both rounds TOW-2B damage / penetration (ammo 52: 11 / 140), roof hits (OverpressureRadius 5), not interceptable.
    T, TU, TW, M, O = t['TurretsJson'], t['TurretUnitsJson'], t['TurretWeaponsJson'], t['ModificationsJson'], t['OptionsJson']
    T2B = A[52]
    ok((T2B.get('Name'), T2B['Damage'], T2B['PenetrationAtGroundRange'], T2B['PenetrationAtMinRange']) == ('Missile AT TOW2B', 11.0, 140.0, 140.0), 'TOW-2B stats')
    ok(A[2009623]['PenetrationAtGroundRange'] == 90.0 and A[2009623]['Damage'] == 13.0 and A[2009623]['GroundRange'] == 800.0, 'HJ-10 round before')
    STATS = {'Damage': T2B['Damage'], 'PenetrationAtGroundRange': T2B['PenetrationAtGroundRange'], 'PenetrationAtMinRange': T2B['PenetrationAtMinRange']}
    hj = lambda: [r for r in TU.values() if r and r.get('UnitId') == 936]
    ok(not [m for m in M.values() if m and m.get('UnitId') == 936] and [(r['TurretId'], r['Order']) for r in hj()] == [(2009620, 0)]
       and [(r['WeaponId'], r['Order']) for r in TW.values() if r and r.get('TurretId') == 2009620] == [(2009619, 0)] and T[2009620]['IsDefault'] is True
       and (W[HJ10_LAUNCHER]['AimTimeMin'], W[HJ10_LAUNCHER]['AimTimeMax']) == (3.0, 4.0), 'HJ-10 single launcher, no options, before')
    # NLOS option: the existing launcher, turret and round.
    g.put('AmmunitionsJson', 2009623, {**STATS, 'GroundRange': 2000.0, 'HUDName': 'HJ-10 NLOS'})
    g.put('WeaponsJson', HJ10_LAUNCHER, {'AimTimeMin': 0.2, 'AimTimeMax': 0.2, 'HUDName': 'HJ-10 NLOS'})
    g.put('TurretsJson', 2009620, {'IsDefault': False})
    g.put('TurretUnitsJson', hj()[0]['Id'], {'Order': 1})
    # FNF default: new round, launcher and turret.
    fnf = g.add('AmmunitionsJson', A[2009623], {**STATS, 'GroundRange': 800.0, 'Name': 'PLA HJ-10 HJ-10 FNF missile', 'HUDName': 'HJ-10 FNF', 'LaserGuided': False, 'Seeker': 50, 'TargetType': 36})
    fw = g.add('WeaponsJson', W[HJ10_LAUNCHER], {'Name': 'PLA HJ-10 HJ-10 FNF', 'HUDName': 'HJ-10 FNF', 'AimTimeMin': 3.0, 'AimTimeMax': 4.0})
    ft = g.add('TurretsJson', T[2009620], {'Name': 'PLA HJ-10 mount FNF', 'IsDefault': True})
    g.add('TurretWeaponsJson', [r for r in TW.values() if r and r.get('TurretId') == 2009620][0], {'TurretId': ft, 'WeaponId': fw})
    g.add('TurretUnitsJson', hj()[0], {'TurretId': ft, 'Order': 1})
    wa = [r for r in WA.values() if r and r.get('WeaponId') == HJ10_LAUNCHER]
    ok(len(wa) == 1 and wa[0]['UnitId'] == 936 and wa[0]['Quantity'] == 8, 'HJ-10 ammo row before')
    g.add('WeaponAmmunitionsJson', wa[0], {'WeaponId': fw, 'AmmunitionId': fnf, 'Quantity': 8})
    mod = g.add('ModificationsJson', M[88], {'UnitId': 936, 'Name': 'PLA loadout HJ-10', 'UIName': 'Custom_Slot_Weapon_package', 'Order': 0})
    o_f = g.add('OptionsJson', O[244], {'ModificationId': mod, 'Name': 'PLA loadout HJ-10 FNF', 'UIName': 'HJ-10 FNF', 'Order': 0, 'Cost': 0, 'Turret1Id': ft, 'OptionPicture': 'JAVELIN'})
    o_n = g.add('OptionsJson', O[245], {'ModificationId': mod, 'Name': 'PLA loadout HJ-10 NLOS', 'UIName': 'HJ-10 NLOS (laser, 2000 m)', 'Order': 1, 'Cost': 20, 'Turret1Id': 2009620, 'OptionPicture': 'HELLFIRE_X4'})
    ok(A[fnf]['Seeker'] == 50 and A[fnf]['LaserGuided'] is False and A[fnf]['TrajectoryType'] == 200 and A[fnf]['OverpressureRadius'] == 5.0 and A[fnf]['CanBeIntercepted'] is False
       and A[2009623]['LaserGuided'] is True and A[2009623]['GroundRange'] == 2000.0 and A[2009623]['Damage'] == A[fnf]['Damage'] == 11.0
       and A[2009623]['PenetrationAtGroundRange'] == A[fnf]['PenetrationAtGroundRange'] == 140.0, 'HJ-10 FNF / NLOS rounds')
    ok(sorted((r['TurretId'], r['Order']) for r in hj()) == sorted([(2009620, 1), (ft, 1)]) and T[ft]['IsDefault'] is True and T[2009620]['IsDefault'] is False
       and (W[fw]['AimTimeMin'], W[fw]['AimTimeMax'], W[HJ10_LAUNCHER]['AimTimeMin']) == (3.0, 4.0, 0.2)
       and sorted((O[o]['Cost'], O[o]['Turret1Id']) for o in (o_f, o_n)) == sorted([(0, ft), (20, 2009620)]), 'HJ-10 loadout: FNF default, NLOS +20')
    rec['hj10_modes'] = {'fnf': {'round': fnf, 'weapon': fw, 'turret': ft, 'option': o_f}, 'nlos': {'round': 2009623, 'weapon': HJ10_LAUNCHER, 'turret': 2009620, 'option': o_n, 'cost': 20}, 'stats': STATS}
    rec['nlos_cruise_fix'] = {'launch_margin_180': ROUNDS, 'hj10_launcher': {'id': HJ10_LAUNCHER, 'before': {'Type': 81, 'IsVerticalLauncher': False}, 'after': new}}

"""KF-21 Block 1 and XQ-58A Valkyrie cards for the C5 models (Osama 23 Nov 2026, thread "blue dragons"). 0.9.6 model rework TEST build only.
- KF-21 Block 1: full copy of KF-21 Boramae (1290) WITH its 5 option slots, same price and cards (Blue Dragon, spec 23). Osama 03:3x: "don't replace the
  current KF-21 by the way, the other one is the Block 1 for now". FAModels draws the C5 model (models.json key = NAME); Boramae keeps m_kf21.
- XQ-58A: Osama 02:1x "we're adding the XQ-58 as a FH-97A clone same price just replace the munitions with US equivalents"; 04:2x "just add them to the
  model build". Copy of PLA FH-97A (1253): same body, price (185), cards (2) and option prices; each PLA pylon gets an own US copy whose weapon is a copy of
  the US launcher (MagazineSize as the PLA launcher) firing the US round. The PLA rows are stat clones of US rows: LS-6 500kg / LT-2 = GBU-55 1000lb,
  LS-6 1000kg = GBU-56 2000lb, PL-15C = AMRAAM; PL-12 -> AMRAAM (PLA damage 17, US 16); PL-15 / PL-16 -> AIM-260 JATM (the US next-generation long-range
  missile: range 5500 vs 4500). Spec Air Naval (5; was USMC 3 until Osama 04:3x "XQ-58A goes to Air tab for Air naval"). Card art: X-47B (no XQ-58 art yet)."""
KF, XQ = 'KF-21 Block 1', 'US XQ-58A Valkyrie'
# PLA weapon -> (US launcher to copy, US round, label)
XQ_W = {2018505: (231, 89, 'AMRAAM'), 2018510: (675, 531, 'AIM-260 JATM'), 2018528: (231, 89, 'AMRAAM'), 2018539: (675, 531, 'AIM-260 JATM'),
        2018516: (376, 290, 'GBU-55 LJDAM 1000lb'), 2018523: (376, 290, 'GBU-55 LJDAM 1000lb'), 2018483: (377, 291, 'GBU-56 LJDAM 2000lb')}
XQ_OPT = {31029: ('Light CAP (2x AIM-120 AMRAAM)', 'AMRAAM_MISSILE'), 31030: ('Light CAP (2x AIM-260 JATM)', 'JATM'),
          31031: ('Light strike (2x GBU-55 LJDAM 1000lb)', 'GBU55'), 31032: ('Light strike (4x GBU-55 LJDAM 1000lb)', 'GBU55'),
          31033: ('Heavy CAP (AIM-120 AMRAAM)', 'AMRAAM_MISSILE'), 31034: ('Heavy CAP (3x AIM-260 JATM)', 'JATM'),
          31037: ('Light strike (2x GBU-56 LJDAM 2000lb)', 'GBU56')}


def apply(t, g, ok, rec):
    U, S, SA, A, W, T, O = t['Units'], t['SpecializationsJson'], t['SpecializationAvailabilitiesJson'], t['AmmunitionsJson'], t['WeaponsJson'], t['TurretsJson'], t['OptionsJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    def copy_unit(parent, name, extra):
        ok(not any(u and name in (u.get('Name'), u.get('HUDName')) for u in U.values()), name + ' name free')
        d = dict(U[parent]); d.pop('Id'); d.update({'Name': name, 'OriginalCost': 0, 'DisplayInArmory': True, **extra})
        uid = g.put('Units', max(U) + 1, d)
        for tab, field, target in (('UnitArmorsJson', 'ArmorId', 'ArmorsJson'), ('UnitPropulsionsJson', 'MobilityId', 'MobilityJson')):
            for r in rows(tab, UnitId=parent):
                g.add(tab, r, {'UnitId': uid, field: g.add(target, t[target][r[field]], {'Name': f'{t[target][r[field]]["Name"]} {name}'})})
        for tab in ('UnitAbilitiesJson', 'SensorUnitsJson'):
            for r in rows(tab, UnitId=parent): g.add(tab, r, {'UnitId': uid})
        return uid

    # KF-21 Block 1 = KF-21 Boramae with all rows (turrets/options shared with the parent, as france_preview.py)
    ok(U[1290]['Name'] == 'KF-21 Boramae' and U[1290]['CountryId'] == 2, 'KF-21 Boramae is 1290')
    kf = copy_unit(1290, KF, {'HUDName': KF})
    for tab in ('TurretUnitsJson', 'WeaponAmmunitionsJson'):
        for r in rows(tab, UnitId=1290): g.add(tab, r, {'UnitId': kf})
    for m in rows('ModificationsJson', UnitId=1290):
        nm = g.add('ModificationsJson', m, {'UnitId': kf})
        for o in rows('OptionsJson', ModificationId=m['Id']): g.add('OptionsJson', o, {'ModificationId': nm})
    for r in rows('SpecializationAvailabilitiesJson', UnitId=1290): g.add('SpecializationAvailabilitiesJson', r, {'UnitId': kf})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitArmorsJson', 'UnitPropulsionsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson', 'ModificationsJson', 'SpecializationAvailabilitiesJson'):
        ok(len(rows(tab, UnitId=kf)) == len(rows(tab, UnitId=1290)), (KF, tab, 'copied'))
    ok(sum(len(rows('OptionsJson', ModificationId=m['Id'])) for m in rows('ModificationsJson', UnitId=kf)) == 21, 'KF-21 Block 1: 21 options')

    # XQ-58A = FH-97A with US pylons
    ok(U[1253]['Name'] == 'PLA FH-97A' and S[5]['UIName'] == 'Air Naval' and S[5]['CountryId'] == 2 and U[969]['Name'] == 'X-47B', 'FH-97A 1253, Air Naval spec 5, X-47B art')
    xq = copy_unit(1253, XQ, {'HUDName': 'XQ-58A Valkyrie', 'CountryId': 2, 'ThumbnailFileName': U[969]['ThumbnailFileName'], 'PortraitFileName': U[969]['PortraitFileName']})
    wmap, tmap = {}, {160: 160}
    for wa in rows('WeaponAmmunitionsJson', UnitId=1253):
        pw = wa['WeaponId']; uw, ua, lab = XQ_W[pw]; n = wa['Quantity']
        ok(A[ua]['HUDName'] and W[uw]['HUDName'] and W[uw]['Type'] == W[pw]['Type'], ('US launcher and round', pw, uw, ua))
        wmap[pw] = g.add('WeaponsJson', W[uw], {'Name': f'US air XQ-58 {lab} x{n}', 'MagazineSize': W[pw]['MagazineSize']})
        g.add('WeaponAmmunitionsJson', wa, {'UnitId': xq, 'WeaponId': wmap[pw], 'AmmunitionId': ua})
    for tu in rows('TurretUnitsJson', UnitId=1253):
        tid = tu['TurretId']
        if tid not in tmap:
            (tw,) = rows('TurretWeaponsJson', TurretId=tid)
            tmap[tid] = g.add('TurretsJson', T[tid], {'Name': T[tid]['Name'].replace('PLA air pylon', 'US air pylon XQ-58')})
            g.add('TurretWeaponsJson', tw, {'TurretId': tmap[tid], 'WeaponId': wmap[tw['WeaponId']]})
        g.add('TurretUnitsJson', tu, {'UnitId': xq, 'TurretId': tmap[tid]})
    for m in rows('ModificationsJson', UnitId=1253):
        nm = g.add('ModificationsJson', m, {'UnitId': xq})
        for o in rows('OptionsJson', ModificationId=m['Id']):
            ui, pic = XQ_OPT[o['Id']]
            g.add('OptionsJson', o, {'ModificationId': nm, 'Name': o['Name'].replace('PLA loadout FH-97A', 'US loadout XQ-58'), 'UIName': ui, 'OptionPicture': pic,
                                     'Turret0Id': tmap[o['Turret0Id']], 'Turret1Id': tmap[o['Turret1Id']]})
    (tpl,) = rows('SpecializationAvailabilitiesJson', UnitId=1253)
    g.add('SpecializationAvailabilitiesJson', tpl, {'UnitId': xq, 'SpecializationId': 5})   # Osama 23 Nov 04:3x: "XQ-58A goes to Air tab for Air naval"
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitArmorsJson', 'UnitPropulsionsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson', 'ModificationsJson'):
        ok(len(rows(tab, UnitId=xq)) == len(rows(tab, UnitId=1253)), (XQ, tab, 'copied'))
    xo = [o for m in rows('ModificationsJson', UnitId=xq) for o in rows('OptionsJson', ModificationId=m['Id'])]
    po = [o for m in rows('ModificationsJson', UnitId=1253) for o in rows('OptionsJson', ModificationId=m['Id'])]
    ok([o['Cost'] for o in xo] == [o['Cost'] for o in po] and U[xq]['Cost'] == U[1253]['Cost'] == 185, 'XQ-58 price and option prices = FH-97A')
    us_rounds = {wa['AmmunitionId'] for wa in rows('WeaponAmmunitionsJson', UnitId=xq)}
    ok(us_rounds == {89, 531, 290, 291}, ('XQ-58 fires only US rounds', us_rounds))
    ok(all(T[tmap[o['Turret0Id']]]['Name'].startswith(('US air pylon', 'Turret Empty')) for o in po), 'XQ-58 options use US pylons')
    rec['c5_cards'] = {'kf21_block1': {'unit': kf, 'parent': 1290, 'cost': U[kf]['Cost'], 'spec': 23},
                       'xq58': {'unit': xq, 'parent': 1253, 'cost': 185, 'spec': 3, 'weapons': {str(k): v for k, v in wmap.items()},
                                'turrets': {str(k): v for k, v in tmap.items()}, 'options': [(o['UIName'], o['Cost']) for o in xo]}}

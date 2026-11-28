"""Osama 27 Nov 2026 21:4x PST, thread 1567745029781454889: "WZ-551 shows up as a transport option" / "zsl-92B has two autocannons" / "no remove the
wz-551 it's the ZSL-92B" / "ZSL-92B is an option for the ZSL-92 base." / "so the zsl-92 is the base model and the 92b is the weapons package".
- ZSL-92 (1232, 25 pts, QJC-88 12.7 mm) gets a weapons-package loadout (Leopard 2A8 'Custom_Slot_Weapon_package' pattern, as ZSL-92B 1079):
  QJC-88 12.7 mm (default, +0); 'ZSL-92B 30 mm' (+10 = 35, the ZSL-92B price) = the ZSL-92B 30 mm tower with its Type 86 coax on point 1;
  'ZSL-92B 30 mm + 4x HJ-73D' (+20 = 45, the ZSL-92B ATGM price) = the ZSL-92B HJ-73D tower (30 mm 0, HJ-73D 2) with the Type 86 on point 1.
  Weapon points 0/1/2 on the RU_BTR82A slot-0 tower, as vanilla's BTR-82AT (2A72 0, PKT 1, Konkurs 2). The ZSL-92B's own ammunition counts.
- The WZ-551 (962) and the separate ZSL-92B (1079) come off every transport list; the ZSL-92 stays (it was on the same 7 Light CAB cards).
- Unit 1079 keeps only its hidden test card. Runs in the plb scope, after zsl92b_atgm_1127 (its towers are reused). Not yet tested in a game."""
ZSL92, ZSL92B, WZ551, TYPE86 = 1232, 1079, 962, None


def apply(t, g, ok, rec):
    U, W, T, O, MO, TA = t['Units'], t['WeaponsJson'], t['TurretsJson'], t['OptionsJson'], t['ModificationsJson'], t['TransportAvailabilitiesJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    lay = lambda tid: [(x['Order'], W[x['WeaponId']]['HUDName']) for x in rows('TurretWeaponsJson', TurretId=tid)]
    ok(U[ZSL92]['HUDName'] == 'ZSL-92' and U[ZSL92B]['HUDName'] == 'ZSL-92B' and U[WZ551]['HUDName'] == 'WZ-551', 'units')
    ok(U[ZSL92]['ModelFileName'] == U[ZSL92B]['ModelFileName'] == 'RU_BTR82A' and U[ZSL92]['Cost'] == 25 and not rows('ModificationsJson', UnitId=ZSL92), 'ZSL-92 25 pts, same body, no loadouts yet')
    base_tu = rows('TurretUnitsJson', UnitId=ZSL92); ok([r['Order'] for r in base_tu] == [0] and lay(base_tu[0]['TurretId']) == [(0, 'QJC-88 12.7 mm')], ('ZSL-92 one HMG tower', lay(base_tu[0]['TurretId'])))
    b_tu = rows('TurretUnitsJson', UnitId=ZSL92B)
    m0, m1, atgm = b_tu[0]['TurretId'], b_tu[1]['TurretId'], b_tu[2]['TurretId']
    ok(lay(m0) == [(0, '30 mm autocannon')] and lay(m1) == [(1, 'Type 86 7.62 mm')] and lay(atgm) == [(0, '30 mm autocannon'), (2, 'HJ-73D')], ('ZSL-92B towers', lay(m0), lay(m1), lay(atgm)))
    coax = rows('TurretWeaponsJson', TurretId=m1)[0]
    towers = {}
    for key, src, name in (('30', m0, 'PLA ZSL-92 package 30 mm'), ('atgm', atgm, 'PLA ZSL-92 package 30 mm HJ-73D')):
        nt = g.add('TurretsJson', T[src], {'Name': name})
        for x in rows('TurretWeaponsJson', TurretId=src): g.add('TurretWeaponsJson', x, {'TurretId': nt})
        g.add('TurretWeaponsJson', coax, {'TurretId': nt})
        g.add('TurretUnitsJson', base_tu[0], {'TurretId': nt})
        towers[key] = nt
    for r in rows('WeaponAmmunitionsJson', UnitId=ZSL92B): g.add('WeaponAmmunitionsJson', r, {'UnitId': ZSL92})
    nm = g.add('ModificationsJson', MO[594], {'UnitId': ZSL92, 'Name': 'Weapons ZSL-92'})
    ob = g.add('OptionsJson', O[2118], {'ModificationId': nm, 'Name': 'MainTurret ZSL-92 QJC-88', 'UIName': 'QJC-88 12.7 mm', 'Turret0Id': base_tu[0]['TurretId'], 'Cost': 0, 'IsDefault': True})
    o30 = g.add('OptionsJson', O[2118], {'ModificationId': nm, 'Name': 'MainTurret ZSL-92 ZSL-92B', 'UIName': 'ZSL-92B 30 mm', 'Turret0Id': towers['30'], 'Cost': 10, 'IsDefault': False})
    oat = g.add('OptionsJson', O[2119], {'ModificationId': nm, 'Name': 'MainTurret ZSL-92 ZSL-92B HJ-73D', 'UIName': 'ZSL-92B 30 mm + 4x HJ-73D', 'OptionPicture': 'KONKURS_VEHICAL',
                                         'Turret0Id': towers['atgm'], 'Cost': 20, 'IsDefault': False})
    ok(all(0 < o <= 32767 for o in (ob, o30, oat)), ('option ids fit the network short', ob, o30, oat))
    gone = []
    for k, r in list(TA.items()):
        if r and r.get('UnitId') in (WZ551, ZSL92B):
            gone.append((U[r['UnitId']]['HUDName'], U[t['SpecializationAvailabilitiesJson'][r['SpecializationAvailabilityId']]['UnitId']]['HUDName'])); g.remove('TransportAvailabilitiesJson', k)
    ok(not [r for r in t['TransportAvailabilitiesJson'].values() if r and r.get('UnitId') in (WZ551, ZSL92B)], 'no WZ-551 / ZSL-92B transport rows left')
    left = sorted(U[t['SpecializationAvailabilitiesJson'][r['SpecializationAvailabilityId']]['UnitId']]['HUDName'] for r in rows('TransportAvailabilitiesJson', UnitId=ZSL92))
    rec['osama_zsl92_package_1127'] = {'loadouts': {'QJC-88': 0, 'ZSL-92B 30 mm': [10, lay(towers['30'])], 'ZSL-92B 30 mm + 4x HJ-73D': [20, lay(towers['atgm'])]},
                                       'removed_transport_rows': gone, 'zsl92_transport_on': left}
    print('ZSL-92 PACKAGE', rec['osama_zsl92_package_1127'])

"""US recon helicopters (Lateralus 23 Nov 2026 17:3x-18:3x PST, thread 1572962048705429598).
17:3x "change all the new recon helicopters that Osama created, so that they no longer have any cargo capacity (other than infantry slots) ...
either finding existing suitable instances that match ... Only make new instances as a last resort ... Start with just the USA".
18:3x "remove the OH-58D Recon Optronic ... keep the OH-58D Recon's current optics, and give it the port/starboard pylon options that the Recon
Optronic had, but do not give it sensor loadout options. Make the new OH-58D Recon a shared unit between Air Naval and Armored Brigade. keep the
UH-1Y Venom's current optics. keep the Dauphin Recon's current optics. RAH-66 Comanche Recon can keep its radar built in. remove the MH-6 Little
Bird Recon ... remove the AH-64D Longbow Recon".
- Hidden (rows kept; out of every spec, DisplayInArmory False; list in docs/roster/hidden-units.md): OH-58D Recon Optronic 733,
  MH-6 Little Bird Recon 736, AH-64D Longbow Recon 746.
- OH-58D Recon 734 (same unit row as 733 apart from name and cost): the Optronic's port and starboard pylons - GAU-21 (+0) or 7x Hydra (+5) each,
  turrets 485 / 162 / 723 with their ammunition - as its own modification and option rows (option rows belong to one unit). No sensor slot,
  optics unchanged (Very Good), cost 55, no laser. Specs: Air Naval (5, as before) and Armored Brigade (4), 4 cards each.
- Cargo 0, seats unchanged:
  - MH-60M SOAR Recon 735: mobility 28 'Heli UH60M Supply' (4000, shared with the UH-60M cards) -> vanilla 217 'Heli UH60M' (0; same fields).
  - AS-365 Dauphin Recon 738: 258 'Heli AS365' (1500, shared with the AS-365 Dauphin) -> 2018990 (0; the AS365 row without cargo, used by the Z-19s).
  - UH-1Y Venom Recon 732: 57 'Heli UH1Y' (2500, shared with the vanilla UH-1Y) has no 0-cargo twin -> new row, a copy of 57 with
    HeavyLiftWeight 0 (last resort; the nearest 0-cargo row, 34 AH1Z, is faster: 300 vs 290).
- Unchanged: optics of every recon card, the RAH-66 Comanche Recon's built-in radar, MH-60M SOAR Recon and AH-1Z Viper Recon.
"""
HIDE = {733: 'OH-58D Recon Optronic', 736: 'MH-6 Little Bird Recon', 746: 'AH-64D Longbow Recon'}
OPT_SRC, RECON = 733, 734
AIR_NAVAL, ARMORED = 5, 4
PYLON_MODS = (2001030, 2001033)
SAME = lambda a, b: {k for k in set(a) | set(b) if k not in ('Id', 'Name', 'HeavyLiftWeight') and a.get(k) != b.get(k)}


def apply(t, g, ok, rec):
    U, S, SA, TA, M, O, TU, WA, UP, SU, MB = (t[k] for k in ('Units', 'SpecializationsJson', 'SpecializationAvailabilitiesJson', 'TransportAvailabilitiesJson',
        'ModificationsJson', 'OptionsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson', 'UnitPropulsionsJson', 'SensorUnitsJson', 'MobilityJson'))
    ok(all(U[i]['HUDName'] == h and U[i]['CountryId'] == 2 for i, h in HIDE.items()), ('US recon cards to hide', {i: U[i]['HUDName'] for i in HIDE}))
    ok((S[AIR_NAVAL]['UIName'], S[ARMORED]['Name']) == ('Air Naval', 'Armored Brigade'), 'spec 5 = Air Naval, 4 = Armored Brigade')
    sensors = {u: sorted(r['SensorId'] for r in SU.values() if r and r['UnitId'] == u) for u in (732, 734, 735, 737, 738, 745)}
    # 734 has the same unit row as 733 (model, armour, mobility) apart from name and cost
    diff = {k for k in set(U[OPT_SRC]) | set(U[RECON]) if U[OPT_SRC].get(k) != U[RECON].get(k)}
    ok(diff == {'Id', 'Name', 'HUDName', 'Cost'} and U[RECON]['Cost'] == 55, ('734 = 733 apart from name and cost', diff))
    # 1. hide three cards (the roster_1123b.py method)
    hidden = {}
    for uid, hud in HIDE.items():
        rows = [r['Id'] for r in SA.values() if r and r['UnitId'] == uid]
        links = [r['Id'] for r in TA.values() if r and (r['UnitId'] == uid or r['SpecializationAvailabilityId'] in rows)]
        for i in links: g.remove('TransportAvailabilitiesJson', i)
        for i in rows: g.remove('SpecializationAvailabilitiesJson', i)
        g.put('Units', uid, {'DisplayInArmory': False})
        hidden[hud] = {'unit': uid, 'spec_rows': rows, 'transport_links': links}
    ok(not any(r and r['UnitId'] in HIDE for r in SA.values()) and all(U[i]['DisplayInArmory'] is False for i in HIDE), 'hidden: no spec, not in the Armory')
    # 2. OH-58D Recon: the Optronic's pylons, no sensor slot
    ok(not g.rows('ModificationsJson', RECON) and not g.rows('TurretUnitsJson', RECON) and not g.rows('WeaponAmmunitionsJson', RECON), '734 has no weapons or options yet')
    tus = g.rows('TurretUnitsJson', OPT_SRC)
    was = g.rows('WeaponAmmunitionsJson', OPT_SRC)
    ok(sorted(r['TurretId'] for r in tus) == [162, 485, 723] and sorted((r['WeaponId'], r['Quantity']) for r in was) == [(109, 7), (547, 7), (661, 200)],
       ('733 pylon turrets and ammo', [r['TurretId'] for r in tus], [(r['WeaponId'], r['Quantity']) for r in was]))
    for r in tus: g.add('TurretUnitsJson', r, {'UnitId': RECON})
    for r in was: g.add('WeaponAmmunitionsJson', r, {'UnitId': RECON})
    new_opts = {}
    for mid in PYLON_MODS:
        m = M[mid]
        ok(m['UnitId'] == OPT_SRC and m['Type'] == 3, (mid, 'a 733 weapon slot'))
        nm = g.add('ModificationsJson', m, {'UnitId': RECON})
        for o in sorted((o for o in O.values() if o and o.get('ModificationId') == mid), key=lambda o: o['Id']):
            new_opts[g.add('OptionsJson', o, {'ModificationId': nm})] = (o['UIName'], o['Cost'])
    ok(sorted(new_opts.values()) == sorted([('Custom_Option_GAU21_HMG', 0), ('Custom_Option_7xHydra', 5)] * 2), ('734 pylon options', new_opts))
    ok(not any(M[m]['Type'] == 4 for m in [r['Id'] for r in g.rows('ModificationsJson', RECON)]), '734 has no sensor slot')
    ok(sorted(r['SensorId'] for r in SU.values() if r and r['UnitId'] == RECON) == [3], '734 keeps Very Good optics only')
    sa = [r for r in SA.values() if r and r['UnitId'] == RECON]
    ok([r['SpecializationId'] for r in sa] == [AIR_NAVAL] and sa[0]['MaxAvailabilityXp0'] == 4, ('734 in Air Naval, 4 cards', sa))
    arm = g.add('SpecializationAvailabilitiesJson', sa[0], {'SpecializationId': ARMORED})
    ok(sorted(r['SpecializationId'] for r in SA.values() if r and r['UnitId'] == RECON) == [ARMORED, AIR_NAVAL], '734 shared: Air Naval and Armored Brigade')
    # 3. cargo 0 (seats unchanged)
    def prop(uid):
        rows = [r for r in UP.values() if r and r['UnitId'] == uid]
        ok(len(rows) == 1, (uid, 'one propulsion row', rows)); return rows[0]
    ok(not SAME(MB[28], MB[217]) and MB[217]['HeavyLiftWeight'] == 0 and MB[28]['HeavyLiftWeight'] == 4000, '217 = 28 without cargo')
    ok(not SAME(MB[258], MB[2018990]) and MB[2018990]['HeavyLiftWeight'] == 0 and MB[258]['HeavyLiftWeight'] == 1500, '2018990 = 258 without cargo')
    ok(not [m for m in MB.values() if m and m.get('HeavyLiftWeight') == 0 and not SAME(MB[57], m)], 'no 0-cargo twin of 57 exists')
    cargo = {}
    for uid, old, new in ((735, 28, 217), (738, 258, 2018990), (732, 57, None)):
        r = prop(uid)
        ok(r['MobilityId'] == old, (uid, 'mobility before', r['MobilityId']))
        if new is None:
            new = g.add('MobilityJson', MB[57], {'Name': 'FA Heli UH1Y no cargo', 'HeavyLiftWeight': 0})
        g.put('UnitPropulsionsJson', r['Id'], {'MobilityId': new})
        ok(not any(o and o.get('MobilityId') for o in O.values() if o and M.get(o.get('ModificationId'), {}).get('UnitId') == uid), (uid, 'no option changes mobility'))
        cargo[U[uid]['HUDName']] = {'unit': uid, 'mobility': [old, new], 'cargo': [MB[old]['HeavyLiftWeight'], MB[new]['HeavyLiftWeight']]}
    ok(all(MB[prop(u)['MobilityId']]['HeavyLiftWeight'] == 0 for u in (732, 733, 734, 735, 736, 737, 738, 745, 746)), 'every US recon helicopter: cargo 0')
    ok([r['UnitId'] for r in UP.values() if r and r['MobilityId'] == 57] == [159] and MB[57]['HeavyLiftWeight'] == 2500, 'vanilla UH-1Y keeps 2500')
    ok(sensors == {u: sorted(r['SensorId'] for r in SU.values() if r and r['UnitId'] == u) for u in sensors}, 'recon optics unchanged')
    rec['recon_helis_us_1123'] = {'hidden': hidden, 'oh58d_recon': {'options': new_opts, 'armored_row': arm}, 'cargo': cargo}
    print('RECON HELIS US', rec['recon_helis_us_1123'])

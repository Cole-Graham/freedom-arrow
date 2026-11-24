"""Russian recon helicopters (Lateralus 23 Nov 2026 18:5x PST, thread 1572962048705429598), after recon_helis_us_1123.py.
"Cargo: Go, and use whatever naming style/convention vanilla uses for shared rows (if any) / Ka-60 Razvedchik, keep current optics /
Ka-226T, hide it from the mod / Ka-29 Razvedchik, keep current optics / Mi-8AMTSh Razvedchik, keep current optics / Ka-52K Razvedchik, hide it".
- Hidden (rows kept; out of every spec, DisplayInArmory False; docs/roster/hidden-units.md): Ka-226T Razvedchik 728, Ka-52K Razvedchik 748.
- Cargo 0, seats unchanged:
  - Ka-60 Razvedchik 727: 118 'Heli KA60' (2000, shared with the KA-60) -> the US section's 0-cargo copy of 57 'Heli UH1Y KA60' (same fields as
    118 apart from cargo). Vanilla names a shared row after the airframes it serves ('Heli KA50 52' for the Ka-50 and Ka-52).
  - Mi-8AMTSh Razvedchik 731: 62 'Heli MI8AMTSh' (3000, shared with the Mi-8AMTSh) -> vanilla 401 'Heli MI8AMTSh-VN' (the Sapsan's; same fields, 0).
  - Ka-29 Razvedchik 729: 125 'Heli KA29' (3000, shared with the Ka-29) has no 0-cargo twin -> new row 'Heli KA29 Razvedchik', a copy of 125
    with HeavyLiftWeight 0 (last resort; vanilla names variant rows by the variant, e.g. 'Heli MI8AMTSh-VN').
- Optics of every recon card unchanged. Mi-24K and Mi-28NM Razvedchik unchanged.
"""
HIDE = {728: 'Ka-226T Razvedchik', 748: 'Ka-52K Razvedchik'}
SAME = lambda a, b: {k for k in set(a) | set(b) if k not in ('Id', 'Name', 'HeavyLiftWeight') and a.get(k) != b.get(k)}


def apply(t, g, ok, rec):
    U, SA, TA, M, O, UP, SU, MB = (t[k] for k in ('Units', 'SpecializationAvailabilitiesJson', 'TransportAvailabilitiesJson', 'ModificationsJson',
        'OptionsJson', 'UnitPropulsionsJson', 'SensorUnitsJson', 'MobilityJson'))
    RU = (727, 728, 729, 730, 731, 747, 748)
    ok([U[i]['HUDName'] for i in RU] == ['Ka-60 Razvedchik', 'Ka-226T Razvedchik', 'Ka-29 Razvedchik', 'Mi-24K Razvedchik', 'Mi-8AMTSh Razvedchik',
       'Mi-28NM Razvedchik', 'Ka-52K Razvedchik'] and all(U[i]['CountryId'] == 1 for i in RU), 'Russian recon helicopter cards')
    sensors = {u: sorted(r['SensorId'] for r in SU.values() if r and r['UnitId'] == u) for u in RU}
    hidden = {}
    for uid, hud in HIDE.items():
        rows = [r['Id'] for r in SA.values() if r and r['UnitId'] == uid]
        links = [r['Id'] for r in TA.values() if r and (r['UnitId'] == uid or r['SpecializationAvailabilityId'] in rows)]
        for i in links: g.remove('TransportAvailabilitiesJson', i)
        for i in rows: g.remove('SpecializationAvailabilitiesJson', i)
        g.put('Units', uid, {'DisplayInArmory': False})
        hidden[hud] = {'unit': uid, 'spec_rows': rows, 'transport_links': links}
    ok(not any(r and r['UnitId'] in HIDE for r in SA.values()) and all(U[i]['DisplayInArmory'] is False for i in HIDE), 'hidden: no spec, not in the Armory')
    def prop(uid):
        rows = [r for r in UP.values() if r and r['UnitId'] == uid]
        ok(len(rows) == 1, (uid, 'one propulsion row', rows)); return rows[0]
    uh1y = rec['recon_helis_us_1123']['cargo']['UH-1Y Venom Recon']['mobility'][1]
    ok(MB[uh1y]['Name'] == 'Heli UH1Y KA60' and MB[uh1y]['HeavyLiftWeight'] == 0 and not SAME(MB[118], MB[uh1y]), 'Heli UH1Y KA60 = 118 without cargo')
    ok(not SAME(MB[62], MB[401]) and MB[401]['HeavyLiftWeight'] == 0 and MB[62]['HeavyLiftWeight'] == 3000, '401 = 62 without cargo')
    ok(not [m for m in MB.values() if m and m.get('HeavyLiftWeight') == 0 and not SAME(MB[125], m)], 'no 0-cargo twin of 125 exists')
    cargo = {}
    for uid, old, new in ((727, 118, uh1y), (731, 62, 401), (729, 125, None)):
        r = prop(uid)
        ok(r['MobilityId'] == old and MB[old]['HeavyLiftWeight'] > 0, (uid, 'mobility before', r['MobilityId']))
        if new is None:
            new = g.add('MobilityJson', MB[125], {'Name': 'Heli KA29 Razvedchik', 'HeavyLiftWeight': 0})
        g.put('UnitPropulsionsJson', r['Id'], {'MobilityId': new})
        ok(not any(o.get('MobilityId') for o in O.values() if o and M.get(o.get('ModificationId'), {}).get('UnitId') == uid), (uid, 'no option changes mobility'))
        cargo[U[uid]['HUDName']] = {'unit': uid, 'mobility': [old, new], 'cargo': [MB[old]['HeavyLiftWeight'], MB[new]['HeavyLiftWeight']]}
    ok(all(MB[prop(u)['MobilityId']]['HeavyLiftWeight'] == 0 for u in RU), 'every Russian recon helicopter: cargo 0')
    for vid, mid in ((257, 118), (145, 62), (273, 125)):
        ok(prop(vid)['MobilityId'] == mid and MB[mid]['HeavyLiftWeight'] > 0, (U[vid]['HUDName'], 'keeps its cargo'))
    ok(sensors == {u: sorted(r['SensorId'] for r in SU.values() if r and r['UnitId'] == u) for u in RU}, 'recon optics unchanged')
    rec['recon_helis_ru_1123'] = {'hidden': hidden, 'cargo': cargo}
    print('RECON HELIS RU', rec['recon_helis_ru_1123'])

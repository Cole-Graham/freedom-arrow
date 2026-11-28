"""VU-T10 speed (Osama 27 Nov 17:3x, thread "China cosmetic work": "VU-T10 speed is 60/20"): road 60, cross-country 20. The VU-T10 shared the
ZRZ-100's mobility row (2020655, pla_light_brigade_vut10_para_1126), so it gets its own copy with the new speeds; the ZRZ-100 keeps its row."""
ZRZ_MOB = 2020655


def apply(t, g, ok, rec):
    U, MO = t['Units'], t['MobilityJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    v = [u['Id'] for u in U.values() if u and u.get('Name') == 'PLA VU-T10']
    ok(len(v) == 1, 'one VU-T10 unit');v = v[0]
    pr = rows('UnitPropulsionsJson', UnitId=v)
    ok(len(pr) == 1 and pr[0]['MobilityId'] == ZRZ_MOB, 'VU-T10 on the ZRZ-100 mobility row')
    before = (MO[ZRZ_MOB]['MaxSpeedRoad'], MO[ZRZ_MOB]['MaxCrossCountrySpeed'])
    mo = g.add('MobilityJson', MO[ZRZ_MOB], {'Name': 'Mobility VU-T10', 'MaxSpeedRoad': 60.0, 'MaxCrossCountrySpeed': 20.0})
    g.put('UnitPropulsionsJson', pr[0]['Id'], {'MobilityId': mo})
    ok(MO[mo]['MaxSpeedRoad'] == 60.0 and MO[mo]['MaxCrossCountrySpeed'] == 20.0 and (MO[ZRZ_MOB]['MaxSpeedRoad'], MO[ZRZ_MOB]['MaxCrossCountrySpeed']) == before, 'VU-T10 60/20, ZRZ-100 unchanged')
    rec['osama_vut10_speed_1127'] = {'vut10': v, 'mobility': mo, 'before_road_xc': before, 'after_road_xc': [60.0, 20.0], 'airdrop': MO[mo].get('IsAirDroppable')}

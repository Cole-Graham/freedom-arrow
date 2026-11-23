"""PLARF planes are drones (Osama 23 Nov 2026 00:2x PST, thread 1567745029781454889: "we need to rename all the planes in rocket forces as J-x drone.
We add a drone at the end. In english and chinese localization"). The four planes in the PLARF spec (19), each in no other spec: J-5 (1089),
J-6W (1091), J-7 (1092), J-8D (975). The J-8D stays a manned fighter (Osama 23 Nov 00:5x: "J-8 shouldn't be drone"). Card names follow the China bilingual pattern ("Reservists 预备役"): "J-5 Drone 歼-5无人机". When the
per-language name switch lands, the English half is "J-5 Drone" and the Chinese half "歼-5无人机" (DRONES below). Names only."""

PLARF = 19
DRONES = {1089: ('J-5', '歼-5'), 1091: ('J-6W', '歼-6W'), 1092: ('J-7', '歼-7')}
MANNED = {975: 'J-8D'}


def apply(t, g, ok, rec):
    U, SA = t['Units'], t['SpecializationAvailabilitiesJson']
    planes = sorted(r['UnitId'] for r in SA.values() if r and r.get('SpecializationId') == PLARF and U.get(r['UnitId'], {}).get('Type') == 16)
    ok(planes == sorted([*DRONES, *MANNED]), ('PLARF planes', planes))
    out = {}
    for uid, (en, zh) in DRONES.items():
        ok(U[uid]['HUDName'] == en and {r['SpecializationId'] for r in SA.values() if r and r.get('UnitId') == uid} == {PLARF}, (en, 'PLARF only'))
        g.put('Units', uid, {'HUDName': f'{en} Drone {zh}无人机'})
        out[uid] = U[uid]['HUDName']
    ok(all(U[u]['HUDName'].endswith('无人机') and ' Drone ' in U[u]['HUDName'] for u in DRONES) and all(U[u]['HUDName'] == n for u, n in MANNED.items()), 'PLARF drone names; J-8D unchanged')
    rec['rocket_drones'] = {'names': out, 'en': {u: f'{e} Drone' for u, (e, z) in DRONES.items()}, 'zh': {u: f'{z}无人机' for u, (e, z) in DRONES.items()}}
    print('PLARF DRONES', out)

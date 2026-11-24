"""PLARF planes are drones (Osama 23 Nov 2026 00:2x PST, thread 1567745029781454889: "we need to rename all the planes in rocket forces as J-x drone.
We add a drone at the end. In english and chinese localization"). The four planes in the PLARF spec (19), each in no other spec: J-5 (1089),
J-6W (1091), J-7 (1092), J-8D (975). The J-8D stays a manned fighter (Osama 23 Nov 00:5x: "J-8 shouldn't be drone"); the J-7 is renamed J-7IIH, not a drone (Osama 01:0x: "J-7IIH rename, not drone"). Card names are English only (Osama 24 Nov 01:0x, "what the fuck is this localization?"): "J-5 Drone". The Chinese name (DRONES) is kept
here for when cards get a proven per-language path. Names only."""

PLARF = 19
DRONES = {1089: ('J-5', '歼-5'), 1091: ('J-6W', '歼-6W')}
MANNED = {975: 'J-8D'}
RENAMED = {1092: ('J-7', 'J-7IIH')}


def apply(t, g, ok, rec):
    U, SA = t['Units'], t['SpecializationAvailabilitiesJson']
    planes = sorted(r['UnitId'] for r in SA.values() if r and r.get('SpecializationId') == PLARF and U.get(r['UnitId'], {}).get('Type') == 16)
    ok(planes == sorted([*DRONES, *MANNED, *RENAMED]), ('PLARF planes', planes))
    for uid, (old, new) in RENAMED.items():
        ok(U[uid]['HUDName'] == old and {r['SpecializationId'] for r in SA.values() if r and r.get('UnitId') == uid} == {PLARF}, (old, 'PLARF only'))
        g.put('Units', uid, {'HUDName': new})
    out = {}
    for uid, (en, zh) in DRONES.items():
        ok(U[uid]['HUDName'] == en and {r['SpecializationId'] for r in SA.values() if r and r.get('UnitId') == uid} == {PLARF}, (en, 'PLARF only'))
        g.put('Units', uid, {'HUDName': f'{en} Drone'})
        out[uid] = U[uid]['HUDName']
    ok(all(U[u]['HUDName'] == DRONES[u][0] + ' Drone' for u in DRONES) and all(U[u]['HUDName'] == n for u, n in MANNED.items()) and all(U[u]['HUDName'] == n for u, (o, n) in RENAMED.items()), 'PLARF drone names; J-8D unchanged; J-7 -> J-7IIH')
    rec['rocket_drones'] = {'names': out, 'en': {u: f'{e} Drone' for u, (e, z) in DRONES.items()}, 'zh': {u: f'{z}无人机' for u, (e, z) in DRONES.items()}}
    print('PLARF DRONES', out)

"""Plane high-altitude optics 16,000 -> 14,500 m on the card (Lateralus 27 Nov 2026 10:0x PST, thread 1572962048705429598, "queue it up").
Sensor 6 "Optics Plane Air Superiority": OpticsHighAltitude 8000 -> 7250 raw (card metres = raw x 2). It is the only sensor at 8000 and every
deck unit on it is a plane (63 on 27 Nov: the fighters and multirole jets). Vanilla is 6000 (12,000 m); 8000 came with the 0.9.3 base.
Low-altitude (2000) and ground optics are unchanged. Air spotting (docs/engine/low-altitude-and-air-sight.md 2a): range = optics x stealth x
max(flash, spotted), bounded by the larger of optics and the longest weapon (5500 raw), so the bound becomes 7250. Existing row only."""

SENSOR, OLD, NEW = 6, 8000.0, 7250.0


def apply(t, g, ok, rec):
    S = t['SensorsJson'][SENSOR]
    ok(S['OpticsHighAltitude'] == OLD and S['OpticsLowAltitude'] == 2000.0, ('sensor 6 before', S['OpticsHighAltitude'], S['OpticsLowAltitude']))
    ok(not [s['Id'] for s in t['SensorsJson'].values() if s and s['Id'] != SENSOR and s.get('OpticsHighAltitude') == OLD], 'only sensor 6 at 8000')
    g.put('SensorsJson', SENSOR, {'OpticsHighAltitude': NEW})
    users = sorted({r['UnitId'] for r in t['SensorUnitsJson'].values() if r and r['SensorId'] == SENSOR})
    ok(all(t['Units'][u].get('Type') == 16 for u in users), ('sensor 6 is planes only', [u for u in users if t['Units'][u].get('Type') != 16]))
    rec['plane_high_optics_1127'] = {'sensor': SENSOR, 'high_raw': [OLD, NEW], 'card_m': [OLD * 2, NEW * 2], 'units': len(users)}

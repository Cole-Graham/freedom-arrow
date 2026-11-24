"""HQ-17 hidden (Osama 24 Nov 2026 01:1x PST, thread 1567745029781454889: "Hq-17 remove(hide unit) NOT the HQ-17A").
The card 'HQ-17' (unit 910, 'PLA HQ-17', PLAGF Armored Force spec 18, 4 cards, row 2014502) leaves its only spec and is hidden in the Armory.
The HQ-17A (unit 1049, Motorized) is not changed. Unit, weapon and ammunition rows stay. Recorded in rec['hidden_rows'], so it shows in the
China hidden-units test spec 26 (runs before test_specs_1123.py)."""
HQ17, HQ17A, AVAIL = 910, 1049, 2014502


def apply(t, g, ok, rec):
    U, SA, TA = t['Units'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson']
    ok(U[HQ17]['HUDName'] == 'HQ-17' and U[HQ17]['Name'] == 'PLA HQ-17' and U[HQ17A]['HUDName'] == 'HQ-17A', 'HQ-17 / HQ-17A cards')
    ok([r['Id'] for r in SA.values() if r and r['UnitId'] == HQ17] == [AVAIL] and not any(r and r['UnitId'] == HQ17 for r in TA.values()),
       'HQ-17: one availability row, no transport links')
    a17 = [r['Id'] for r in SA.values() if r and r['UnitId'] == HQ17A]
    rec.setdefault('hidden_rows', {})[HQ17] = ([dict(SA[AVAIL])], [])   # for test_specs_1123.py
    g.remove('SpecializationAvailabilitiesJson', AVAIL)
    g.put('Units', HQ17, {'DisplayInArmory': False})
    ok(not any(r and r['UnitId'] == HQ17 for r in SA.values()) and U[HQ17]['DisplayInArmory'] is False
       and [r['Id'] for r in SA.values() if r and r['UnitId'] == HQ17A] == a17 and a17 and U[HQ17A]['DisplayInArmory'], 'HQ-17 hidden; HQ-17A unchanged')
    rec['hq17_removed'] = {'unit': HQ17, 'availability_removed': AVAIL, 'hq17a_rows': a17}
    print('HQ-17 removed', rec['hq17_removed'])

"""ZTL-191 Recon hidden (Osama 24 Nov 2026 02:1x PST, thread 1567745029781454889: "remove ZTL-191 recon").
The card 'ZTL-191 Recon' (unit 1263, PLAGF Motorized spec 21, 2 cards, row 2018744) leaves its only spec and is hidden in the Armory. The plain
ZTL-191 (unit 1080, Motorized, 6 cards) is not changed. Unit, weapon and ammunition rows stay. Recorded in rec['hidden_rows'], so it shows in the
China hidden-units test spec 26 (runs before test_specs_1123.py)."""
RECON, BASE, AVAIL = 1263, 1080, 2018744


def apply(t, g, ok, rec):
    U, SA, TA = t['Units'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson']
    ok(U[RECON]['HUDName'] == 'ZTL-191 Recon' and U[BASE]['HUDName'] == 'ZTL-191', 'ZTL-191 Recon / ZTL-191 cards')
    ok([r['Id'] for r in SA.values() if r and r['UnitId'] == RECON] == [AVAIL] and not any(r and r['UnitId'] == RECON for r in TA.values()),
       'ZTL-191 Recon: one availability row, no transport links')
    base = [r['Id'] for r in SA.values() if r and r['UnitId'] == BASE]
    rec.setdefault('hidden_rows', {})[RECON] = ([dict(SA[AVAIL])], [])   # for test_specs_1123.py
    g.remove('SpecializationAvailabilitiesJson', AVAIL)
    g.put('Units', RECON, {'DisplayInArmory': False})
    ok(not any(r and r['UnitId'] == RECON for r in SA.values()) and U[RECON]['DisplayInArmory'] is False
       and [r['Id'] for r in SA.values() if r and r['UnitId'] == BASE] == base and base and U[BASE]['DisplayInArmory'], 'ZTL-191 Recon hidden; ZTL-191 unchanged')
    rec['ztl191_recon_removed'] = {'unit': RECON, 'availability_removed': AVAIL, 'ztl191_rows': base}
    print('ZTL-191 Recon removed', rec['ztl191_recon_removed'])

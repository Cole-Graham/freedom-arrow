"""Osama 23 Nov 2026 18:2x-18:3x PST, thread 1567745029781454889:
- "All current QBZ-95 called QBZ-95-1, QBZ-03 reskinned (same stats but new icon and models) as QBZ-95": weapon 2012205 (QBZ-95, 54 soldiers in
  10 squads) is shown as 'QBZ-95-1'; weapon 2019303 (QBZ-03, 9 soldiers of Reservists 1166) is shown as 'QBZ-95' with the QBZ-95 icon. Stats
  unchanged. The QBZ-95 rifle model (w_qbz95) on the Reservists is in the model build (work/model-rework-096/stage.py, infantry-weapons.json).
- "QJZ-89 PLAGF Armored Force removed ... or hidden I mean": the QJZ-89 Team card in Armored Force (1157) is hidden like roster_1123b.py
  (out of its spec and transport lists, DisplayInArmory False, rows kept). The PLARF QJZ-89 Team (1170) stays."""

QBZ95, QBZ03, QJZ89 = 2012205, 2019303, 1157


def apply(t, g, ok, rec):
    U, W, SA, TA = t['Units'], t['WeaponsJson'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson']
    ok((W[QBZ95]['HUDName'], W[QBZ95]['HUDIcon'], W[QBZ03]['HUDName']) == ('QBZ-95', 'FA_PLA_WP_QBZ95', 'QBZ-03'), 'QBZ-95 / QBZ-03 weapons')
    g.put('WeaponsJson', QBZ95, {'HUDName': 'QBZ-95-1'})
    g.put('WeaponsJson', QBZ03, {'HUDName': 'QBZ-95', 'HUDIcon': W[QBZ95]['HUDIcon']})
    ok((W[QBZ95]['HUDName'], W[QBZ03]['HUDName'], W[QBZ03]['HUDIcon']) == ('QBZ-95-1', 'QBZ-95', 'FA_PLA_WP_QBZ95')
       and [w['HUDName'] for w in W.values() if w and w.get('HUDName') == 'QBZ-03'] == [], 'QBZ-95-1 and QBZ-95 (ex QBZ-03) names and icon')
    rows = [r['Id'] for r in SA.values() if r and r['UnitId'] == QJZ89]
    ok(U[QJZ89]['HUDName'] == 'QJZ-89 Team' and len(rows) == 1 and SA[rows[0]]['SpecializationId'] == 18, 'QJZ-89 Team Armored Force card')
    links = [r['Id'] for r in TA.values() if r and (r['UnitId'] == QJZ89 or r['SpecializationAvailabilityId'] in rows)]
    rec.setdefault('hidden_rows', {})[QJZ89] = ([dict(SA[i]) for i in rows], [dict(TA[i]) for i in links])   # for china_test_spec_1123.py
    for i in links: g.remove('TransportAvailabilitiesJson', i)
    for i in rows: g.remove('SpecializationAvailabilitiesJson', i)
    g.put('Units', QJZ89, {'DisplayInArmory': False})
    ok(not any(r and r['UnitId'] == QJZ89 for r in SA.values()) and U[QJZ89]['DisplayInArmory'] is False, 'QJZ-89 Team (Armored) hidden')
    rec['qbz95_qjz89'] = {'qbz95_1': QBZ95, 'qbz95_ex_qbz03': QBZ03, 'qjz89_hidden': {'unit': QJZ89, 'spec_rows': rows, 'transport_links': links}}
    print('QBZ/QJZ', rec['qbz95_qjz89'])

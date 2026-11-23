"""J-10A renamed J-10B (Osama 23 Nov 2026 14:2x PST, thread 1567745029781454889: "Rename J-10A to J-10B"). Card name only (Units.HUDName of 1226).
Units.Name 'PLA J-10A' stays: FAModels models.json keys the model by it. Loadout UINames do not contain the plane name; stats unchanged."""

J10 = 1226


def apply(t, g, ok, rec):
    U = t['Units']
    ok(U[J10]['HUDName'] == 'J-10A' and U[J10]['Name'] == 'PLA J-10A', 'J-10A card')
    ok([i for i, u in U.items() if u and 'J-10A' in (u.get('HUDName') or '')] == [J10], 'one J-10A card')
    g.put('Units', J10, {'HUDName': 'J-10B'})
    ok(U[J10]['HUDName'] == 'J-10B' and U[J10]['Name'] == 'PLA J-10A' and not any(u and 'J-10A' in (u.get('HUDName') or '') for u in U.values()), 'J-10A -> J-10B, model key kept')
    rec['j10b_name'] = {'unit': J10, 'name': ['J-10A', 'J-10B']}
    print('J-10B', rec['j10b_name'])

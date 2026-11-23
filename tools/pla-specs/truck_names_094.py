"""China truck names (Osama 21 Nov 2026 20:57 PST, thread 1572407822849810463, quoting a Chinese player: "4x4型号为SX2121 6x6型号为SX2220 8x8型号为SX2306
10X10型号为SX2553 ... 对应LVSR", "Let's make these recommended changes to the names of the cargo trucks"). Shaanxi series by wheel count of the model
the card shows: SX2220 FAModels model (6x6) on the KamAZ-6560 cards, HEMTT 8x8 on the HMV3 cards, LMTV 4x4 on the SX2190 (1269) card. Only the shown name
(HUDName) changes; the internal Name stays, because FAModels, paint schemes and decks key on it. No China card uses a 10x10 (LVSR) truck, so SX2553 is unused.
PHL-11 (SX2190 chassis rocket launcher) is not a cargo truck and keeps its name. Called from batch_0_9_5b.py."""
NEW = {  # card id: (old shown name, new shown name, model shown)
    912: ('Shaanxi SX2190', 'Shaanxi SX2220', 'm_sx2220 6x6'),
    1231: ('Shaanxi Troop Truck', 'Shaanxi SX2220 Troop Truck', 'm_sx2220 6x6'),
    1235: ('Shaanxi HMV3', 'Shaanxi SX2306', 'US_HEMTT 8x8'),
    1247: ('Shaanxi HMV3 Cargo', 'Shaanxi SX2306 Cargo', 'US_HEMTT 8x8'),
    1269: ('SX2190', 'Shaanxi SX2121', 'US_LMTV 4x4'),
}
def apply(t, g, ok, rec):
    U = t['Units'];out = {}
    for u, (old, new, model) in NEW.items():
        ok((U[u].get('HUDName') or '').strip() == old, ('truck card', u, U[u].get('HUDName')))
        rows = sorted(i for i, r in U.items() if r and (r.get('HUDName') or '').strip() == old and r.get('ModelFileName') == U[u]['ModelFileName']
                      and r.get('CountryId') == U[u].get('CountryId'))
        for r in rows: g.put('Units', r, {'HUDName': new})
        out[u] = {'from': old, 'to': new, 'model': model, 'rows': rows}
    ok(not [r for r in U.values() if r and (r.get('HUDName') or '').strip() in ('Shaanxi HMV3', 'Shaanxi HMV3 Cargo', 'Shaanxi Troop Truck')
            and r.get('CountryId') == U[912].get('CountryId') and r['Id'] not in sum((v['rows'] for v in out.values()), [])], 'no China truck row left on an old name')
    rec['truck_names'] = {str(k): v for k, v in out.items()}

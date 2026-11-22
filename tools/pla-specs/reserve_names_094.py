"""China reserve names (Osama 21 Nov 2026 21:2x PST, thread 1572407822849810463: a Chinese player wrote "这个义务兵我们称之为预备役"; Osama: "yeah we
should update it"). In the PLA 义务兵 are active-duty two-year servicemen, the ordinary rank and file; the cheap low-tier squad is reserve troops, 预备役.
Shown name (HUDName) only; the internal Name stays (decks, FAModels and card art key on it). Called from apply_0_9_4_dev1.py."""
NEW = {1166: ('Conscripts 义务兵', 'Reservists 预备役'), 1213: ('Conscript Recon', 'Reservist Recon')}
def apply(t, g, ok, rec):
    U = t['Units'];out = {}
    for u, (old, new) in NEW.items():
        ok((U[u].get('HUDName') or '').strip() == old, ('reserve card', u, U[u].get('HUDName')))
        rows = sorted(i for i, r in U.items() if r and (r.get('HUDName') or '').strip() == old)
        for r in rows: g.put('Units', r, {'HUDName': new})
        out[str(u)] = {'from': old, 'to': new, 'rows': rows}
    ok(not [r for r in U.values() if r and '义务兵' in (r.get('HUDName') or '') and r['Id'] not in (1166,)], 'no other card shows 义务兵')
    rec['reserve_names'] = out

"""QBZ rounds read 5.8 mm (Osama 23 Nov 2026 22:4x PST, thread 1567745029781454889: "did you make sure all the QBZ weapons were 5.8 not 5.56").
No QBZ round showed 5.56, but these QBZ rounds did not show 5.8: the QBZ-95 (the Reservists' renamed QBZ-03) showed '5.45x39mm', and the QBZ-191,
QBZ-192 and QBZ-97 rounds showed their weapon name. Their own FA rows get HUDName '5.8 mm ammunition', like the QBZ-95-1, QBB-95, QBU-88 and QJB-201
rounds already. Names only; damage, range and the bullet visuals are unchanged."""
WEAPS = ('QBZ-95', 'QBZ-95-1', 'QBZ-191', 'QBZ-192', 'QBZ-97')
NEW = '5.8 mm ammunition'


def apply(t, g, ok, rec):
    U, W, WA, A = t['Units'], t['WeaponsJson'], t['WeaponAmmunitionsJson'], t['AmmunitionsJson']
    rows = [r for r in WA.values() if r and W.get(r['WeaponId']) and W[r['WeaponId']].get('HUDName') in WEAPS and U.get(r['UnitId'], {}).get('CountryId') == 4]
    ammo = sorted({r['AmmunitionId'] for r in rows})
    ok(all(a >= 2000000 for a in ammo), ('QBZ rounds are own FA rows', ammo))
    users = {a: {W[r['WeaponId']]['HUDName'] for r in WA.values() if r and r['AmmunitionId'] == a} for a in ammo}
    ok(all(u <= set(WEAPS) for u in users.values()), ('QBZ rounds used by QBZ rifles only', users))
    before = {a: A[a]['HUDName'] for a in ammo}
    for a in ammo:
        if A[a]['HUDName'] != NEW: g.put('AmmunitionsJson', a, {'HUDName': NEW})
    ok(all(A[a]['HUDName'] == NEW for a in ammo) and not any('5.56' in A[a]['HUDName'] or '5.45' in A[a]['HUDName'] for a in ammo), 'all QBZ rounds read 5.8 mm')
    rec['qbz_58_ammo'] = {a: [before[a], NEW] for a in ammo if before[a] != NEW}
    print('QBZ 5.8', rec['qbz_58_ammo'])

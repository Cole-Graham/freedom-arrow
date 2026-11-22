"""Helicopter launcher layout fixes (Osama 21 Nov 2026 19:1x PST, thread 1567745029781454889: "Z-10 Fire support TY-90's should only have 2 launchers
(but 8 missiles). Several Z-19 Ty-90 loadouts have 1 launcher and 8 missiles, they should have 2 launchers. Please double check and see if there are any
launcher oddities"). Same missile totals; only the number of launchers changes. Called from apply_0_9_4_dev1.py (section 20).
- Z-10 / Z-10U / Z-10K Fire support (AH-1Z body, slots 1-6): TY-90 was 4 single rails (1 each) + 1 turret standing for 2 pylons (4) = 5 launchers.
  Now slots 1 and 2 carry the TY-90 x4 turret (2 launchers x 4 = 8); slots 3, 4 and 6 empty; the rocket pod on slot 5 unchanged.
- Z-21 Heavy anti-armor (8x HJ-10) (AH-64 body, slots 1-4): HJ-10 was 1 launcher x 8, TY-90 3 launchers (2 + 1 + 1). Now HJ-10 x4 on slots 1-2 and
  TY-90 x2 on slots 3-4 (2 + 2 launchers, 8 HJ-10 and 4 TY-90 as before).
The Z-19 / Z-19G / Z-9WA (AS-365 Dauphin body) have only 2 pylons, so 2 TY-90 launchers would push the HJ-8 / FS-90A off the loadout: not changed, asked."""


def apply(t, g, ok, rec):
    O, M, TW, TU, WA, W, U = (t[k] for k in ('OptionsJson', 'ModificationsJson', 'TurretWeaponsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson', 'WeaponsJson', 'Units'))
    EMPTY = 160
    uid_of = lambda o: M[O[o]['ModificationId']]['UnitId']
    wp = lambda tid: [r['WeaponId'] for r in TW.values() if r and r.get('TurretId') == tid]
    q = lambda u, w: [r['Quantity'] for r in WA.values() if r and r.get('UnitId') == u and r.get('WeaponId') == w]
    linked = lambda u, tid: any(r.get('UnitId') == u and r.get('TurretId') == tid for r in TU.values() if r)
    slots = lambda o: [O[o].get(f'Turret{i}Id') for i in range(1, 7)]

    def total(o, name):
        u = uid_of(o); n = 0; k = 0
        for tid in slots(o):
            for w in (wp(tid) if tid and tid != EMPTY else []):
                if W[w]['HUDName'] == name: n += q(u, w)[0]; k += 1
        return n, k
    out = {}
    # Z-10 family Fire support
    for o, ty in ((24496, 2019122), (24503, 2019128), (24509, 2019128), (31089, 2019128)):
        u = uid_of(o); s = slots(o)
        ok(O[o]['UIName'] == 'Fire support' and s[0] == s[1] == s[2] == s[3] == 2017087 and s[5] == ty and wp(2017087) == [2017088]
           and q(u, 2017088) == [1] and len(wp(ty)) == 1 and q(u, wp(ty)[0]) == [4] and linked(u, ty), (o, U[u]['HUDName'], 'Fire support layout', s))
        before = total(o, 'TY-90'); rocket = s[4]
        g.put('OptionsJson', o, {'Turret1Id': ty, 'Turret2Id': ty, 'Turret3Id': EMPTY, 'Turret4Id': EMPTY, 'Turret6Id': EMPTY})
        after = total(o, 'TY-90'); ok(before == (8, 5) and after == (8, 2) and slots(o)[4] == rocket, (o, 'TY-90 8 on 2 launchers', before, after))
        out[f'{U[u]["HUDName"]} ({u}) {o}'] = {'TY-90 missiles/launchers': [list(before), list(after)]}
    # Z-21 Heavy anti-armor (8x HJ-10)
    o = 24643; u = uid_of(o); s = slots(o)
    ok(U[u]['HUDName'] == 'Z-21' and s[:4] == [2017891, 2019155, 2017896, 2017896] and wp(2017898) == [2017899] and q(u, 2017899) == [4]
       and wp(2019155) == [2019153] and q(u, 2019153) == [2] and linked(u, 2017898) and linked(u, 2019155), ('Z-21 Heavy anti-armor layout', s))
    b = (total(o, 'HJ-10'), total(o, 'TY-90'))
    g.put('OptionsJson', o, {'Turret1Id': 2017898, 'Turret2Id': 2017898, 'Turret3Id': 2019155, 'Turret4Id': 2019155})
    a = (total(o, 'HJ-10'), total(o, 'TY-90'))
    ok(b == ((8, 1), (4, 3)) and a == ((8, 2), (4, 2)), ('Z-21 HJ-10 8 on 2, TY-90 4 on 2', b, a))
    out[f'Z-21 ({u}) {o}'] = {'HJ-10': [list(b[0]), list(a[0])], 'TY-90': [list(b[1]), list(a[1])]}
    rec['heli_launchers_094'] = out

"""China machine guns (Lateralus 26 Nov 2026 19:4x PST, thread 1568104480459722894, "queue it up"). After aa_squads_qjy_1126 (its QJY-201 = PKP-N
copy is replaced here).
- QJB-201 (infantry weapon 2011834, round 2011835): damage 2.55 -> 2.40; penetration 17 -> 20 at minimum range and 5 -> 10 at maximum range
  (Lateralus: "Penetration 10 - 20mm"; read as 20 near, 10 far, the PKM / PKP-N / Mk.48 shape).
- QJY-201 (2012411 / 2012412): exact stat copy of the infantry Mk.48 (weapon 531, round 621 '7.62x51mm', T3, 2.7 damage, Close quarter).
- QJY-88 (2021552 / 2021553): exact stat copy of the infantry PKM (weapon 158, round 75 '7.62x54mm': 1.8 damage, no minimum range, Close quarter).
Names, HUD names, icons and 3D models stay the Chinese weapons'. Only the rows above change; no other weapon fires these rounds.
"""
QJB201, QJB201_AMMO = 2011834, 2011835
CLONES = {'QJY-201': (2012411, 2012412, 531, 621, 'Mk.48'), 'QJY-88': (2021552, 2021553, 158, 75, 'PKM')}
KEEP_W = ('Id', 'Name', 'HUDName', 'HUDIcon', 'ModelFileName')
KEEP_A = ('Id', 'Name', 'HUDName')


def apply(t, g, ok, rec):
    W, A = t['WeaponsJson'], t['AmmunitionsJson']
    fired = lambda a: {r['WeaponId'] for r in t['WeaponAmmunitionsJson'].values() if r and r['AmmunitionId'] == a}
    ok(W[QJB201]['HUDName'] == 'QJB-201' and fired(QJB201_AMMO) <= {QJB201}, 'QJB-201 round only on the QJB-201')
    r = A[QJB201_AMMO]
    ok(r['Damage'] == 2.55 and r['PenetrationAtMinRange'] == 17 and r['PenetrationAtGroundRange'] == 5, ('QJB-201 before', r['Damage'], r['PenetrationAtMinRange'], r['PenetrationAtGroundRange']))
    g.put('AmmunitionsJson', QJB201_AMMO, {'Damage': 2.4, 'PenetrationAtMinRange': 20.0, 'PenetrationAtGroundRange': 10.0})
    blank = lambda v: False if isinstance(v, bool) else 0 if isinstance(v, (int, float)) else None
    same = lambda x, y, skip: all(x.get(k) == y.get(k) or (not x.get(k) and not y.get(k)) for k in set(x) | set(y) if k not in skip)
    out = {}
    for name, (w, a, sw, sa, src) in CLONES.items():
        ok(W[w]['HUDName'] == name and W[sw]['HUDName'] == src and fired(a) <= {w} and fired(sa) == {sw}, (name, 'and', src, 'rows'))
        for tab, mine, s, keep in (('WeaponsJson', w, sw, KEEP_W), ('AmmunitionsJson', a, sa, KEEP_A)):
            x, y = t[tab][mine], t[tab][s]
            g.put(tab, mine, {k: y[k] if k in y else blank(x[k]) for k in set(x) | set(y) if k not in keep})
        ok(same(W[w], W[sw], KEEP_W) and same(A[a], A[sa], KEEP_A) and W[w]['HUDName'] == name, (name, '=', src, 'stats'))
        out[name] = f"{src} copy: damage {A[a]['Damage']}, pen {A[a]['PenetrationAtMinRange']}->{A[a]['PenetrationAtGroundRange']}, min range {A[a].get('MinimalRange') or 0}, CQC {bool(W[w].get('CQC'))}"
    rec['china_mg_clones_1126'] = {'QJB-201': 'damage 2.55 -> 2.4, pen 17->5 -> 20->10', **out}
    print('CHINA MG CLONES', rec['china_mg_clones_1126'])

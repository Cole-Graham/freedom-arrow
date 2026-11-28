"""Osama 27 Nov 2026 22:0x PST, thread 1567745029781454889: "Chinese Marines get QMK over QBZ-191" / 22:0x "I only meant hte marine line team
not the weapons teams". The Marines 陆战队 line squad of the PLAN & PLAGF Amphibious CAB (spec 20) gets the QMK instead of its QBZ-191 (2019300, round 2019301, 160 per carrier as every QMK row,
the pla_light_brigade_late3_1126 Tank Hunters swap). The weapons teams (Marine HJ-12 Team, Marine QW-2 Team, Marines PF-98) keep the QBZ-191. Men, special weapons,
death priority, prices and cards unchanged. Put-only (QBZ-191 rows re-pointed, or dropped where the squad already lists the QMK)."""
QMK, QMK_A, SPEC = 2019300, 2019301, 20


def apply(t, g, ok, rec):
    U, W, A, SA = t['Units'], t['WeaponsJson'], t['AmmunitionsJson'], t['SpecializationAvailabilitiesJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok(W[QMK]['HUDName'] == 'QMK' and A[QMK_A]['HUDName'] == 'QMK ammunition', 'QMK weapon + round')
    qbz = {k for k, w in W.items() if w and w.get('HUDName') == 'QBZ-191'}
    spec = {r['UnitId'] for r in SA.values() if r and r.get('SpecializationId') == SPEC}
    units = sorted(u for u in spec if U[u].get('HUDName') == 'Marines 陆战队' and any(m['PrimaryWeaponId'] in qbz or m.get('SpecialWeaponId') in qbz for m in rows('SquadMembersJson', UnitId=u)))
    ok(len(units) == 1, ('Marines line squad with QBZ-191', [U[u]['HUDName'] for u in units]))
    out = {}
    for u in units:
        n = 0
        for m in rows('SquadMembersJson', UnitId=u):
            ch = {f: QMK for f in ('PrimaryWeaponId', 'SpecialWeaponId') if m.get(f) in qbz}
            if ch: g.put('SquadMembersJson', m['Id'], ch); n += 1
        has_sw = bool(rows('SquadWeaponsJson', UnitId=u, WeaponId=QMK)); has_wa = bool(rows('WeaponAmmunitionsJson', UnitId=u, WeaponId=QMK))
        for r in [r for r in rows('SquadWeaponsJson', UnitId=u) if r['WeaponId'] in qbz]:
            if has_sw: g.remove('SquadWeaponsJson', r['Id'])
            else: g.put('SquadWeaponsJson', r['Id'], {'WeaponId': QMK}); has_sw = True
        for r in [r for r in rows('WeaponAmmunitionsJson', UnitId=u) if r['WeaponId'] in qbz]:
            if has_wa: g.remove('WeaponAmmunitionsJson', r['Id'])
            else: g.put('WeaponAmmunitionsJson', r['Id'], {'WeaponId': QMK, 'AmmunitionId': QMK_A, 'Quantity': 160}); has_wa = True
        men = rows('SquadMembersJson', UnitId=u)
        carried = {x for m in men for x in (m['PrimaryWeaponId'], m.get('SpecialWeaponId')) if x}
        ok(not (carried & qbz) and QMK in carried, (U[u]['HUDName'], 'QMK carried, no QBZ-191'))
        ok({r['WeaponId'] for r in rows('SquadWeaponsJson', UnitId=u)} == carried == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=u)}, (U[u]['HUDName'], 'card + ammo = carried'))
        out[U[u]['HUDName']] = {'unit': u, 'men_switched': n, 'qmk_rounds_per_man': [r['Quantity'] for r in rows('WeaponAmmunitionsJson', UnitId=u, WeaponId=QMK)]}
    rec['osama_marines_qmk_1127'] = out
    print('MARINES QMK', out)

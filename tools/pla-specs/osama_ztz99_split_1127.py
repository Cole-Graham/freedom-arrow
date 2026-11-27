"""ZTZ-99 split (Osama 27 Nov 2026 04:2x PST, thread 1572407822849810463: "the ZTZ-99-II which uses our old ZTZ-99 model. ZTZ-99-ii takes the current
ZTZ-99 stats and the current model of the ZTZ-99 gets moved to a new tank called the ZTZ-99G. That one has 700/800 armor and its round is 425-475 and
it is 180 points").
Two parts: apply() inside the plb scope creates the rows (no section may create rows after it); finish(), after the last section that edits
the ZTZ-99 (ztz99_front_1126: front 700/850 -> 750/950), copies the final ZTZ-99 values into them and renames 1083.
- 'PLA Catalogue ZTZ-99' (1083) keeps every stat and is shown as ZTZ-99-II. Model: the old m_ztz99c (model stage, 'PLA Catalogue ZTZ-99' key).
- 'PLA ZTZ-99G' (948, a hidden 21 Nov ZTZ-99 copy; models.json key 'PLA ZTZ-99G' = m_ztz99g, the current ZTZ-99 model): every stat row re-copied
  from 1083 as pla_light_brigade_ztz98_1127.py does, then front armour KE 700 / HEAT 800 (1083: 750 / 950), APFSDS 475 mm at min range and 425 mm at
  max range (1083: 500 / 450) on an own row (no existing 125 mm APFSDS row has those values), 180 pts (1083: 200), the same Armored Force card (spec 18)."""
NAME, Z99, Z99G = 'PLA ZTZ-99G', 1083, 948
KEEP = ('Id', 'Name', 'HUDName', 'OriginalName', 'Description', 'DisplayInArmory', 'OriginalCost')
APFSDS = 2011385


def _rows(t):
    return lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])


def apply(t, g, ok, rec):
    """Rows for the ZTZ-99G, copied from the ZTZ-99 as it is now; values are set again in finish()."""
    U, A = t['Units'], t['AmmunitionsJson'];rows = _rows(t)
    ok(U[Z99]['Name'] == 'PLA Catalogue ZTZ-99' and U[Z99]['HUDName'] == 'ZTZ-99', 'ZTZ-99 is 1083')
    ok(U[Z99G]['Name'] == NAME and U[Z99G]['DisplayInArmory'] is False and not rows('SpecializationAvailabilitiesJson', UnitId=Z99G), 'ZTZ-99G 948 hidden, no card')
    ok(A[APFSDS]['Name'] == 'PLA ZTZ-99 ZPT-98 125 mm APFSDS', 'ZTZ-99 APFSDS row')
    ok(len(rows('UnitArmorsJson', UnitId=Z99G)) == len(rows('UnitArmorsJson', UnitId=Z99)) == 1 and len(rows('UnitPropulsionsJson', UnitId=Z99G)) == len(rows('UnitPropulsionsJson', UnitId=Z99)),
       'ZTZ-99G has its own armour and mobility rows')
    for m in rows('ModificationsJson', UnitId=Z99G):
        for o in rows('OptionsJson', ModificationId=m['Id']): g.remove('OptionsJson', o['Id'])
        g.remove('ModificationsJson', m['Id'])
    ap = g.add('AmmunitionsJson', A[APFSDS], {'Name': 'PLA ZTZ-99G ZPT-98 125 mm APFSDS'})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson'):
        for r in rows(tab, UnitId=Z99G): g.remove(tab, r['Id'])
        for r in rows(tab, UnitId=Z99): g.add(tab, r, {'UnitId': Z99G, **({'AmmunitionId': ap} if tab == 'WeaponAmmunitionsJson' and r['AmmunitionId'] == APFSDS else {})})
    opts = []
    for m in rows('ModificationsJson', UnitId=Z99):
        nm = g.add('ModificationsJson', m, {'UnitId': Z99G})
        for o in rows('OptionsJson', ModificationId=m['Id']):
            oid = g.add('OptionsJson', o, {'ModificationId': nm});opts.append(oid)
            ok(0 < oid <= 32767, ('ZTZ-99G option id fits the network short', oid))
    (card,) = rows('SpecializationAvailabilitiesJson', UnitId=Z99)
    nc = g.add('SpecializationAvailabilitiesJson', card, {'UnitId': Z99G})
    rec['osama_ztz99_split_1127'] = {'ztz99_ii': Z99, 'ztz99g': Z99G, 'apfsds': ap, 'card': nc, 'options': opts}


def finish(t, g, ok, rec):
    """The final ZTZ-99 values into the ZTZ-99G rows, then its own armour, round and price; 1083 renamed."""
    U, A, SA = t['Units'], t['AmmunitionsJson'], t['SpecializationAvailabilitiesJson'];rows = _rows(t);r = rec['osama_ztz99_split_1127'];ap = r['apfsds']
    (arm,) = rows('UnitArmorsJson', UnitId=Z99);za = t['ArmorsJson'][arm['ArmorId']]
    ok((za['KinArmorFront'], za['HeatArmorFront']) == (750, 950) and U[Z99]['Cost'] == 200, ('final ZTZ-99 front 750/950, 200 pts', za['KinArmorFront'], za['HeatArmorFront'], U[Z99]['Cost']))
    ok((A[APFSDS]['PenetrationAtMinRange'], A[APFSDS]['PenetrationAtGroundRange']) == (500, 450), 'ZTZ-99 APFSDS 500/450')
    same = [a for a in A.values() if a and a['Id'] != ap and a.get('PenetrationAtMinRange') == 475 and a.get('PenetrationAtGroundRange') == 425
            and all(a.get(k) == A[APFSDS].get(k) for k in A[APFSDS] if k not in ('Id', 'Name', 'HUDName', 'PenetrationAtMinRange', 'PenetrationAtGroundRange'))]
    ok(not same, ('an existing row already has these values: reuse it', [a['Id'] for a in same]))
    g.put('Units', Z99G, {**{k: v for k, v in U[Z99].items() if k not in KEEP}, 'HUDName': 'ZTZ-99G', 'DisplayInArmory': True, 'OriginalCost': 0, 'Cost': 180})
    for tab, field, target in (('UnitArmorsJson', 'ArmorId', 'ArmorsJson'), ('UnitPropulsionsJson', 'MobilityId', 'MobilityJson')):
        for a, b in zip(rows(tab, UnitId=Z99G), rows(tab, UnitId=Z99)):
            g.put(target, a[field], {k: v for k, v in t[target][b[field]].items() if k not in ('Id', 'Name')})
    (ga,) = rows('UnitArmorsJson', UnitId=Z99G);g.put('ArmorsJson', ga['ArmorId'], {'KinArmorFront': 700, 'HeatArmorFront': 800})
    g.put('AmmunitionsJson', ap, {**{k: v for k, v in A[APFSDS].items() if k not in ('Id', 'Name')}, 'PenetrationAtMinRange': 475, 'PenetrationAtGroundRange': 425})
    g.put('Units', Z99, {'HUDName': 'ZTZ-99-II'})
    # checks: every ZTZ-99G row = the final ZTZ-99's (later sections may not have changed the ZTZ-99's row sets)
    key = lambda u, tab, f: sorted(tuple((ap if (k == 'AmmunitionId' and x[k] == APFSDS) else x[k]) for k in f) for x in rows(tab, UnitId=u))
    for tab, f in (('WeaponAmmunitionsJson', ('WeaponId', 'AmmunitionId', 'Quantity', 'Order')), ('TurretUnitsJson', ('TurretId', 'Order')), ('UnitAbilitiesJson', ('AbilityId',)), ('SensorUnitsJson', ('SensorId',))):
        mine = sorted(tuple(x[k] for k in f) for x in rows(tab, UnitId=Z99G));ok(mine == key(Z99, tab, f), ('ZTZ-99G', tab, '= ZTZ-99'))
    po = [(o['UIName'], o['Cost'], o.get('Turret0Id')) for m in rows('ModificationsJson', UnitId=Z99) for o in rows('OptionsJson', ModificationId=m['Id'])]
    go = [(o['UIName'], o['Cost'], o.get('Turret0Id')) for m in rows('ModificationsJson', UnitId=Z99G) for o in rows('OptionsJson', ModificationId=m['Id'])]
    ok(po == go and len(go) == 3, ('ZTZ-99G options = ZTZ-99', go))
    gr = t['ArmorsJson'][ga['ArmorId']]
    ok((gr['KinArmorFront'], gr['HeatArmorFront']) == (700, 800) and all(gr[k] == za[k] for k in za if k not in ('Id', 'Name', 'KinArmorFront', 'HeatArmorFront')), 'ZTZ-99G front 700/800, rest = ZTZ-99')
    ok((A[ap]['PenetrationAtMinRange'], A[ap]['PenetrationAtGroundRange']) == (475, 425) and (A[APFSDS]['PenetrationAtMinRange'], A[APFSDS]['PenetrationAtGroundRange']) == (500, 450), 'APFSDS 475/425; ZTZ-99-II keeps 500/450')
    ok(all(U[Z99G][k] == U[Z99][k] for k in U[Z99] if k not in KEEP + ('Cost',)) and U[Z99G]['Cost'] == 180 and U[Z99]['HUDName'] == 'ZTZ-99-II' and U[Z99G]['HUDName'] == 'ZTZ-99G', 'unit fields, prices, names')
    r.update(spec=SA[r['card']]['SpecializationId'], cards=SA[r['card']]['MaxAvailabilityXp0'], cost=180, front=(700, 800), apfsds_pen=(475, 425))
    print('ZTZ-99 SPLIT', r)

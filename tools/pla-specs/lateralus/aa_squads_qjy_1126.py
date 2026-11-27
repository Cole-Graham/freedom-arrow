"""Troopers AA, Mech. Riflemen AA and the QJY-201 (Lateralus 26 Nov 2026 18:4x PST, thread 1568104480459722894, "queue it up"). Runs after the
PLA Light Brigade Troopers AA and machine-gun sections, on their result.
- Troopers AA "Standard" (unit 413): the M-25 CDTE comes off. Its carrier keeps his M4A1 (head count and HP unchanged); the M-25 CDTE card row
  and ammo row of unit 413 go. The "Mixed" loadout (unit 706) keeps its M-25 CDTE.
- Troopers AA "Mixed": 55 -> 70 points = option 3334 Cost 0 -> +15 and its swap row 706 Cost 55 -> 70 (swap-row rule, audit_swap_prices.py).
- Mech. Riflemen AA "Standard" (unit 371): 45 -> 40 points; M4A1 x5 -> x4 and M249E3 x1 -> x2 (the plain rifleman at death priority 2 takes the
  M249E3, 400 rounds as the other gunner); FIM-92F Stinger ammunition 5 -> 6. The Mixed loadout (705) stays 50 points, so option 3332 goes
  +5 -> +10.
- QJY-201 (infantry weapon 2012411 and its round 2012412): an exact stat copy of the infantry PKP-N (weapon 125, round 362): Close quarter, no
  minimum range, damage 2.25 -> 2.4. Names, icon and 3D model stay the QJY-201's. Vehicle and helicopter QJY-201 mounts are separate weapons.
"""
TROOPERS_AA, TAA_MIXED_OPT, TAA_MIXED = 413, 3334, 706
MRAA, MRAA_MIXED_OPT, MRAA_MIXED = 371, 3332, 705
M4A1, M249E3, M25, STINGER = 50, 60, 2002020, 65
QJY201, QJY201_AMMO, PKPN, PKPN_AMMO = 2012411, 2012412, 125, 362
KEEP_W = ('Id', 'Name', 'HUDName', 'HUDIcon', 'ModelFileName')
KEEP_A = ('Id', 'Name', 'HUDName')


def apply(t, g, ok, rec):
    U, O, W, A, SM, SW, WA = (t[k] for k in ('Units', 'OptionsJson', 'WeaponsJson', 'AmmunitionsJson', 'SquadMembersJson', 'SquadWeaponsJson', 'WeaponAmmunitionsJson'))
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    men = lambda u: rows('SquadMembersJson', UnitId=u)
    ok(U[TROOPERS_AA]['HUDName'] == U[TAA_MIXED]['HUDName'] == 'Troopers AA' and U[MRAA]['HUDName'] == U[MRAA_MIXED]['HUDName'] == 'Mech. Riflemen AA', 'AA squad rows')
    ok(W[M4A1]['HUDName'] == 'M4A1' and W[M249E3]['HUDName'] == 'M249E3' and W[M25]['HUDName'] == 'M-25 CDTE' and W[STINGER]['HUDName'] == 'FIM-92F Stinger', 'weapon rows')
    ok(W[PKPN]['HUDName'] == 'PKP-N' and A[PKPN_AMMO]['HUDName'] == '7.62x54mm' and W[QJY201]['HUDName'] == 'QJY-201' and A[QJY201_AMMO]['HUDName'] == '7.62 mm ammunition', 'PKP-N / QJY-201 rows')
    # Troopers AA Standard: M-25 CDTE off
    cdte = [r for r in men(TROOPERS_AA) if r.get('SpecialWeaponId') == M25]
    ok(len(cdte) == 1 and cdte[0]['PrimaryWeaponId'] == M4A1, ('Troopers AA Standard: one M4A1 + M-25 CDTE man', len(cdte)))
    plain = [r for r in men(TROOPERS_AA) if r['PrimaryWeaponId'] == M4A1 and not r.get('SpecialWeaponId')]
    g.put('SquadMembersJson', cdte[0]['Id'], {'SpecialWeaponId': plain[0].get('SpecialWeaponId')})
    sw = rows('SquadWeaponsJson', UnitId=TROOPERS_AA, WeaponId=M25); wa = rows('WeaponAmmunitionsJson', UnitId=TROOPERS_AA, WeaponId=M25)
    ok(len(sw) == 1 and len(wa) == 1, ('Troopers AA M-25 CDTE card/ammo rows', len(sw), len(wa)))
    g.remove('SquadWeaponsJson', sw[0]['Id']); g.remove('WeaponAmmunitionsJson', wa[0]['Id'])
    ok(any(r.get('SpecialWeaponId') == M25 for r in men(TAA_MIXED)), 'Mixed loadout keeps its M-25 CDTE')
    # Troopers AA Mixed 55 -> 70
    ok(U[TROOPERS_AA]['Cost'] == 55 and U[TAA_MIXED]['Cost'] == 55 and not O[TAA_MIXED_OPT].get('Cost') and O[TAA_MIXED_OPT]['ReplaceUnitId'] == TAA_MIXED, 'Troopers AA prices before')
    g.put('OptionsJson', TAA_MIXED_OPT, {'Cost': 15}); g.put('Units', TAA_MIXED, {'Cost': 70})
    # Mech. Riflemen AA Standard
    ok(U[MRAA]['Cost'] == 45 and U[MRAA_MIXED]['Cost'] == 50 and O[MRAA_MIXED_OPT].get('Cost') == 5 and O[MRAA_MIXED_OPT]['ReplaceUnitId'] == MRAA_MIXED, 'Mech. Riflemen AA prices before')
    g.put('Units', MRAA, {'Cost': 40}); g.put('OptionsJson', MRAA_MIXED_OPT, {'Cost': 10})
    m = men(MRAA)
    ok(sum(r['PrimaryWeaponId'] == M4A1 for r in m) == 5 and sum(r['PrimaryWeaponId'] == M249E3 for r in m) == 1, 'Mech. Riflemen AA: 5 M4A1, 1 M249E3')
    gunner = [r for r in m if r['PrimaryWeaponId'] == M4A1 and not r.get('SpecialWeaponId') and r['DeathPriority'] == 2]
    ok(len(gunner) == 1, ('plain M4A1 rifleman at priority 2', len(gunner)))
    g.put('SquadMembersJson', gunner[0]['Id'], {'PrimaryWeaponId': M249E3})
    st = rows('WeaponAmmunitionsJson', UnitId=MRAA, WeaponId=STINGER)
    ok(len(st) == 1 and st[0]['Quantity'] == 5, ('Mech. Riflemen AA Stinger ammo 5', st))
    g.put('WeaponAmmunitionsJson', st[0]['Id'], {'Quantity': 6})
    # QJY-201 = PKP-N stats
    users = {(r['UnitId'], r['WeaponId']) for r in rows('WeaponAmmunitionsJson', AmmunitionId=QJY201_AMMO)}
    # no squad carries it yet at this point: the Tiger Brigade (plb block, below) is made later and links it
    ok({w for _, w in users} <= {QJY201}, ('round 2012412 only on the QJY-201', sorted(users), [(w, W[w].get('Name')) for _, w in users]))
    blank = lambda v: False if isinstance(v, bool) else 0 if isinstance(v, (int, float)) else None
    for tab, mine, src, keep in (('WeaponsJson', QJY201, PKPN, KEEP_W), ('AmmunitionsJson', QJY201_AMMO, PKPN_AMMO, KEEP_A)):
        a, b = t[tab][mine], t[tab][src]
        g.put(tab, mine, {k: b[k] if k in b else blank(a[k]) for k in set(a) | set(b) if k not in keep})
    same = lambda x, y, skip: all(x.get(k) == y.get(k) or (not x.get(k) and not y.get(k)) for k in set(x) | set(y) if k not in skip)
    ok(same(W[QJY201], W[PKPN], KEEP_W) and same(A[QJY201_AMMO], A[PKPN_AMMO], KEEP_A), 'QJY-201 = PKP-N stats')
    ok(W[QJY201]['HUDName'] == 'QJY-201' and A[QJY201_AMMO]['HUDName'] == '7.62 mm ammunition', 'QJY-201 keeps its names')
    # checks after
    for u in (TROOPERS_AA, MRAA):
        carried = {w for r in men(u) for w in (r['PrimaryWeaponId'], r.get('SpecialWeaponId')) if w}
        ok(M25 not in carried if u == TROOPERS_AA else True, 'no M-25 CDTE on Troopers AA Standard')
        ok(carried <= {r['WeaponId'] for r in rows('SquadWeaponsJson', UnitId=u)} and carried <= {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=u)},
           ('card + ammo rows for every carried weapon', U[u]['HUDName']))
    m = men(MRAA)
    ok(sum(r['PrimaryWeaponId'] == M4A1 for r in m) == 4 and sum(r['PrimaryWeaponId'] == M249E3 for r in m) == 2 and len(m) == 6, 'Mech. Riflemen AA: 4 M4A1, 2 M249E3, 6 men')
    ok(U[TROOPERS_AA]['Cost'] + O[TAA_MIXED_OPT]['Cost'] == U[TAA_MIXED]['Cost'] == 70 and U[MRAA]['Cost'] + O[MRAA_MIXED_OPT]['Cost'] == U[MRAA_MIXED]['Cost'] == 50, 'swap-row prices')
    rec['aa_squads_qjy_1126'] = {'Troopers AA Standard': 'M-25 CDTE removed (carrier keeps M4A1)', 'Troopers AA Mixed': '55 -> 70 (option 0 -> +15)',
                                 'Mech. Riflemen AA Standard': '45 -> 40, M4A1 5 -> 4, M249E3 1 -> 2, Stinger ammo 5 -> 6 (Mixed stays 50: option +5 -> +10)',
                                 'QJY-201': 'stat copy of PKP-N: damage 2.25 -> 2.4, min range 5 -> 0, Close quarter'}
    print('AA SQUADS QJY', rec['aa_squads_qjy_1126'])

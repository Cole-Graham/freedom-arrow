"""J-11BHG gets the J-16's Heavy CAP loadout (Osama 24 Nov 2026 11:5x PST, thread 1567745029781454889: "give J-16's Heavy CAP loadout to J-11BHG").
The J-16 option 24412 'Heavy CAP' (175 pts; PL-15 x4, PL-10 x4, PL-17 x2 on slots 1-12; slots 10-11 empty) is copied into the J-11BHG's loadout
slot (unit 1241, Su-27SM body; its own loadouts already use slots up to 12 and share the J-16's pylon turrets). Same price, 175, not default
(Light CAP stays default). Needed for the turrets to spawn on the J-11BHG: its TurretUnits get the 3 pylons it did not have (PL-15 2016535,
PL-10 2016537, PL-17 2016563, copied from the J-16's rows) and a PL-17 ammunition row (copy of the J-16's: weapon 2016509, ammo 2016474, 1)."""
J16, J11, SRC = 916, 1241, 24412
NEW_TURRETS, PL17 = (2016535, 2016537, 2016563), 2016509


def apply(t, g, ok, rec):
    U, O, M, TU, WA = (t[k] for k in ('Units', 'OptionsJson', 'ModificationsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson'))
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok(U[J16]['HUDName'] == 'J-16' and U[J11]['HUDName'] == 'J-11BHG' and O[SRC]['UIName'] == 'Heavy CAP' and M[O[SRC]['ModificationId']]['UnitId'] == J16, 'J-16 Heavy CAP / J-11BHG')
    mods = rows('ModificationsJson', UnitId=J11); ok(len(mods) == 1, ('J-11BHG one loadout slot', len(mods)))
    opts = rows('OptionsJson', ModificationId=mods[0]['Id'])
    ok('Heavy CAP' not in [o['UIName'] for o in opts], 'J-11BHG has no Heavy CAP yet')
    have = {r['TurretId'] for r in rows('TurretUnitsJson', UnitId=J11)}
    for tid in NEW_TURRETS:
        if tid not in have:
            src = rows('TurretUnitsJson', UnitId=J16, TurretId=tid); ok(len(src) == 1, ('J-16 pylon row', tid))
            g.add('TurretUnitsJson', src[0], {'UnitId': J11})
    if not rows('WeaponAmmunitionsJson', UnitId=J11, WeaponId=PL17):
        src = rows('WeaponAmmunitionsJson', UnitId=J16, WeaponId=PL17); ok(len(src) == 1, 'J-16 PL-17 ammo row')
        g.add('WeaponAmmunitionsJson', src[0], {'UnitId': J11})
    new = g.add('OptionsJson', O[SRC], {'ModificationId': mods[0]['Id'], 'Name': 'PLA loadout J-11BHG Heavy CAP', 'IsDefault': False,
                                        'Order': max(o.get('Order', 0) for o in opts) + 1})
    slots = {O[new][f'Turret{i}Id'] for i in range(21)} - {0}
    have = {r['TurretId'] for r in rows('TurretUnitsJson', UnitId=J11)}
    ok(slots <= have, ('J-11BHG has every pylon of the option', sorted(slots - have)))
    tw = [r['WeaponId'] for tid in slots for r in rows('TurretWeaponsJson', TurretId=tid)]
    ok(all(rows('WeaponAmmunitionsJson', UnitId=J11, WeaponId=w) for w in tw), 'every Heavy CAP weapon has a J-11BHG ammo row')
    ok([o['IsDefault'] for o in rows('OptionsJson', ModificationId=mods[0]['Id'])].count(True) == 1 and O[new]['Cost'] == 175, 'one default; Heavy CAP 175')
    rec['j11bhg_heavy_cap_1124'] = {'option': new, 'cost': 175, 'turrets_added': list(NEW_TURRETS)}
    print('J-11BHG HEAVY CAP', rec['j11bhg_heavy_cap_1124'])

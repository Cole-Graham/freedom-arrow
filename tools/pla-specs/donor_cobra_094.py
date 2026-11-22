"""Z-19 and armed Z-9 on the AH-1W SuperCobra stand-in (Osama 21 Nov 2026 19:3x PST, thread 1567745029781454889: "Z-19 should just use the Cobra as
its standin", "Z-9 and Z-19 that way we have more pylons, but just don't change the stats"). Called from apply_0_9_4_dev1.py (section 21).
The AS-365 Dauphin body has 2 pylons (slots 0, 1); the AH-1W has 4 (inner 1-2, outer 3-4; slot 0 is its chin turret, left empty because these
units have no gun). Only Units.ModelFileName and the loadout pylon layout change: every unit stat, price and every missile/rocket total stays.
- A loadout with the same pylon on both Dauphin slots keeps it on the inner pylons 1-2 (same rounds per launcher).
- A loadout with two different pylons: slot 0 -> inner 1-2, slot 1 -> outer 3-4, each with half the rounds per launcher (2 launchers each).
The Z-9 transport (1107, 8 seats) stays on the Dauphin (the Cobra has no cabin). FAModels draws the Z-19/Z-9 models over the stand-in; where the
weapons hang on them still needs a look in game."""

DAUPHIN, COBRA, EMPTY = 'DLC2_AS365_Dauphin', 'US_AH-1W Super_Cobra', 160
UNITS = {940: 'Z-19', 1103: 'Z-19', 1132: 'Z-19 Recon', 1134: 'Z-19 Recon', 1236: 'Z-19G', 1237: 'Z-19G Recon', 941: 'Z-9WA', 1133: 'Z-9WA Recon'}


def apply(t, g, ok, rec):
    U, O, M, TW, WA, W, TU = (t[k] for k in ('Units', 'OptionsJson', 'ModificationsJson', 'TurretWeaponsJson', 'WeaponAmmunitionsJson', 'WeaponsJson', 'TurretUnitsJson'))
    wp = lambda tid: [r['WeaponId'] for r in TW.values() if r and r.get('TurretId') == tid] if tid and tid != EMPTY else []
    war = lambda u, w: [r for r in WA.values() if r and r.get('UnitId') == u and r.get('WeaponId') == w]
    ok(any(u and u.get('ModelFileName') == COBRA and u.get('HUDName') == 'AH-1W Supercobra' for u in U.values()), 'AH-1W stand-in exists')

    def totals(u, o):
        s = {}
        for i in range(10):
            for w in wp(O[o].get(f'Turret{i}Id')):
                n = W[w]['HUDName']; q = war(u, w)[0]['Quantity']; s.setdefault(n, [0, 0]); s[n][0] += q; s[n][1] += 1
        return s
    out = {}
    for u, name in UNITS.items():
        ok(U[u]['HUDName'].strip() == name and U[u]['ModelFileName'] == DAUPHIN, (u, name, 'on the Dauphin'))
        opts = sorted([o['Id'] for o in O.values() if o and M.get(o.get('ModificationId'), {}).get('UnitId') == u])
        for o in opts:
            ok(all(not O[o].get(f'Turret{i}Id') for i in range(2, 10)), (u, o, 'Dauphin loadout uses slots 0-1 only'))
        # weapons that will be split: used on one Dauphin slot only, in every loadout of this unit
        split = {}
        for o in opts:
            a, b = O[o].get('Turret0Id'), O[o].get('Turret1Id')
            if a != b:
                for tid in (a, b):
                    for w in wp(tid): split[w] = True
        for o in opts:
            a, b = O[o].get('Turret0Id'), O[o].get('Turret1Id')
            if a == b:
                for w in wp(a): ok(w not in split, (u, o, 'weapon both doubled and split', w))
        before = {o: totals(u, o) for o in opts}
        for w in split:
            r = war(u, w); ok(len(r) == 1 and r[0]['Quantity'] % 2 == 0, (u, W[w]['HUDName'], 'even rounds to split', [x['Quantity'] for x in r]))
            g.put('WeaponAmmunitionsJson', r[0]['Id'], {'Quantity': r[0]['Quantity'] // 2})
        for o in opts:
            a, b = O[o].get('Turret0Id') or EMPTY, O[o].get('Turret1Id') or EMPTY
            f = {'Turret0Id': 0, 'Turret1Id': a, 'Turret2Id': a} if a == b else {'Turret0Id': 0, 'Turret1Id': a, 'Turret2Id': a, 'Turret3Id': b, 'Turret4Id': b}
            g.put('OptionsJson', o, f)
            aft = totals(u, o)
            ok({k: v[0] for k, v in aft.items()} == {k: v[0] for k, v in before[o].items()}, (u, o, 'round totals unchanged', before[o], aft))
            out.setdefault(f'{name} ({u})', {})[O[o].get('UIName')] = {k: f'{before[o][k][0]} on {before[o][k][1]} -> {aft[k][1]} launchers' for k in aft}
        g.put('Units', u, {'ModelFileName': COBRA})
    ok(t['Units'][1107]['ModelFileName'] == DAUPHIN and t['Units'][1107]['InfantrySlots'] == 8, 'Z-9 transport stays on the Dauphin')
    rec['donor_cobra_094'] = out

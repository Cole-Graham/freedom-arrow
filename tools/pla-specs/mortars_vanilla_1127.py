"""Mortars back to vanilla (Osama 27 Nov 2026 11:3x PST, thread 1567745029781454889: "Let's just revert all the mortars back to vanilla status. Let's
just keep it simple for now ... for the Chinese mortars just try to match something similar in vanilla"). Replaces the 11:0x smoke cap
(smoke_standard_1127, taken out of the batch). Mortar = every carded unit firing a mortar-trajectory round (TrajectoryType 30), 120 mm gun-mortars included.
Vanilla units (what FA changed since 0.4 dev.31 "mortar range +50%, smoke on every mortar loadout" and 0.6 dev.25 "15 smoke rounds on Nona-S,
Nona-SVK, Magnolia and LAV-M"):
- Range: every vanilla mortar round back to its vanilla GroundRange (FA had x1.5). FA's global artillery rules (IgnoreCover and HE penetration,
  the same on every howitzer and rocket) stay.
- Smoke: Nona-S 120 mm smoke 15 -> 5 and Nona-SVK 15 -> 9 (vanilla), and the 11 smoke rows FA added to vanilla loadouts are removed (Nona-S, Nona-SVK,
  Vena, Magnolia x2, Floks, Drok, Tulpan, LAV-M Dragonfire, MT-LB 2B9 and 2B12). Every such weapon keeps its other vanilla rounds.
- Price back to vanilla: Stryker MC 90 -> 75, LAV-M 80 -> 60, 2S41 Drok 80 -> 40, 2S23 Nona-SVK 80 -> 65.
China mortars matched to their closest vanilla twin (counts and range; their prices and supply weights stay as Osama set them):
- PLZ-10 / PLZ-25 (2S31 Vena copies) = Vena: HE / smoke loadout 45 + 15, guided loadout 60 with no smoke (row removed), range 1050 / 1200 world.
- PLL-05 (wheeled 120 mm gun-mortar) = 2S23 Nona-SVK: 21 HE + 9 smoke, range 1050 world.
- Lynx 120mm Mortar (vanilla 120 mm rounds) = M1287 MCV: 45 HE + 15 smoke; its range follows the vanilla rounds (1000 world).
- Lynx 81mm Mortar (81 mm automatic mortar) = 2S41 Drok: 40 HE + 24 smoke, range 900 world (the vanilla 82 mm); its 6 HEAT stay.
Not mortars, unchanged: howitzers (incl. PLL-09, PLZ-07B, PLZ-70 and the Lynx Howitzer at Hawkeye range) and rocket smoke. Not yet tested in a game."""
import json, pathlib
VAN = pathlib.Path(__file__).resolve().parents[3] / 'lateralus-infantry-20261110' / 'vanilla'
PRICES = {5: 75, 154: 60, 155: 40, 218: 65}
CN = {  # (unit HUDName, weapon id, ammo id): new quantity, or None = remove the row
    ('PLZ-10', 2020593, 2020596): 45, ('PLZ-10', 2020593, 2020599): 15, ('PLZ-10', 2020594, 2020598): 60, ('PLZ-10', 2020594, 2020599): None,
    ('PLZ-25', 2020593, 2020596): 45, ('PLZ-25', 2020593, 2020599): 15, ('PLZ-25', 2020594, 2020598): 60, ('PLZ-25', 2020594, 2020599): None,
    ('PLL-05', 2009459, 2009463): 21, ('PLL-05', 2009459, 2018957): 9,
    ('Lynx 120mm Mortar', 2021337, 183): 45, ('Lynx 120mm Mortar', 2021337, 87): 15,
    ('Lynx 81mm Mortar', 2021324, 2021525): 40, ('Lynx 81mm Mortar', 2021324, 2021526): 24}
CN_RANGE = {2020596: 1050.0, 2020599: 1050.0, 2020598: 1200.0, 2009463: 1050.0, 2018957: 1050.0, 2021525: 900.0, 2021526: 900.0}


def apply(t, g, ok, rec):
    U, A, WA, SA = t['Units'], t['AmmunitionsJson'], t['WeaponAmmunitionsJson'], t['SpecializationAvailabilitiesJson']
    vU = {r['Id']: r for r in json.loads((VAN / 'Units.json').read_text())}
    vA = {r['Id']: r for r in json.loads((VAN / 'AmmunitionsJson.json').read_text())}
    vWA = {r['Id']: r for r in json.loads((VAN / 'WeaponAmmunitionsJson.json').read_text())}
    carded = {r['UnitId'] for r in SA.values() if r}
    rows = [r for r in WA.values() if r and r['UnitId'] in carded and A[r['AmmunitionId']].get('TrajectoryType') == 30]
    van_rows = [r for r in rows if r['UnitId'] in vU]
    # vanilla rounds: range
    ranges = {}
    for a in sorted({r['AmmunitionId'] for r in rows if r['AmmunitionId'] in vA}):
        if A[a].get('GroundRange') != vA[a].get('GroundRange'):
            ranges[A[a]['HUDName'] + f' ({a})'] = [A[a]['GroundRange'], vA[a]['GroundRange']]
            g.put('AmmunitionsJson', a, {'GroundRange': vA[a]['GroundRange']})
    # vanilla units: quantities back, FA-added rows out
    qty, removed = [], []
    for r in van_rows:
        if r['Id'] in vWA:
            if r['Quantity'] != vWA[r['Id']]['Quantity']:
                qty.append((U[r['UnitId']]['HUDName'].strip(), A[r['AmmunitionId']]['HUDName'], r['Quantity'], vWA[r['Id']]['Quantity']))
                g.put('WeaponAmmunitionsJson', r['Id'], {'Quantity': vWA[r['Id']]['Quantity']})
        else:
            ok(A[r['AmmunitionId']].get('GenerateSmoke'), ('FA-added row on a vanilla mortar is a smoke row', r['Id']))
            removed.append((U[r['UnitId']]['HUDName'].strip(), r['WeaponId'], A[r['AmmunitionId']]['HUDName'], r['Quantity']))
            g.remove('WeaponAmmunitionsJson', r['Id'])
    ok(len(removed) == 11 and len(qty) == 2, ('11 FA smoke rows, 2 changed quantities', len(removed), len(qty)))
    for u, c in PRICES.items():
        ok(vU[u]['Cost'] == c, (u, 'vanilla price', vU[u]['Cost']))
        g.put('Units', u, {'Cost': c})
    # China mortars
    cn = {}
    for (h, w, a), q in CN.items():
        (r,) = [r for r in WA.values() if r and U[r['UnitId']]['HUDName'] == h and r['WeaponId'] == w and r['AmmunitionId'] == a]
        if q is None:
            g.remove('WeaponAmmunitionsJson', r['Id']); cn.setdefault(h, []).append((A[a]['HUDName'], r['Quantity'], 'removed'))
        else:
            cn.setdefault(h, []).append((A[a]['HUDName'], r['Quantity'], q)); g.put('WeaponAmmunitionsJson', r['Id'], {'Quantity': q})
    for a, rng in CN_RANGE.items():
        users = {U[r['UnitId']]['HUDName'] for r in WA.values() if r and r['AmmunitionId'] == a}
        ok(users <= {'PLZ-10', 'PLZ-25', 'PLL-05', 'Lynx 81mm Mortar'}, (a, 'China mortar round only', users))
        g.put('AmmunitionsJson', a, {'GroundRange': rng})
    # every weapon still has a round
    for r0 in rows:
        if r0['Id'] in WA:
            continue
        ok(any(x and x['UnitId'] == r0['UnitId'] and x['WeaponId'] == r0['WeaponId'] for x in WA.values()), ('weapon keeps a round', r0['UnitId'], r0['WeaponId']))
    rec['mortars_vanilla_1127'] = {'range_world': ranges, 'quantities': qty, 'removed_smoke_rows': removed, 'prices': PRICES, 'china': cn}
    print('MORTARS VANILLA', json.dumps(rec['mortars_vanilla_1127'], ensure_ascii=False)[:3000])

"""Disposable launchers: one launcher per round (Lateralus 23 Nov 2026 22:4x PST, thread 1572962048705429598: "chinese 'Thermobaric Assault'
infantry only has 3 launchers for their 6 disposable ammo, you need to stop making that mistake for disposable launchers").
A disposable launcher (Weapons.Type 63: AT4, M72 LAW, RPG-26, PF-97 ...) is fired once and thrown away. Vanilla gives each carrier one round
(WeaponAmmunitions.Quantity 1; 97 of 100 rows), so the squad's rounds = its carriers (docs/engine/infantry-ammo.md). More rounds = more carriers.
- apply: Thermobaric Assault 温压突击 (1209). thermobaric_pf97_1123.py (33d4ac7a, 23 Nov 14:4x) made its 6 PF-97 rounds as 3 carriers x 2. Now
  6 carriers x 1: riflemen 2015621-2015623 (QBZ-191, no special weapon, death priority 4) get the PF-97 at priority 3, as the other carriers
  (riflemen with a disposable AT weapon, tier C, infantry_order_1122.py). Row 2015630 Quantity 2 -> 1. Men, price and armour unchanged.
- check: every disposable row on a unit with carriers has Quantity 1, unless it is the vanilla row with vanilla's Quantity
  (Ognemetchiki MRO-Z x4 and RPO-M x2, PDSS RPG-28 x2). batch_0_9_5b.py runs it after every other section."""
import json
from pathlib import Path
DISPOSABLE = 63
PF97, ROW, NEW = 2012515, 2015630, (2015621, 2015622, 2015623)


def apply(t, g, ok, rec):
    U, SM, WA, W = t['Units'], t['SquadMembersJson'], t['WeaponAmmunitionsJson'], t['WeaponsJson']
    ok(U[1209]['HUDName'].strip().startswith('Thermobaric Assault') and W[PF97]['Type'] == DISPOSABLE, 'unit 1209 Thermobaric Assault; PF-97 is disposable')
    car = lambda: sorted(m['Id'] for m in SM.values() if m and m.get('UnitId') == 1209 and m.get('SpecialWeaponId') == PF97)
    ok(car() == [2015618, 2015619, 2015620] and WA[ROW]['UnitId'] == 1209 and WA[ROW]['WeaponId'] == PF97 and WA[ROW]['Quantity'] == 2, ('3 carriers x 2', car(), WA[ROW]))
    for mid in NEW:
        m = SM[mid]
        ok(m['UnitId'] == 1209 and m['PrimaryWeaponId'] == 2003998 and not m.get('SpecialWeaponId') and m['DeathPriority'] == 4, (mid, 'plain QBZ-191 rifleman, priority 4'))
        g.put('SquadMembersJson', mid, {'SpecialWeaponId': PF97, 'DeathPriority': 3})
    g.put('WeaponAmmunitionsJson', ROW, {'Quantity': 1})
    ok(len(car()) * WA[ROW]['Quantity'] == 6 and sum(1 for m in SM.values() if m and m.get('UnitId') == 1209) == 9, 'Thermobaric Assault: 6 PF-97 = 6 carriers x 1, 9 men')
    rec['disposable_launchers_1123'] = {'unit': 1209, 'pf97_carriers': [3, 6], 'quantity_per_carrier': [2, 1], 'rounds': 6, 'new_carriers': list(NEW)}


def check(t, ok, vanilla_dir):
    """Every disposable launcher row: Quantity 1 per carrier, or the vanilla row unchanged."""
    SM, WA, W, U = t['SquadMembersJson'], t['WeaponAmmunitionsJson'], t['WeaponsJson'], t['Units']
    van = {r['Id']: r for r in json.loads((Path(vanilla_dir) / 'WeaponAmmunitionsJson.json').read_text())}
    carriers = {}
    for m in SM.values():
        if m and m.get('SpecialWeaponId'):carriers[(m['UnitId'], m['SpecialWeaponId'])] = carriers.get((m['UnitId'], m['SpecialWeaponId']), 0) + 1
    bad, kept = [], []
    for r in WA.values():
        if not r or W.get(r['WeaponId'], {}).get('Type') != DISPOSABLE or not carriers.get((r['UnitId'], r['WeaponId'])) or r['Quantity'] == 1:continue
        v = van.get(r['Id'])
        (kept if v and (v['UnitId'], v['WeaponId'], v['Quantity']) == (r['UnitId'], r['WeaponId'], r['Quantity']) else bad).append((r['UnitId'], U[r['UnitId']]['HUDName'], W[r['WeaponId']]['HUDName'], r['Quantity'], carriers[(r['UnitId'], r['WeaponId'])]))
    ok(not bad, ('disposable launchers must be one round per carrier: add carriers, not Quantity', bad))
    ok(sorted((k[0], k[2], k[3]) for k in kept) == [(122, 'MRO-Z', 4), (358, 'RPO-M', 2)], ('vanilla multi-round disposable rows with carriers', kept))
    return kept

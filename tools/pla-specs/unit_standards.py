"""Freedom Arrow unit standards, enforced on every batch run (Lateralus 26 Nov 2026 17:1x PST, thread 1572962048705429598: "implement the fixes,
and do it in a way that these things are automatically maintained from now on. When Osama is making new units they should use all the mod's design
standards for reloading, etc."). The rules are listed in docs/development/UNIT-STANDARDS.md; each one is a check here or in the module it names.

squad_reload_table(): the disposable-launcher squad rate table (squad-reload.json, read by SquadReload.cs and the unit card), rebuilt from the
current data each build. Before 26 Nov it was carried unchanged from the 0.9.3 base, so 56 squads made later had no entry (they fired at their data
reload) and Ukrainian squad 354 kept 4 carriers in the table with 6 in the data. Rule (mod/squad-rof-contract.json, Lateralus 0.5 dev.35):
squad rate = k x carriers^exponent per minute, reload = 60 x carriers / rate, for every squad and every disposable (type 63, magazine 1) its soldiers
carry.

check(): fails the batch when a squad in a deck breaks a rule:
- a reusable launcher (type 62, magazine 1) with 3+ carriers in one squad: SquadReload.cs fixes the rate only for 1 (10/min) and 2 (15/min);
- one infantry weapon name firing one round name at different damage on different squads (Lateralus 26 Nov: "one name, one set of stats").
  KNOWN lists the cases already in the game, with their exact damage sets: a new squad that adds another damage, or a new weapon, fails.
The one-round-per-carrier rule for disposables is disposable_launchers_1123.check; weapon rows need ammo rows: weapon_coverage_check."""
import collections
import json
from pathlib import Path

CONTRACT = Path(__file__).resolve().parents[2] / 'mod/squad-rof-contract.json'
REUSABLE_TYPE, REUSABLE_RATES = 62, (1, 2)
# Infantry weapons still firing tiered damage on different squads (26 Nov 2026, after the M240L/PKP/PKM/M249/R-20/HK 416A5 standardisation).
KNOWN = {('Ksp 58B', '7.62x51mm'): {1.8, 2.25}, ('M249 Para', '5.56x45mm'): {2.05, 2.4, 3.1}}


def _live(t, tab):
    return [r for r in t[tab].values() if r]


def _carriers(t):
    c = collections.Counter()
    for m in _live(t, 'SquadMembersJson'):
        for k in ('PrimaryWeaponId', 'SpecialWeaponId'):
            if m.get(k):
                c[(m['UnitId'], m[k])] += 1
    return c


def deck_units(t):
    """Cards in a specialization shown in the hangar, their transports and the units their loadout options swap in (same rule as the DPM site)."""
    hangar = {s['Id'] for s in _live(t, 'SpecializationsJson') if s.get('ShowInHangar')}
    units, cards = set(), set()
    for r in _live(t, 'SpecializationAvailabilitiesJson'):
        if r['SpecializationId'] in hangar:
            units.add(r['UnitId']); cards.add(r['Id'])
    for r in _live(t, 'TransportAvailabilitiesJson'):
        if r.get('SpecializationAvailabilityId') in cards:
            units.add(r['UnitId'])
    mods = {m['Id']: m['UnitId'] for m in _live(t, 'ModificationsJson')}
    for o in _live(t, 'OptionsJson'):
        if o.get('ReplaceUnitId') and mods.get(o.get('ModificationId')) in units:
            units.add(o['ReplaceUnitId'])
    return units


def squad_reload_table(t):
    sr = json.loads(CONTRACT.read_text())
    W, table = t['WeaponsJson'], {}
    for (u, w), n in sorted(_carriers(t).items()):
        if W.get(w) and W[w]['Type'] == sr['disposable_type'] and W[w]['MagazineSize'] == 1:
            rate = sr['k'] * n ** sr['exponent']
            table[f'{u}:{w}'] = {'carriers': n, 'rate': round(rate, 3), 'reload': round(60 * n / rate, 3)}
    return {'k': sr['k'], 'exponent': sr['exponent'], 'disposableType': sr['disposable_type'], 'squads': table}


def check(t, ok, rec):
    W, A, U = t['WeaponsJson'], t['AmmunitionsJson'], t['Units']
    car, deck = _carriers(t), deck_units(t)
    bad = [(u, U[u]['HUDName'], W[w]['HUDName'], n) for (u, w), n in car.items()
           if u in deck and W.get(w) and W[w]['Type'] == REUSABLE_TYPE and W[w]['MagazineSize'] == 1 and n not in REUSABLE_RATES]
    ok(not bad, ('reusable launcher: 1 or 2 carriers per squad (SquadReload.cs 10/15 per minute)', bad))
    dmg = collections.defaultdict(set)
    for r in _live(t, 'WeaponAmmunitionsJson'):
        if r['UnitId'] in deck and car.get((r['UnitId'], r['WeaponId'])):
            dmg[(W[r['WeaponId']]['HUDName'], A[r['AmmunitionId']].get('HUDName'))].add(A[r['AmmunitionId']]['Damage'])
    tiered = {k: v for k, v in dmg.items() if len(v) > 1}
    new = {k: sorted(v) for k, v in tiered.items() if KNOWN.get(k) != v}
    ok(not new, ('infantry weapon: one name, one damage on every squad (unit_standards.KNOWN lists the old exceptions)', new))
    table = squad_reload_table(t)
    rec['unit_standards'] = {'deck_units': len(deck), 'disposable_squad_rates': len(table['squads']), 'tiered_known': sorted(map(list, tiered))}
    return table

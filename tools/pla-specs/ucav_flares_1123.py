"""UCAVs get flares (Osama 23 Nov 2026 20:4x PST, thread 1567745029781454889): "UCAV's get flares", "except WZ-8", "UCAVs only not the recon
drones"; earlier "all UCAVs get flares now, but they can't go low alt" (all of these are already high-altitude only).
UCAVs = the jet combat drones: S-70 Okhotnik, GJ-11, X-47B, FH-97A, MD-22 and (model build) XQ-58A. Not the recon drones (WZ-7, WZ-8, RQ-4,
RQ-170, RQ-7, Forpost, Korsar, Jiutian) and not the propeller drones (MQ-9, MQ-1, MQ-1C, Orion, Wing Loong).
Flares = the jets' standard decoy: 25 flares, accuracy x0.9, 3 s, cooldown 1 s, supply 100, resupply 3 s (vanilla row 2001399, 12 jets).
- FH-97A, MD-22, XQ-58A: from 'ECM Plane 20 + Laser No Decoy FA 0.55' (2019218) to vanilla 'ECM Plane 20 + Laser Default FA 0.55' (2001399),
  identical apart from the flares (ability-row-reuse rule).
- S-70, GJ-11, X-47B: 'Laser plane Default' (45) has no flare twin, so one new row = row 45 + those flares. Row 45 stays for its other users."""
import copy
WITH_FLARES, NO_DECOY, LASER = 2001399, 2019218, 45
NAMES = {'S-70 Okhotnik', 'GJ-11', 'X-47B', 'FH-97A', 'MD-22', 'XQ-58A Valkyrie'}
DEC = ('IsDecoy', 'DecoyFXPreset', 'DecoyQuantity', 'DecoyAccuracyMultiplier', 'DecoyDuration', 'DecoyCooldown', 'DecoySupplyCost', 'DecoyResupplyTime')


def apply(t, g, ok, rec):
    U, UA, A, O = t['Units'], t['UnitAbilitiesJson'], t['AbilitiesJson'], t['OptionsJson']
    units = {i: u['HUDName'] for i, u in U.items() if u and u.get('HUDName') in NAMES and u.get('DisplayInArmory')}
    ok(set(units.values()) >= NAMES - {'XQ-58A Valkyrie'}, ('UCAV cards', sorted(units.values())))
    f, n = A[WITH_FLARES], A[NO_DECOY]
    ok(f['IsDecoy'] and f['DecoyQuantity'] == 25 and not n['IsDecoy'] and all(f[k] == n[k] for k in f if k not in ('Id', 'Name', 'IsDefault') + DEC),
       '2001399 = 2019218 plus flares')
    ok(not any(o and any(o.get(k) for k in ('Ability1Id', 'Ability2Id', 'Ability3Id')) and t['ModificationsJson'][o['ModificationId']]['UnitId'] in units
               for o in O.values()), 'no loadout option sets an ability on them')
    new = None; out = {}
    for uid, hud in sorted(units.items()):
        rows = [r for r in UA.values() if r and r['UnitId'] == uid]
        ok(len(rows) == 1 and rows[0]['AbilityId'] in (NO_DECOY, LASER), (hud, 'one ability row, no flares', [r['AbilityId'] for r in rows]))
        old = rows[0]['AbilityId']
        if old == NO_DECOY: to = WITH_FLARES
        else:
            if new is None:
                new = g.add('AbilitiesJson', A[LASER], {**{k: copy.deepcopy(f[k]) for k in DEC}, 'Name': 'Laser plane + Decoy UCAV FA', 'IsDefault': False})
            to = new
        g.put('UnitAbilitiesJson', rows[0]['Id'], {'AbilityId': to})
        out[hud] = [old, to]
    ok(all(A[r['AbilityId']]['IsDecoy'] and A[r['AbilityId']]['DecoyQuantity'] == 25 for r in UA.values() if r and r['UnitId'] in units), 'every UCAV has 25 flares')
    ok(not A[LASER]['IsDecoy'] and any(r and r['AbilityId'] == LASER and U[r['UnitId']]['HUDName'] == 'WZ-8' for r in UA.values()), 'WZ-8 and recon drones keep row 45, no flares')
    rec['ucav_flares'] = {'abilities': out, 'new_row': new}
    print('UCAV FLARES', rec['ucav_flares'])

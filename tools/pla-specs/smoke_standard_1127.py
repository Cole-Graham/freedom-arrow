"""Artillery smoke standard (Osama 27 Nov 2026 11:0x PST, thread 1567745029781454889, after the cross-faction comparison: "yeah lets bring smoke down to
about that much. can you sort of standardize the smoke amounts"). China's guns were cut to 6-8 at 04:4x (osama_arty_smoke_1127); US / Russian / DLC
tube artillery and mortars carried 9-70.
Rule: every carded ground unit's smoke shell row for a tube weapon (howitzer, gun-mortar or mortar: ammo GenerateSmoke, TrajectoryType 20 or 30,
GroundRange >= 600 world) is capped at 8 rounds. Rows already at 8 or fewer stay (Lynx Howitzer 6, Lynx 81mm 6, Hawkeye 5, Tulpan 5).
Rocket smoke (TrajectoryType 40: 9K51 Grad 40, Lynx MRL 24) is not included: those are salvo loads. Only weapon-ammo row quantities change;
the smoke rounds are unchanged. Every row it touches is printed."""
CAP = 8


def apply(t, g, ok, rec):
    U, W, A, WA, SA = t['Units'], t['WeaponsJson'], t['AmmunitionsJson'], t['WeaponAmmunitionsJson'], t['SpecializationAvailabilitiesJson']
    carded = {r['UnitId'] for r in SA.values() if r}
    rows = [r for r in WA.values() if r and r['UnitId'] in carded and U[r['UnitId']].get('Type') == 4 and A[r['AmmunitionId']].get('GenerateSmoke')
            and A[r['AmmunitionId']].get('TrajectoryType') in (20, 30) and (A[r['AmmunitionId']].get('GroundRange') or 0) >= 600]
    ok(len(rows) >= 50, ('tube artillery smoke rows found', len(rows)))
    out = []
    for r in sorted(rows, key=lambda r: (U[r['UnitId']]['HUDName'], r['Id'])):
        if r['Quantity'] > CAP:
            out.append((U[r['UnitId']]['HUDName'].strip(), W[r['WeaponId']]['HUDName'], r['Quantity'], CAP))
            g.put('WeaponAmmunitionsJson', r['Id'], {'Quantity': CAP})
    ok(all(r['Quantity'] <= CAP for r in rows), 'every tube smoke row at most 8')
    rec['smoke_standard_1127'] = {'rows_checked': len(rows), 'capped': out}
    print('SMOKE STANDARD', len(rows), 'rows,', len(out), 'capped:', out)

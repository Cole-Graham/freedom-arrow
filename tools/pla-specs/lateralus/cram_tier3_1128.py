"""C-RAM to a tier 3 SPAAG, 110 points; the SeaRAM loadout stays 200 (Lateralus 28 Nov 2026 12:05 PST, thread 1568104480459722894: "change c-ram so it
is a tier 3 SPAAG (burst length can stop at least 3 sead missiles) / Increase its price to 110, and adjust SeaRAM loadout price down so it stays at 200
/ queue it up").
- Tiers (Lateralus 15 Nov 2026 SPAAG/SEAD tests, spaag_sead_data.py): light burst 3 / mid 7 with a 2-3 s pause, heavy (tier 3) burst 11 with a
  1.5-2.0 s pause; 1 / 2 / 3 SEAD missiles per burst. The C-RAM M61 CIWS (weapon 345) was mid; it takes the heavy guns' burst and pause
  (625 six-barrel 2009365, 2x 30 mm 2009599). Its round (262, 2.7 damage, a 2-hit kill on a 5 HP missile), shot interval 0.2 s, aim and magazine
  stay. Calculated card DPS 5.1 -> 7.9.
- Centurion C-RAM (unit 250) 80 -> 110 points. SeaRAM option 2111 (11x RIM-116, no swap row) +120 -> +90, so the loadout stays 80 + 120 = 110 + 90 = 200.
"""
CRAM, M61, SEARAM_OPT, HEAVY = 250, 345, 2111, (2009365, 2009599)
BURST = ('ShotsPerBurstMin', 'ShotsPerBurstMax', 'TimeBetweenBurstsMin', 'TimeBetweenBurstsMax')


def apply(t, g, ok, rec):
    U, O, W, WA = (t[k] for k in ('Units', 'OptionsJson', 'WeaponsJson', 'WeaponAmmunitionsJson'))
    ok(U[CRAM]['HUDName'].strip() == 'Centurion C-RAM' and U[CRAM]['Cost'] == 80 and not U[CRAM].get('OriginalCost'), ('C-RAM price', U[CRAM]['Cost']))
    ok(W[M61]['HUDName'] == 'M61 CIWS' and [W[M61][k] for k in BURST] == [7, 7, 2.0, 3.0], ('M61 mid-tier burst', [W[M61][k] for k in BURST]))
    users = sorted({r['UnitId'] for r in WA.values() if r and r.get('WeaponId') == M61})
    ok(users == [CRAM], ('weapon 345 only on the C-RAM', users))
    tier3 = {k: W[HEAVY[0]][k] for k in BURST}
    ok(all({k: W[h][k] for k in BURST} == tier3 for h in HEAVY) and tier3 == dict(zip(BURST, (11, 11, 1.5, 2.0))), ('heavy-tier burst', tier3))
    o = O[SEARAM_OPT]
    ok(o['UIName'] == '11x RIM-116 SeaRAM' and o['Cost'] == 120 and not o.get('ReplaceUnitId'), ('SeaRAM option', o.get('Cost')))
    ok(not [x for x in O.values() if x and x.get('ReplaceUnitId') == CRAM], 'no swap row points at the C-RAM')
    g.put('WeaponsJson', M61, tier3)
    g.put('Units', CRAM, {'Cost': 110})
    g.put('OptionsJson', SEARAM_OPT, {'Cost': 90})
    ok({k: W[M61][k] for k in BURST} == tier3 and U[CRAM]['Cost'] == 110 and U[CRAM]['Cost'] + O[SEARAM_OPT]['Cost'] == 200, 'C-RAM tier 3, 110, SeaRAM 200')
    rec['cram_tier3_1128'] = {'M61 CIWS (345)': 'burst 7 -> 11, pause 2.0-3.0 -> 1.5-2.0 s (tier 3)', 'Centurion C-RAM': '80 -> 110',
                              'SeaRAM option': '+120 -> +90 (loadout 200)'}
    print('CRAM TIER3', rec['cram_tier3_1128'])

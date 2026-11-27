"""Sprut price (Osama 27 Nov 2026 03:1x PST, bugs thread 1573561286803980289: "Spruts need like 25 points increase across the board"; 04:3x,
thread 1567745029781454889: "we nerfed spruts already right" - it was only proposed, so it is queued here).
Sprut-SD (144) 55 -> 80, Sprut-SDM (722) 70 -> 95. The cage-armour loadout stays +10 (90 / 105 with it). OriginalCost 0, no swap rows.
Armour (Osama 27 Nov 15:1x PST, bugs thread: "the Sprut should be bmp-2 armor"): the Sprut's own two rows take the armour values of the BMP-2
rows (base 2000068, SLAT 2000069). HP stays 12 and the rows keep their names and the cage model; only the Sprut-SD/SDM use them."""
PRICES = {144: ('Sprut-SD', 55, 80), 722: ('Sprut-SDM', 70, 95)}
ARMOR = {2000554: 2000068, 2000555: 2000069}  # Sprut row <- BMP-2 row
FACES = [f'{k}Armor{s}' for k in ('Kin', 'Heat') for s in ('Front', 'Sides', 'Rear', 'Top')]


def apply(t, g, ok, rec):
    U, O, M = t['Units'], t['OptionsJson'], t['ModificationsJson']
    out = {}
    for u, (h, a, b) in PRICES.items():
        ok(U[u]['HUDName'] == h and U[u]['Cost'] == a and not U[u].get('OriginalCost'), (h, U[u]['Cost']))
        ok(not any(o and o.get('ReplaceUnitId') and M.get(o['ModificationId'], {}).get('UnitId') == u for o in O.values()), (h, 'no swap rows'))
        g.put('Units', u, {'Cost': b}); out[h] = [a, b]
    A = t['ArmorsJson']
    for row, src in ARMOR.items():
        users = {r['UnitId'] for r in t['UnitArmorsJson'].values() if r and r['ArmorId'] == row}
        ok(users == {144, 722}, ('Sprut armour row used only by the Sprut-SD/SDM', row, users))
        ok(A[src]['Name'] in ('Armor BMP2 Base', 'Armor BMP2 SLAT'), ('BMP-2 source row', src, A[src]['Name']))
        before = {f: A[row][f] for f in FACES}
        g.put('ArmorsJson', row, {f: A[src][f] for f in FACES})
        ok(all(A[row][f] == A[src][f] for f in FACES) and A[row]['MaxHealthPoints'] == 12, ('Sprut armour = BMP-2, HP 12', row))
        out[A[row]['Name']] = {'before': before, 'after': {f: A[row][f] for f in FACES}}
    rec['osama_sprut_1127'] = out
    print('SPRUT', out)

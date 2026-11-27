"""M8 AGS and ZTQ-15 Light front armour (Osama 27 Nov 2026 15:2x PST, bugs thread 1573561286803980289: "Ztq-15 light let's drop to 150 Heat.
M8 AGS is 100/100. Ztq-15 light is front 100 ke").
- M8 base row 145 (Armor M8AGS Base, used by the M8 AGS 183 and the M8 Thunderbolt 719): front KE 60 -> 100, HEAT 60 -> 100.
- ZTQ-15 Light row 2018999 (only unit 1268): front KE 80 -> 100, HEAT 250 -> 150.
Sides, rear and top unchanged. The M8 option rows keep their armour values.
15:3x ("Airborne tanks to 12 HP. M8 thunderbolt to 95." / "Ztq-15 light to 135"):
- HP 14 -> 12 on every armour row of the M8 AGS / M8 Thunderbolt (6 rows), the M551A1 Sheridan (row 144, also on the hidden Scimitar 445)
  and the ZTQ-15 Light. The Sprut, PTZ-89, Type 16 MCV and Stryker MGS are already 12.
- M8 Thunderbolt (719) 85 -> 95; ZTQ-15 Light (1268) 145 -> 135. Both OriginalCost 0, no swap rows."""
HP12 = {145: {183, 719}, 2000053: {183}, 2000054: {183}, 2000055: {183, 719}, 2000522: {719}, 2000523: {719}, 144: {182, 445}, 2018999: {1268}}
PRICE = {719: ('M8 Thunderbolt', 85, 95), 1268: ('ZTQ-15 Light', 145, 135)}
ROWS = {145: ('Armor M8AGS Base', {183, 719}, {'KinArmorFront': (60, 100), 'HeatArmorFront': (60, 100)}),
        2018999: ('PLA ZTQ-15 Light ArmorsJson', {1268}, {'KinArmorFront': (80, 100), 'HeatArmorFront': (250, 150)})}


def apply(t, g, ok, rec):
    A = t['ArmorsJson']
    out = {}
    for row, (name, units, ch) in ROWS.items():
        users = {r['UnitId'] for r in t['UnitArmorsJson'].values() if r and r['ArmorId'] == row}
        ok(A[row]['Name'] == name and users == units, (name, 'row users', users))
        ok(all(A[row][f] == a for f, (a, b) in ch.items()), (name, 'before', {f: A[row][f] for f in ch}))
        g.put('ArmorsJson', row, {f: b for f, (a, b) in ch.items()})
        ok(all(A[row][f] == b for f, (a, b) in ch.items()), (name, 'after'))
        out[name] = {f: [a, b] for f, (a, b) in ch.items()}
    for row, units in HP12.items():
        users = {r['UnitId'] for r in t['UnitArmorsJson'].values() if r and r['ArmorId'] == row}
        ok(users == units and A[row]['MaxHealthPoints'] == 14, ('HP 14 -> 12 row', row, A[row]['Name'], users, A[row]['MaxHealthPoints']))
        g.put('ArmorsJson', row, {'MaxHealthPoints': 12})
        ok(A[row]['MaxHealthPoints'] == 12, ('HP 12', row))
    out['HP 14 -> 12'] = sorted(A[r]['Name'] for r in HP12)
    U, O, M = t['Units'], t['OptionsJson'], t['ModificationsJson']
    for u, (h, a, b) in PRICE.items():
        ok(U[u]['HUDName'] == h and U[u]['Cost'] == a and not U[u].get('OriginalCost'), (h, U[u]['Cost']))
        ok(not any(o and o.get('ReplaceUnitId') and M.get(o['ModificationId'], {}).get('UnitId') == u for o in O.values()), (h, 'no swap rows'))
        g.put('Units', u, {'Cost': b}); out[h] = [a, b]
    rec['osama_m8_ztq15_1127'] = out
    print('M8+ZTQ15', out)

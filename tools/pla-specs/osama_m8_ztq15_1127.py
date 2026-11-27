"""M8 AGS and ZTQ-15 Light front armour (Osama 27 Nov 2026 15:2x PST, bugs thread 1573561286803980289: "Ztq-15 light let's drop to 150 Heat.
M8 AGS is 100/100. Ztq-15 light is front 100 ke").
- M8 base row 145 (Armor M8AGS Base, used by the M8 AGS 183 and the M8 Thunderbolt 719): front KE 60 -> 100, HEAT 60 -> 100.
- ZTQ-15 Light row 2018999 (only unit 1268): front KE 80 -> 100, HEAT 250 -> 150.
Sides, rear, top and HP unchanged. The M8 option rows (ERA, Applique, Applique Trophy) are not changed."""
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
    rec['osama_m8_ztq15_1127'] = out
    print('M8+ZTQ15', out)

"""Lateralus 22 Nov 2026 17:5x PST, thread 1572962048705429598: "PRP-5G 35 -> 60 points". Called from apply_0_9_4_dev1.py.
PRP-5G (715, Russian FA card, BRM-3K base): Units.Cost 35 -> 60. OriginalCost is 0, so the card price is Cost + options (docs: unit-originalcost).
It has no loadout swap rows (its options are a turret and the Kaktus +20 armour option, no ReplaceUnitId), so no swap row price moves."""


def apply(t, g, ok, rec):
    U, O, M = t['Units'], t['OptionsJson'], t['ModificationsJson']
    u = U[715]
    ok(u['HUDName'].strip() == 'PRP-5G' and u['Cost'] == 35 and not u.get('OriginalCost'), ('PRP-5G 715 at 35, OriginalCost 0', u['Cost'], u.get('OriginalCost')))
    mods = {m['Id'] for m in M.values() if m and m.get('UnitId') == 715}
    ok(not [o for o in O.values() if o and o.get('ModificationId') in mods and o.get('ReplaceUnitId')], 'PRP-5G has no loadout swap rows')
    g.put('Units', 715, {'Cost': 60})
    rec['prices_1122'] = {'PRP-5G': [35, 60]}

"""Lateralus 22 Nov 2026 17:5x PST, thread 1572962048705429598: "PRP-5G 35 -> 60 points"; 17:5x "Tigr BRShM optronic loadout +10 -> +0",
"PRP-5G Reactive Armor loadout +20 -> +10". Called from batch_0_9_5b.py.
Option rows 425 (Tigr BRShM 195, Optronic system) and 20003 (PRP-5G 715, Kaktus reactive armour) belong to one unit each (own Modification).
PRP-5G (715, Russian FA card, BRM-3K base): Units.Cost 35 -> 60. OriginalCost is 0, so the card price is Cost + options (docs: unit-originalcost).
It has no loadout swap rows (its options are a turret and the Kaktus +20 armour option, no ReplaceUnitId), so no swap row price moves."""


def apply(t, g, ok, rec):
    U, O, M = t['Units'], t['OptionsJson'], t['ModificationsJson']
    u = U[715]
    ok(u['HUDName'].strip() == 'PRP-5G' and u['Cost'] == 35 and not u.get('OriginalCost'), ('PRP-5G 715 at 35, OriginalCost 0', u['Cost'], u.get('OriginalCost')))
    mods = {m['Id'] for m in M.values() if m and m.get('UnitId') == 715}
    ok(not [o for o in O.values() if o and o.get('ModificationId') in mods and o.get('ReplaceUnitId')], 'PRP-5G has no loadout swap rows')
    g.put('Units', 715, {'Cost': 60})
    for oid, uid, ui, old, new in ((425, 195, 'Custom_Option_Optronic_system', 10, 0), (20003, 715, 'Custom_Option_Reactive_armor', 20, 10)):
        o = O[oid]
        ok(o['UIName'] == ui and o['Cost'] == old and not o.get('ReplaceUnitId') and M[o['ModificationId']]['UnitId'] == uid, (oid, ui, 'at', old))
        g.put('OptionsJson', oid, {'Cost': new})
    ok(U[195]['HUDName'].strip() == 'Tigr BRShM', 'option 425 belongs to Tigr BRShM')
    rec['prices_1122'] = {'PRP-5G': [35, 60], 'Tigr BRShM optronic option 425': [10, 0], 'PRP-5G reactive armour option 20003': [20, 10]}

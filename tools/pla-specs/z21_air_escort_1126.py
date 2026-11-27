"""Z-21 'Air escort' loadout price (Osama 26 Nov 2026 21:0x PST, bugs thread: "we need to increase the points of the Z-21 with air escort";
23:1x, thread 1567745029781454889: "Z-21 Air escort should be +90"). Option 24513 'Air escort' (loadout mod 2017193 of the Z-21, unit 1104,
140 pts): +50 -> +90, so 190 -> 230 in total. No swap row (ReplaceUnitId), so no second price to keep in step. Other Z-21 loadouts unchanged."""
Z21, MOD, OPT = 1104, 2017193, 24513


def apply(t, g, ok, rec):
    U, O, M = t['Units'], t['OptionsJson'], t['ModificationsJson']
    o = O[OPT]
    ok(U[Z21]['HUDName'] == 'Z-21' and M[MOD]['UnitId'] == Z21 and o['ModificationId'] == MOD and o['UIName'] == 'Air escort' and o['Cost'] == 50
       and not o.get('ReplaceUnitId'), ('Z-21 Air escort +50, no swap row', o['Cost'], o.get('ReplaceUnitId')))
    g.put('OptionsJson', OPT, {'Cost': 90})
    rec['z21_air_escort_1126'] = {'option': OPT, 'cost': [50, O[OPT]['Cost']], 'total': U[Z21]['Cost'] + O[OPT]['Cost']}
    print('Z-21 AIR ESCORT', rec['z21_air_escort_1126'])

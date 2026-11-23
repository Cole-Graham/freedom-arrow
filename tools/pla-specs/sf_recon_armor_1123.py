"""Lateralus 23 Nov 2026 15:1x PST, thread 1568104480459722894: "Taishan Eagles: Smoke corrected from 4 -> 1, Armor corrected from 10 -> 8.
Whistling Arrows: Armor corrected from 10 -> 8". Called from batch_0_9_5b.py. Links move to existing rows that differ only in the changed
value (ability-row-reuse rule); the old FA armour rows were used by these units only and stay in the table, unused. HP and men unchanged.
- Taishan Eagles 泰山雄鹰 (1203): smoke link 2013760 row 81 "Sprint30 Smoke x4" -> row 11 "Sprint Smoke" (x1);
  armour link 2013756 row 2013755 (10 / 30) -> vanilla 289 "Armor Infantry Shock 6Men" (8 / 30).
- Whistling Arrows 响箭 (1184): armour link 2013186 row 2013185 (10 / 15) -> vanilla 279 "Armor Infantry Shock 3Men" (8 / 15)."""


def apply(t, g, ok, rec):
    U, UAB, UA, AB, AR, O, M = t['Units'], t['UnitAbilitiesJson'], t['UnitArmorsJson'], t['AbilitiesJson'], t['ArmorsJson'], t['OptionsJson'], t['ModificationsJson']
    ign = {'Id', 'Name'}
    diff = lambda a, b: {k for k in set(a) | set(b) if k not in ign and a.get(k) != b.get(k)}
    ok(U[1203]['HUDName'].strip().startswith('Taishan Eagles') and U[1184]['HUDName'].strip().startswith('Whistling Arrows'), 'units 1203 / 1184')
    mods = {m['Id'] for m in M.values() if m and m.get('UnitId') in (1203, 1184)}
    ok(not any(o.get('ReplaceUnitId') or any(o.get(f'Ability{i}Id') for i in (1, 2, 3)) for o in O.values() if o and o.get('ModificationId') in mods), 'no loadout swaps or ability options')
    # Taishan Eagles smoke 4 -> 1
    ok(UAB[2013760]['UnitId'] == 1203 and UAB[2013760]['AbilityId'] == 81 and diff(AB[81], AB[11]) == {'SmokeAmmunitionQuantity'} and AB[11]['SmokeAmmunitionQuantity'] == 1, 'Taishan smoke 81 (x4) -> 11 (x1)')
    g.put('UnitAbilitiesJson', 2013760, {'AbilityId': 11})
    # armour 10 -> 8
    for link, unit, old, new in ((2013756, 1203, 2013755, 289), (2013186, 1184, 2013185, 279)):
        ok(UA[link]['UnitId'] == unit and UA[link]['ArmorId'] == old and AR[old]['ArmorValue'] == 10, (unit, 'armour link', link, 'row', old, 'at 10'))
        ok(diff(AR[old], AR[new]) == {'ArmorValue'} and AR[new]['ArmorValue'] == 8, (unit, 'row', new, '= row', old, 'with armour 8'))
        g.put('UnitArmorsJson', link, {'ArmorId': new})
    rec['sf_recon_armor_1123'] = {'Taishan Eagles 1203': {'smoke': [4, 1], 'armor': [10, 8], 'rows': [[81, 11], [2013755, 289]]}, 'Whistling Arrows 1184': {'armor': [10, 8], 'rows': [2013185, 279]}}

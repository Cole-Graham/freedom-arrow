"""Sky Wolf Commandos AA / AT loadouts (Osama 28 Nov 2026 01:3x PST, thread 1567745029781454889: "Skywolf commandos they get 2 loadouts, AA and AT,
AA is just what we have now but +2 QW-12 ammo, AT is the same as what we have but +2 PF-98 ammo").
Sky Wolf Commandos 天狼突击队 (6001, Light CAB): 6 VQX191, one PF-98A carrier, one QW-12 carrier; PF-98A 4 rounds, QW-12 4 rounds.
- AA (default, the card unit 6001): QW-12 4 -> 6. Everything else as now.
- AT (new loadout row, a copy of 6001 with IsUnitModification): PF-98A 4 -> 6, QW-12 stays 4. Same men, armour, abilities, sensors, price 75.
- A squad loadout slot on 6001 in the vanilla pattern (Force Recon slot 401: Type 7 'Custom_Slot_Squad_loadout'; options with ReplaceUnitId only):
  'AA' -> 6001 (+0, default, Order 0), 'AT' -> the new row (+0). Swap row Cost = base + option = 75 (audit_swap_prices).
In the plb scope (adds rows), after onelayer_test_units_1128 so the TEST unit IDs stay put. The AT row's PLA bodies and weapon models: stage.py
'SKY WOLF AT BODIES' copies 6001's infantry-bodies-plb / infantry-weapons rules to it (next models build)."""
SW = 6001
AT_NAME = 'PLA Sky Wolf Commandos AT'


def apply(t, g, ok, rec):
    U, W, O, M = t['Units'], t['WeaponsJson'], t['OptionsJson'], t['ModificationsJson']
    rows = lambda tab, **kw: sorted((r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())), key=lambda r: r['Id'])
    ammo = lambda u: {W[r['WeaponId']]['HUDName']: r['Quantity'] for r in rows('WeaponAmmunitionsJson', UnitId=u)}
    kit = lambda u: sorted(W[m['PrimaryWeaponId']]['HUDName'] + (' + ' + W[m['SpecialWeaponId']]['HUDName'] if m.get('SpecialWeaponId') else '') for m in rows('SquadMembersJson', UnitId=u))
    before = {'kit': kit(SW), 'ammo': ammo(SW)}
    ok(U[SW]['HUDName'] == 'Sky Wolf Commandos 天狼突击队' and U[SW]['Cost'] == 75 and not U[SW].get('IsUnitModification') and not U[SW].get('OriginalCost'), ('Sky Wolf card 6001 at 75', U[SW].get('Cost')))
    ok(before['ammo'] == {'VQX191': 160, 'PF-98A': 4, 'QW-12': 4} and before['kit'] == ['VQX191', 'VQX191', 'VQX191', 'VQX191', 'VQX191 + PF-98A', 'VQX191 + QW-12'], ('Sky Wolf before', before))
    ok(not rows('ModificationsJson', UnitId=SW) and not [o for o in O.values() if o and o.get('ReplaceUnitId') == SW], 'Sky Wolf has no loadout slot yet')
    ok(not any(u and u.get('Name') == AT_NAME for u in U.values()), 'AT name free')
    ok(M[401]['UIName'] == 'Custom_Slot_Squad_loadout' and M[401]['Type'] == 7 and O[1477]['ModificationId'] == 401 and O[1477]['IsDefault'], 'vanilla Force Recon slot 401 / option 1477 as template')
    # AT loadout row: a copy of 6001
    at = g.add('Units', U[SW], {'Name': AT_NAME, 'IsUnitModification': True})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitArmorsJson', 'UnitPropulsionsJson', 'SquadMembersJson', 'SquadWeaponsJson'):
        for r in rows(tab, UnitId=SW): g.add(tab, r, {'UnitId': at})
    for r in rows('WeaponAmmunitionsJson', UnitId=SW):
        g.add('WeaponAmmunitionsJson', r, {'UnitId': at, **({'Quantity': 6} if W[r['WeaponId']]['HUDName'] == 'PF-98A' else {})})
    # AA = the card unit
    (qw,) = [r for r in rows('WeaponAmmunitionsJson', UnitId=SW) if W[r['WeaponId']]['HUDName'] == 'QW-12']
    g.put('WeaponAmmunitionsJson', qw['Id'], {'Quantity': 6})
    # loadout slot
    nm = g.add('ModificationsJson', M[401], {'UnitId': SW, 'Name': 'Sky Wolf Commandos', 'Order': 0})
    oa = g.add('OptionsJson', O[1477], {'ModificationId': nm, 'Order': 0, 'IsDefault': True, 'Name': 'Squad Sky Wolf Commandos AA', 'UIName': 'AA',
                                         'ReplaceUnitId': SW, 'ReplaceUnitName': None, 'OptionPicture': 'INF_IGLA', 'Cost': 0})
    ob = g.add('OptionsJson', O[1477], {'ModificationId': nm, 'Order': 1, 'IsDefault': False, 'Name': 'Squad Sky Wolf Commandos AT', 'UIName': 'AT',
                                         'ReplaceUnitId': at, 'ReplaceUnitName': None, 'OptionPicture': 'INF_Carl_M3', 'Cost': 0})
    # after
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitArmorsJson', 'UnitPropulsionsJson', 'SquadMembersJson', 'SquadWeaponsJson', 'WeaponAmmunitionsJson'):
        ok(len(rows(tab, UnitId=at)) == len(rows(tab, UnitId=SW)), ('AT row', tab, 'copied'))
    after = {'AA': {'kit': kit(SW), 'ammo': ammo(SW)}, 'AT': {'kit': kit(at), 'ammo': ammo(at)}}
    ok(after['AA']['ammo'] == {'VQX191': 160, 'PF-98A': 4, 'QW-12': 6} and after['AT']['ammo'] == {'VQX191': 160, 'PF-98A': 6, 'QW-12': 4}, ('ammo after', after))
    ok(after['AA']['kit'] == after['AT']['kit'] == before['kit'], 'same men and weapons in both loadouts')
    ok(U[at]['Cost'] == U[SW]['Cost'] + O[ob]['Cost'] == 75 and U[SW]['Cost'] + O[oa]['Cost'] == 75, 'AA 75, AT 75')
    ok([(o['UIName'], o['ReplaceUnitId'], o['Cost'], bool(o.get('IsDefault'))) for o in rows('OptionsJson', ModificationId=nm)] == [('AA', SW, 0, True), ('AT', at, 0, False)], 'slot: AA default, AT')
    ok(not rows('SpecializationAvailabilitiesJson', UnitId=at), 'AT row is a loadout, not a card')
    rec['osama_skywolf_loadouts_1128'] = {'card': SW, 'at_row': at, 'slot': nm, 'options': {'AA': oa, 'AT': ob}, 'before': before, 'after': after}
    print('SKY WOLF LOADOUTS', rec['osama_skywolf_loadouts_1128'])

"""PLA Light Brigade build, ZTZ-98 back in the game with a new model (Osama 27 Nov 2026 02:5x PST, thread 1573418243715113213: "I just downloaded
a new model, can you please prep it for implmentation? ZTZ-98 takes the current ZTZ-99 stats"). Branch codex/batch/osama/pla-light-brigade only;
the last plb section, so the ZTZ-99 it copies is the final one of this build.
- 'PLA ZTZ-98' (ztz98_1123.py; a ZTZ-99 copy of 23 Nov, hidden by roster_1123b.py on 25 Nov with Shawn's model held out): every stat row is
  re-copied from the current PLA Catalogue ZTZ-99 (1083): unit fields (price, HP, stealth, size...), its own armour and mobility rows rewritten
  with the ZTZ-99's values, and abilities, sensors, turrets, weapons/ammo and loadout options replaced by copies of the ZTZ-99's.
- Card: back in the Armory, in its 23 Nov deck, PLA PLARF Rocket Conscript Force (19), with the ZTZ-99's card count. The hidden test-spec row stays.
- Model: the new seller ZTZ-98 (work/c5-cn-1123 slug ztz98n, models.json key 'PLA ZTZ-98'); Shawn's m_ztz98_ files stay banned."""
NAME, ZTZ99, PLARF = 'PLA ZTZ-98', 1083, 19
KEEP = ('Id', 'Name', 'HUDName', 'OriginalName', 'Description', 'DisplayInArmory', 'OriginalCost')


def apply(t, g, ok, rec):
    U, SA = t['Units'], t['SpecializationAvailabilitiesJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    (z98,) = [i for i, u in U.items() if u and u.get('Name') == NAME]
    ok(U[ZTZ99]['Name'] == 'PLA Catalogue ZTZ-99' and U[z98]['DisplayInArmory'] is False and t['SpecializationsJson'][PLARF]['Name'] == 'PLA PLARF Rocket Conscript Force'
       and not rows('SpecializationAvailabilitiesJson', UnitId=z98, SpecializationId=PLARF), 'ZTZ-98 hidden, ZTZ-99 1083, PLARF spec 19')
    g.put('Units', z98, {**{k: v for k, v in U[ZTZ99].items() if k not in KEEP}, 'DisplayInArmory': True, 'OriginalCost': 0})
    # own armour / mobility rows: same count as the ZTZ-99, rewritten with its values
    for tab, field, target in (('UnitArmorsJson', 'ArmorId', 'ArmorsJson'), ('UnitPropulsionsJson', 'MobilityId', 'MobilityJson')):
        mine, src = rows(tab, UnitId=z98), rows(tab, UnitId=ZTZ99)
        ok(len(mine) == len(src), (NAME, tab, len(mine), len(src)))
        for a, b in zip(mine, src):
            g.put(target, a[field], {k: v for k, v in t[target][b[field]].items() if k not in ('Id', 'Name')})
    # everything else: drop the 23 Nov copies, copy the ZTZ-99's current rows
    for m in rows('ModificationsJson', UnitId=z98):
        for o in rows('OptionsJson', ModificationId=m['Id']): g.remove('OptionsJson', o['Id'])
        g.remove('ModificationsJson', m['Id'])
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson'):
        for r in rows(tab, UnitId=z98): g.remove(tab, r['Id'])
        for r in rows(tab, UnitId=ZTZ99): g.add(tab, r, {'UnitId': z98})
    opts = []
    for m in rows('ModificationsJson', UnitId=ZTZ99):
        nm = g.add('ModificationsJson', m, {'UnitId': z98})
        for o in rows('OptionsJson', ModificationId=m['Id']):
            oid = g.add('OptionsJson', o, {'ModificationId': nm});opts.append(oid)
            ok(0 < oid <= 32767, ('ZTZ-98 option id fits the network short', oid))
    card = max(rows('SpecializationAvailabilitiesJson', UnitId=ZTZ99), key=lambda r: r['MaxAvailabilityXp0'])
    nc = g.add('SpecializationAvailabilitiesJson', card, {'UnitId': z98, 'SpecializationId': PLARF})
    # checks after
    same = lambda tab, key: sorted(tuple(r[k] for k in key) for r in rows(tab, UnitId=z98)) == sorted(tuple(r[k] for k in key) for r in rows(tab, UnitId=ZTZ99))
    ok(same('TurretUnitsJson', ('TurretId', 'Order')) and same('WeaponAmmunitionsJson', ('WeaponId', 'AmmunitionId', 'Quantity')) and same('UnitAbilitiesJson', ('AbilityId',))
       and same('SensorUnitsJson', ('SensorId',)), 'ZTZ-98 turrets, ammo, abilities, sensors = ZTZ-99')
    ok(all(U[z98][k] == U[ZTZ99][k] for k in U[ZTZ99] if k not in KEEP) and U[z98]['DisplayInArmory'] is True, 'ZTZ-98 unit fields = ZTZ-99')
    ok(len(rows('ModificationsJson', UnitId=z98)) == len(rows('ModificationsJson', UnitId=ZTZ99)), 'ZTZ-98 loadout slots = ZTZ-99')
    rec['pla_light_brigade_ztz98_1127'] = {'unit': z98, 'cost': U[z98]['Cost'], 'card': nc, 'spec': PLARF, 'cards': SA[nc]['MaxAvailabilityXp0'], 'options': len(opts)}
    print('PLA LIGHT BRIGADE ZTZ-98', rec['pla_light_brigade_ztz98_1127'])

"""No HJ-12, APS or reactive armour loadouts on the new PLAN vehicles (Osama 23 Nov 2026 22:4x PST, thread 1567745029781454889: "there shouldn't be a
HJ-12 or aps or reactive armor loadout"). MODEL BUILD ONLY. After sinicize_1123.py.
- ZSD-05: removes '30 mm autocannon + HJ-12' (with its turret link and HJ-12 ammunition), 'Reactive armor' and 'Reactive armour + GL-5 APS'.
- ZBD-05: removes 'Reactive armor' and 'Reactive armour + GL-5 APS'.
- ZTD-05: removes 'GL-5 APS'.
24 Nov 01:0x "zsd-05 shoud NOT have an autocannon option": the ZSD-05 also loses '30 mm autocannon' (keeps QJC-88 +0 and QLZ-87 AGL +5).
The armour slot keeps only its default option (smoke, supply); the weapon options are unchanged otherwise.
22:5x "non of these get aps options or reactive armor": their copied APS abilities (Iron Fist 82 / APS US Light 88) leave UnitAbilities too, and
the ZSD-05 / ZBD-05 lose the AMPV's second ('armoured', reactive-armour) mobility row, which no option uses any more."""
DROP = {'PLA ZSD-05': ('30 mm autocannon + HJ-12', '30 mm autocannon', 'Custom_Option_Reactive_armor', 'Reactive armour + GL-5 APS'),
        'PLA ZBD-05': ('Custom_Option_Reactive_armor', 'Reactive armour + GL-5 APS'),
        'PLA ZTD-05': ('GL-5 APS',)}


def apply(t, g, ok, rec):
    U, O, M, TU, TW, WA, W, A = (t[k] for k in ('Units', 'OptionsJson', 'ModificationsJson', 'TurretUnitsJson', 'TurretWeaponsJson',
                                                 'WeaponAmmunitionsJson', 'WeaponsJson', 'AmmunitionsJson'))

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    out = {}
    for name, drop in DROP.items():
        (u,) = [i for i, x in U.items() if x and x.get('Name') == name]
        opts = [o for m in rows('ModificationsJson', UnitId=u) for o in rows('OptionsJson', ModificationId=m['Id'])]
        gone = [o for o in opts if o['UIName'] in drop]
        ok(sorted(o['UIName'] for o in gone) == sorted(drop), (name, 'options to remove', [o['UIName'] for o in opts]))
        dropped = {o[k] for o in gone for k in o if k.startswith('Turret') and k.endswith('Id') and o[k]}
        for o in gone: g.remove('OptionsJson', o['Id'])
        left = [o for m in rows('ModificationsJson', UnitId=u) for o in rows('OptionsJson', ModificationId=m['Id'])]
        used = {o[k] for o in left for k in o if k.startswith('Turret') and k.endswith('Id') and o[k]}
        for r in rows('TurretUnitsJson', UnitId=u):   # only turrets that just lost their last option; fixed turrets (ZTD-05 cupola) stay
            if r['TurretId'] in dropped and r['TurretId'] not in used: g.remove('TurretUnitsJson', r['Id'])
        onturret = {w['WeaponId'] for r in rows('TurretUnitsJson', UnitId=u) for w in rows('TurretWeaponsJson', TurretId=r['TurretId'])}
        for r in rows('WeaponAmmunitionsJson', UnitId=u):
            if r['WeaponId'] not in onturret: g.remove('WeaponAmmunitionsJson', r['Id'])
        for m in rows('ModificationsJson', UnitId=u):
            ok(len(rows('OptionsJson', ModificationId=m['Id'])) >= 1, (name, 'every slot keeps an option', m['Id']))
        for r in rows('UnitAbilitiesJson', UnitId=u):
            if t['AbilitiesJson'][r['AbilityId']]['IsAPS']:
                ok(not any(o.get(k) == r['AbilityId'] for o in left for k in ('Ability1Id', 'Ability2Id', 'Ability3Id')), (name, 'APS used by no option'))
                g.remove('UnitAbilitiesJson', r['Id'])
        mobs = rows('UnitPropulsionsJson', UnitId=u)
        if len(mobs) > 1:
            usedm = {o.get('MobilityId') for o in left if o.get('MobilityId')}
            for r in mobs[1:]:
                if r['MobilityId'] not in usedm: g.remove('UnitPropulsionsJson', r['Id'])
        ok(not any(t['AbilitiesJson'][r['AbilityId']]['IsAPS'] for r in rows('UnitAbilitiesJson', UnitId=u)) and len(rows('UnitPropulsionsJson', UnitId=u)) == 1
           and t['MobilityJson'][rows('UnitPropulsionsJson', UnitId=u)[0]['MobilityId']]['IsAmphibious'], (name, 'no APS ability, one amphibious mobility row'))
        names = sorted(o['UIName'] for m in rows('ModificationsJson', UnitId=u) for o in rows('OptionsJson', ModificationId=m['Id']))
        shown = {W[r['WeaponId']]['HUDName'] for r in rows('WeaponAmmunitionsJson', UnitId=u)}
        ok(not any(s in n for n in names for s in ('HJ-12', 'APS', 'eactive')) and 'HJ-12' not in shown, (name, 'no HJ-12 / APS / reactive armour', names))
        if name == 'PLA ZTD-05': ok('QJC-88 12.7 mm' in shown, 'ZTD-05 keeps its cupola QJC-88')
        out[name] = {'removed': list(drop), 'options': names, 'weapons': sorted(shown)}
    rec['plan_trim_options'] = out
    print('PLAN TRIM', out)

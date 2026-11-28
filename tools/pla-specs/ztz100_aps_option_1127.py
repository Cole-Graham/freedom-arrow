"""ZTZ-100 APS as a loadout (Osama 27 Nov 2026 17:3x PST, thread 1567745029781454889: "ZTZ-100 lets make a new model that remove the aps and give it
as an option. base price goes down by 60 and then the APS option is 60 pts" / "actually the unit goes down by 80 points overall").
- Base 355 -> 275 (-80); protection slot like the ZTZ-99A's (modification 2019383 pattern): None 0 (default) / APS +60 -> 335 with APS.
- The ZTZ-100's own ability row 2010187 (smoke + ECM 0.7 + APS, used by 968 only) loses the APS; the APS option links the existing row 82
  'APS IronFist NoModel' (same 2 charges, 10 s cooldown, hitbox 2.0, supply 200), as the ZTZ-99B. Empty slot = row 4. No new ability rows.
- Option Name 'PLA ZTZ-100 APS' is the FAModels variant key: the APS option shows the current model, the default the no-APS model.
  Before the plb scope (adds rows)."""
Z100, ABIL, APS, EMPTY, TURRET, OLD, NEW, APS_COST = 968, 2010187, 82, 4, 2010192, 355, 275, 60
APS_FIELDS = {'IsAPS': False, 'APSHitboxProportion': 0.0, 'APSQuantity': 0, 'APSCooldown': 0.0, 'APSSupplyCost': 0.0, 'APSResupplyTime': 0.0}


def apply(t, g, ok, rec):
    U, AB, UA, MO, O, TU = t['Units'], t['AbilitiesJson'], t['UnitAbilitiesJson'], t['ModificationsJson'], t['OptionsJson'], t['TurretUnitsJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok(U[Z100]['HUDName'] == 'ZTZ-100' and U[Z100]['Cost'] == OLD and not U[Z100].get('OriginalCost'), ('ZTZ-100 as read', U[Z100]['Cost']))
    ok(not rows('ModificationsJson', UnitId=Z100) and [r['AbilityId'] for r in rows('UnitAbilitiesJson', UnitId=Z100)] == [ABIL], 'ZTZ-100: no loadouts, one ability row')
    ok([r['UnitId'] for r in rows('UnitAbilitiesJson', AbilityId=ABIL)] == [Z100] and AB[ABIL]['IsAPS'] and AB[ABIL]['IsSmoke'], 'ability 2010187 = ZTZ-100 only')
    a, b = AB[ABIL], AB[APS]
    ok(all(a[k] == b[k] for k in ('APSHitboxProportion', 'APSQuantity', 'APSCooldown', 'APSSupplyCost', 'APSResupplyTime')) and b['IsAPS'] and not b.get('ModelFileName'),
       'row 82 = the ZTZ-100 APS values')
    ok([r['TurretId'] for r in rows('TurretUnitsJson', UnitId=Z100) if r.get('Order') == 0] == [TURRET], 'ZTZ-100 main turret')
    g.put('AbilitiesJson', ABIL, APS_FIELDS)
    link = rows('UnitAbilitiesJson', UnitId=Z100)[0]
    for ab in (EMPTY, APS): g.add('UnitAbilitiesJson', link, {'AbilityId': ab})
    m = g.add('ModificationsJson', MO[2019383], {'UnitId': Z100, 'Name': 'PLA ZTZ-100 protection'})
    base = {k: O[31098].get(k) for k in O[31098]}
    pic = O[31172]['OptionPicture']
    none = g.add('OptionsJson', O[31098], {'ModificationId': m, 'Name': 'PLA ZTZ-100 No APS', 'Ability1Id': ABIL, 'Ability2Id': EMPTY, 'Turret0Id': TURRET, 'Cost': 0, 'Order': 0})
    aps = g.add('OptionsJson', O[31098], {'ModificationId': m, 'Name': 'PLA ZTZ-100 APS', 'UIName': 'APS', 'OptionPicture': pic, 'Ability1Id': ABIL, 'Ability2Id': APS,
                                         'Turret0Id': TURRET, 'Cost': APS_COST, 'Order': 1})
    ok(all(0 < o <= 32767 for o in (none, aps)), ('option ids fit the network short', none, aps))
    g.put('Units', Z100, {'Cost': NEW})
    ok(not AB[ABIL]['IsAPS'] and AB[ABIL]['IsSmoke'] and AB[ABIL]['ECMAccuracyMultiplier'] == 0.7, 'default keeps smoke + ECM, no APS')
    ok(sorted(r['AbilityId'] for r in rows('UnitAbilitiesJson', UnitId=Z100)) == sorted([ABIL, EMPTY, APS]), 'option abilities linked')
    rec['ztz100_aps_option_1127'] = {'unit': Z100, 'cost': [OLD, NEW], 'options': {'None': none, 'APS': [aps, APS_COST]}, 'aps_ability': APS, 'picture': pic}
    print('ZTZ-100 APS OPTION', rec['ztz100_aps_option_1127'])

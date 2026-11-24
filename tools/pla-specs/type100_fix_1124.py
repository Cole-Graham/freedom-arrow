"""Type 100 CSV (ZBD-100) loadout fix (Osama 24 Nov 2026 00:1x PST, bugs thread 1573561286803980289: "make the fix").
Two player reports (QQ bug sheet; SteelPlate, amok):
1. APS lost with the CH-901 package: the 9x CH-901 loadout is a unit swap (ReplaceUnitId -> 'PLA ZBD-100 CH-901'), the GL-5 APS sits in a separate
   protection slot on the base unit, and vanilla never combines a swap with another option slot.
2. "Type 100 in both the recon tab and the infantry tab (as a transport), both with missiles + APS: after 2-3 are out, availability drops to 0."
   The recon card and the 7 transport links all pointed at the same unit 1294, and its CH-901 loadout deploys the same swap row. Not proven which
   game rule counts them together, so the fix separates them: the transports get their own unit rows.
Fix (the dev.28 layout, proven to load on the Bradley body; bradley-turret-swap-rule):
- One loadout slot, four choices, every one a unit swap: 40 mm CT (+0), 40 mm CT + GL-5 APS (+40), 9x CH-901 (+40), 9x CH-901 + GL-5 APS (+80).
  The APS rows carry the APS in their one default ability row (smoke + supply + laser + APS). The separate protection slot is removed.
- Transport copies: a 'PLA ZBD-100 transport' base and its three swap rows, same stats and the same four-way slot; the TransportAvailabilities
  links (6 in the 0.9.6 data; 7 in 0.9.5b before the QJZ-89 Team was hidden) move to it. The recon card stays on 1294.
- FAModels draws by unit Name: the 6 new Names need models.json / paint-schemes.json entries (copies of 'PLA ZBD-100' and 'PLA ZBD-100 CH-901')."""
BASE_NAME, CH_NAME, APS = 'PLA ZBD-100', 'PLA ZBD-100 CH-901', 82
LINK_TABLES = ('UnitAbilitiesJson', 'UnitArmorsJson', 'UnitPropulsionsJson', 'SensorUnitsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson')
APS_FIELDS = ('IsAPS', 'APSHitboxProportion', 'APSQuantity', 'APSCooldown', 'APSSupplyCost', 'APSResupplyTime')
NEW_NAMES = {}   # new unit Name -> existing Name whose FAModels entry it copies


def apply(t, g, ok, rec):
    U, AB, UA, M, O, TA, SA = (t[k] for k in ('Units', 'AbilitiesJson', 'UnitAbilitiesJson', 'ModificationsJson', 'OptionsJson',
                                               'TransportAvailabilitiesJson', 'SpecializationAvailabilitiesJson'))
    rows = lambda tab, **kw: [r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())]
    base = [u for u in U.values() if u and u.get('Name') == BASE_NAME]
    ch = [u for u in U.values() if u and u.get('Name') == CH_NAME]
    ok(len(base) == 1 and len(ch) == 1 and ch[0]['IsUnitModification'] and not base[0]['IsUnitModification'], 'ZBD-100 base and CH-901 swap rows')
    B, C = base[0]['Id'], ch[0]['Id']
    mods = {m['Type']: m for m in rows('ModificationsJson', UnitId=B)}
    ok(sorted(mods) == [3, 6] and not rows('ModificationsJson', UnitId=C), ('ZBD-100 slots before: loadout (3) + protection (6)', sorted(mods)))
    lo = sorted(rows('OptionsJson', ModificationId=mods[3]['Id']), key=lambda o: o['Order'])
    po = sorted(rows('OptionsJson', ModificationId=mods[6]['Id']), key=lambda o: o['Order'])
    ok([(o['UIName'], o['Cost'], o['ReplaceUnitId']) for o in lo] == [('40 mm CT', 0, B), ('9x CH-901', 40, C)], 'loadout options before')
    ok([(o['Cost'], o['Ability1Id']) for o in po] == [(0, 0), (40, APS)], 'protection options before: none / GL-5 APS +40')
    aps_cost, ch_cost = po[1]['Cost'], lo[1]['Cost']
    ok(U[C]['Cost'] == U[B]['Cost'] + ch_cost, 'CH-901 swap price = base + option')
    tr = rows('TransportAvailabilitiesJson', UnitId=B)
    cards = rows('SpecializationAvailabilitiesJson', UnitId=B)
    ok(len(tr) >= 1 and len(cards) == 1 and all(SA[r['SpecializationAvailabilityId']]['SpecializationId'] == cards[0]['SpecializationId'] for r in tr),
       ('one recon card + 7 transport links in the same spec', len(cards), len(tr)))

    def default_ability(uid):
        d = [r for r in rows('UnitAbilitiesJson', UnitId=uid) if AB[r['AbilityId']].get('IsDefault')]
        ok(len(d) == 1, (uid, 'one default ability row'))
        return d[0]

    dflt = default_ability(B)['AbilityId']
    ok(default_ability(C)['AbilityId'] == dflt and not AB[dflt].get('IsAPS'), 'base and CH-901 share the smoke/supply/laser row')
    want = dict(AB[dflt], **{k: AB[APS][k] for k in APS_FIELDS})   # ability-row reuse rule: link an identical row if one exists
    same = [i for i, r in AB.items() if r and all(r.get(k) == v for k, v in want.items() if k not in ('Id', 'Name'))]
    aps_row = same[0] if same else g.add('AbilitiesJson', AB[dflt], {'Name': 'PLA ZBD-100 smoke supply laser APS', **{k: AB[APS][k] for k in APS_FIELDS}})

    def clone(src, name, cost, swap, ability=None):
        uid = max(U) + 1
        g.put('Units', uid, dict({k: v for k, v in U[src].items() if k != 'Id'}, Name=name, Cost=cost, IsUnitModification=swap))
        for tab in LINK_TABLES:
            for r in rows(tab, UnitId=src):
                if tab == 'UnitAbilitiesJson' and r['AbilityId'] == APS: continue       # the protection-slot link is not needed any more
                f = {'UnitId': uid}
                if tab == 'UnitAbilitiesJson' and ability and r['AbilityId'] == dflt: f['AbilityId'] = ability
                g.add(tab, r, f)
        NEW_NAMES[name] = U[src]['Name'] if src in (B, C) else NEW_NAMES.get(U[src]['Name'], U[src]['Name'])
        return uid

    def slot(owner, units):
        """Turn owner's slots into one four-way loadout slot pointing at units = [plain, plain+APS, CH-901, CH-901+APS]."""
        lm = g.add('ModificationsJson', mods[3], {'UnitId': owner, 'Name': U[owner]['Name'] + ' loadout', 'Order': 0}) if owner != B else mods[3]['Id']
        if owner == B:
            for o in lo: g.remove('OptionsJson', o['Id'])
            for o in po: g.remove('OptionsJson', o['Id'])
            g.remove('ModificationsJson', mods[6]['Id'])
        for n, (u, ui, cost, pic) in enumerate(((units[0], '40 mm CT', 0, lo[0]['OptionPicture']),
                                                (units[1], '40 mm CT + GL-5 APS', aps_cost, po[1]['OptionPicture']),
                                                (units[2], '9x CH-901', ch_cost, lo[1]['OptionPicture']),
                                                (units[3], '9x CH-901 + GL-5 APS', ch_cost + aps_cost, lo[1]['OptionPicture']))):
            g.add('OptionsJson', lo[0], {'ModificationId': lm, 'Name': U[owner]['Name'] + ' loadout ' + str(n), 'UIName': ui, 'Order': n,
                                         'IsDefault': False, 'Cost': cost, 'ReplaceUnitId': u,
                                         'ReplaceUnitName': None if n == 0 else lo[1].get('ReplaceUnitName'), 'OptionPicture': pic})
            ok(U[u]['Cost'] == U[owner]['Cost'] + cost, (U[u]['Name'], 'swap price = base + option'))

    p0 = U[B]['Cost']
    card = [B, clone(B, BASE_NAME + ' APS', p0 + aps_cost, True, aps_row), C, clone(C, CH_NAME + ' APS', p0 + ch_cost + aps_cost, True, aps_row)]
    trb = clone(B, BASE_NAME + ' transport', p0, False)
    trans = [trb, clone(B, BASE_NAME + ' transport APS', p0 + aps_cost, True, aps_row),
             clone(C, CH_NAME + ' transport', p0 + ch_cost, True), clone(C, CH_NAME + ' transport APS', p0 + ch_cost + aps_cost, True, aps_row)]
    # the old CH-901 row loses its APS link too (APS now only on the +APS rows)
    for r in rows('UnitAbilitiesJson', UnitId=C):
        if r['AbilityId'] == APS: g.remove('UnitAbilitiesJson', r['Id'])
    for r in rows('UnitAbilitiesJson', UnitId=B):
        if r['AbilityId'] == APS: g.remove('UnitAbilitiesJson', r['Id'])
    slot(B, card)
    slot(trb, trans)
    for r in tr: g.put('TransportAvailabilitiesJson', r['Id'], {'UnitId': trb})

    # checks
    for owner, us in ((B, card), (trb, trans)):
        ms = rows('ModificationsJson', UnitId=owner)
        ok(len(ms) == 1 and ms[0]['Type'] == 3, (U[owner]['Name'], 'one loadout slot'))
        os_ = sorted(rows('OptionsJson', ModificationId=ms[0]['Id']), key=lambda o: o['Order'])
        ok([o['ReplaceUnitId'] for o in os_] == us and [o['Cost'] for o in os_] == [0, aps_cost, ch_cost, ch_cost + aps_cost], (U[owner]['Name'], 'four choices'))
        for u, aps in zip(us, (False, True, False, True)):
            d = default_ability(u)['AbilityId']
            ok(bool(AB[d].get('IsAPS')) == aps and (not aps or AB[d]['APSQuantity'] == AB[APS]['APSQuantity']), (U[u]['Name'], 'APS in default row' if aps else 'no APS'))
            ok(not any(r['AbilityId'] == APS for r in rows('UnitAbilitiesJson', UnitId=u)), (U[u]['Name'], 'no leftover option APS link'))
    ok(not rows('TransportAvailabilitiesJson', UnitId=B) and len(rows('TransportAvailabilitiesJson', UnitId=trb)) == len(tr), 'transports moved to their own rows')
    ok(rows('SpecializationAvailabilitiesJson', UnitId=B) == cards and not rows('SpecializationAvailabilitiesJson', UnitId=trb), 'recon card unchanged')
    rec['type100_fix_1124'] = {'card_units': card, 'transport_units': trans, 'aps_ability': aps_row, 'new_models_json_names': dict(NEW_NAMES)}
    print('TYPE100 FIX', rec['type100_fix_1124'])

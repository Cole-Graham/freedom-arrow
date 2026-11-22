"""New cards for new models (Osama 22 Nov 2026 11:1x-11:4x PST, thread 1572407822849810463; voice note: "give me a list of all the models that Shawn
has uploaded that we have not yet implemented ... and my downloads ... prep them for Armory, Battle and LOD"; then "Type59d we add back for rocket force
vehicle tab"; "Korean models add to Korea").
- ZTZ-59D: full copy of the ZTZ-59D1 (1260, Recon tab) as a Vehicles-tab tank in PLARF Rocket Force (spec 19), with the ZTZ-59's sensor row and its
  spec-19 card count. Model: the 13 Nov CGTrader Type 59D (work/china-new-20261122, m_t59d_*).
- Korea (Blue Dragon, spec 23, 2 cards each like the other Blue Dragon cards): K263 / M163 VADS = copy of the vanilla M163 PIVADS (188); K200 KIFV =
  copy of the vanilla M113A3 (185). Models: Osama's cgmodel purchases 571291 / 571294 (work/blue-dragon-models-20261122, m_m163_* / m_k200_*).
Stats are the parents' until Osama or Lateralus set them."""

SPEC_BD, SPEC_RF = 23, 19


def apply(t, g, ok, rec):
    U, SA = t['Units'], t['SpecializationAvailabilitiesJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    def clone(parent, name, hud, upd):
        ok(not any(u and name == u.get('Name') for u in U.values()), name + ' name free')
        d = dict(U[parent]); d.pop('Id')
        d.update({'Name': name, 'HUDName': hud, 'OriginalCost': 0, 'Description': None, 'OriginalName': None, 'DisplayInArmory': True, **upd})
        uid = g.put('Units', max(U) + 1, d)
        for tab in ('UnitArmorsJson', 'UnitPropulsionsJson', 'UnitAbilitiesJson', 'SensorUnitsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson'):
            for r in rows(tab, UnitId=parent):
                g.add(tab, r, {'UnitId': uid})
        for m in rows('ModificationsJson', UnitId=parent):
            nm = g.add('ModificationsJson', m, {'UnitId': uid})
            for o in rows('OptionsJson', ModificationId=m['Id']):
                g.add('OptionsJson', o, {'ModificationId': nm, **({'ReplaceUnitId': uid} if o.get('ReplaceUnitId') == parent else {})})
        ok(not any(o.get('ReplaceUnitId') not in (0, None, uid) for m in rows('ModificationsJson', UnitId=uid) for o in rows('OptionsJson', ModificationId=m['Id'])),
           (name, 'no swap rows to other units'))
        return uid

    # ZTZ-59D in the Rocket Force Vehicles tab
    ok((U[1260]['HUDName'].strip(), U[1260]['CategoryType'], U[1060]['HUDName'].strip()) == ('ZTZ-59D1', 0, 'ZTZ-59'), 'ZTZ-59D1 recon card, ZTZ-59 tank card')
    z = clone(1260, 'PLA ZTZ-59D', 'ZTZ-59D', {'CategoryType': U[1060]['CategoryType']})
    s59 = rows('SensorUnitsJson', UnitId=1060)
    ok(len(s59) == 1 and len(rows('SensorUnitsJson', UnitId=z)) == 1, 'one sensor row each')
    g.put('SensorUnitsJson', rows('SensorUnitsJson', UnitId=z)[0]['Id'], {'SensorId': s59[0]['SensorId']})
    rf = [r for r in SA.values() if r and r['UnitId'] == 1060 and r['SpecializationId'] == SPEC_RF]
    ok(len(rf) == 1, 'ZTZ-59 card in Rocket Force')
    g.add('SpecializationAvailabilitiesJson', rf[0], {'UnitId': z})

    # Korea
    ok((U[188]['HUDName'], U[185]['HUDName']) == ('M163 PIVADS', 'M113A3'), 'vanilla M163 / M113A3')
    tpl = next(r for r in SA.values() if r and r['SpecializationId'] == SPEC_BD)
    kr = {}
    for parent, name in ((188, 'K263 Vulcan'), (185, 'K200 KIFV')):
        u = clone(parent, name, name, {'IsUnitModification': False})
        g.add('SpecializationAvailabilitiesJson', tpl, {'UnitId': u, 'SpecializationId': SPEC_BD, 'MaxAvailabilityXp0': 2})
        kr[name] = u

    for u in [z, *kr.values()]:
        for tab in ('UnitArmorsJson', 'UnitPropulsionsJson', 'SensorUnitsJson', 'TurretUnitsJson'):
            ok(rows(tab, UnitId=u), (U[u]['Name'], tab))
    ok({r['SpecializationId'] for r in SA.values() if r and r['UnitId'] == z} == {SPEC_RF} and U[z]['CategoryType'] == U[1060]['CategoryType'], 'ZTZ-59D: Rocket Force Vehicles tab')
    rec['new_cards_1122'] = {'ZTZ-59D': z, **kr}
    print('NEWCARDS', rec['new_cards_1122'])

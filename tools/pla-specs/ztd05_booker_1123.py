"""ZTD-05 = amphibious M10 Booker (Osama 23 Nov 2026 22:2x PST, thread 1567745029781454889: "ZTD-05 please make it a copy of the booker but
amphibious"). MODEL BUILD ONLY. Last in the batch, so the new unit id follows every existing card.
- New card 'PLA ZTD-05': full copy of vanilla 'M10 Booker' (453, M35 105 mm: body, armour, mobility, abilities, sensors, turrets, ammunition,
  both modifications with their 3 options, 100 pts, its card count), CountryId 4, in PLAN Naval/Special Forces (spec 20).
- Amphibious: its own copy of the Booker's mobility row with IsAmphibious True (water speed 20, as the Booker row and the old ZTD-05), and
  WaterDiveOffset 1.44 from the old ZTD-05 card. Card art (label and portrait) from the old ZTD-05 card. The body stays the Booker's (US_M10)
  so the Booker turrets fit; FAModels draws the ZTD-05 model (models.json 'PLA ZTD-05' = ztd05ag), the same model the old card had.
- The old 'PLA ZTD-05' card (930: Sprut-SD body, 65 pts, hidden, in no spec) is renamed 'PLA ZTD-05 (old Sprut)' so the model key goes to the
  new card; it stays hidden."""
BOOKER, OLD, SPEC, NAME = 453, 930, 20, 'PLA ZTD-05'


def apply(t, g, ok, rec):
    U, S = t['Units'], t['SpecializationsJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    ok(U[BOOKER]['Name'] == 'M10 Booker' and U[BOOKER]['HUDName'] == 'M10 Booker M35' and U[OLD]['Name'] == NAME and U[OLD]['DisplayInArmory'] is False
       and not rows('SpecializationAvailabilitiesJson', UnitId=OLD), 'Booker 453; old hidden ZTD-05 930')
    ok(S[SPEC]['Name'] == 'PLA PLAN Special Forces', 'spec 20 = PLAN Naval/SF')
    g.put('Units', OLD, {'Name': 'PLA ZTD-05 (old Sprut)'})
    d = dict(U[BOOKER]); d.pop('Id')
    d.update({'Name': NAME, 'HUDName': 'ZTD-05', 'OriginalCost': 0, 'CountryId': 4, 'DisplayInArmory': True, 'Description': None, 'OriginalName': None,
              'WaterDiveOffset': U[OLD]['WaterDiveOffset'], 'ThumbnailFileName': U[OLD]['ThumbnailFileName'], 'PortraitFileName': U[OLD]['PortraitFileName']})
    uid = g.put('Units', max(U) + 1, d)
    for tab, field, target in (('UnitArmorsJson', 'ArmorId', 'ArmorsJson'), ('UnitPropulsionsJson', 'MobilityId', 'MobilityJson')):
        for r in rows(tab, UnitId=BOOKER):
            g.add(tab, r, {'UnitId': uid, field: g.add(target, t[target][r[field]], {'Name': f'{t[target][r[field]]["Name"]} {NAME}'})})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson'):
        for r in rows(tab, UnitId=BOOKER): g.add(tab, r, {'UnitId': uid})
    for m in rows('ModificationsJson', UnitId=BOOKER):
        nm = g.add('ModificationsJson', m, {'UnitId': uid})
        for o in rows('OptionsJson', ModificationId=m['Id']): g.add('OptionsJson', o, {'ModificationId': nm})
    (mob,) = rows('UnitPropulsionsJson', UnitId=uid)
    g.put('MobilityJson', mob['MobilityId'], {'IsAmphibious': True})
    (sa,) = rows('SpecializationAvailabilitiesJson', UnitId=BOOKER)
    g.add('SpecializationAvailabilitiesJson', sa, {'UnitId': uid, 'SpecializationId': SPEC})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitPropulsionsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson', 'ModificationsJson', 'UnitArmorsJson'):
        ok(len(rows(tab, UnitId=uid)) == len(rows(tab, UnitId=BOOKER)), ('ZTD-05', tab, 'copied'))
    no = lambda u: sum(len(rows('OptionsJson', ModificationId=m['Id'])) for m in rows('ModificationsJson', UnitId=u))
    m2 = t['MobilityJson'][mob['MobilityId']]
    ok(no(uid) == no(BOOKER) and U[uid]['Cost'] == 100 and m2['IsAmphibious'] and m2['MaxSpeedWater'] == 20
       and not t['MobilityJson'][rows('UnitPropulsionsJson', UnitId=BOOKER)[0]['MobilityId']]['IsAmphibious'], 'ZTD-05: Booker copy, 100 pts, amphibious; Booker unchanged')
    ok([u['Name'] for u in U.values() if u and u.get('Name') == NAME] == [NAME], 'one PLA ZTD-05 (models.json key)')
    rec['ztd05_booker'] = {'unit': uid, 'cost': U[uid]['Cost'], 'spec': SPEC, 'cards': sa['MaxAvailabilityXp0'], 'options': no(uid), 'mobility': mob['MobilityId'],
                           'content': U[uid].get('ContentMembership'), 'old_card': OLD}
    print('ZTD-05', rec['ztd05_booker'])

"""VN-3 and ZSL-191 transports for the MarkII_ China models (Osama 23 Nov 2026 20:4x PST, thread "blue dragons"): "the 4x4, it's called the VN-3 and
it's a replica of the BPM-97 Kord and goes to airborne as a transport for all its infantry. Stat clone of the Kord (although I'm almost certain this
Kord thing should be 25pts)", "ZSL-191 goes into china motorized".
- PLA VN-3: full copy of DLC3 BPM-97 (219, the "Kord", 20 pts) WITH its 4 turret options, CountryId 4. Body, sound and DLC3 gate as the Kord
  (ContentMembership 3, as the 9 China units already on DLC3 bodies, e.g. CSK-131 on DLC3_Tigr). Price unchanged: the 25 pts is Osama's open question.
  Transport for every PLAAF Air Force (spec 17, the airborne spec) infantry card that already has transports.
- PLA ZSL-191: no stats given -> copy of the APC 'PLA Catalogue ZSL-92 family' (1079, 35 pts); card art of the ZBL-191 (same hull). Transport for
  every PLAGF Motorized (spec 21) infantry card that already has transports.
Both are transports only (no own card), as ZBD-04 Rocket Force. FAModels draws the MarkII_ models (models.json key = Name, c5-cn-1123)."""
NEW = {'PLA VN-3': (219, 'VN-3', 17, {}), 'PLA ZSL-191': (1079, 'ZSL-191', 21, {'ThumbnailFileName': None})}


def apply(t, g, ok, rec):
    U, S, SA, TA = t['Units'], t['SpecializationsJson'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    ok(U[219]['Name'] == 'DLC3 BPM-97' and U[1079]['Name'] == 'PLA Catalogue ZSL-92 family' and U[979]['Name'] == 'PLA ZBL-191', 'donors 219 / 1079, art 979')
    ok(S[17]['Name'] == 'PLA PLAAF Air Force' and S[21]['Name'] == 'PLA PLAGF Motorized', 'specs 17 airborne, 21 motorized')
    out = {}
    for name, (parent, hud, spec, extra) in NEW.items():
        ok(not any(u and name in (u.get('Name'), u.get('HUDName')) for u in U.values()), name + ' name free')
        d = dict(U[parent]); d.pop('Id')
        d.update({'Name': name, 'HUDName': hud, 'OriginalCost': 0, 'CountryId': 4, 'DisplayInArmory': True, 'Description': None, 'OriginalName': None})
        if 'ThumbnailFileName' in extra: d['ThumbnailFileName'] = U[979]['ThumbnailFileName']
        uid = g.put('Units', max(U) + 1, d)
        for tab, field, target in (('UnitArmorsJson', 'ArmorId', 'ArmorsJson'), ('UnitPropulsionsJson', 'MobilityId', 'MobilityJson')):
            for r in rows(tab, UnitId=parent):
                g.add(tab, r, {'UnitId': uid, field: g.add(target, t[target][r[field]], {'Name': f'{t[target][r[field]]["Name"]} {name}'})})
        for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson'):
            for r in rows(tab, UnitId=parent): g.add(tab, r, {'UnitId': uid})
        for m in rows('ModificationsJson', UnitId=parent):
            nm = g.add('ModificationsJson', m, {'UnitId': uid})
            for o in rows('OptionsJson', ModificationId=m['Id']): g.add('OptionsJson', o, {'ModificationId': nm})
        for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'UnitPropulsionsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson', 'ModificationsJson', 'UnitArmorsJson'):
            ok(len(rows(tab, UnitId=uid)) == len(rows(tab, UnitId=parent)), (name, tab, 'copied'))
        no = lambda u: sum(len(rows('OptionsJson', ModificationId=m['Id'])) for m in rows('ModificationsJson', UnitId=u))
        ok(no(uid) == no(parent), (name, 'options copied', no(uid)))
        tpl = next(r for r in sorted(TA.values(), key=lambda r: r['Id']) if r)   # rows are {Id, SpecializationAvailabilityId, UnitId}
        ok(set(tpl) == {'Id', 'SpecializationAvailabilityId', 'UnitId'}, ('transport row fields', sorted(tpl)))
        inf = [r for r in sorted(SA.values(), key=lambda r: r['Id']) if r and r['SpecializationId'] == spec and r['UnitId'] != uid
               and any(x and x.get('SpecializationAvailabilityId') == r['Id'] for x in TA.values())]
        ok(len(inf) >= 8 and all(U[r['UnitId']].get('Type') == 2 for r in inf), (name, 'infantry cards with transports', len(inf)))
        for r in inf: g.add('TransportAvailabilitiesJson', tpl, {'SpecializationAvailabilityId': r['Id'], 'UnitId': uid})
        ok(len(rows('TransportAvailabilitiesJson', UnitId=uid)) == len(inf), (name, 'offered to every infantry card'))
        ok(U[uid]['Cost'] == U[parent]['Cost'] and U[uid]['ContentMembership'] == U[parent]['ContentMembership'], (name, 'price and content as the donor'))
        out[name] = {'unit': uid, 'parent': parent, 'cost': U[uid]['Cost'], 'spec': spec, 'options': no(uid), 'content': U[uid]['ContentMembership'],
                     'infantry_cards': [U[r['UnitId']]['HUDName'] for r in inf]}
    rec['mk_china_1123'] = out
    print('MK CHINA', out)

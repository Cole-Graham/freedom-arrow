"""PLA Light Brigade build, new Falcons unit (Osama 26 Nov 2026 02:4x PST, thread 1567745029781454889: "New Falcons unit, swaps the 2x MG's for the
QLZ-87", with his DPM visualizer custom unit 'Falcons New' from Falcons 1185: 75 pts, 40 HP, the Falcons' armour row; QBU-201, QLZ-04, QLU-11 and
QBZ-192 rifles). Branch codex/batch/osama/pla-light-brigade only; inside g.scope('plb'), after the MG section (Falcons MGs are QJY-88 there).
- 'Falcons New' (working name from his custom unit) = copy of Falcons 猎鹰 (1185: 8 men, 75 pts, armour 2013216, its Light CAB card row: 3 cards and
  its transports). The Falcons stay as they are.
- The 2 MG gunners: one carries the QLZ-87 (2012157, the QLZ-04's stat copy; QLZ-87 Team body), the other a QBZ-192. The 4 QMK men carry the
  QBZ-192, as in his custom unit; the leader keeps the PF-98. QLU-11 and QBU-201 men unchanged. Death priorities unchanged.
- Ammo per carrier as the China rows: QBZ-192 160, QLZ-87 190; the others as the Falcons'."""
FALCONS, QLZ87, QLZ87_A, QBZ192, QBZ192_A = 1185, 2012157, 2012158, 2013087, 2013088
NAME = 'Falcons New'


def apply(t, g, ok, rec):
    U, W, SM, SA = (t[k] for k in ('Units', 'WeaponsJson', 'SquadMembersJson', 'SpecializationAvailabilitiesJson'))
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    wn = lambda i: W[i]['HUDName'] if i else ''
    men = rows('SquadMembersJson', UnitId=FALCONS)
    kit = [(wn(r['PrimaryWeaponId']), wn(r['SpecialWeaponId'])) for r in men]
    ok(U[FALCONS]['HUDName'] == 'Falcons 猎鹰' and U[FALCONS]['Cost'] == 75 and not rows('ModificationsJson', UnitId=FALCONS)
       and sorted(kit) == sorted([('QJY-88', ''), ('QJY-88', ''), ('QLU-11', ''), ('QBU-203', ''), ('QMK', 'PF-98'), ('QMK', ''), ('QMK', ''), ('QMK', '')]), ('Falcons kit', kit))
    ok(wn(QLZ87) == 'QLZ-87' and wn(QBZ192) == 'QBZ-192', 'QLZ-87, QBZ-192')
    ok(not any(u and NAME in (u.get('Name', ''), u.get('HUDName', '')) for u in U.values()), 'name free')
    nu = g.add('Units', U[FALCONS], {'Name': 'PLA ' + NAME, 'HUDName': NAME, 'OriginalCost': 0, 'Description': None, 'OriginalName': None})
    for tab in ('UnitArmorsJson', 'UnitPropulsionsJson', 'UnitAbilitiesJson', 'SensorUnitsJson'):
        for r in rows(tab, UnitId=FALCONS): g.add(tab, r, {'UnitId': nu})
        ok(len(rows(tab, UnitId=nu)) == len(rows(tab, UnitId=FALCONS)), (NAME, tab, 'copied'))
    agl_body = rows('SquadMembersJson', PrimaryWeaponId=QLZ87)[0]['ModelFileName']
    first_mg = True
    for r in men:
        p, ch = r['PrimaryWeaponId'], {'UnitId': nu}
        if wn(p) == 'QJY-88':
            ch.update({'PrimaryWeaponId': QLZ87, 'ModelFileName': agl_body} if first_mg else {'PrimaryWeaponId': QBZ192}); first_mg = False
        elif wn(p) == 'QMK': ch['PrimaryWeaponId'] = QBZ192
        g.add('SquadMembersJson', r, ch)
    new = rows('SquadMembersJson', UnitId=nu)
    carried = {w for r in new for w in (r['PrimaryWeaponId'], r['SpecialWeaponId']) if w}
    sw0, wa_f = rows('SquadWeaponsJson', UnitId=FALCONS)[0], {r['WeaponId']: r for r in rows('WeaponAmmunitionsJson', UnitId=FALCONS)}
    ammo = {QLZ87: (QLZ87_A, 190), QBZ192: (QBZ192_A, 160)}
    for n, w in enumerate(sorted(carried, key=lambda w: (w not in (QBZ192,), wn(w))), 1):
        g.add('SquadWeaponsJson', sw0, {'UnitId': nu, 'WeaponId': w, 'Order': n})
        if w in ammo: g.add('WeaponAmmunitionsJson', next(iter(wa_f.values())), {'UnitId': nu, 'WeaponId': w, 'AmmunitionId': ammo[w][0], 'Quantity': ammo[w][1]})
        else: g.add('WeaponAmmunitionsJson', wa_f[w], {'UnitId': nu})
    fc = rows('SpecializationAvailabilitiesJson', UnitId=FALCONS); ok(len(fc) == 1, 'Falcons: one card row')
    nc = g.add('SpecializationAvailabilitiesJson', fc[0], {'UnitId': nu})
    for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=fc[0]['Id']): g.add('TransportAvailabilitiesJson', r, {'SpecializationAvailabilityId': nc})
    # checks after
    ok({r['WeaponId'] for r in rows('SquadWeaponsJson', UnitId=nu)} == carried == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=nu)}, 'card + ammo = carried')
    got = sorted((wn(r['PrimaryWeaponId']), wn(r['SpecialWeaponId']), r['DeathPriority']) for r in new)
    ok(len(new) == 8 and sum(r['PrimaryWeaponId'] == QLZ87 for r in new) == 1 and sum(r['PrimaryWeaponId'] == QBZ192 for r in new) == 5
       and not any(wn(r['PrimaryWeaponId']) in ('QJY-88', 'QMK') for r in new), (NAME, got))
    rec['pla_light_brigade_falcons_1126'] = {'unit': nu, 'kit': got, 'cost': U[nu]['Cost'], 'spec': fc[0]['SpecializationId'], 'cards': fc[0]['MaxAvailabilityXp0'],
                                             'transports': [U[r['UnitId']]['HUDName'] for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=nc)]}
    print('PLA LIGHT BRIGADE FALCONS NEW', rec['pla_light_brigade_falcons_1126'])

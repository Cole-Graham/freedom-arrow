"""QQ bug sheet fixes (Osama 25 Nov 2026 03:4x PST, bugs thread 1573561286803980289: "rename the QBU-201 to QBU-203, ZBD-86A recon removed (don't have
model). Rename CSK-181 to CTL-181. CSK-181 add an mg").
- QBU-201 (FA-110): weapon 2020834 shows as QBU-203, the 7.62 mm bolt rifle it fires (QBU-201 is the 12.7 mm one). Card name only (HUDName).
- ZBD-86 Recon (FA-104): its Rocket Force card goes (no ZBD-86A model). Unit rows stay in the data.
- CSK-181 (FA-111 / FA-115): the Rocket Force transport 'PLA CSK-181 Transport' draws the CTL-181 model, so its card shows CTL-181 (HUDName; the
  Name stays, FAModels draws by Name). Its empty mount becomes the CSK-131 Mengshi's QJZ-89 12.7 mm RWS (turret 2009002 on the same DLC3_Tigr body,
  100 rounds, as the CSK-131)."""
QBU, CSK, ZBD86R, RWS, RWS_W, EMPTY = 2020834, 'PLA CSK-181 Transport', 'ZBD-86 Recon', 2009002, 2009001, 2018554


def apply(t, g, ok, rec):
    U, W, SA = t['Units'], t['WeaponsJson'], t['SpecializationAvailabilitiesJson']
    rows = lambda tab, **kw: [r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())]
    ok(W[QBU]['HUDName'] == 'QBU-201' and W[QBU]['ModelFileName'] == 'M40A5', 'QBU-201 weapon row')
    g.put('WeaponsJson', QBU, {'HUDName': 'QBU-203'})
    # ZBD-86 Recon card
    recon = [i for i, u in U.items() if u and u.get('HUDName') == ZBD86R]
    cards = [r for r in SA.values() if r and r['UnitId'] in recon]
    ok(len(cards) == 1 and cards[0]['SpecializationId'] == 19, ('ZBD-86 Recon: one Rocket Force card', [(r['Id'], r['SpecializationId']) for r in cards]))
    ok(not rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=cards[0]['Id']), 'ZBD-86 Recon card carries no infantry')
    for r in cards: g.remove('SpecializationAvailabilitiesJson', r['Id'])
    # CSK-181 -> CTL-181 + QJZ-89 RWS
    (c,) = [i for i, u in U.items() if u and u.get('Name') == CSK]
    ok(U[c]['HUDName'] == 'CSK-181' and U[c]['ModelFileName'] == 'DLC3_Tigr', 'CSK-181 transport row')
    g.put('Units', c, {'HUDName': 'CTL-181'})
    (tu,) = rows('TurretUnitsJson', UnitId=c)
    ok(tu['TurretId'] == EMPTY and not rows('WeaponAmmunitionsJson', UnitId=c), 'CSK-181: one empty mount, no weapons')
    (donor,) = rows('WeaponAmmunitionsJson', UnitId=900, WeaponId=RWS_W)
    ok(U[900]['ModelFileName'] == 'DLC3_Tigr' and [r['TurretId'] for r in rows('TurretUnitsJson', UnitId=900)] == [RWS], 'CSK-131 QJZ-89 RWS donor')
    g.put('TurretUnitsJson', tu['Id'], {'TurretId': RWS})
    g.add('WeaponAmmunitionsJson', donor, {'UnitId': c})
    ok([r['TurretId'] for r in rows('TurretUnitsJson', UnitId=c)] == [RWS] and [(r['WeaponId'], r['Quantity']) for r in rows('WeaponAmmunitionsJson', UnitId=c)] == [(RWS_W, 100)],
       'CTL-181 transport: QJZ-89 12.7 mm, 100 rounds')
    ok(W[QBU]['HUDName'] == 'QBU-203' and not [r for r in SA.values() if r and r['UnitId'] in recon] and U[c]['HUDName'] == 'CTL-181', 'QQ fixes applied')
    rec['qq_fixes_1125'] = {'qbu': QBU, 'removed_cards': [r['Id'] for r in cards], 'ctl181_unit': c}
    print('QQ FIXES 1125', rec['qq_fixes_1125'])

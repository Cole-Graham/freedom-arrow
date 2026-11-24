"""PLA ZBL-08 Recon (ZZC-07) card for the MarkII_ model (Osama 23 Nov 2026 21:3x PST, thread "China cosmetic work": "just downlaoded the ZBL-08
recon, this is a recon variant with no missiles"). Made the way the existing China recon vehicles are (ZBD-04A Recon 1255 from ZBD-04A 902):
a copy of the PLA ZBL-08 (903) in the recon tab (CategoryType 0), vanilla "Very Good Optics" (sensor 3), its own armour and mobility rows, +10 pts
(40 -> 50), 4 cards in PLAGF Medium Combined Arms Brigade (21, wheeled, as ZTL-191 Recon). No missiles: only the 30 mm and Type 86 mounts are
copied; the ZBL-08's HJ-73D option (modification 2019086 and its option turrets) is not. Runs last; model work/c5-cn-1123 (models.json key = Name)."""
# HUD name ZZC-07 (Osama 24 Nov 01:1x, thread blue dragons: 'zbl-08 recon changed to zzc-07'). The internal Name stays: models.json and the card
# picture are keyed on it.
BASE, NAME, HUD, COST, SPEC, CARDS = 903, 'PLA ZBL-08 Recon', 'ZZC-07', 50, 21, 4
KEEP_TURRETS = (2009046, 2009054)   # PLA ZBL-08 mount 0 (30 mm) and mount 1 (Type 86 7.62 mm)
VGO = 3                             # vanilla sensor row "Very Good Optics", as ZBD-04A / ZTL-191 / ZTQ-15 Recon
LASER = 10                          # vanilla ability row "Laser Veh Default"
COMBINED = 2010731                  # smoke x1 + light supply + vehicle laser (the ZBD-251 row)


def apply(t, g, ok, rec):
    U, S, SA = t['Units'], t['SpecializationsJson'], t['SpecializationAvailabilitiesJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    ok(U[BASE]['Name'] == 'PLA ZBL-08' and U[BASE]['CategoryType'] == 2, 'ZBL-08 base row')
    ok(not any(u and NAME in (u.get('Name'), u.get('HUDName')) for u in U.values()), NAME + ' name free')
    ok(t['SensorsJson'][VGO]['Name'] == 'Very Good Optics', 'sensor 3 = Very Good Optics')
    ok(sorted(r['TurretId'] for r in rows('TurretUnitsJson', UnitId=BASE) if r['TurretId'] in KEEP_TURRETS) == sorted(KEEP_TURRETS), 'ZBL-08 base mounts')
    ok(S[SPEC]['UIName'].startswith('PLAGF Medium Combined Arms Brigade'), 'spec 21')
    # template = the ZTL-191 Recon's Motorized row; since 24 Nov 02:1x that card is hidden (ztl191_recon_removed_1124.py), so use its saved row
    tpl = next((r for r in rows('SpecializationAvailabilitiesJson', SpecializationId=SPEC) if U[r['UnitId']]['Name'] == 'PLA ZTL-191 Recon'), None) \
        or next(r[0] for u, (r, _) in rec.get('hidden_rows', {}).items() if U[u]['Name'] == 'PLA ZTL-191 Recon' and r and r[0]['SpecializationId'] == SPEC)
    d = dict(U[BASE]); d.pop('Id'); d.update({'Name': NAME, 'HUDName': HUD, 'Cost': COST, 'OriginalCost': 0, 'CategoryType': 0, 'DisplayInArmory': True,
                                              'Description': None, 'OriginalName': None})
    uid = g.put('Units', max(U) + 1, d)
    for tab, field, target in (('UnitArmorsJson', 'ArmorId', 'ArmorsJson'), ('UnitPropulsionsJson', 'MobilityId', 'MobilityJson')):
        for r in rows(tab, UnitId=BASE):
            g.add(tab, r, {'UnitId': uid, field: g.add(target, t[target][r[field]], {'Name': f'{t[target][r[field]]["Name"]} ZBL-08 Recon'})})
    # Osama 21:5x "make sure it can laser designate". Only the FIRST default ability row loads (0.9.6-dev.17 audit_mp_equipment: a second link to
    # row 10 'Laser Veh Default' was dropped), so the unit links ONE existing row that is the ZBL-08's 'Smoke x1 Supply Light Default' (2000212)
    # plus the vehicle laser of row 10 (1500 m, usable on the move): 2010731 'PLA ZBD-251 AbilitiesJson'. Existing row reused, no new row.
    (b0,) = rows('UnitAbilitiesJson', UnitId=BASE)
    A_ = t['AbilitiesJson'];sm, cmb = A_[b0['AbilityId']], A_[COMBINED]
    ok(b0['AbilityId'] == 2000212 and all(cmb[k] == (A_[LASER][k] if k in ('IsLaserDesignator', 'LaserMaxRange', 'LaserUsableInMove') else sm[k]) for k in sm if k not in ('Id', 'Name')),
       'row 2010731 = ZBL-08 smoke/supply row + row 10 laser')
    g.add('UnitAbilitiesJson', b0, {'UnitId': uid, 'AbilityId': COMBINED})
    kept_w = {w['WeaponId'] for tid in KEEP_TURRETS for w in rows('TurretWeaponsJson', TurretId=tid)}
    for r in rows('WeaponAmmunitionsJson', UnitId=BASE):
        if r['WeaponId'] in kept_w: g.add('WeaponAmmunitionsJson', r, {'UnitId': uid})   # HJ-73D ammo stays with the ZBL-08
    for r in rows('TurretUnitsJson', UnitId=BASE):
        if r['TurretId'] in KEEP_TURRETS: g.add('TurretUnitsJson', r, {'UnitId': uid})
    s0 = rows('SensorUnitsJson', UnitId=BASE)[0]; g.add('SensorUnitsJson', s0, {'UnitId': uid, 'SensorId': VGO})
    g.add('SpecializationAvailabilitiesJson', tpl, {'UnitId': uid, 'SpecializationId': SPEC, 'MaxAvailabilityXp0': CARDS})
    ok(not rows('ModificationsJson', UnitId=uid), 'no ATGM option')
    ok(sorted(r['TurretId'] for r in rows('TurretUnitsJson', UnitId=uid)) == sorted(KEEP_TURRETS), 'recon mounts = 30 mm + MG only')
    ok([r['SensorId'] for r in rows('SensorUnitsJson', UnitId=uid)] == [VGO], 'Very Good Optics')
    ok([r['AbilityId'] for r in rows('UnitAbilitiesJson', UnitId=uid)] == [COMBINED], 'one default ability: smoke/supply + laser designator')
    ok({r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=uid)} == kept_w, 'ammo only for 30 mm + MG')
    print('ZBL-08 RECON ammo', [(r['WeaponId'], t['AmmunitionsJson'][r['AmmunitionId']]['Name'], r.get('Quantity')) for r in rows('WeaponAmmunitionsJson', UnitId=uid)])
    rec['zbl08_recon'] = {'unit': uid, 'cost': COST, 'spec': SPEC, 'cards': CARDS, 'turrets': list(KEEP_TURRETS), 'sensor': VGO, 'abilities': [2000212, LASER]}
    print('ZBL-08 RECON', rec['zbl08_recon'])

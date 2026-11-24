"""PLA PLZ-25 card for the MarkII_ PLZ-25 model (Osama 23 Nov 2026 21:5x-22:0x PST, thread "China cosmetic work": "did we add the PLZ25? it should go
into navy", "PLZ-25 is a Vena clone, just make sure you change the name of the ammunition so the russian names aren't there").
A full copy of the vanilla 2S31 Vena (210): both loadout options (short 2A80 / long double), Laser Smoke ability 27, Good Optics, 100 pts, own
copies of its armour and mobility rows. So that no Russian name shows, its weapons (2A80 short/long, PKT), turrets and 120 mm rounds are own
renamed copies with identical stats: '120 mm gun-mortar', 'Type 86 7.62 mm', HE / HEAT / laser-guided / smoke (was '120mm Kitolov-2'). The
7.62x54mm belt stays the vanilla row (no Russian name). 3 cards in PLAN Naval/Special Forces (20) beside the PLZ-07B. Runs last; model work/c5-cn-1123
slug plz25 (models.json key = Name)."""
VENA, NAME, HUD, SPEC, CARDS = 210, 'PLA PLZ-25', 'PLZ-25', 20, 3
WEAP = {290: ('PLA PLZ-25 120 mm gun-mortar', '120 mm gun-mortar'), 558: ('PLA PLZ-25 120 mm gun-mortar (long)', '120 mm gun-mortar'),
        7: ('PLA PLZ-25 Type 86 7.62 mm', 'Type 86 7.62 mm')}
AMMO = {417: ('PLA PLZ-25 120 mm HE', '120 mm HE'), 187: ('PLA PLZ-25 120 mm HEAT', '120 mm HEAT'),
        415: ('PLA PLZ-25 120 mm laser-guided', '120 mm laser-guided'), 414: ('PLA PLZ-25 120 mm smoke', '120 mm smoke')}
RUSSIAN = ('2A80', 'PKT', 'Kitolov', 'Vena', 'Magnolia')


def apply(t, g, ok, rec):
    U, S, T, W, A = t['Units'], t['SpecializationsJson'], t['TurretsJson'], t['WeaponsJson'], t['AmmunitionsJson']

    def rows(tab, **kw):
        return sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])

    ok(U[VENA]['Name'] == '2S31 Vena', 'vanilla 2S31 Vena')
    ok(not any(u and NAME in (u.get('Name'), u.get('HUDName')) for u in U.values()), NAME + ' name free')
    ok(S[SPEC]['UIName'].startswith('PLAN Naval/Special Forces'), 'spec 20 = navy')
    tpl = next(r for r in rows('SpecializationAvailabilitiesJson', SpecializationId=SPEC) if U[r['UnitId']]['Name'] == 'PLA PLZ-07B')
    vt = [r['TurretId'] for r in rows('TurretUnitsJson', UnitId=VENA)]
    vw = {w['WeaponId'] for tid in vt for w in rows('TurretWeaponsJson', TurretId=tid)}
    va = {r['AmmunitionId'] for r in rows('WeaponAmmunitionsJson', UnitId=VENA)}
    ok(vw == set(WEAP) and va - {9} == set(AMMO), ('Vena weapons / rounds as read', vw, va))
    d = dict(U[VENA]); d.pop('Id')
    d.update({'Name': NAME, 'HUDName': HUD, 'OriginalCost': 0, 'CountryId': 4, 'DisplayInArmory': True, 'Description': None, 'OriginalName': None})
    uid = g.put('Units', max(U) + 1, d)
    for tab, field, target in (('UnitArmorsJson', 'ArmorId', 'ArmorsJson'), ('UnitPropulsionsJson', 'MobilityId', 'MobilityJson')):
        for r in rows(tab, UnitId=VENA):
            g.add(tab, r, {'UnitId': uid, field: g.add(target, t[target][r[field]], {'Name': f'PLA PLZ-25 {target}'})})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson'):
        for r in rows(tab, UnitId=VENA): g.add(tab, r, {'UnitId': uid})
    wmap = {w: g.add('WeaponsJson', W[w], {'Name': n, 'HUDName': h}) for w, (n, h) in WEAP.items()}
    amap = {a: g.add('AmmunitionsJson', A[a], {'Name': n, 'HUDName': h}) for a, (n, h) in AMMO.items()}
    tmap = {}
    for tid in vt:
        tmap[tid] = g.add('TurretsJson', T[tid], {'Name': T[tid]['Name'].replace('Vena Magnolia', 'PLZ-25')})
        for w in rows('TurretWeaponsJson', TurretId=tid): g.add('TurretWeaponsJson', w, {'TurretId': tmap[tid], 'WeaponId': wmap[w['WeaponId']]})
    for r in rows('TurretUnitsJson', UnitId=VENA): g.add('TurretUnitsJson', r, {'UnitId': uid, 'TurretId': tmap[r['TurretId']]})
    for r in rows('WeaponAmmunitionsJson', UnitId=VENA):
        g.add('WeaponAmmunitionsJson', r, {'UnitId': uid, 'WeaponId': wmap[r['WeaponId']], 'AmmunitionId': amap.get(r['AmmunitionId'], r['AmmunitionId'])})
    nopt = 0
    for m in rows('ModificationsJson', UnitId=VENA):
        nm = g.add('ModificationsJson', m, {'UnitId': uid})
        for o in rows('OptionsJson', ModificationId=m['Id']):
            tf = {k: tmap[v] for k, v in o.items() if k.startswith('Turret') and k.endswith('Id') and v in tmap}
            ok(all(not (k.startswith('Turret') and k.endswith('Id')) or not v or v in tmap for k, v in o.items()), ('option turrets mapped', o['Id']))
            g.add('OptionsJson', o, {'ModificationId': nm, **tf}); nopt += 1
    g.add('SpecializationAvailabilitiesJson', tpl, {'UnitId': uid, 'SpecializationId': SPEC, 'MaxAvailabilityXp0': CARDS})
    for tab in ('UnitAbilitiesJson', 'SensorUnitsJson', 'TurretUnitsJson', 'WeaponAmmunitionsJson', 'ModificationsJson', 'UnitArmorsJson', 'UnitPropulsionsJson'):
        ok(len(rows(tab, UnitId=uid)) == len(rows(tab, UnitId=VENA)), (NAME, tab, 'copied'))
    shown = [W[w['WeaponId']]['HUDName'] for r in rows('TurretUnitsJson', UnitId=uid) for w in rows('TurretWeaponsJson', TurretId=r['TurretId'])]
    shown += [A[r['AmmunitionId']]['HUDName'] for r in rows('WeaponAmmunitionsJson', UnitId=uid)]
    ok(not any(x in s for s in shown for x in RUSSIAN), ('no Russian names', shown))
    rec['plz25'] = {'unit': uid, 'cost': U[uid]['Cost'], 'spec': SPEC, 'cards': CARDS, 'options': nopt, 'weapons_ammo_shown': sorted(set(shown))}
    print('PLZ-25', rec['plz25'])

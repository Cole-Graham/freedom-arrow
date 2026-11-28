"""Airborne Tracked Carrier -> ZSD-251, 45 -> 35 pts (Osama 27 Nov 2026 15:5x, thread 1567745029781454889: "rename the Chinese airborne armored troop
carrier so that it's called ZSD-251. Make a model that takes off the missiles so the base version is 35 points with hmg and agl, and the missiles
for +10" / "The hmg and agl can fire simultaneously").
- Card name only (HUDName); the row Name 'PLA Airborne Tracked Carrier' stays, it is the FAModels models.json key.
- Base 35 = QLZ-87 AGL + QJC-88 12.7 mm, both on the one mount (points 0 and 1), so they fire at the same time (pla_light_brigade_carrier_1126);
  '+ 4x HJ-8H' stays +10. Model: no-missile default, the HJ-8H option keeps the armed model (work/model-rework-096/stage.py, work/zsd251-1127)."""
NAME, OLD, NEW, COST_OLD, COST, ATGM = 'PLA Airborne Tracked Carrier', 'Airborne Tracked Carrier', 'ZSD-251', 45, 35, 10


def apply(t, g, ok, rec):
    U, O, MO, TW, TU, W = t['Units'], t['OptionsJson'], t['ModificationsJson'], t['TurretWeaponsJson'], t['TurretUnitsJson'], t['WeaponsJson']
    (c,) = [i for i, u in U.items() if u and u.get('Name') == NAME]
    ok(U[c]['HUDName'] == OLD and U[c]['Cost'] == COST_OLD, ('carrier as read', U[c]['HUDName'], U[c]['Cost']))
    ok(not any(u and u.get('HUDName') == NEW for u in U.values()), 'ZSD-251 name free')
    mods = [m for m, r in MO.items() if r and r.get('UnitId') == c]
    opts = {r['Name']: r for r in O.values() if r and r.get('ModificationId') in mods}
    base, hj = opts['MainTurret Airborne Tracked Carrier AGL HMG'], opts['MainTurret Airborne Tracked Carrier HJ-8H']
    ok(base['IsDefault'] and base['Cost'] == 0 and hj['Cost'] == ATGM, 'default AGL + HMG free, HJ-8H +10')
    lay = sorted((r['Order'], W[r['WeaponId']]['HUDName']) for r in TW.values() if r and r.get('TurretId') == base['Turret0Id'])
    ok(lay == [(0, 'QLZ-87 35 mm AGL'), (1, 'QJC-88 12.7 mm')], ('AGL and 12.7 mm on one mount', lay))
    g.put('Units', c, {'HUDName': NEW, 'Cost': COST})
    rec['zsd251_1127'] = {'unit': c, 'name': NEW, 'cost': COST, 'hj8h_option': (hj['Id'], ATGM), 'default_mount': lay}
    print('ZSD-251', rec['zsd251_1127'])

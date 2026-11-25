"""ZTZ-99 LSDW price and LSDW panic speed (Osama 25 Nov 2026 12:2x PST, bugs thread 1573561286803980289: "For the ztz 99 not the a version, can we
make the price of the lsdw 60 points? ... I want it's panicking capability to just go down a bit it seems a bit fast. I think it does full panic in
about 8 seconds").
- ZTZ-99 (not 99A) option 'LSDW' +100 -> +60 (turret option, no swap row). The ZTZ-99A's LSDW (+100) and LSDW + GL-6 (+150) are unchanged.
- LSDW laser pulse 2019387 (ZTZ-99A, ZTZ-99, ZTZ-98) StressDamage 80 -> 70. Calculated, not measured: one pulse a second, armour ignored
  (0.08 damage), panic at 80% of a 1000 bar, no recovery between hits a second apart: 10 hits (~9.5 s) before, 12 hits (~11.5 s) after.
- Lynx Laser (Osama 12:2x "the laser lynx ground range should be 1,000 instead of 800"): its own round '50 kW laser pulse' GroundRange
  400 -> 500 (card 800 -> 1000 m). Helicopter range (LowAltRange 550) unchanged."""
ZTZ99, LSDW_AMMO, LYNX_AMMO = 'PLA Catalogue ZTZ-99', 2019387, 2021488


def apply(t, g, ok, rec):
    U, O, M, A = t['Units'], t['OptionsJson'], t['ModificationsJson'], t['AmmunitionsJson']
    (z,) = [i for i, u in U.items() if u and u.get('Name') == ZTZ99]
    opts = [i for i, o in O.items() if o and o.get('UIName') == 'LSDW' and M.get(o['ModificationId'], {}).get('UnitId') == z]
    ok(len(opts) == 1 and O[opts[0]]['Cost'] == 100 and not O[opts[0]].get('ReplaceUnitId'), ('ZTZ-99 LSDW option +100, no swap', opts))
    g.put('OptionsJson', opts[0], {'Cost': 60})
    ok(A[LSDW_AMMO]['HUDName'] == 'LSDW laser pulse' and A[LSDW_AMMO]['StressDamage'] == 80.0, 'LSDW pulse stress 80 before')
    g.put('AmmunitionsJson', LSDW_AMMO, {'StressDamage': 70.0})
    ok(O[opts[0]]['Cost'] == 60 and A[LSDW_AMMO]['StressDamage'] == 70.0, 'ZTZ-99 LSDW +60; LSDW stress 70')
    users = {r['UnitId'] for r in t['WeaponAmmunitionsJson'].values() if r and r['AmmunitionId'] == LYNX_AMMO}
    ok(A[LYNX_AMMO]['HUDName'] == '50 kW laser pulse' and A[LYNX_AMMO]['GroundRange'] == 400.0 and [U[x].get('HUDName') for x in users] == ['Lynx Laser'], 'Lynx Laser own pulse, ground 400')
    g.put('AmmunitionsJson', LYNX_AMMO, {'GroundRange': 500.0})
    ok(A[LYNX_AMMO]['GroundRange'] == 500.0, 'Lynx Laser ground range 500 (1000 m)')
    rec['ztz99_lsdw_1125'] = {'unit': z, 'option': opts[0], 'cost': [100, 60], 'stress': [80, 70], 'lynx_ground': [400, 500]}
    print('ZTZ99 LSDW', rec['ztz99_lsdw_1125'])

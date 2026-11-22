"""Card renames (Osama 22 Nov 2026 12:1x PST, thread 1572407822849810463: "Zbd-100 change to Type 100 CSV and then ZBD-20 change to vn-17").
HUDName only: the unit Names stay (FAModels models.json keys). The ZBD-100 loadout swap rows show the same name."""
def apply(t, g, ok, rec):
    U, O = t['Units'], t['OptionsJson']
    zb = [i for i, u in U.items() if u and (u.get('Name') or '').startswith('PLA ZBD-100')]
    z20 = [i for i, u in U.items() if u and u.get('Name') == 'PLA ZBD-20']
    ok(len(zb) == 4 and len(z20) == 1 and U[z20[0]]['HUDName'].strip() == 'ZBD-20', ('ZBD-100 rows', zb, 'ZBD-20', z20))
    for i in zb:
        g.put('Units', i, {'HUDName': 'Type 100 CSV'})
    g.put('Units', z20[0], {'HUDName': 'VN-17'})
    sw = [o['Id'] for o in O.values() if o and o.get('ReplaceUnitName') == 'ZBD-100']
    for o in sw:
        g.put('OptionsJson', o, {'ReplaceUnitName': 'Type 100 CSV'})
    ok(all(U[i]['HUDName'] == 'Type 100 CSV' for i in zb) and U[z20[0]]['HUDName'] == 'VN-17', 'renamed')
    rec['rename_1122'] = {'Type 100 CSV': zb, 'VN-17': z20, 'swap_names': sw}

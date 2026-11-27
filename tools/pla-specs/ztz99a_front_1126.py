"""ZTZ-99A front armour (Osama 26 Nov 2026 22:5x PST, thread 1567745029781454889: "ZTZ-99A front armor to 750/950").
Armour row 2009063 'PLA ZTZ-99A ArmorsJson' (only the ZTZ-99A, unit 904, uses it): KinArmorFront 850 -> 750, HeatArmorFront 1075 -> 950.
Sides, rear, top and health unchanged. The ZTZ-99A2 / 99G (800 / 1100) and ZTZ-99 (700 / 850) rows are not touched. Not yet tested in a game."""
ZTZ99A, ARMOR = 904, 2009063


def apply(t, g, ok, rec):
    U, AR = t['Units'], t['ArmorsJson']
    users = [r['UnitId'] for r in t['UnitArmorsJson'].values() if r and r['ArmorId'] == ARMOR]
    ok(U[ZTZ99A]['HUDName'] == 'ZTZ-99A' and users == [ZTZ99A], ('ZTZ-99A armour row, own row', users))
    a = AR[ARMOR]; before = (a['KinArmorFront'], a['HeatArmorFront'])
    ok(before == (850, 1075), ('ZTZ-99A front before', before))
    g.put('ArmorsJson', ARMOR, {'KinArmorFront': 750, 'HeatArmorFront': 950})
    rec['ztz99a_front_1126'] = {'armor': ARMOR, 'front_ke_heat': [before, (AR[ARMOR]['KinArmorFront'], AR[ARMOR]['HeatArmorFront'])]}
    print('ZTZ-99A FRONT', rec['ztz99a_front_1126'])

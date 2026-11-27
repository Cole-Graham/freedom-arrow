"""ZTZ-99 front armour (Osama 26 Nov 2026 22:5x PST, thread 1567745029781454889: "ZTZ-99A front armor to 750/950", corrected 22:58 "No I meant
the ZTZ-99 not the 99A"). Replaces ztz99a_front_1126.py (never in a build): the ZTZ-99A stays 850 / 1075.
Armour row 2011373 'PLA ZTZ-99 ArmorsJson' (only the ZTZ-99, unit 1083 'PLA Catalogue ZTZ-99', uses it): KinArmorFront 700 -> 750,
HeatArmorFront 850 -> 950. Sides, rear, top and health unchanged. Not yet tested in a game."""
ZTZ99, ARMOR, ZTZ99A, ARMOR_A = 1083, 2011373, 904, 2009063


def apply(t, g, ok, rec):
    U, AR = t['Units'], t['ArmorsJson']
    users = [r['UnitId'] for r in t['UnitArmorsJson'].values() if r and r['ArmorId'] == ARMOR]
    ok(U[ZTZ99]['HUDName'] == 'ZTZ-99' and users == [ZTZ99], ('ZTZ-99 armour row, own row', users))
    a = AR[ARMOR]; before = (a['KinArmorFront'], a['HeatArmorFront'])
    ok(before == (700, 850), ('ZTZ-99 front before', before))
    g.put('ArmorsJson', ARMOR, {'KinArmorFront': 750, 'HeatArmorFront': 950})
    ok((AR[ARMOR_A]['KinArmorFront'], AR[ARMOR_A]['HeatArmorFront']) == (850, 1075), 'ZTZ-99A unchanged')
    rec['ztz99_front_1126'] = {'armor': ARMOR, 'front_ke_heat': [before, (AR[ARMOR]['KinArmorFront'], AR[ARMOR]['HeatArmorFront'])]}
    print('ZTZ-99 FRONT', rec['ztz99_front_1126'])

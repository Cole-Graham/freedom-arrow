"""ZTZ-100 front KE back to 750 (Osama 27 Nov 2026 18:0x PST, thread 1567745029781454889: "ZTZ-100 back to 750 front KE armor").
Own armour row 2010183 (unit 968 only); front HEAT and the rest unchanged."""
ROW, UNIT = 2010183, 968


def apply(t, g, ok, rec):
    AR, UA = t['ArmorsJson'], t['UnitArmorsJson']
    ok({r['UnitId'] for r in UA.values() if r and r['ArmorId'] == ROW} == {UNIT}, 'ZTZ-100 own armour row')
    old = AR[ROW]['KinArmorFront']
    g.put('ArmorsJson', ROW, {'KinArmorFront': 750})
    rec['osama_ztz100_ke_1127'] = {'row': ROW, 'front_ke': [old, 750], 'front_heat': AR[ROW]['HeatArmorFront']}
    print('ZTZ-100 KE', rec['osama_ztz100_ke_1127'])

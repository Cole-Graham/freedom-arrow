"""ZTQ-15 Light side HEAT 250 -> 100 (Osama 27 Nov 2026 17:5x PST, thread 1567745029781454889: "ztq-15 light side armor heat to 100").
Own armour row 2018999 (unit 1268 only); no armour loadouts. After osama_m8_ztq15_1127 (front 100 / 150)."""
ROW, UNIT = 2018999, 1268


def apply(t, g, ok, rec):
    AR, UA = t['ArmorsJson'], t['UnitArmorsJson']
    ok({r['UnitId'] for r in UA.values() if r and r['ArmorId'] == ROW} == {UNIT} and AR[ROW]['HeatArmorSides'] == 250, ('ZTQ-15 Light side HEAT', AR[ROW]['HeatArmorSides']))
    g.put('ArmorsJson', ROW, {'HeatArmorSides': 100})
    rec['osama_ztq15_side_1127'] = {'row': ROW, 'side_heat': [250, 100]}
    print('ZTQ-15 SIDE', rec['osama_ztq15_side_1127'])

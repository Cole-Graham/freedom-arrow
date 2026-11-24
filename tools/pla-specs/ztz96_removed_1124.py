"""Base ZTZ-96 card removed (Osama 24 Nov 2026 03:0x PST, thread 1567745029781454889: "ah ok we will not use it then, remove the unit",
"remove it next build"). Its only good model was cgmodel 826690, whose textures are War Thunder files, so it stayed on Osama's PC; the public
build showed the ZTZ-96A model on it. The ZTZ-96A (1082) and ZTZ-96B cards are not changed.
- ztz96_rocket_force_1123.py (PLARF, 6 cards; 23 Nov 21:4x, withdrawn and restored 24 Nov) is no longer run. Instead its row is recorded as the
  card's old row in rec['hidden_rows'], so the card shows in the China hidden-units test spec 26 with 6 cards; DisplayInArmory False.
- Unit, weapon and ammunition rows stay. Runs before test_specs_1123.py."""
UNIT, ZTZ96A, ROCKET = 949, 1082, 19


def apply(t, g, ok, rec):
    U, SA, TA = t['Units'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson']
    ok(U[UNIT]['Name'] == 'PLA ZTZ-96' and not any(r and r['UnitId'] == UNIT for r in SA.values()) and not any(r and r['UnitId'] == UNIT for r in TA.values()),
       'base ZTZ-96: in no spec, no transport links')
    tpl = [r for r in SA.values() if r and r['UnitId'] == ZTZ96A]
    ok(len(tpl) == 1 and U[ZTZ96A]['HUDName'] == 'ZTZ-96A' and U[ZTZ96A]['DisplayInArmory'], 'ZTZ-96A card row (template, unchanged)')
    old = dict(tpl[0]); old.update({'UnitId': UNIT, 'SpecializationId': ROCKET, 'MaxAvailabilityXp0': 6})
    rec.setdefault('hidden_rows', {})[UNIT] = ([old], [])   # for test_specs_1123.py: the PLARF row it had (6 cards)
    g.put('Units', UNIT, {'DisplayInArmory': False})
    ok(U[UNIT]['DisplayInArmory'] is False, 'base ZTZ-96 hidden in the Armory')
    rec['ztz96_removed'] = {'unit': UNIT, 'ztz96a_row': tpl[0]['Id']}
    print('ZTZ-96 removed', rec['ztz96_removed'])

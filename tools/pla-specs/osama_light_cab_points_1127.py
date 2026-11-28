"""Osama 27 Nov 2026 23:0x PST, thread 1567745029781454889: "this is the US socom spec point distribution, China's light cab should be 1000 recon
instead and give the 250 to the vehicle tab, then the helo tab takes 250 and gives it to support giving it total 500 for support". PLAGF Light
Combined Arms Brigade (spec 70) points = the vanilla Special Operations Forces (spec 13: recon 1250, infantry 1250, vehicles 0, support 250,
helicopters 1000, aircraft 1250) with recon -250 -> vehicles and helicopters -250 -> support: recon 1000, infantry 1250, vehicles 250, support 500,
helicopters 750, aircraft 1250 (5000 total, as SOF). Slots and logistics are not changed. Put-only."""
LIGHT, SOF = 70, 13
NEW = {'ReconPoints': 1000, 'InfantryPoints': 1250, 'CombatPoints': 250, 'SupportPoints': 500, 'HelicoptersPoints': 750, 'AirPoints': 1250}


def apply(t, g, ok, rec):
    S = t['SpecializationsJson']
    ok(S[SOF].get('ReconPoints') == 1250 and (S[SOF].get('CombatPoints') or 0) == 0 and S[SOF].get('SupportPoints') == 250 and S[SOF].get('HelicoptersPoints') == 1000, 'vanilla SOF points')
    sof = sum(S[SOF].get(k) or 0 for k in NEW)
    ok(sum(NEW.values()) == sof == 5000, ('same total as SOF', sum(NEW.values()), sof))
    before = {k: S[LIGHT].get(k) for k in list(NEW) + ['LogisticsPoints']}
    slots = {k: S[LIGHT].get(k) for k in ('ReconSlots', 'InfantrySlots', 'CombatSlots', 'SupportSlots', 'HelicoptersSlots', 'AirSlots', 'MaxSlots')}
    g.put('SpecializationsJson', LIGHT, NEW)
    rec['osama_light_cab_points_1127'] = {'before': before, 'after': {k: S[LIGHT].get(k) for k in list(NEW) + ['LogisticsPoints']}, 'slots_unchanged': slots}
    print('LIGHT CAB POINTS', rec['osama_light_cab_points_1127'])

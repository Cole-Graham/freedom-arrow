"""PF-98 tripod crewed like the SPG-9 (Osama 25 Nov 2026 00:3x PST, thread "blue dragons": "notice the pf-98 with the tripod that goes to
the PLARF and that should be rigged like an SPG 9m"). Weapon 2016259 'PLA PF-98 tripod' used the RPG-29 stand-in model (shoulder-fired
animation); vanilla SPG-9M rows 159/663 are the same weapon type (62 RocketLauncher) with ModelFileName SPG9 (tripod on the ground, crew
around it). Sets ModelFileName SPG9 on 2016259 only; FAModels draws the new tripod PF-98 model (w_pf98t) on it. Nothing else changes."""


def apply(t, g, ok, rec):
    W = t['WeaponsJson']
    ok(W[159]['ModelFileName'] == 'SPG9' and W[159]['Type'] == 62, 'vanilla SPG-9M 159 = SPG9, type 62')
    ok(W[2016259]['HUDName'] == 'PF-98 (tripod)' and W[2016259]['Type'] == 62 and W[2016259]['ModelFileName'] == 'RPG29', ('PF-98 tripod 2016259', W[2016259]['ModelFileName']))
    g.put('WeaponsJson', 2016259, {'ModelFileName': 'SPG9'})
    ok(W[2016259]['ModelFileName'] == 'SPG9', 'PF-98 tripod uses the SPG-9 model/crew')
    rec['pf98_tripod_spg9'] = {'weapon': 2016259, 'model': ['RPG29', 'SPG9']}
    print('PF-98 TRIPOD', rec['pf98_tripod_spg9'])

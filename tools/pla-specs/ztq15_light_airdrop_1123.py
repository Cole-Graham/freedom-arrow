"""ZTQ-15 Light can be air-dropped (Osama 23 Nov 2026 19:5x PST, thread 1567745029781454889: "ZTQ-15 light should have paradrop ability").
Air-drop is Mobility.IsAirDroppable (vanilla BMD-4M). The ZTQ-15 Light (unit 1268, PLAAF Air Force) moves on its own mobility row 2019001
'PLA ZTQ-15 MobilityJson', used by no other unit and by no loadout option, so that row changes in place (ability-row-reuse rule: no new row).
No vanilla air-droppable row has the same movement values to link instead."""
UNIT, MOB = 1268, 2019001


def apply(t, g, ok, rec):
    U, UP, MB, O, M = (t[k] for k in ('Units', 'UnitPropulsionsJson', 'MobilityJson', 'OptionsJson', 'ModificationsJson'))
    ok(U[UNIT]['HUDName'] == 'ZTQ-15 Light' and [r['MobilityId'] for r in UP.values() if r and r['UnitId'] == UNIT] == [MOB], 'ZTQ-15 Light mobility row')
    ok([r['UnitId'] for r in UP.values() if r and r.get('MobilityId') == MOB] == [UNIT] and not any(o and o.get('MobilityId') == MOB for o in O.values()),
       'mobility row used only by the ZTQ-15 Light')
    mods = {i for i, m in M.items() if m and m['UnitId'] == UNIT}
    ok(not any(o and o['ModificationId'] in mods and o.get('MobilityId') for o in O.values()), 'no loadout option overrides its mobility')
    ok(MB[MOB]['IsAirDroppable'] is False and any(r and r.get('IsAirDroppable') for r in MB.values()), 'not air-droppable yet; vanilla rows use the flag')
    g.put('MobilityJson', MOB, {'IsAirDroppable': True})
    ok(MB[MOB]['IsAirDroppable'] is True, 'ZTQ-15 Light air-droppable')
    rec['ztq15_light_airdrop'] = {'unit': UNIT, 'mobility': MOB}
    print('ZTQ-15 LIGHT AIRDROP', rec['ztq15_light_airdrop'])

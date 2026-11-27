"""PLA Light Brigade build, H-6K high altitude only (Osama 26 Nov 2026 21:0x PST, thread 1567745029781454889: "H-6 should not low fly").
Branch codex/batch/osama/pla-light-brigade only; the last plb section.
- The H-6K (919) is the only H-6. Its mobility 'Plane H-6K FA' (2019704, used by no other unit) copies the Tu-22M3 fly preset 4 'BigFast Tu22'
  with IsChangeAltitude on, so the player can order it down to low altitude. The vanilla heavy bombers (B-52H, Tu-95, Tu-142, Tu-160, B-2, B-21)
  have IsChangeAltitude off: they stay at high altitude. The H-6K gets the same: IsChangeAltitude off. LowAltitudeIsDefault is off on preset 4,
  so it flies high. Speed, turn and loiter are unchanged. Not yet tested in a game."""
import re
H6K, MOB = 919, 2019704


def apply(t, g, ok, rec):
    U, MO = t['Units'], t['MobilityJson']
    users = [r['UnitId'] for r in t['UnitPropulsionsJson'].values() if r and r['MobilityId'] == MOB]
    ok(U[H6K]['HUDName'] == 'H-6K' and users == [H6K] and MO[MOB]['IsChangeAltitude'] is True, ('H-6K mobility, own row, can change altitude', users))
    ok(not t['FlyPresetsJson'][MO[MOB]['FlyPresetId']]['LowAltitudeIsDefault'], 'fly preset: high altitude by default')
    ok([i for i, u in U.items() if u and re.search(r'(^|[^A-Z])H-6', u['HUDName'])] == [H6K], 'only one H-6')
    g.put('MobilityJson', MOB, {'IsChangeAltitude': False})
    rec['pla_light_brigade_h6_1126'] = {'mobility': MOB, 'IsChangeAltitude': MO[MOB]['IsChangeAltitude']}
    print('PLA LIGHT BRIGADE H-6K', rec['pla_light_brigade_h6_1126'])

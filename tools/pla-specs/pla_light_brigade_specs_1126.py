"""PLA Light Brigade build, spec moves (Osama 26 Nov 2026 01:4x PST, thread 1567745029781454889: "China marines get ZTL-11 and ZTQ-15 From Medium CAB";
"ZTQ-15 Recon goes to Medium CAB"). Branch codex/batch/osama/pla-light-brigade only. Each card row keeps its availability and category; only its spec changes.
- ZTQ-15 (906, row 2008168) and ZTL-11 (938, row 2008225): PLAGF Medium Combined Arms Brigade (21) -> PLAN Naval/Special Forces (20, the China marines).
- ZTQ-15 Recon (1240, row 2016073): PLAGF Heavy Combined Arms Brigade (18) -> Medium Combined Arms Brigade (21)."""
MOVES = [(2008168, 906, 'ZTQ-15', 21, 20), (2008225, 938, 'ZTL-11', 21, 20), (2016073, 1240, 'ZTQ-15 Recon', 18, 21)]


def apply(t, g, ok, rec):
    U, SA = t['Units'], t['SpecializationAvailabilitiesJson']
    out = []
    for row, unit, name, old, new in MOVES:
        r = SA[row]
        ok(r['UnitId'] == unit and U[unit]['HUDName'] == name and r['SpecializationId'] == old, ('card row before', name, row))
        ok(not [x for x in SA.values() if x and x['UnitId'] == unit and x['SpecializationId'] == new], (name, 'not already in spec', new))
        g.put('SpecializationAvailabilitiesJson', row, {'SpecializationId': new})
        ok(SA[row]['SpecializationId'] == new, (name, 'moved'))
        out.append((name, old, new))
    rec['pla_light_brigade_specs_1126'] = out
    print('PLA LIGHT BRIGADE SPECS', out)

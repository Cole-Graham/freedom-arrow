"""PLA Light Brigade build, Mountain Leopards price (Osama 26 Nov 2026 20:4x PST, thread 1567745029781454889: "Mountain leopards 110").
Branch codex/batch/osama/pla-light-brigade only; the last plb section.
- Mountain Leopards 高原雪豹 (1186, Light CAB, no loadouts): 100 -> 110 pts."""
ML = 1186


def apply(t, g, ok, rec):
    U = t['Units']
    ok(U[ML]['HUDName'] == 'Mountain Leopards 高原雪豹' and U[ML]['Cost'] == 100 and not U[ML].get('OriginalCost'), 'Mountain Leopards 100 pts')
    ok(not [m for m in t['ModificationsJson'].values() if m and m.get('UnitId') == ML], 'no loadouts')
    g.put('Units', ML, {'Cost': 110})
    rec['pla_light_brigade_late5_1126'] = {'mountain_leopards': 110}
    print('PLA LIGHT BRIGADE LATE5', rec['pla_light_brigade_late5_1126'])

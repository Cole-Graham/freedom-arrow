"""France (Preview) 24 and Germany (Preview) 25: battlegroup size 0 (Osama 24 Nov 2026 02:0x PST, thread "China cosmetic work": "set the french
and germany specs to 0 battlegroup size"). Every *Slots and *Points field and MaxSlots -> 0, so a Eurocorp battlegroup holds no cards; the
cards stay viewable in the Armory (ShowInHangar unchanged)."""
SPECS = {24: 'France (Preview)', 25: 'Germany (Preview)'}


def apply(t, g, ok, rec):
    S = t['SpecializationsJson']; before = {}
    for i, ui in SPECS.items():
        ok(S[i]['UIName'] == ui, (i, ui))
        keys = [k for k in S[i] if k.endswith('Slots') or k.endswith('Points')]
        ok('MaxSlots' in keys and len(keys) >= 15, (i, 'slot/point fields', keys))
        before[i] = {k: S[i][k] for k in keys}
        g.put('SpecializationsJson', i, {k: 0 for k in keys})
    ok(all(S[i][k] == 0 for i in SPECS for k in before[i]) and all(S[i]['ShowInHangar'] for i in SPECS), 'France/Germany battlegroup size 0, still in the Armory')
    rec['euro_bg_zero'] = before
    print('EURO BG 0', {i: before[i]['MaxSlots'] for i in SPECS})

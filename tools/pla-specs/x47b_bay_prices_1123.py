"""X-47B bay prices (Osama 23 Nov 2026 22:1x PST, thread 1567745029781454889: "X-47 Aim 120 loadout to +15 each bay, AIM-260 to +40 each bay").
Port and starboard bay (modifications 2001579 / 2001585): 2x AIM-120 AMRAAM 35 -> 15 (default, so the card price drops by 40 with both bays),
2x AIM-260 JATM 60 -> 40. Bomb and missile options unchanged."""
X47 = 969
NEW = {'2x AIM-120 AMRAAM': (35, 15), '2x AIM-260 JATM': (60, 40)}


def apply(t, g, ok, rec):
    U, O, M = t['Units'], t['OptionsJson'], t['ModificationsJson']
    bays = sorted(m for m, x in M.items() if x and x['UnitId'] == X47)
    ok(U[X47]['HUDName'] == 'X-47B' and bays == [2001579, 2001585], ('X-47B bays', bays))
    out = {}
    for m in bays:
        for o in sorted((o for o in O.values() if o and o['ModificationId'] == m and o['UIName'] in NEW), key=lambda o: o['Id']):
            old, new = NEW[o['UIName']]
            ok(o['Cost'] == old, (o['Id'], o['UIName'], 'price before', o['Cost']))
            g.put('OptionsJson', o['Id'], {'Cost': new}); out[o['Id']] = [o['UIName'], old, new]
    ok(len(out) == 4, ('4 options changed', out))
    rec['x47b_bay_prices'] = out
    print('X-47B BAYS', out)

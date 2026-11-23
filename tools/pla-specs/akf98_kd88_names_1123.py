"""AKF-98A <-> KD-88 names swapped (Osama 23 Nov 2026 00:1x PST, thread 1572407822849810463: "we didn't swap the missile names?", with a QQ
player's screenshot; QQ sheet FA-002/032, option A of 20 Nov: names only). Our KD-88 rows are the Kh-59MK cluster cruise missile and our AKF-98A rows
the AGM-65 Maverick copy; in real life AKF-98A is the stealthy cruise missile and KD-88 the shorter guided air-to-surface missile. Only the names move
(weapon/round Name and HUDName, and the loadout names that mention them); every plane keeps its weapons, stats and icons."""
import re

SWAP = {'AKF-98A': 'KD-88', 'KD-88': 'AKF-98A'}


def swap(s):
    return re.sub(r'AKF-98A|KD-88', lambda m: SWAP[m.group(0)], s) if s else s


def apply(t, g, ok, rec):
    W, A, O = t['WeaponsJson'], t['AmmunitionsJson'], t['OptionsJson']
    hit = lambda r, *k: any(re.search(r'AKF-98A|KD-88', r.get(x) or '') for x in k)
    ws = [i for i, w in W.items() if w and hit(w, 'Name', 'HUDName')]
    am = [i for i, a in A.items() if a and hit(a, 'Name', 'HUDName')]
    op = [i for i, o in O.items() if o and hit(o, 'Name', 'UIName')]
    ok((len(ws), len(am), len(op)) == (4, 2, 7) and A[2016552]['HUDName'] == 'KD-88' and A[2016661]['HUDName'] == 'AKF-98A'
       and A[2016552]['GroundRange'] > A[2016661]['GroundRange'], ('AKF-98A / KD-88 rows before', ws, am, op))
    before = {i: (A[i]['HUDName'], A[i]['GroundRange']) for i in am}
    for tab, ids, keys in (('WeaponsJson', ws, ('Name', 'HUDName')), ('AmmunitionsJson', am, ('Name', 'HUDName')), ('OptionsJson', op, ('Name', 'UIName'))):
        for i in ids:
            g.put(tab, i, {k: swap(t[tab][i][k]) for k in keys})
    ok(A[2016552]['HUDName'] == 'AKF-98A' and A[2016661]['HUDName'] == 'KD-88' and all(A[i]['GroundRange'] == before[i][1] for i in am),
       'long-range cruise round is now AKF-98A, short guided round KD-88; ranges unchanged')
    rec['akf98_kd88_names'] = {'weapons': {i: W[i]['HUDName'] for i in ws}, 'rounds': {i: A[i]['HUDName'] for i in am}, 'options': {i: O[i]['UIName'] for i in op}}
    print('AKF98', rec['akf98_kd88_names'])

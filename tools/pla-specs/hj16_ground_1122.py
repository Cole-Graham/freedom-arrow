"""HJ-16 ground only (Osama 22 Nov 2026 17:5x PST, thread 1567745029781454889: "They should all be ground only", after public feedback in #dev
from General Raticus: "why can the HJ-16 ATGM semi-active or fire-and-forget version hit helicopters?"). Vanilla has no AT missile that can
target helicopters (all 59 AT / gun-launched missile rows: no helicopter bit, LowAltRange 0); the only vanilla vehicle-and-helicopter guided
missile is the Hellfire SHORAD on dedicated AA units. Three HJ-16 rounds still could:
  2019312 ZBD-20 HJ-16 (semi-active) and 2019313 ZBD-20 HJ-16 IIR: on the ZBD-20 (VN-17 card, 945) and ZBD-20 Recon (1256); made in 0.9.0-dev.14
    (Osama 16 Nov "ZBD-20 gets 1300 low alt range"), 550 since 0.9.0-dev.32;
  2014656 ZBD-251 HJ-16 (row named 'PLA HJ-10', HJ-10 stats): on the ZBD-251 (1056) since 0.8.0-dev.55, low altitude 1000.
Each gets the ground-only target set of the ZBL-191 HJ-16 (TargetType 36, LowAltRange 0, HighAltRange 0). Everything else stays.
The AFT-10's HJ-10 (2010725, also 44 / 1000) is not an HJ-16 and is left as it is. Called from batch_0_9_5b.py."""

ROUNDS = (2019312, 2019313, 2014656)


def apply(t, g, ok, rec):
    A = t['AmmunitionsJson']
    ok(all(A[i]['HUDName'].startswith('HJ-16') and A[i]['TargetType'] == 44 and A[i]['LowAltRange'] > 0 for i in ROUNDS),
       ('HJ-16 rounds with helicopter targeting before', {i: (A[i]['HUDName'], A[i]['TargetType'], A[i]['LowAltRange']) for i in ROUNDS}))
    ok(A[2010339]['HUDName'] == 'HJ-16' and (A[2010339]['TargetType'], A[2010339]['LowAltRange'], A[2010339]['HighAltRange']) == (36, 0.0, 0.0),
       'ZBL-191 HJ-16 2010339 = the ground-only pattern')
    for i in ROUNDS:
        g.put('AmmunitionsJson', i, {'TargetType': 36, 'LowAltRange': 0.0, 'HighAltRange': 0.0})
    ok(not [i for i, r in A.items() if r and str(r.get('HUDName', '')).startswith('HJ-16') and (r['TargetType'] & 8 or r.get('LowAltRange', 0) > 0)],
       'no HJ-16 round can target helicopters')
    rec['hj16_ground'] = {'rounds': list(ROUNDS), 'TargetType': [44, 36], 'LowAltRange': 'to 0'}

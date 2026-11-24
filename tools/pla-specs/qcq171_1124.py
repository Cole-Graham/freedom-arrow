"""QCW-05 -> QCQ-171, cosmetic only (Osama 24 Nov 2026 02:1x PST, thread "blue dragons": "Let's replace the QCW-05 with the QCQ-171, it's a cosmetic
change only", then "make sure it shows 9mmx19mm").
- Weapon 2013349 (6 China squads): HUDName QCW-05 -> QCQ-171, HUDIcon FA_PLA_WP_QCW05 -> FA_PLA_WP_QCQ171 (work/qcq171-icon/make_icon.py from his render).
- Its round 2013350: HUDName '5.8 mm SMG ammunition' -> '9x19 mm SMG ammunition'.
No stat changes. The soldiers still hold the MP5SD model (no QCQ-171 3D model)."""
import os
WID, AID, ICON = 2013349, 2013350, 'FA_PLA_WP_QCQ171'
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'mod', 'source', 'runtime-qa', 'icons')


def apply(t, g, ok, rec):
    W, A = t['WeaponsJson'], t['AmmunitionsJson']
    ok(all(os.path.isfile(os.path.join(DIR, ICON + s + '.png')) for s in ('', '_OUTLINE')), ICON + ' + outline in runtime-qa/icons')
    ok(W[WID]['HUDName'].strip() == 'QCW-05' and A[AID]['HUDName'] == '5.8 mm SMG ammunition', ('QCW-05 weapon + round', W[WID]['HUDName'], A[AID]['HUDName']))
    ok(sorted({r['WeaponId'] for r in t['WeaponAmmunitionsJson'].values() if r and r['AmmunitionId'] == AID}) == [WID], 'round used by the QCW-05 only')
    ok([w['Id'] for w in W.values() if w and 'QCW' in (w.get('HUDName') or '')] == [WID], 'one QCW weapon row')
    before = (W[WID]['HUDName'], W[WID].get('HUDIcon'), A[AID]['HUDName'])
    g.put('WeaponsJson', WID, {'HUDName': 'QCQ-171', 'HUDIcon': ICON})
    g.put('AmmunitionsJson', AID, {'HUDName': '9x19 mm SMG ammunition'})
    after = (W[WID]['HUDName'], W[WID]['HUDIcon'], A[AID]['HUDName'])
    ok(after == ('QCQ-171', ICON, '9x19 mm SMG ammunition'), ('QCQ-171', after))
    rec['qcq171_1124'] = {'before': before, 'after': after}
    print('QCQ-171', rec['qcq171_1124'])

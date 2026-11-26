"""PGL-625 main gun at 7 damage/s (Osama 25 Nov 2026 23:0x PST, bugs thread 1573561286803980289: "PGL625 main gun should have 7 dps. How come it
wasn't changed?"). Earlier: 24 Nov 10:5x 4.9 -> 3.5 damage (pgl625_lsdw_1124.py), which is 10.4/s on the card; the 7 damage/s request on 24 Nov
was the Lynx SPAAG's own round (lynx_spaag_dps_1124.py, later 6/s). The PGL-625 round 2009369 on the six-barrel 25 mm gun 2009365 (a
spaag-weapons.json gun: card DPS = Damage x shots/s without the magazine reload, 2.971 shots/s): Damage 3.5 -> 7 / 2.971 = 2.356. Only this round;
the Lynx SPAAG and the FK-2000 keep their own rounds. After lynx_spaag_dps_1124.py (which checks the PGL round is 3.5 before)."""
import json, os
from lynx_spaag_dps_1124 import rof, CFG
PGL_AMMO, GUN, TARGET = 2009369, 2009365, 7.0


def apply(t, g, ok, rec):
    U, W, A, WA = t['Units'], t['WeaponsJson'], t['AmmunitionsJson'], t['WeaponAmmunitionsJson']
    users = sorted({(r['UnitId'], U[r['UnitId']].get('HUDName')) for r in WA.values() if r and r['AmmunitionId'] == PGL_AMMO})
    ok(A[PGL_AMMO]['Damage'] == 3.5 and all(r['WeaponId'] == GUN for r in WA.values() if r and r['AmmunitionId'] == PGL_AMMO), ('PGL-625 gun round 3.5 on 2009365', users))
    listed = GUN in json.load(open(CFG))['weapons']
    r = rof(W[GUN], not listed); old = A[PGL_AMMO]['Damage']; new = round(TARGET / r, 3)
    g.put('AmmunitionsJson', PGL_AMMO, {'Damage': new})
    ok(abs(A[PGL_AMMO]['Damage'] * r - TARGET) < 0.01, ('PGL-625 card DPS 7', round(A[PGL_AMMO]['Damage'] * r, 3)))
    rec['pgl625_dps_1125'] = {'round': PGL_AMMO, 'users': users, 'shots_per_s': round(r, 4), 'damage': [old, new], 'dps': [round(old * r, 2), round(new * r, 2)]}
    print('PGL-625 DPS', rec['pgl625_dps_1125'])

"""Lynx SPAAG gun at 7 damage/s (Osama 24 Nov 2026 23:4x PST, thread "China cosmetic work": "the Lynx SPAAG should be 7 damage/s").
The gun is the PGL-625's six-barrel 25 mm weapon (2009365, shared, not changed) with its own round (lynx_rework_1124.py copy
'PLA Lynx SPAAG 625 six-barrel 25 mm gun ammunition'). Card DPS = Damage x RateOfFireSecond; 2009365 is in spaag-weapons.json, so the card
leaves out the magazine reload (SpaagWeapons.cs): 400 rounds, bursts of 11 at 0.2 s, 1.5-2.0 s between bursts = 2.971 shots/s.
Damage 3.5 (10.4/s) -> 6 / 2.971 = 2.019 (6.0/s; was 7 until Osama 25 Nov 00:2x "we'll drop this to 6 dps actually"). Only the Lynx round changes; the PGL-625 keeps 3.5. Changes one row."""
import json, os
NAME, TARGET = 'PLA Lynx SPAAG 625 six-barrel 25 mm gun ammunition', 6.0   # 25 Nov 00:2x "we'll drop this to 6 dps actually"
CFG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../mod/source/UserData/FreedomArrow/spaag-weapons.json')


def rof(w, reload):
    mag = max(1.0, w.get('MagazineSize') or 1); b = max(1.0, ((w.get('ShotsPerBurstMin') or 0) + (w.get('ShotsPerBurstMax') or 0)) / 2)
    tb = ((w.get('TimeBetweenBurstsMin') or 0) + (w.get('TimeBetweenBurstsMax') or 0)) / 2
    rl = ((w.get('MagazineReloadTimeMin') or 0) + (w.get('MagazineReloadTimeMax') or 0)) / 2 if reload else 0.0
    bursts = mag / b; cyc = max(0.0, mag - bursts) * (w.get('TimeBetweenShotsInBurst') or 0) + max(0.0, bursts - 1) * tb + rl
    return mag / cyc


def apply(t, g, ok, rec):
    U, W, A, WA = t['Units'], t['WeaponsJson'], t['AmmunitionsJson'], t['WeaponAmmunitionsJson']
    sp = [i for i, u in U.items() if u and u.get('Name') == 'PLA Lynx 66 SPAAG']
    am = [i for i, a in A.items() if a and a.get('Name') == NAME]
    ok(len(sp) == 1 and len(am) == 1, ('Lynx SPAAG unit and gun round', sp, am))
    links = [r for r in WA.values() if r and r['AmmunitionId'] == am[0]]
    ok([r['UnitId'] for r in links] == sp, ('round used only by the Lynx SPAAG', links))
    wid = links[0]['WeaponId']; listed = wid in json.load(open(CFG))['weapons']
    ok(listed, ('gun is a spaag-weapons.json gun (card DPS without reload)', wid))
    r = rof(W[wid], not listed); old = A[am[0]]['Damage']; new = round(TARGET / r, 3)
    g.put('AmmunitionsJson', am[0], {'Damage': new})
    ok(abs(A[am[0]]['Damage'] * r - TARGET) < 0.01, ('Lynx SPAAG card DPS', round(A[am[0]]['Damage'] * r, 3)))
    pgl = [x['AmmunitionId'] for x in WA.values() if x and x['WeaponId'] == wid and x['UnitId'] != sp[0]]
    ok(pgl and all(A[a]['Damage'] == 3.5 for a in pgl), ('PGL-625 round unchanged at 3.5', pgl))
    rec['lynx_spaag_dps_1124'] = {'round': am[0], 'weapon': wid, 'shots_per_s': round(r, 4), 'damage': [old, new], 'dps': [round(old * r, 2), round(new * r, 2)]}
    print('LYNX SPAAG DPS', rec['lynx_spaag_dps_1124'])

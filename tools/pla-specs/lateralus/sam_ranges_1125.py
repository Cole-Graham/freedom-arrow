"""SAM ranges brought into line (Lateralus 25 Nov 2026 11:0x PST, thread 1568104480459722894: items "1.-6. agreed", "AMRAAM: yes increase the burn",
"Osa and HQ-7B: leave them as they are [motors]", "queue it all"). Basis: "SAM missiles" tab of the Lateralus 0.9 Changelog sheet (best in-game range vs
ln(real range); in-game shown = table x 2 x radar multiplier). Each missile is matched to its nearest in-line real peer.
1. 57E6E Pantsir (20; Tunguska-M Pantsir round 234): Low 1200 -> 1100, High 1200 -> 900 (= AMRAAM on SA radar: 3300 / 1800 m).
2. FK-2000 SAM (2009607, FK-2000 and FK-3000): Low 1200 -> 1100, High 1200 -> 900 (= Tor-M2 / HQ-17A class).
3. HQ-6A (2010573, LR radar kept): Low 925 -> 800, High 925 -> 600 (3200 / 3600 m).
4. 9M96 (216, S-350): Low / High 975 -> 900 (= IRIS-T SLM: 3600 / 5400 m).
5. HQ-7B (2009449): Low 1050 -> 1100 (= Tor-M1/M2, HQ-17: 3300 m).
6. Osa-AKM 9M33M3 upgraded (452): Low 1100 -> 1050 (= base round 69: 3150 m).
AMRAAM ground (464): BurnTime 2.65 -> 3.35, so its catch range against a jet flying away at 225 covers its 3300 m range (2784 -> 3300 m shown, calculated).
Helicopter range in helicopter-range.json follows the new Low range for the rounds that can target helicopters. Runs after shorad_radar_1124 (which sets
the AMRAAM burn to 2.65)."""
RANGE = {20: ((1200, 1200), (1100, 900)), 234: ((1200, 1200), (1100, 900)), 2009607: ((1200, 1200), (1100, 900)), 2010573: ((925, 925), (800, 600)),
         216: ((975, 975), (900, 900)), 2009449: ((1050, 675), (1100, 675)), 452: ((1100, 675), (1050, 675))}
BURN = {464: (2.65, 3.35)}


def apply(t, g, ok, rec, heli):
    A = t['AmmunitionsJson'];out = {}
    for i, (old, new) in RANGE.items():
        a = A[i];ok((a['LowAltRange'], a['HighAltRange']) == old, (i, a['Name'], 'ranges before', (a['LowAltRange'], a['HighAltRange']), old))
        g.put('AmmunitionsJson', i, {'LowAltRange': float(new[0]), 'HighAltRange': float(new[1])})
        if str(i) in heli['ammo']:
            ok(heli['ammo'][str(i)] == old[0], (i, 'helicopter range before', heli['ammo'][str(i)]));heli['ammo'][str(i)] = float(new[0])
        out[i] = (a['Name'], old, new, str(i) in heli['ammo'])
    for i, (old, new) in BURN.items():
        ok(A[i]['BurnTime'] == old, (i, 'burn before', A[i]['BurnTime']));g.put('AmmunitionsJson', i, {'BurnTime': new});out[i] = (A[i]['Name'], 'BurnTime', old, new)
    rec['sam_ranges_1125'] = {str(k): v for k, v in out.items()}
    return out

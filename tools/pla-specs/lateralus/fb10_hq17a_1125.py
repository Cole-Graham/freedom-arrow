"""FB-10 = HQ-17A missile stat clone (Lateralus 25 Nov 2026 11:1x PST, thread 1568104480459722894: "Do you think the FB-10 should even be an AMRAAM
stat clone, what would be relatively realistic ranges and burn time ?", then "ok queue it" on the proposal).
Real FB-10A: about 17-18 km, about 7.5 km ceiling, radio command + imaging-IR terminal seeker (secondary sources): Tor-M2 / HQ-17A class, not AMRAAM.
Round 2009373 (PGL-625; the Lynx SPAAG carries QW-2 since the 24 Nov Lynx rework) takes every value of the HQ-17A missile 2010629 except its own name, icon, model, sound and impact effect.
Ranges stay 1100 / 900 (3300 / 1800 m on SA radar). Motor 600/300/2.65 s -> 700/350/2.7 s (ignition 0.15 s, launch 75): catch against a jet flying away
at 225 about 2784 -> 3880 m shown (calculated). Seeker Terminal guidance (50) -> Semi-active (100), as Tor / Pantsir; damage 15 -> 14, blast 15 -> 30,
fuse 12 -> 24, seeker range 700 -> 1600, seeker angle 140 -> 120, supply 125 -> 100. Runs after shorad_radar_1124 and sam_ranges_1125, so it copies the
HQ-17A's final values (burn 2.7 after option B). Replaces the 24 Nov AMRAAM clone (fb10_amraam_1124.py still runs first; its SA radar split stands)."""
FB10, HQ17A = 2009373, 2010629
KEEP = ('Id', 'Name', 'HUDName', 'HUDIcon', 'ModelFileName', 'AudioPreset', 'FXPreset',
        'LaunchMarginAngle', 'PreEgnitionRotationSpeed')   # vertical-launch fields (HQ-17A 180 / 600): the FB-10 fires from trainable pods, keeps 30 / 0


def apply(t, g, ok, rec, heli):
    A, WA = t['AmmunitionsJson'], t['WeaponAmmunitionsJson']
    ok(A[HQ17A]['HUDName'] == 'HQ-17A missile' and A[FB10]['HUDName'] == 'FB-10 ammunition', 'FB-10 and HQ-17A rows')
    ok((A[HQ17A]['LowAltRange'], A[HQ17A]['HighAltRange'], A[HQ17A]['BurnTime']) == (1100, 900, 2.7), ('HQ-17A after the SAM passes', A[HQ17A]['BurnTime']))
    ok(sorted({r['UnitId'] for r in WA.values() if r and r['AmmunitionId'] == FB10}) == [920], 'FB-10 user: PGL-625 only (Lynx SPAAG carries QW-2 since the 24 Nov Lynx rework)')
    before = {k: v for k, v in A[FB10].items() if k not in KEEP and A[HQ17A].get(k) != v}
    g.put('AmmunitionsJson', FB10, {k: v for k, v in A[HQ17A].items() if k not in KEEP})
    ok(all(A[FB10].get(k) == v for k, v in A[HQ17A].items() if k not in KEEP), 'FB-10 has every HQ-17A stat')
    if str(HQ17A) in heli['ammo']:heli['ammo'][str(FB10)] = heli['ammo'][str(HQ17A)]
    rec['fb10_hq17a_1125'] = {'round': FB10, 'from': HQ17A, 'changed': {k: [v, A[FB10][k]] for k, v in before.items()}}
    return rec['fb10_hq17a_1125']

"""Air-launched fast missiles at 600 and their prices (Osama 24 Nov 2026 21:1x PST, thread 1567745029781454889: "ok 600 is a good speed for air
launched balistic missiles. YJ-12, ARRW, MAKO, Khinzal ... set them all to 600 speed. Mig-31k to 220 (HE) cluster warhead, Cluster warhead +60.
B-52 ARRW loadout +250 each loadout (both options total 4x ARRW and total 600points for hte plane) F-35 MAKO's to +60 points").
Tested first on his PC: ARRW 1000 -> 900 -> 800 -> 700 -> 600 (Patriot engagement logs in work/arrw-intercept-1124).
- MaxSpeed 600: ARRW 2001364, MAKO 2002024, Kinzhal HE 455 / Cluster 919 / Nuke 340 (from 1000) and YJ-12 2016948 (from 500: faster).
  Every carrier shares these rounds (B-52H, B-21, F-22, F-35A/C, MiG-31K, MiG-31K (S), H-6K).
  21:2x ("YJ-21 should be 600 speed, F-22 MAKO options are also 60"): YJ-21 2016952 1000 -> 600; F-22 MAKO options 31000, 31001 80 -> 60.
- MiG-31K 318: Cost 300 -> 220 (HE warhead); Cluster warhead option 1747 0 -> 60. MiG-31K (S) 702 unchanged.
- B-52H 300: both 2x ARRW options (20157 bomb bay, 20158 wing pylons) 200 -> 250: 100 + 250 + 250 = 600 with 4 ARRW.
- F-35A / F-35C 1x MAKO options 31191, 31192, 31193, 31194 and F-22 31000, 31001: 80 -> 60. Not asked, so unchanged: B-21 ARRW (200), Kh-32."""
SPEED = {2001364: 'AGM-183A ARRW', 2002024: 'MAKO', 455: 'Kh-47M2 Kinzhal', 919: 'Kh-47M2 Kinzhal', 340: 'Kh-47M2 Kinzhal', 2016948: 'YJ-12', 2016952: 'YJ-21'}
MIG31K, CLUSTER, HE = 318, 1747, 1746
B52, B52_ARRW = 300, (20157, 20158)
MAKO_F35 = {31191: 294, 31192: 294, 31193: 741, 31194: 741, 31000: 297, 31001: 297}


def apply(t, g, ok, rec):
    A, U, O, M = t['AmmunitionsJson'], t['Units'], t['OptionsJson'], t['ModificationsJson']
    unit_of = lambda o: M[O[o]['ModificationId']]['UnitId']
    ok(all(A[i]['HUDName'] == n for i, n in SPEED.items()), ('rounds', SPEED))
    ok(all(A[i]['MaxSpeed'] == 1000.0 for i in SPEED if i != 2016948) and A[2016948]['MaxSpeed'] == 500.0, 'speeds before: 1000, YJ-12 500')
    ok(U[MIG31K]['HUDName'] == 'MiG-31K' and U[MIG31K]['Cost'] == 300 and O[CLUSTER]['UIName'] == 'Custom_Option_Cluster_warhead'
       and O[CLUSTER]['Cost'] == 0 and O[HE]['Cost'] == 0 and unit_of(CLUSTER) == unit_of(HE) == MIG31K, 'MiG-31K 300, warheads 0')
    ok(U[B52]['HUDName'] == 'B-52H Stratofortress' and U[B52]['Cost'] == 100
       and all(O[o]['UIName'] == '2x AGM-183A ARRW' and O[o]['Cost'] == 200 and unit_of(o) == B52 for o in B52_ARRW), 'B-52H 100, ARRW 2x200')
    ok(all(O[o]['UIName'] == '1x MAKO' and O[o]['Cost'] == 80 and unit_of(o) == u for o, u in MAKO_F35.items()), 'F-35A/C + F-22 MAKO 80')
    for i in SPEED:
        g.put('AmmunitionsJson', i, {'MaxSpeed': 600.0})
    g.put('Units', MIG31K, {'Cost': 220})
    g.put('OptionsJson', CLUSTER, {'Cost': 60})
    for o in B52_ARRW:
        g.put('OptionsJson', o, {'Cost': 250})
    for o in MAKO_F35:
        g.put('OptionsJson', o, {'Cost': 60})
    ok(all(A[i]['MaxSpeed'] == 600.0 for i in SPEED) and U[MIG31K]['Cost'] == 220 and O[CLUSTER]['Cost'] == 60
       and U[B52]['Cost'] + sum(O[o]['Cost'] for o in B52_ARRW) == 600 and all(O[o]['Cost'] == 60 for o in MAKO_F35), 'after')
    rec['air_hypersonic_600'] = {'speed': 600.0, 'rounds': sorted(SPEED), 'mig31k': 220, 'cluster': 60, 'b52_arrw_each': 250, 'f35_mako': 60}
    print('AIR 600', rec['air_hypersonic_600'])

"""China recon helicopters (Lateralus 23 Nov 2026 19:0x PST, thread 1572962048705429598), after recon_helis_us/ru_1123.py.
"Z-9WA Recon, Very Good / The "PLA Z-20 optics" sensor module shouldn't exist if there is an identical vanilla sensor module that can be used /
Z-20S, keep it Very Good / Z-11WB, change it to Very Good and delete its custom optics module. Also, make this a shared unit with PLAGF Armored
Force / AR-2000, keep it Very Good / Z-6B UAV, keep it Very Good".
- Z-9WA Recon 1133: Medium (2) -> Very Good (3), its own sensor link.
- Z-11WB 942: 'PLA Z-11WB optics' 2009769 (ground 1650, low 700, high 1000; used only by the Z-11WB) -> Very Good (3); row 2009769 removed.
  Also in PLAGF Armored Force (18), 4 cards like its Motorized row.
- 'PLA Z-20 optics' 2009259 (Z-20KA, Z-20J, Z-20) stays: no vanilla sensor row has its values (ground 1650, low 700, high 1000); the
  nearest, Good Optics (1), has low 1100. Its only identical row was the Z-11WB's, removed here.
- Cargo: every China recon helicopter already has 0. Z-20S, AR-2000 and Z-6B UAV unchanged (Very Good).
"""
VG = 3


def apply(t, g, ok, rec):
    U, SA, O, SU, SN, S = (t[k] for k in ('Units', 'SpecializationAvailabilitiesJson', 'OptionsJson', 'SensorUnitsJson', 'SensorsJson', 'SpecializationsJson'))
    def links(uid): return [r for r in SU.values() if r and r['UnitId'] == uid]
    ok(SN[VG]['Name'] == 'Very Good Optics' and (SN[VG]['OpticsGround'], SN[VG]['OpticsLowAltitude']) == (2300.0, 1250.0), 'sensor 3 = Very Good')
    # Z-9WA Recon
    z9 = links(1133)
    ok(U[1133]['HUDName'] == 'Z-9WA Recon' and [r['SensorId'] for r in z9] == [2], ('Z-9WA Recon on Medium', z9))
    g.put('SensorUnitsJson', z9[0]['Id'], {'SensorId': VG})
    # Z-11WB: Very Good, custom row removed, Armored Force
    z11 = links(942)
    ok(U[942]['HUDName'] == 'Z-11WB' and [r['SensorId'] for r in z11] == [2009769] and SN[2009769]['Name'] == 'PLA Z-11WB optics', ('Z-11WB custom optics', z11))
    ok([r['UnitId'] for r in SU.values() if r and r['SensorId'] == 2009769] == [942]
       and not any(o and 2009769 in (o.get('MainSensorId'), o.get('ExtraSensorId')) for o in O.values()), 'PLA Z-11WB optics used only by the Z-11WB')
    g.put('SensorUnitsJson', z11[0]['Id'], {'SensorId': VG})
    g.remove('SensorsJson', 2009769)
    ok(2009769 not in SN, 'PLA Z-11WB optics row removed')
    ok(S[18]['Name'] == 'PLA PLAGF Armored Force', 'spec 18 = Armored Force')
    sa = [r for r in SA.values() if r and r['UnitId'] == 942]
    ok([(r['SpecializationId'], r['MaxAvailabilityXp0']) for r in sa] == [(21, 4)], ('Z-11WB in Motorized only, 4 cards', sa))
    arm = g.add('SpecializationAvailabilitiesJson', sa[0], {'SpecializationId': 18})
    ok(sorted(r['SpecializationId'] for r in SA.values() if r and r['UnitId'] == 942) == [18, 21], 'Z-11WB shared: Armored Force + Motorized')
    # PLA Z-20 optics: keep unless a vanilla row is identical
    z20 = SN[2009259]
    same = [s['Id'] for s in SN.values() if s and s['Id'] != 2009259 and all(z20.get(k) == s.get(k) for k in z20 if k not in ('Id', 'Name'))]
    ok(same == [], ('PLA Z-20 optics has an identical row - use it', same))
    for uid in (1243, 1084, 1105):
        ok([r['SensorId'] for r in links(uid)] == [VG], (U[uid]['HUDName'], 'stays Very Good'))
    rec['recon_helis_cn_1123'] = {'z9wa_recon': [2, VG], 'z11wb': {'optics': [2009769, VG], 'removed_sensor': 2009769, 'armored_row': arm},
                                  'pla_z20_optics_kept': 'no identical vanilla row'}
    print('RECON HELIS CN', rec['recon_helis_cn_1123'])

"""China roster changes (Osama 23 Nov 2026 18:0x-18:1x PST, thread 1567745029781454889): "Hide VN-20 and VN-17 from the armory, ZTQ-15 from Armored
forces goes to motorized, hide VT-5 from the armory selection. VN-20, VN-17 and VT-5 should still be kept in the game just not useable right now",
"also hide ZTZ-98 and ZTZ-59", "Z-10K and Z-10U should swap names", 18:1x "HQ-6A hide from armory, PCL-181 hide from armory (we need to keep a
running list of units we're hiding and moving off the main build) ZSL-92 removed too", 18:2x "PLZ-70 removed", "PLL-05 moved to airborne", 18:3x "let's undo the Z-10 changes. Keep Z-10k in the PLAAF, Z-10 removed (hidden), Z-19G (and the recon) removed/hidden", "F-35 JASDF, let's hide this for now". The running list is docs/roster/hidden-units.md.
- Hidden (rows kept, so nothing that points to them breaks): out of every spec, off every transport list, DisplayInArmory False.
  VN20 (1274, Armored), VN-17 (945: the ZBD-20 used only as a transport, 8 transport links), VT-5 (1261, Motorized + PLAN SF) and VT-5 Recon
  (1262, Motorized), ZTZ-59 (1060 'PLA Catalogue Type 59', PLARF), ZTZ-98 ('PLA ZTZ-98', PLARF; only in the model build),
  PCL-181 (1034, Motorized), HQ-6A (1045, Motorized), ZSL-92 (1079: used only as a transport, 10 transport links), PLZ-70 (1040, PLAAF).
- ZTQ-15 (906): its Armored Force card (row 2008168, 6 cards) moves to PLAGF Motorized. ZTQ-15 Recon / Light unchanged.
- PLL-05 (926): its PLARF card (row 2008210, 3 cards) moves to the airborne spec, PLAAF Air Force (17).
- Z-10K (913, PLAAF) and Z-10U (1270, PLAN SF) keep their names (the 18:1x name swap is undone). Hidden too: Z-10 (1239 'PLA Air Force Z-10', PLAAF),
  Z-19G (1236) and Z-19G Recon (1237, both PLAN SF), F-35B (JASDF) (1291, Blue Dragon)."""

HIDE = {1274: 'VN20', 945: 'VN-17', 1261: 'VT-5', 1262: 'VT-5 Recon', 1060: 'ZTZ-59', 1034: 'PCL-181', 1045: 'HQ-6A', 1079: 'ZSL-92', 1040: 'PLZ-70', 1239: 'Z-10', 1236: 'Z-19G', 1237: 'Z-19G Recon', 1291: 'F-35B (JASDF)'}
ZTQ15, ZTQ15_ROW, ARMORED, MOTORIZED = 906, 2008168, 18, 21
Z10K, Z10U = 913, 1270


def apply(t, g, ok, rec):
    U, SA, TA, S = t['Units'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson'], t['SpecializationsJson']
    hide = dict(HIDE)
    z98 = [i for i, u in U.items() if u and u.get('Name') == 'PLA ZTZ-98']
    if z98: hide[z98[0]] = 'ZTZ-98'
    ok(all(U[i]['HUDName'] == h for i, h in hide.items()), ('cards to hide', {i: U[i]['HUDName'] for i in hide}))
    out = {}
    for uid, hud in hide.items():
        rows = [r['Id'] for r in SA.values() if r and r['UnitId'] == uid]
        links = [r['Id'] for r in TA.values() if r and (r['UnitId'] == uid or r['SpecializationAvailabilityId'] in rows)]
        rec.setdefault('hidden_rows', {})[uid] = ([dict(SA[i]) for i in rows], [dict(TA[i]) for i in links])   # for test_specs_1123.py
        for i in links: g.remove('TransportAvailabilitiesJson', i)
        for i in rows: g.remove('SpecializationAvailabilitiesJson', i)
        g.put('Units', uid, {'DisplayInArmory': False})
        out[hud] = {'unit': uid, 'spec_rows': rows, 'transport_links': links}
    ok(not any(r and r['UnitId'] in hide for r in SA.values()) and not any(r and r['UnitId'] in hide for r in TA.values())
       and all(U[i]['DisplayInArmory'] is False for i in hide), 'hidden cards: no spec, no transport link, not in the Armory')
    ok(SA[ZTQ15_ROW]['UnitId'] == ZTQ15 and SA[ZTQ15_ROW]['SpecializationId'] == ARMORED and S[MOTORIZED]['Name'] == 'PLA PLAGF Motorized'
       and not any(r and r['UnitId'] == ZTQ15 and r['SpecializationId'] == MOTORIZED for r in SA.values()), 'ZTQ-15 Armored row; Motorized free')
    g.put('SpecializationAvailabilitiesJson', ZTQ15_ROW, {'SpecializationId': MOTORIZED})
    ok([r['SpecializationId'] for r in SA.values() if r and r['UnitId'] == ZTQ15] == [MOTORIZED], 'ZTQ-15 only in Motorized')
    ok(U[926]['HUDName'] == 'PLL-05' and [(r['Id'], r['SpecializationId']) for r in SA.values() if r and r['UnitId'] == 926] == [(2008210, 19)]
       and S[17]['Name'] == 'PLA PLAAF Air Force', 'PLL-05 in PLARF only; PLAAF = airborne')
    g.put('SpecializationAvailabilitiesJson', 2008210, {'SpecializationId': 17})
    ok([r['SpecializationId'] for r in SA.values() if r and r['UnitId'] == 926] == [17], 'PLL-05 only in PLAAF (airborne)')
    ok((U[Z10K]['HUDName'], U[Z10U]['HUDName']) == ('Z-10K', 'Z-10U') and any(r and r['UnitId'] == Z10K and r['SpecializationId'] == 17 for r in SA.values()),
       'Z-10K (PLAAF) and Z-10U keep their names (swap undone)')
    rec['roster_1123b'] = {'hidden': out, 'ztq15': [ARMORED, MOTORIZED], 'pll05': [19, 17], 'z10_names_kept': [Z10K, Z10U]}
    print('ROSTER', rec['roster_1123b'])

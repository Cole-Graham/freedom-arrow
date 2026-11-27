"""MV-22B / CV-22B Osprey minigun loadout price (Osama 26 Nov 2026 19:4x PST, thread 1567745029781454889: "CV-22 and MV-22 GAU-15 loadouts should both
be +10"). The Ospreys' gun loadout is the GAU-17 minigun ("GAU-15" in the request; no GAU-15 exists in the data): vanilla option 366 'Option GAu17'
(MV-22B Osprey 80, USMC) +5 -> +10; option 662 'BellyTurret CV22 Minigun' (CV-22B Osprey 259, SOCOM) is already +10 and stays. Unit prices and the
unarmed options (+0) are unchanged. Not swap options (no unit change), so the swap-row price rule does not apply."""
MV22, CV22, MV_OPT, CV_OPT = 80, 259, 366, 662


def apply(t, g, ok, rec):
    U, O, MO = t['Units'], t['OptionsJson'], t['ModificationsJson']
    ok(U[MV22]['HUDName'] == 'MV-22B Osprey' and U[CV22]['HUDName'] == 'CV-22B Osprey', 'Ospreys')
    ok(MO[O[MV_OPT]['ModificationId']]['UnitId'] == MV22 and MO[O[CV_OPT]['ModificationId']]['UnitId'] == CV22, 'options belong to the Ospreys')
    ok(O[MV_OPT]['UIName'] == O[CV_OPT]['UIName'] == 'Custom_Option_GAU17_minigun' and O[MV_OPT]['Cost'] == 5 and O[CV_OPT]['Cost'] == 10, ('GAU-17 options', O[MV_OPT]['Cost'], O[CV_OPT]['Cost']))
    g.put('OptionsJson', MV_OPT, {'Cost': 10})
    ok(O[MV_OPT]['Cost'] == O[CV_OPT]['Cost'] == 10, 'both +10')
    rec['osprey_gau17_1126'] = {'MV-22B GAU-17': '+5 -> +10', 'CV-22B GAU-17': '+10 (unchanged)'}
    print('OSPREY GAU-17', rec['osprey_gau17_1126'])

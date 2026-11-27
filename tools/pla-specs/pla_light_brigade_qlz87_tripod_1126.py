"""PLA Light Brigade build, tripod QLZ-87 name (Osama 26 Nov 2026 10:4x PST, thread 1567745029781454889: "so the PLARF QLZ-87 is a tripod based system and
DIFFERNT (should say tripod in parenthesis) from the handheld QLZ-87. they should be two different weapons"). Branch codex/batch/osama/pla-light-brigade
only; after the QLZ-87 icon section (which checks the old name).
- They are already two weapon rows: the tripod QLZ-87 (2012157: QLZ-87 Team of the PLARF Rocket Reservists, Airborne QLZ-87 Team; tripod model AGS30)
  and the hand-held squad copy (Falcons, Tiger Brigade; QLU-11 model, pla_light_brigade_late_1126.py). Same stats. The tripod one's card / HUD name
  becomes 'QLZ-87 (tripod)'; the hand-held one stays 'QLZ-87'."""
QLZ87_TRIPOD = 2012157


def apply(t, g, ok, rec):
    W, U = t['WeaponsJson'], t['Units']
    hand = [i for i, w in W.items() if w and w.get('Name') == 'PLA infantry QLZ-87 squad (QLU-11 model)']
    ok(W[QLZ87_TRIPOD]['HUDName'] == 'QLZ-87' and W[QLZ87_TRIPOD]['ModelFileName'] == 'AGS30' and len(hand) == 1 and W[hand[0]]['HUDName'] == 'QLZ-87', 'tripod + hand-held QLZ-87 rows')
    g.put('WeaponsJson', QLZ87_TRIPOD, {'HUDName': 'QLZ-87 (tripod)'})
    users = sorted({U[m['UnitId']]['HUDName'] for m in t['SquadMembersJson'].values() if m and m.get('PrimaryWeaponId') == QLZ87_TRIPOD})
    ok(users == ['Airborne QLZ-87 Team', 'QLZ-87 Team'], ('tripod users', users))
    rec['pla_light_brigade_qlz87_tripod_1126'] = {'tripod': QLZ87_TRIPOD, 'hand_held': hand[0], 'tripod_users': users}
    print('QLZ-87 TRIPOD', rec['pla_light_brigade_qlz87_tripod_1126'])

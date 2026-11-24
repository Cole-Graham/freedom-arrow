"""China hidden-units test spec (Osama 23 Nov 2026 18:5x PST, thread 1567745029781454889): "we don't need to lock things away but we can just have a
hidden toggle for a China test spec that has all the units that we had removed that are largely complete", "we don't need a pin, just leave it as a
toggle, and I don't want EVERY single unit we had, just units we removed just now", "that old spec I think has a ton of old shit we don't want
anyone to even see".
- New spec 26 'PLA Test Hidden', a copy of the old Test spec 22 (64 slots and 100000 points per tab), ShowInHangar False. Spec 22 and its 35 old
  test cards are not changed and stay off.
- Cards: the China cards hidden on 23 Nov by roster_1123b.py and qbz95_qjz89_1123.py, each with its old card count (first old row) and the old
  transport options of that row. VN-17 (945) and ZSL-92 (1079) were transports only, so they get one card with the VN20 card count.
  F-35B (JASDF) is not a China unit and YJ-18 was removed from the game, so neither is here.
- The units get DisplayInArmory True again; they stay out of every other spec, so the normal Armory and deck creation still do not show them.
- The toggle is runtime-qa/TestSpec.cs: UserData/FreedomArrow/test-spec.json {"show": true} sets ShowInHangar True for spec 26 when the game loads
  its database (restart to change). No file = off. The packaged data is the same for every player."""
SPEC, TEMPLATE = 26, 22
NO_CARD = {945: 'VN-17', 1079: 'ZSL-92'}   # transports only: no old card
CARD_TEMPLATE = 1274                       # VN20


def apply(t, g, ok, rec):
    U, S, SA, TA = t['Units'], t['SpecializationsJson'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson']
    hidden = rec['hidden_rows']
    china = {uid: v for uid, v in hidden.items() if U[uid]['CountryId'] == 4}
    ok(set(hidden) - set(china) == {1291} and set(NO_CARD) <= set(china) and 1157 in china, ('hidden China cards', sorted(china)))
    ok(SPEC not in S and S[TEMPLATE]['Name'] == 'PLA Test' and S[TEMPLATE]['ShowInHangar'] is False, 'spec 26 free; old Test spec 22 off')
    g.put('SpecializationsJson', SPEC, {**{k: v for k, v in S[TEMPLATE].items() if k != 'Id'}, 'Name': 'PLA Test Hidden', 'UIName': 'Test: Hidden Units',
        'UIDescription': 'DEVELOPER TEST. China cards hidden from the main build on 23 Nov 2026. Not balanced. Switched on in UserData/FreedomArrow/test-spec.json.',
        'ShowInHangar': False})
    out = {}
    for uid, (rows, links) in sorted(china.items()):
        ok(bool(rows) != (uid in NO_CARD), (U[uid]['HUDName'], 'old card' if uid not in NO_CARD else 'transport only'))
        tpl = rows[0] if rows else china[CARD_TEMPLATE][0][0]
        new = g.add('SpecializationAvailabilitiesJson', tpl, {'UnitId': uid, 'SpecializationId': SPEC})
        own = [l for l in links if rows and l['SpecializationAvailabilityId'] == rows[0]['Id']]
        for l in own: g.add('TransportAvailabilitiesJson', l, {'SpecializationAvailabilityId': new})
        g.put('Units', uid, {'DisplayInArmory': True})
        out[U[uid]['HUDName']] = {'unit': uid, 'cards': SA[new]['MaxAvailabilityXp0'], 'transports': [l['UnitId'] for l in own]}
    ok(sorted(r['UnitId'] for r in SA.values() if r and r['SpecializationId'] == SPEC) == sorted(china), 'spec 26 = the hidden China cards')
    ok(all([r['SpecializationId'] for r in SA.values() if r and r['UnitId'] == uid] == [SPEC] for uid in china), 'hidden cards in no other spec')
    ok(all(S[s]['ShowInHangar'] is False for s in (TEMPLATE, SPEC)) and len([r for r in SA.values() if r and r['SpecializationId'] == TEMPLATE]) == 35,
       'spec 22 unchanged (35 cards); both test specs off in the data')
    rec['china_test_spec'] = {'spec': SPEC, 'name': S[SPEC]['UIName'], 'cards': out}
    print('CHINA TEST SPEC', rec['china_test_spec'])

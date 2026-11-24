"""Hidden-units test specs (Osama 23 Nov 2026, thread 1567745029781454889). 18:5x: "we don't need to lock things away but we can just have a hidden
toggle for a China test spec", "just leave it as a toggle", "that old spec I think has a ton of old shit we don't want anyone to even see";
19:3x: "in the hidden units why is there zbd04a and zsd-89? you can put all the hidden units here btw".
- One test spec per nation, each a copy of the old Test spec 22 (64 slots and 100000 points per tab), ShowInHangar False:
  26 China, 27 USA, 28 Russia. Spec 22 and its 35 old test cards are not changed and stay off.
- Cards: every card hidden on 23 Nov (docs/roster/hidden-units.md). Each section that hides a card records its old rows in rec['hidden_rows']:
  roster_1123b, qbz95_qjz89_1123, yj18_removed_1123, recon_helis_us_1123, recon_helis_ru_1123 (and on the model build type19_removed_1123).
  A card gets its old card count (first old row). VN-17 and ZSL-92 were transports only, so they get the VN20 card count (2).
- No transports: the Armory shows a spec's transports as cards too, so the QJZ-89 Team's ZBD-04A, ZSD-89A and Type 100 CSV showed in the
  China test spec. Infantry cards without transports exist in vanilla, so the infantry here walk.
- The units get DisplayInArmory True again; they stay out of every normal spec, so the normal Armory and deck creation still do not show them.
- The toggle is runtime-qa/TestSpec.cs: UserData/FreedomArrow/test-spec.json {"show": true} sets ShowInHangar True for specs 26-28 when the game
  loads its database (restart to change). No file = off. The packaged data is the same for every player."""
TEMPLATE = 22
SPECS = {4: (26, 'PLA Test Hidden', 'FA_CHINA_FLAG'), 2: (27, 'US Test Hidden', 'SPEC_US_Marines'), 1: (28, 'RU Test Hidden', 'SPEC_RU_VDV')}
NO_CARD = {945: 'VN-17', 1079: 'ZSL-92', 1308: 'ZBD-04 Rocket Force'}   # transports only: no old card (ZBD-04 RF: 24 Nov 03:1x)
CARD_TEMPLATE = 1274                       # VN20


def apply(t, g, ok, rec):
    U, S, SA = t['Units'], t['SpecializationsJson'], t['SpecializationAvailabilitiesJson']
    hidden = rec['hidden_rows']
    ok(all(U[uid]['CountryId'] in SPECS for uid in hidden) and set(NO_CARD) | {1157, 1129, 733, 728} <= set(hidden), ('hidden cards', sorted(hidden)))
    ok(all(SPECS[c][0] not in S for c in SPECS) and S[TEMPLATE]['Name'] == 'PLA Test' and S[TEMPLATE]['ShowInHangar'] is False,
       'specs 26-28 free; old Test spec 22 off')
    out = {}
    for country, (spec, name, icon) in SPECS.items():
        g.put('SpecializationsJson', spec, {**{k: v for k, v in S[TEMPLATE].items() if k != 'Id'}, 'CountryId': country, 'Name': name,
            'UIName': 'Test: Hidden Units', 'Icon': icon, 'ShowInHangar': False,
            'UIDescription': 'DEVELOPER TEST. Cards hidden from the main build on 23 Nov 2026. Not balanced. Switched on in UserData/FreedomArrow/test-spec.json.'})
        out[name] = {}
    for uid, (rows, links) in sorted(hidden.items()):
        ok(bool(rows) != (uid in NO_CARD), (U[uid]['HUDName'], 'old card' if uid not in NO_CARD else 'transport only'))
        spec, name, _ = SPECS[U[uid]['CountryId']]
        new = g.add('SpecializationAvailabilitiesJson', rows[0] if rows else hidden[CARD_TEMPLATE][0][0], {'UnitId': uid, 'SpecializationId': spec})
        g.put('Units', uid, {'DisplayInArmory': True})
        out[name][U[uid]['HUDName']] = {'unit': uid, 'cards': SA[new]['MaxAvailabilityXp0']}
    for country, (spec, name, _) in SPECS.items():
        mine = sorted(u for u in hidden if U[u]['CountryId'] == country)
        ok(sorted(r['UnitId'] for r in SA.values() if r and r['SpecializationId'] == spec) == mine, (name, 'test spec = the hidden cards of its nation'))
    ok(all([r['SpecializationId'] for r in SA.values() if r and r['UnitId'] == uid] == [SPECS[U[uid]['CountryId']][0]] for uid in hidden),
       'hidden cards in no other spec')
    rows = {s for s, _, _ in SPECS.values()}
    ok(not any(r and r['SpecializationAvailabilityId'] in {a['Id'] for a in SA.values() if a and a['SpecializationId'] in rows}
               for r in t['TransportAvailabilitiesJson'].values()), 'no transports in the test specs')
    ok(all(S[s]['ShowInHangar'] is False for s in rows | {TEMPLATE}) and len([r for r in SA.values() if r and r['SpecializationId'] == TEMPLATE]) == 35,
       'spec 22 unchanged (35 cards); all test specs off in the data')
    rec['test_specs'] = {'specs': {n: s for s, n, _ in SPECS.values()}, 'cards': out}
    print('TEST SPECS', rec['test_specs'])

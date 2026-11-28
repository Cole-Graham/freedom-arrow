"""Ground optics "Proposal W" (Lateralus 28 Nov 2026 10:4x PST, thread 1572962048705429598, "Ok queue up W proposal").
Ground optics tiers (raw, card metres = raw x 2) and the spotting cap of SpottingCap.cs:
  Bad 900 -> 450, Medium 1300 -> 700, Medium+ 1450 -> 925, Good 1650 -> 1375, Very Good 2300 -> 1950, Exceptional 2800 -> 2500 (2525 until 28 Nov 11:4x, Lateralus: "use 2500").
  Cap: per tier 500 / 600 / 700 / 875 / 1000 / 1200 -> one cap 1075 (2150 m) for every tier, 1300 (2600 m) for Exceptional.
Why: with the per-tier cap at 43-56% of the optics, every unit with stealth >= ~0.45 hit the cap in the open, so vehicles, recon vehicles and
infantry were all seen at the same range; and the card had to show the cap instead of the optics. With W the cap binds only for vehicles seen by
Good+ optics, stealth matters in the open again, and the card shows the real optics (SpottingCap.CardAfter). Stealth, cover 3 / 3.5, flash and
the forest walk (option B) are unchanged. Drones (4650 / 5250 / 6400, caps 2000 / 2250 / 2750) and air optics are unchanged.
Calculator: Optics and Stealth sheet 1oxreXr0ydZR2PD3pM3c74V2Ju6fBdpySVAq5KDZ-Wbo, tab "Proposal W". Existing rows only: every sensor row whose
ground optics is an FA tier value is rewritten in place, so all units on that row (any nation, ROC included) move together."""

TIERS = {900.0: 450.0, 1300.0: 700.0, 1450.0: 925.0, 1650.0: 1375.0, 2300.0: 1950.0, 2800.0: 2500.0}
GROUND_CAP, EXCEPTIONAL_CAP = 1075.0, 1300.0
# OpticsGround -> cap (raw) for spotting-caps.json. 0 = planes, 50 = blind optics, drones keep their 0.9.3 caps.
CAPS = {0.0: 0.0, 50.0: 50.0, **{w: (EXCEPTIONAL_CAP if w == 2500.0 else GROUND_CAP) for w in TIERS.values()},
        4650.0: 2000.0, 5250.0: 2250.0, 6400.0: 2750.0}
# Card names (Lateralus 28 Nov 2026 11:5x: "look up how we implemented the terminology before" - 0.4 dev.19/20 optics-names.json, colours and
# Exceptional I-IV as then). The card shows the ground tier name; its tooltip gives the true open-ground distances (SpottingCap.CardAfter).
NAMES = {'Colors': {'red': '#FF1744', 'orange': '#FF9100', 'green': '#39FF14', 'blue': '#00B0FF', 'grey': '#9E9E9E'},
         'Ground': [[0, 'None', 'grey'], [50, 'Blind', 'red'], [450, 'Bad', 'red'], [700, 'Medium', 'orange'], [925, 'Medium+', 'orange'],
                    [1375, 'Good', 'green'], [1950, 'Very Good', 'green'], [2500, 'Exceptional I', 'blue'], [4650, 'Exceptional II', 'blue'],
                    [5250, 'Exceptional III', 'blue'], [6400, 'Exceptional IV', 'blue']]}


def apply(t, g, ok, rec):
    S = t['SensorsJson']
    moved = {}
    for sid, s in S.items():
        if s and s.get('OpticsGround') in TIERS:
            old = s['OpticsGround']
            g.put('SensorsJson', sid, {'OpticsGround': TIERS[old]})
            moved.setdefault(f'{old:g}->{TIERS[old]:g}', []).append(sid)
    ok(not [sid for sid, s in S.items() if s and s.get('OpticsGround') in TIERS], 'no sensor left on an old FA ground tier')
    # Every sensor a deck unit uses must be capped (or be one of the two China rows that already sat at vanilla-scale 500 / 600 and stay uncapped).
    SA = t['SpecializationAvailabilitiesJson']
    deck = {r['UnitId'] for r in SA.values() if r} | {r['UnitId'] for r in t['TransportAvailabilitiesJson'].values() if r and r.get('SpecializationAvailabilityId') in SA}
    used = {S[r['SensorId']]['OpticsGround'] for r in t['SensorUnitsJson'].values() if r and r.get('UnitId') in deck and r.get('SensorId') in S}
    ok(used <= set(CAPS) | {500.0, 600.0}, ('deck sensor without a cap', sorted(used - set(CAPS))))
    rec['optics_w_1128'] = {'tiers_raw': {f'{k:g}': v for k, v in TIERS.items()}, 'caps_raw': {f'{k:g}': v for k, v in CAPS.items()},
                            'sensor_rows': {k: len(v) for k, v in moved.items()}, 'deck_ground_values': sorted(used)}
    ok([n[0] for n in NAMES['Ground']] == sorted({0.0, 50.0, *TIERS.values(), 4650.0, 5250.0, 6400.0}), 'a card name for every ground tier')
    return {'OpticsGroundCaps': {f'{k:g}': v for k, v in sorted(CAPS.items())}}, NAMES

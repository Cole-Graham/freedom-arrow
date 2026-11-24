"""Type 100 CSV as a transport only (Osama 24 Nov 2026 01:0x PST, thread 1567745029781454889: "Just leave the CSV as a transport then only, not on
its own"). MODEL BUILD ONLY. After type100_fix_1124.py.
Since type100_fix_1124 the Armored Force showed two 'Type 100 CSV' cards: the recon card (unit 1294, 4 cards) and the transport copy (1416) of its 6
infantry teams. The recon card row goes; the transport copy and its four-way loadout stay. Unit 1294 and its swap rows stay in the data (no spec)."""
BASE = 'PLA ZBD-100'


def apply(t, g, ok, rec):
    U, SA, TA = t['Units'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson']
    (u,) = [i for i, x in U.items() if x and x.get('Name') == BASE]
    (tr,) = [i for i, x in U.items() if x and x.get('Name') == BASE + ' transport']
    card = [r for r in SA.values() if r and r['UnitId'] == u]
    ok([(r['SpecializationId'], r['MaxAvailabilityXp0']) for r in card] == [(18, 4)], ('Type 100 CSV recon card', card))
    for r in card: g.remove('SpecializationAvailabilitiesJson', r['Id'])
    links = [r for r in TA.values() if r and r['UnitId'] == tr]
    ok(not any(r and r['UnitId'] == u for r in SA.values()) and len(links) == 6 and not any(r and r['UnitId'] == u for r in TA.values()),
       'Type 100 CSV: no card of its own; transport on 6 infantry cards')
    rec['type100_transport_only'] = {'removed_card': [r['Id'] for r in card], 'transport_unit': tr, 'transport_links': len(links)}
    print('TYPE100 TRANSPORT ONLY', rec['type100_transport_only'])

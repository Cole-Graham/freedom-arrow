"""X-47B to the Marines (Osama 23 Nov 2026 20:4x PST, thread 1567745029781454889: "X-47 moved to Marines in the Air tab").
Its only card row 2001591 (Air Naval, 2 cards) moves to the USMC spec (3); same card count. The Air tab comes from the unit (a plane)."""
X47, ROW, AIR_NAVAL, USMC = 969, 2001591, 5, 3


def apply(t, g, ok, rec):
    U, SA, S = t['Units'], t['SpecializationAvailabilitiesJson'], t['SpecializationsJson']
    ok(U[X47]['HUDName'] == 'X-47B' and S[USMC]['UIName'] == 'ui_spec_usmc_name' and S[USMC]['CountryId'] == 2, 'X-47B card; spec 3 = USMC')
    ok([(r['Id'], r['SpecializationId']) for r in SA.values() if r and r['UnitId'] == X47] == [(ROW, AIR_NAVAL)], 'X-47B only in Air Naval')
    g.put('SpecializationAvailabilitiesJson', ROW, {'SpecializationId': USMC})
    ok([r['SpecializationId'] for r in SA.values() if r and r['UnitId'] == X47] == [USMC], 'X-47B only in the Marines')
    rec['x47b_marines'] = {'unit': X47, 'row': ROW, 'spec': [AIR_NAVAL, USMC], 'cards': SA[ROW]['MaxAvailabilityXp0']}
    print('X-47B MARINES', rec['x47b_marines'])

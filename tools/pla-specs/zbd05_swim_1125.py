"""ZBD-05 family swims at 50 (Osama 25 Nov 2026 01:2x PST, thread "China cosmetic work": "for the ZBD-05 family they should swim at 50 ...
they're extremely fast in the water. That includes PLZ-25, ZSD-05, ZTD-05, ZBD-05"). MaxSpeedWater (same km/h scale as MaxSpeedRoad;
vanilla amphibious units 18-25, most 20) -> 50 on every card whose HUDName is one of the four, and their loadout rows (Name = card Name + ' ...').
A mobility row also used by a unit outside the family is copied for the family first. Changes / adds mobility rows only."""
FAMILY = ('ZBD-05', 'ZTD-05', 'ZSD-05', 'PLZ-25')
WATER = 50.0


def apply(t, g, ok, rec):
    U, M, UP = t['Units'], t['MobilityJson'], t['UnitPropulsionsJson']
    cards = {i: u['Name'] for i, u in U.items() if u and u.get('CountryId') == 4 and (u.get('HUDName') or '').strip() in FAMILY and '(old' not in u['Name']}   # not the hidden '(old)' rows
    ok(sorted({U[i]['HUDName'].strip() for i in cards}) == sorted(FAMILY), ('all four cards found', {U[i]['HUDName'] for i in cards}))
    units = {i for i, u in U.items() if u and '(old' not in (u.get('Name') or '') and any(u.get('Name') == n or (u.get('Name') or '').startswith(n + ' ') for n in cards.values())}
    rows = [r for r in UP.values() if r and r['UnitId'] in units]
    ok(rows and all(M[r['MobilityId']].get('IsAmphibious') for r in rows), ('family amphibious', [(U[r['UnitId']]['Name'], M[r['MobilityId']].get('IsAmphibious')) for r in rows]))
    before = {}; copies = {}
    for r in rows:
        mid = r['MobilityId']
        users = {x['UnitId'] for x in UP.values() if x and x['MobilityId'] == mid}
        before.setdefault(mid, M[mid]['MaxSpeedWater'])
        if users - units:
            if mid not in copies: copies[mid] = g.add('MobilityJson', M[mid], {'Name': f"{M[mid]['Name']} ZBD-05 family swim"})
            g.put('UnitPropulsionsJson', r['Id'], {'MobilityId': copies[mid]})
    for r in rows: g.put('MobilityJson', r['MobilityId'], {'MaxSpeedWater': WATER})
    rows = [r for r in UP.values() if r and r['UnitId'] in units]
    ok(all(M[r['MobilityId']]['MaxSpeedWater'] == WATER for r in rows), 'family swims at 50')
    outside = [x for x in UP.values() if x and x['UnitId'] not in units and M[x['MobilityId']]['MaxSpeedWater'] == WATER]
    ok(not outside, ('no other unit changed', [(U[x['UnitId']]['Name'], x['MobilityId']) for x in outside]))
    rec['zbd05_swim_1125'] = {'units': sorted((i, U[i]['Name']) for i in units), 'water_before': before, 'copied_rows': copies}
    print('ZBD-05 SWIM', rec['zbd05_swim_1125'])

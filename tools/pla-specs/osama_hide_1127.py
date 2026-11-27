"""Hidden and renamed (Osama 27 Nov 2026 04:2x-04:4x PST, thread 1572407822849810463): "ZSD-89 removed from the game (hidden)", "J-10S hidden because
of poor modal quiality", "ZSD-05 ZZC (rename ZZC-05)".
- Hidden as roster_1123b.py does (rows kept, so nothing that points to them breaks): out of every spec, off every transport list, DisplayInArmory False.
  The whole ZSD-89 family: ZSD-89 (1064) and ZSD-89A (1065, 1248), which are transports only, plus the already hidden ZSD-89 copies 1246/1249/1250
  (their transport links go too). J-10S (955, PLAAF 2 cards).
- 'PLA ZSD-05 ZZC' (6007) shown as ZZC-05.
- Armored Force Combat Engineers (card 2012374) rode only the ZSD-89A: its transport link 2018139 now points to the ZBD-04A (902), as the Mech.
  Rifles' (same 7 men). Any other squad that loses its last transport option fails the check."""
HIDE = {1064: 'ZSD-89', 1065: 'ZSD-89A', 1248: 'ZSD-89A', 1246: 'ZSD-89', 1249: 'ZSD-89A', 1250: 'ZSD-89A', 955: 'J-10S'}
ZZC = 6007
ENG_LINK, ZBD04A = 2018139, 902


def apply(t, g, ok, rec):
    U, SA, TA = t['Units'], t['SpecializationAvailabilitiesJson'], t['TransportAvailabilitiesJson']
    ok(all(U[i]['HUDName'] == h for i, h in HIDE.items()), ('units to hide', {i: U[i]['HUDName'] for i in HIDE}))
    ok(U[ZZC]['Name'] == 'PLA ZSD-05 ZZC' and U[ZZC]['HUDName'] == 'ZSD-05 ZZC', 'ZSD-05 ZZC is 6007')
    ok(TA[ENG_LINK]['UnitId'] == 1248 and U[SA[TA[ENG_LINK]['SpecializationAvailabilityId']]['UnitId']]['HUDName'].startswith('Combat Engineers')
       and U[ZBD04A]['HUDName'] == 'ZBD-04A', 'Combat Engineers ZSD-89A link')
    g.put('TransportAvailabilitiesJson', ENG_LINK, {'UnitId': ZBD04A})
    before = {}
    for r in TA.values():
        if r: before.setdefault(r['SpecializationAvailabilityId'], set()).add(r['UnitId'])
    out = {}
    for uid, hud in HIDE.items():
        rows = [r['Id'] for r in SA.values() if r and r['UnitId'] == uid]
        links = [r['Id'] for r in TA.values() if r and (r['UnitId'] == uid or r['SpecializationAvailabilityId'] in rows)]
        rec.setdefault('hidden_rows', {})[uid] = ([dict(SA[i]) for i in rows], [dict(TA[i]) for i in links])
        for i in links: g.remove('TransportAvailabilitiesJson', i)
        for i in rows: g.remove('SpecializationAvailabilitiesJson', i)
        g.put('Units', uid, {'DisplayInArmory': False})
        out[uid] = {'name': hud, 'spec_rows': rows, 'transport_links': len(links)}
    after = {}
    for r in TA.values():
        if r: after.setdefault(r['SpecializationAvailabilityId'], set()).add(r['UnitId'])
    stranded = sorted(s for s in before if s in SA and before[s] and not after.get(s))
    ok(not stranded, ('squad cards left without any transport', [(s, U[SA[s]['UnitId']]['HUDName']) for s in stranded]))
    ok(not any(r and r['UnitId'] in HIDE for r in SA.values()) and not any(r and r['UnitId'] in HIDE for r in TA.values())
       and all(U[i]['DisplayInArmory'] is False for i in HIDE), 'hidden: no spec, no transport link, not in the Armory')
    g.put('Units', ZZC, {'HUDName': 'ZZC-05'})
    rec['osama_hide_1127'] = {'hidden': out, 'renamed': {ZZC: 'ZZC-05'}, 'combat_engineers_transport': {ENG_LINK: 'ZBD-04A'}}
    print('HIDE 1127', {k: (v['name'], len(v['spec_rows']), v['transport_links']) for k, v in out.items()})

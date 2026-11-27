"""PLA Light Brigade build, Light CAB transport trim (Osama 26 Nov 2026 02:5x PST, thread 1567745029781454889: "ZSL-191 should go to medium cab not
Light CAB, ZBD-05 and ZSD-05 should be PLAN"). Branch codex/batch/osama/pla-light-brigade only; after every Light CAB card exists (last plb section).
- None of the three has a card of its own; they are transport choices. Their transport rows on Light CAB cards go: ZSL-191 (1403) from Moto. Riflemen
  (it stays on its 10 Medium CAB cards); ZBD-05 (1413) and ZSD-05 (1412) from every Light CAB card (they stay on the PLAN cards).
- Every Light CAB card that had a transport keeps at least one (checked)."""
ZSL191, ZSD05, ZBD05, PLAN, MEDIUM = 1403, 1412, 1413, 20, 21


def apply(t, g, ok, rec):
    U, SA, S = t['Units'], t['SpecializationAvailabilitiesJson'], t['SpecializationsJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    light = next(s['Id'] for s in S.values() if s and s.get('UIName', '').startswith('PLAGF Light Combined Arms Brigade'))
    ok([U[u]['HUDName'] for u in (ZSL191, ZSD05, ZBD05)] == ['ZSL-191', 'ZSD-05', 'ZBD-05'] and not any(rows('SpecializationAvailabilitiesJson', UnitId=u) for u in (ZSL191, ZSD05, ZBD05)),
       'ZSL-191, ZSD-05, ZBD-05: transport only')
    spec_of = lambda r: SA[r['SpecializationAvailabilityId']]['SpecializationId']
    cards = {c['Id'] for c in rows('SpecializationAvailabilitiesJson', SpecializationId=light)}
    had = {c for c in cards if rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=c)}
    before = {u: (sum(spec_of(r) == PLAN for r in rows('TransportAvailabilitiesJson', UnitId=u)), sum(spec_of(r) == MEDIUM for r in rows('TransportAvailabilitiesJson', UnitId=u)))
              for u in (ZSL191, ZSD05, ZBD05)}
    removed = []
    for u in (ZSL191, ZSD05, ZBD05):
        for r in rows('TransportAvailabilitiesJson', UnitId=u):
            if r['SpecializationAvailabilityId'] in cards:
                g.remove('TransportAvailabilitiesJson', r['Id']); removed.append((U[SA[r['SpecializationAvailabilityId']]['UnitId']]['HUDName'], U[u]['HUDName']))
    # checks after
    ok(not [r for r in t['TransportAvailabilitiesJson'].values() if r and r['UnitId'] in (ZSL191, ZSD05, ZBD05) and r['SpecializationAvailabilityId'] in cards], 'none left in the Light CAB')
    after = {u: (sum(spec_of(r) == PLAN for r in rows('TransportAvailabilitiesJson', UnitId=u)), sum(spec_of(r) == MEDIUM for r in rows('TransportAvailabilitiesJson', UnitId=u)))
             for u in (ZSL191, ZSD05, ZBD05)}
    ok(after == before and after[ZSL191][1] > 0 and after[ZSD05][0] > 0 and after[ZBD05][0] > 0, ('PLAN / Medium CAB rows unchanged', before, after))
    left = {U[SA[c]['UnitId']]['HUDName']: [U[r['UnitId']]['HUDName'] for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=c)] for c in had}
    ok(all(left.values()), ('every Light CAB card keeps a transport', left))
    rec['pla_light_brigade_transports2_1126'] = {'removed': removed, 'light_cab_transports': left}
    print('PLA LIGHT BRIGADE TRANSPORT TRIM', len(removed), 'rows', left)

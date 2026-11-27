"""PLA Light Brigade build, late changes 2 (Osama 26 Nov 2026 16:3x PST, thread 1567745029781454889). Branch codex/batch/osama/pla-light-brigade
only; the last plb section, so no earlier row id moves.
- "Zzc-06 moved back to heavy CAB": ZZC-06 (1420) card row 2018376 (4 cards) PLAN (20) -> Heavy CAB (18), undoing the 10:5x move in
  pla_light_brigade_late_1126. The separate ZSD-05 ZZC stays in PLAN.
- "Marine Scouts should have snipers trait in terms of recon and stealth": Marine Scouts Stealth 0.4 -> 0.333 (card 2.5 -> 3.0), the China sniper
  teams' value (Snipers 1144 / 1202, Armored Sniper Pair 1161) and the vanilla sniper team's. Optics are already the snipers' Very Good Optics (2300)."""
ZZC, ZZC_CARD, HEAVY, PLAN, SNIPERS = 1420, 2018376, 18, 20, (1144, 1161, 1202)


def apply(t, g, ok, rec):
    U, SA, SE, SU = t['Units'], t['SpecializationAvailabilitiesJson'], t['SensorsJson'], t['SensorUnitsJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok(U[ZZC]['HUDName'] == 'ZZC-06' and SA[ZZC_CARD]['UnitId'] == ZZC and SA[ZZC_CARD]['SpecializationId'] == PLAN and len(rows('SpecializationAvailabilitiesJson', UnitId=ZZC)) == 1, 'ZZC-06: one PLAN card row')
    g.put('SpecializationAvailabilitiesJson', ZZC_CARD, {'SpecializationId': HEAVY})
    (ms,) = [i for i, u in U.items() if u and u.get('Name') == 'PLA Marine Scouts']
    sens = lambda u: sorted(SE[r['SensorId']]['Name'] for r in rows('SensorUnitsJson', UnitId=u))
    ok(U[ms]['Stealth'] == 0.4 and all(abs(U[s]['Stealth'] - 0.333) < 1e-9 for s in SNIPERS), ('Marine Scouts 0.4, snipers 0.333', [U[s]['Stealth'] for s in SNIPERS]))
    ok(sens(ms) == ['Very Good Optics'] and all(sens(s) == ['Very Good Optics'] for s in SNIPERS), 'Marine Scouts and snipers: Very Good Optics')
    g.put('Units', ms, {'Stealth': U[SNIPERS[0]]['Stealth']})
    ok(SA[ZZC_CARD]['SpecializationId'] == HEAVY and U[ms]['Stealth'] == U[1144]['Stealth'], 'ZZC-06 Heavy CAB, Marine Scouts sniper stealth')
    rec['pla_light_brigade_late2_1126'] = {'zzc06_card': ZZC_CARD, 'zzc06_spec': 'Heavy CAB', 'marine_scouts': ms, 'stealth': U[ms]['Stealth']}
    print('PLA LIGHT BRIGADE LATE2', rec['pla_light_brigade_late2_1126'])

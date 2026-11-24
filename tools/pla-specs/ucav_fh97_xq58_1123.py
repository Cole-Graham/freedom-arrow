"""FH-97A and XQ-58A as UCAVs (Osama 23 Nov 2026 20:3x PST, thread 1567745029781454889): "xq-58 should have 10 hp same as FH-97A (again all
UCAVs get flares now, but they can't go low alt)", "no after burner on the XQ-58 or FH-97", "FH-97 and XQ-58A each have their CAP
loadouts reduced in price by 20 pts. (note this is a stop gap and further discussion is needed on the pricing)".
- Health: the FH-97A had 20 HP (vanilla 'Armor F35' row 230, shared with the F-35A/B/C, J-35 and J-31). Both now link vanilla row 429
  'Armor S70' (GJ-11, X-47B): the same zero armour, 10 HP, like every other UCAV (MQ-9, WZ-7 also 10). Row 230 is not touched.
- Afterburner off: the FH-97A's own mobility row 2019220 (no other user) gets IsAfterburner False; it already cannot change altitude (high only).
- CAP loadouts -20 (stop gap): FH-97A Light CAP (PL-12) 70 -> 50 (default), Light CAP (PL-15) 90 -> 70, Heavy CAP (PL-16) 135 -> 115; the
  XQ-58A's copies (2x AIM-120 / 2x AIM-260 / 3x AIM-260) the same. Strike loadouts unchanged.
- XQ-58A (model build only; c5_cards_1123.py copies the FH-97A rows): links the same armour and mobility rows, and its two copies are removed."""
FH, ARM_UCAV, ARM_F35, MOB = 1253, 429, 230, 2019220


def apply(t, g, ok, rec):
    U, UAR, AR, UP, MB, O = (t[k] for k in ('Units', 'UnitArmorsJson', 'ArmorsJson', 'UnitPropulsionsJson', 'MobilityJson', 'OptionsJson'))
    xq = [i for i, u in U.items() if u and u.get('Name') == 'US XQ-58A Valkyrie']
    units = [FH] + xq
    ok(U[FH]['HUDName'] == 'FH-97A' and (not xq or U[xq[0]]['HUDName'] == 'XQ-58A Valkyrie'), ('UCAV cards', units))
    a, b = AR[ARM_UCAV], AR[ARM_F35]
    ok(a['Name'] == 'Armor S70' and a['MaxHealthPoints'] == 10 and all(a[k] == b[k] for k in a if k not in ('Id', 'Name', 'MaxHealthPoints')),
       'row 429 = row 230 apart from 10 HP')
    ok(all(not o.get('MobilityId') for o in O.values() if o) or not any(o and o.get('MobilityId') in [r['MobilityId'] for r in UP.values() if r and r['UnitId'] in units] for o in O.values()),
       'no loadout option overrides their mobility')
    ok([r['UnitId'] for r in UP.values() if r and r['MobilityId'] == MOB] == [FH] and MB[MOB]['IsAfterburner'] is True and MB[MOB]['IsChangeAltitude'] is False,
       'FH-97A own mobility row, afterburner on, high only')
    g.put('MobilityJson', MOB, {'IsAfterburner': False})
    out = {}
    for u in units:
        arm = [r for r in UAR.values() if r and r['UnitId'] == u]; mob = [r for r in UP.values() if r and r['UnitId'] == u]
        ok(len(arm) == 1 and len(mob) == 1, (U[u]['HUDName'], 'one armour row, one mobility row'))
        old_a, old_m = arm[0]['ArmorId'], mob[0]['MobilityId']
        g.put('UnitArmorsJson', arm[0]['Id'], {'ArmorId': ARM_UCAV}); g.put('UnitPropulsionsJson', mob[0]['Id'], {'MobilityId': MOB})
        if u != FH:   # the XQ-58A's own copies, now unused
            ok(old_a not in (ARM_F35, ARM_UCAV) and not any(r and r['ArmorId'] == old_a for r in UAR.values())
               and all(MB[old_m].get(k) == MB[MOB].get(k) for k in MB[MOB] if k not in ('Id', 'Name', 'IsAfterburner'))
               and not any(r and r['MobilityId'] == old_m for r in UP.values()), ('XQ-58A copies unused', old_a, old_m))
            g.remove('ArmorsJson', old_a); g.remove('MobilityJson', old_m)
        out[U[u]['HUDName']] = {'armor': [old_a, ARM_UCAV], 'mobility': [old_m, MOB]}
    ok(all([AR[r['ArmorId']]['MaxHealthPoints'] for r in UAR.values() if r and r['UnitId'] == u] == [10] for u in units)
       and all([MB[r['MobilityId']]['IsAfterburner'] for r in UP.values() if r and r['UnitId'] == u] == [False] for u in units), '10 HP, no afterburner')
    ok(AR[ARM_F35]['MaxHealthPoints'] == 20 and sorted(U[r['UnitId']]['HUDName'] for r in UAR.values() if r and r['ArmorId'] == ARM_F35)
       == ['F-35A', 'F-35B', 'F-35C', 'J-31', 'J-35'], 'F-35 armour row unchanged for the F-35s, J-31 and J-35')
    M = t['ModificationsJson']; caps = {}
    for u in units:
        mods = {i for i, m in M.items() if m and m['UnitId'] == u}
        cap = sorted((o for o in O.values() if o and o['ModificationId'] in mods and 'CAP' in o['UIName']), key=lambda o: o['Id'])
        ok([o['Cost'] for o in cap] == [70, 90, 135], (U[u]['HUDName'], 'CAP loadout prices before', [(o['UIName'], o['Cost']) for o in cap]))
        for o in cap: g.put('OptionsJson', o['Id'], {'Cost': o['Cost'] - 20})
        caps[U[u]['HUDName']] = {o['UIName']: [o['Cost'] + 20, o['Cost']] for o in cap}
    ok(all(v[1] == v[0] - 20 for c in caps.values() for v in c.values()), 'CAP loadouts -20')
    out['cap_prices'] = caps
    rec['ucav_fh97_xq58'] = out
    print('UCAV FH-97A/XQ-58A', out)

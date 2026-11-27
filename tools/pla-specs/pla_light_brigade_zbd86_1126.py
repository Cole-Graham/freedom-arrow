"""PLA Light Brigade build, ZBD-86 transport for the Rocket Force (Osama 26 Nov 2026 20:3x PST, thread 1567745029781454889: "zbd-86 transports added
back to rocket battallions" / "and make sure it has 8 hp"). Branch codex/batch/osama/pla-light-brigade only; the last plb section.
- ZBD-86 (1063, 8 seats, 20 pts) is added as a transport to every PLARF Rocket/Reservist Force (19) infantry card whose squad fits its 8 seats
  (HJ-73D Team, FN-6 Team, QJZ-89 Team, QLZ-87 Team, PF-98 Team, Infantry, Counter-Raid Team: 5-7 men). The 12-man Reservists and Thermobaric Team
  keep only their 12-seat CTL-181 / ZSD-89A, as the existing data does (no PLARF card has a transport with fewer seats than its squad).
- ZBD-86 health 10 -> 8 (its own armour row 2010881; the two ZBD-86 Recon rows are separate and unchanged)."""
ZBD86, ARMOR, PLARF = 1063, 2010881, 19


def apply(t, g, ok, rec):
    U, SA, SM, AR = t['Units'], t['SpecializationAvailabilitiesJson'], t['SquadMembersJson'], t['ArmorsJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok(U[ZBD86]['HUDName'] == 'ZBD-86' and U[ZBD86]['InfantrySlots'] == 8 and AR[ARMOR]['MaxHealthPoints'] == 10, 'ZBD-86: 8 seats, 10 HP')
    ok([r['UnitId'] for r in rows('UnitArmorsJson', ArmorId=ARMOR)] == [ZBD86], 'armour row only on ZBD-86')
    g.put('ArmorsJson', ARMOR, {'MaxHealthPoints': 8})
    added, skipped = [], []
    for c in rows('SpecializationAvailabilitiesJson', SpecializationId=PLARF):
        if U[c['UnitId']].get('CategoryType') != 1: continue
        men = len(rows('SquadMembersJson', UnitId=c['UnitId'])); tr = rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=c['Id'])
        ground = [r for r in tr if U[r['UnitId']].get('Type') == 4]
        if not ground or any(r['UnitId'] == ZBD86 for r in tr): continue
        if men > 8: skipped.append((U[c['UnitId']]['HUDName'], men)); continue
        g.add('TransportAvailabilitiesJson', ground[0], {'UnitId': ZBD86}); added.append(U[c['UnitId']]['HUDName'])
    ok(len(added) == 7 and sorted(n for n, _ in skipped) == ['Reservists 预备役', 'Thermobaric Team'], ('ZBD-86 added', added, skipped))
    rec['pla_light_brigade_zbd86_1126'] = {'hp': 8, 'added_to': added, 'too_big': skipped}
    print('PLA LIGHT BRIGADE ZBD-86', rec['pla_light_brigade_zbd86_1126'])

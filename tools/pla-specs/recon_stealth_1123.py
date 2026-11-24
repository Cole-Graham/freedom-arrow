"""Lateralus 23 Nov 2026 16:xx PST, thread 1568104480459722894: "A lot of Chinese recon infantry have the wrong stealth values, they should have
2.5 stealth at minimum, and dedicated sniper teams (usually consisting of 2-3 men with 1 or more sniper rifles) should always have 3.0 stealth".
Called from batch_0_9_5b.py.
Units.Stealth and Units.CurrentStealth hold the reciprocal of the card value: card 2.0 = 0.5, 2.5 = 0.4, 3.0 = 0.333 (vanilla recon
infantry, Role 32, is 0.4; vanilla sniper teams, Role 33, are 0.333).
- Recon infantry = China infantry with Role 32 or 33. Seven had 0.5 (card 2.0); they go to 0.4 (card 2.5).
- Sniper team = 2 or 3 men with at least one sniper rifle. The only China sniper rifle is the QBU-10 (Weapons.Type 4, the type of M107/ASVK);
  the QBU-191 and QBU-88 are marksman rifles (Type 2, the type of M110/SVD). Five units match; they go to 0.333 (card 3.0).
No loadout option of these units replaces the unit, so the unit rows are the whole change. Role is not changed."""

SNIPER_TYPE = 4
RECON = 0.4
SNIPER = 0.333


def apply(t, g, ok, rec):
    U, SM, W, C = t['Units'], t['SquadMembersJson'], t['WeaponsJson'], t['CountriesJson']
    O, M = t['OptionsJson'], t['ModificationsJson']
    china = {i for i, c in C.items() if c and 'China' in str(c.get('Name'))}
    men = {}
    for m in SM.values():
        if m:
            men.setdefault(m['UnitId'], []).append(m)
    recon = sorted(i for i, u in U.items() if u and u.get('CountryId') in china and u.get('Role') in (32, 33) and men.get(i))
    sniper = [i for i in recon if 2 <= len(men[i]) <= 3 and any(W.get(m.get('PrimaryWeaponId'), {}).get('Type') == SNIPER_TYPE for m in men[i])]
    ok(sniper == [1026, 1144, 1161, 1186, 1202], ('sniper teams', sniper))
    before = {i: U[i]['Stealth'] for i in recon}
    ok(sorted(i for i, s in before.items() if s > RECON) == [1144, 1173, 1174, 1184, 1186, 1187, 1203], ('recon below card 2.5', before))
    ok(all(U[i]['Stealth'] == U[i]['CurrentStealth'] for i in recon), 'Stealth = CurrentStealth')
    # No option on these units swaps in another unit, so no loadout keeps the old value.
    mods = {m['Id'] for m in M.values() if m and m.get('UnitId') in recon}
    ok(not [o['Id'] for o in O.values() if o and o.get('ModificationId') in mods and o.get('ReplaceUnitId')], 'no unit-swap options')
    changed = {}
    for i in recon:
        want = SNIPER if i in sniper else min(before[i], RECON)
        if want != before[i]:
            g.put('Units', i, {'Stealth': want, 'CurrentStealth': want})
            changed[i] = [U[i]['HUDName'].strip(), round(1 / before[i], 1), round(1 / want, 1)]
    ok(all(U[i]['Stealth'] <= RECON for i in recon) and all(U[i]['Stealth'] == SNIPER for i in sniper), 'after: recon >= 2.5, snipers 3.0')
    rec['recon_stealth_1123'] = {'card': changed, 'sniper_teams': sniper}
    print('RECON_STEALTH', changed)

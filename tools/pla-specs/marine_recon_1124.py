"""Marine Recon loadout (Osama 24 Nov 2026 02:3x PST, thread 1567745029781454889: "Marine Recon, QTS-11 removed, added 1 QBU-191 and 2xqlg-10A,
please make sure the QLG-10A is the second weapon and the QBU-191 is the third. Make sure their death priority mirrors what the force recon have").
Marine Recon (unit 1224, PLAN Special Forces) now mirrors the USMC Force Recon (unit 61) man for man:
  Force Recon                         Marine Recon
  M27 IAR + M320       DP 2, DP 3     QBZ-192 + QLG-10A    DP 2, DP 3   (were the 2 QTS-11 + QTS-11 grenade launcher men, DP 3, 3)
  M38 DMR + AT4CS-RS   DP 2, DP 2     QBU-191 + PF-89      DP 2, DP 2   (the QBU-191 man, DP 2, plus one QBZ-192 man, DP 3 -> QBU-191)
  M27 IAR + AT4CS-RS   DP 1, DP 3     QBZ-192 + PF-89      DP 1, DP 3   (unchanged)
- Card weapon order: QBZ-192 1, QLG-10A 2, QBU-191 3, PF-89 4. QTS-11 and its grenade launcher leave the squad (rows stay for other squads).
- Ammunition per carrier as on the other China squads: QLG-10A 48 x '35 mm HE-fragmentation' (2011890), QBU-191 100; PF-89 1 per carrier on 4."""
MR, FR = 1224, 61
QLG, QLG_AMMO = 2011889, 2011890


def apply(t, g, ok, rec):
    U, W, A, SM, SW, WA = (t[k] for k in ('Units', 'WeaponsJson', 'AmmunitionsJson', 'SquadMembersJson', 'SquadWeaponsJson', 'WeaponAmmunitionsJson'))
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    name = lambda w: W[w]['HUDName'] if w else None
    ok(U[MR]['HUDName'] == 'Marine Recon' and U[FR]['HUDName'] == 'Force Recon' and W[QLG]['HUDName'] == 'QLG-10A' and A[QLG_AMMO]['HUDName'] == '35 mm HE-fragmentation',
       'Marine Recon / Force Recon / QLG-10A rows')
    men = rows('SquadMembersJson', UnitId=MR)
    was = [(name(m['PrimaryWeaponId']), name(m['SpecialWeaponId']), m['DeathPriority']) for m in men]
    ok(sorted(was) == sorted([('QTS-11', 'QTS-11 grenade launcher', 3)] * 2 + [('QBU-191', 'PF-89', 2), ('QBZ-192', 'PF-89', 1)] + [('QBZ-192', 'PF-89', 3)] * 2),
       ('Marine Recon as built', was))
    fr = sorted((name(m['PrimaryWeaponId']), name(m['SpecialWeaponId']), m['DeathPriority']) for m in rows('SquadMembersJson', UnitId=FR))
    ok(fr == sorted([('M27 IAR', 'M320', 2), ('M27 IAR', 'M320', 3), ('M38 DMR', 'AT4CS-RS', 2), ('M38 DMR', 'AT4CS-RS', 2), ('M27 IAR', 'AT4CS-RS', 1),
                     ('M27 IAR', 'AT4CS-RS', 3)]), ('Force Recon death priorities', fr))
    qbz = next(m['PrimaryWeaponId'] for m in men if name(m['PrimaryWeaponId']) == 'QBZ-192')
    pf = next(m['SpecialWeaponId'] for m in men if name(m['SpecialWeaponId']) == 'PF-89')
    qbu = next(m['PrimaryWeaponId'] for m in men if name(m['PrimaryWeaponId']) == 'QBU-191')
    qts = [m for m in men if name(m['PrimaryWeaponId']) == 'QTS-11']
    rifle3 = [m for m in men if name(m['PrimaryWeaponId']) == 'QBZ-192' and name(m['SpecialWeaponId']) == 'PF-89' and m['DeathPriority'] == 3]   # before any edit
    for m, dp in zip(qts, (2, 3)):                                                       # grenadiers: QBZ-192 + QLG-10A
        g.put('SquadMembersJson', m['Id'], {'PrimaryWeaponId': qbz, 'SpecialWeaponId': QLG, 'DeathPriority': dp})
    g.put('SquadMembersJson', rifle3[0]['Id'], {'PrimaryWeaponId': qbu, 'DeathPriority': 2})   # second marksman: QBU-191 + PF-89, DP 3 -> 2
    # card weapons: QBZ-192 1, QLG-10A 2, QBU-191 3, PF-89 4
    sw = {name(r['WeaponId']): r for r in rows('SquadWeaponsJson', UnitId=MR)}
    ok(set(sw) == {'QBZ-192', 'QTS-11', 'QTS-11 grenade launcher', 'QBU-191', 'PF-89'}, ('squad weapons', sorted(sw)))
    g.put('SquadWeaponsJson', sw['QTS-11']['Id'], {'WeaponId': QLG, 'Order': 2})
    g.remove('SquadWeaponsJson', sw['QTS-11 grenade launcher']['Id'])
    g.put('SquadWeaponsJson', sw['QBU-191']['Id'], {'Order': 3}); g.put('SquadWeaponsJson', sw['PF-89']['Id'], {'Order': 4})
    wa = {name(r['WeaponId']): r for r in rows('WeaponAmmunitionsJson', UnitId=MR)}
    g.put('WeaponAmmunitionsJson', wa['QTS-11']['Id'], {'WeaponId': QLG, 'AmmunitionId': QLG_AMMO, 'Quantity': 48})
    g.remove('WeaponAmmunitionsJson', wa['QTS-11 grenade launcher']['Id'])
    now = sorted((name(m['PrimaryWeaponId']), name(m['SpecialWeaponId']), m['DeathPriority']) for m in rows('SquadMembersJson', UnitId=MR))
    ok(now == sorted([('QBZ-192', 'QLG-10A', 2), ('QBZ-192', 'QLG-10A', 3), ('QBU-191', 'PF-89', 2), ('QBU-191', 'PF-89', 2), ('QBZ-192', 'PF-89', 1),
                      ('QBZ-192', 'PF-89', 3)]), ('Marine Recon now', now))
    order = [name(r['WeaponId']) for r in sorted(rows('SquadWeaponsJson', UnitId=MR), key=lambda r: r['Order'])]
    ok(order == ['QBZ-192', 'QLG-10A', 'QBU-191', 'PF-89'], ('card weapon order', order))
    used = {m[k] for m in rows('SquadMembersJson', UnitId=MR) for k in ('PrimaryWeaponId', 'SpecialWeaponId') if m[k]}
    ok({r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=MR)} == used == {r['WeaponId'] for r in rows('SquadWeaponsJson', UnitId=MR)},
       'every carried weapon has one card row and one ammo row')
    rec['marine_recon_1124'] = {'was': was, 'now': now, 'order': order}
    print('MARINE RECON', rec['marine_recon_1124'])

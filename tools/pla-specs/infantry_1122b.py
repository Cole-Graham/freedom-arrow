"""Lateralus 22 Nov 2026 17:2x PST, thread 1572962048705429598: "chinese Light Riflemen should have 5 PF-89, the only have 3 currently",
"DXL-4 rate of fire 8 -> 6", "OSV-96 rate of fire 6 -> 8". Called from batch_0_9_5b.py after infantry_order_1122.py.
- Light Riflemen (1205): the two riflemen without a special weapon (2015575, 2015576) carry the PF-89 too. A disposable is one round per
  carrier (WeaponAmmunitions.Quantity 1, the vanilla pattern), so 5 carriers = 5 PF-89. Their DeathPriority stays 3 (rifle + disposable AT;
  death_priority_proposal.json updated).
- Card rate of fire (WeaponHelper.RateOfFireSecond 0x2BCE50, x60): MagazineSize / ((MagazineSize / ShotsPerBurst - 1) x TimeBetweenBursts
  + MagazineReloadTime), min/max averaged. With 5 rounds, 1 per burst and a 4 s reload: DXL-4 (526) bursts 7.375-9.375 -> 8.0/min,
  OSV-96 (927) 11-12 -> 6.0/min. The two swap their burst intervals: DXL-4 11-12 -> 6.0, OSV-96 7.375-9.375 -> 8.0. Both are vanilla
  Russian rows (FSB Snaipery loadouts 345 / 623)."""


def rof(w):
    t = lambda b, r: (w['MagazineSize'] / w['ShotsPerBurstMax'] - 1) * b + r
    return 60 * w['MagazineSize'] / ((t(w['TimeBetweenBurstsMin'], w['MagazineReloadTimeMin']) + t(w['TimeBetweenBurstsMax'], w['MagazineReloadTimeMax'])) / 2)


def apply(t, g, ok, rec):
    SM, WA, W = t['SquadMembersJson'], t['WeaponAmmunitionsJson'], t['WeaponsJson']
    PF89 = 2011887
    ok(W[PF89]['HUDName'].strip() == 'PF-89' and W[PF89]['Type'] == 63, 'weapon 2011887 is the disposable PF-89')
    carr = lambda: sorted(m['Id'] for m in SM.values() if m and m['UnitId'] == 1205 and m.get('SpecialWeaponId') == PF89)
    ok(carr() == [2015571, 2015572, 2015573], ('Light Riflemen PF-89 carriers before', carr()))
    wa = [r for r in WA.values() if r and r['UnitId'] == 1205 and r['WeaponId'] == PF89]
    ok(len(wa) == 1 and wa[0]['Quantity'] == 1, ('Light Riflemen PF-89 ammo row', wa))
    for mid in (2015575, 2015576):
        m = SM[mid]
        ok(m['UnitId'] == 1205 and not m.get('SpecialWeaponId') and m['DeathPriority'] == 3, (mid, 'rifleman without a special weapon, DeathPriority 3'))
        g.put('SquadMembersJson', mid, {'SpecialWeaponId': PF89})
    ok(len(carr()) == 5, 'Light Riflemen: 5 PF-89 carriers')
    D, O = W[526], W[927]
    ok(D['HUDName'].strip() == 'DXL-4' and O['HUDName'].strip() == 'OSV-96', 'DXL-4 526 / OSV-96 927')
    ok(round(rof(D), 1) == 8.0 and round(rof(O), 1) == 6.0, ('card rate of fire before', rof(D), rof(O)))
    d = {k: D[k] for k in ('TimeBetweenBurstsMin', 'TimeBetweenBurstsMax')}
    o = {k: O[k] for k in d}
    g.put('WeaponsJson', 526, o)
    g.put('WeaponsJson', 927, d)
    ok(round(rof(W[526]), 1) == 6.0 and round(rof(W[927]), 1) == 8.0, ('card rate of fire after', rof(W[526]), rof(W[927])))
    rec['infantry_1122b'] = {'light_riflemen_pf89_carriers': carr(), 'DXL-4': o, 'OSV-96': d}

"""Type 100 CSV (ZBD-100) 40 mm CT: sound, effects and rate of fire of the Derivatsiya's 57 mm 2A91; damage, penetration and ranges stay
(Osama 24 Nov 2026 01:3x PST, bugs thread 1573561286803980289: "Type 100's 40mm CT should have the derivitsiya 57mm russian autocannon sound and
effects and rof, but keep the technical stats as they are now").
- Gun sound = Weapons.AudioPreset. Rate of fire = the burst/magazine fields of weapon 302 'Autocannon 57 2A91 T15 Derivatsia'.
- Shot effects and sounds of the rounds = Ammunitions.AudioPreset / FXPreset / VfxCountPerShot(Max): APFSDS takes the Derivatsiya AP round 266,
  HE takes the Derivatsiya airburst HE round 201.
- Not data: the muzzle flash comes from the stand-in body prefab (Bradley), so it stays the Bradley flash."""
WEAPON, AP, HE = 'PLA ZBD-100 40 mm', 'PLA ZBD-100 40 mm APFSDS', 'PLA ZBD-100 40 mm HE'
DONOR_W, DONOR_AP, DONOR_HE = 302, 266, 201
ROF = ('ShotsPerBurstMin', 'ShotsPerBurstMax', 'TimeBetweenShotsInBurst', 'TimeBetweenBurstsMin', 'TimeBetweenBurstsMax',
       'MagazineSize', 'MagazineReloadTimeMin', 'MagazineReloadTimeMax')
FX = ('AudioPreset', 'FXPreset', 'VfxCountPerShot', 'VfxCountPerShotMax')


def apply(t, g, ok, rec):
    W, A = t['WeaponsJson'], t['AmmunitionsJson']
    one = lambda tab, name: [r for r in tab.values() if r and r.get('Name') == name]
    w, ap, he = one(W, WEAPON), one(A, AP), one(A, HE)
    ok(len(w) == 1 and len(ap) == 1 and len(he) == 1, 'Type 100 40 mm weapon + APFSDS + HE rows')
    w, ap, he = w[0], ap[0], he[0]
    dw, dap, dhe = W[DONOR_W], A[DONOR_AP], A[DONOR_HE]
    ok(dw['Name'] == 'Autocannon 57 2A91 T15 Derivatsia' and dw['AudioPreset'] == 'WEAPON_SOUND_PRESET_VEH_AUTOCANNON_2A91', 'donor weapon 302')
    ok(dap['Name'] == 'Round 57 2A91 Barbaris AP T3' and dhe['Name'] == 'Round 57 2A91 Derivatsiya AAG HE T3', 'donor rounds 266 / 201')
    keep = lambda r, fields: {k: v for k, v in r.items() if k not in fields}
    before = (keep(w, ROF + ('AudioPreset',)), keep(ap, FX), keep(he, FX))
    g.put('WeaponsJson', w['Id'], {k: dw[k] for k in ROF + ('AudioPreset',)})
    g.put('AmmunitionsJson', ap['Id'], {k: dap[k] for k in FX})
    g.put('AmmunitionsJson', he['Id'], {k: dhe[k] for k in FX})
    # checks: the copied fields match the donors, every other field is unchanged
    ok(all(W[w['Id']][k] == dw[k] for k in ROF + ('AudioPreset',)), 'Type 100 gun: 2A91 sound + rate of fire')
    ok(all(A[ap['Id']][k] == dap[k] for k in FX) and all(A[he['Id']][k] == dhe[k] for k in FX), 'Type 100 rounds: 2A91 effects')
    ok((keep(W[w['Id']], ROF + ('AudioPreset',)), keep(A[ap['Id']], FX), keep(A[he['Id']], FX)) == before, 'Type 100 damage/pen/range unchanged')
    users = sorted({r['UnitId'] for r in t['WeaponAmmunitionsJson'].values() if r and r['WeaponId'] == w['Id']})
    rec['type100_2a91_1124'] = {'weapon': w['Id'], 'rounds': [ap['Id'], he['Id']], 'units_using_gun': users}
    print('TYPE100 2A91', rec['type100_2a91_1124'])

"""PLA Light Brigade build, Troopers and Moto. Riflemen (Osama 26 Nov 2026 01:3x PST, thread 1567745029781454889: "troopers AA in this build lose one
M240L and regains 1 rifle"; "Troopers go to 70 points and Moto Riflemen (chinese) go to 75 points"; "Troopers AA should not have 2 XM-25 in
multipurpose mode. They lose 1 M-25 CDTE and 1 M4A1"). Branch codex/batch/osama/pla-light-brigade only.
- Troopers AA (card 413) and its 'Troopers AA+RPG' mixed loadout (unit 706, option 3334): one M240L gunner (842 / 1640, death priority 3, as the
  riflemen) carries an M4A1 instead. One M240L stays.
- Mixed loadout (706): the second M4A1 + M-25 CDTE soldier (1639) is removed, so one M-25 CDTE stays; 9 -> 8 men, so the loadout takes the game's
  8-man infantry armour row (84: armour 6, 40 HP) instead of the shared 9-man row (85: armour 6, 45 HP), as the Falcons did.
- Troopers (701): 60 -> 70 pts. Moto. Riflemen 摩步班 (1196): 70 -> 75 pts."""
AA, AA_MIX, TROOPERS, MOTO = 413, 706, 701, 1196
AA_MG, MIX_MG, MIX_M25 = 842, 1640, 1639
ARMOR_9, ARMOR_8 = 85, 84


def apply(t, g, ok, rec):
    U, W, SM, SW, WA, UA, AR = (t[k] for k in ('Units', 'WeaponsJson', 'SquadMembersJson', 'SquadWeaponsJson', 'WeaponAmmunitionsJson', 'UnitArmorsJson', 'ArmorsJson'))
    live = lambda tab: [r for r in t[tab].values() if r]
    men = lambda u: sorted([r for r in live('SquadMembersJson') if r['UnitId'] == u], key=lambda r: r['Id'])
    wn = lambda i: W[i]['HUDName'] if i else ''
    kit = lambda u: sorted((wn(r['PrimaryWeaponId']), wn(r['SpecialWeaponId'])) for r in men(u))
    ok(U[AA]['HUDName'] == 'Troopers AA' and U[AA_MIX]['HUDName'] == 'Troopers AA' and U[TROOPERS]['HUDName'] == 'Troopers'
       and U[MOTO]['HUDName'].startswith('Moto. Riflemen'), 'Troopers AA, its mixed loadout, Troopers, Moto. Riflemen')
    ok((U[TROOPERS]['Cost'], U[MOTO]['Cost']) == (60, 70) and not U[TROOPERS].get('OriginalCost') and not U[MOTO].get('OriginalCost'), 'prices before 60 / 70')
    m4 = SM[838]['PrimaryWeaponId']; ok(wn(m4) == 'M4A1', 'M4A1 id from rifleman 838')
    for u, mg in ((AA, AA_MG), (AA_MIX, MIX_MG)):
        ok(SM[mg]['UnitId'] == u and wn(SM[mg]['PrimaryWeaponId']) == 'M240L' and not SM[mg]['SpecialWeaponId'], ('M240L gunner', mg))
        ok(sum(wn(r['PrimaryWeaponId']) == 'M240L' for r in men(u)) == 2, ('two M240L before', u))
        g.put('SquadMembersJson', mg, {'PrimaryWeaponId': m4})
    ok(SM[MIX_M25]['UnitId'] == AA_MIX and (wn(SM[MIX_M25]['PrimaryWeaponId']), wn(SM[MIX_M25]['SpecialWeaponId'])) == ('M4A1', 'M-25 CDTE'), 'second M-25 man')
    ok(sum(wn(r['SpecialWeaponId']) == 'M-25 CDTE' for r in men(AA_MIX)) == 2 and len(men(AA_MIX)) == 9, 'mixed loadout: 9 men, 2 M-25 before')
    g.remove('SquadMembersJson', MIX_M25)
    ua = [r for r in live('UnitArmorsJson') if r['UnitId'] == AA_MIX]
    ok(len(ua) == 1 and ua[0]['ArmorId'] == ARMOR_9 and AR[ARMOR_8]['Name'] == 'Armor Infantry 8Men' and AR[ARMOR_8]['MaxHealthPoints'] == 40
       and AR[ARMOR_8]['ArmorValue'] == AR[ARMOR_9]['ArmorValue'], 'mixed loadout armour 9-man -> 8-man row')
    g.put('UnitArmorsJson', ua[0]['Id'], {'ArmorId': ARMOR_8})
    g.put('Units', TROOPERS, {'Cost': 70}); g.put('Units', MOTO, {'Cost': 75})
    # checks after
    for u in (AA, AA_MIX):
        ok(sum(wn(r['PrimaryWeaponId']) == 'M240L' for r in men(u)) == 1, ('one M240L after', u))
        carried = {w for r in men(u) for w in (r['PrimaryWeaponId'], r['SpecialWeaponId']) if w}
        # the card lists every weapon of the card's loadouts (vanilla), so carried weapons must be a subset of its card and ammo rows
        ok(carried <= {r['WeaponId'] for r in live('SquadWeaponsJson') if r['UnitId'] == u} and carried <= {r['WeaponId'] for r in live('WeaponAmmunitionsJson') if r['UnitId'] == u},
           ('every carried weapon has card + ammo rows', u))
    ok(len(men(AA)) == 9 and len(men(AA_MIX)) == 8 and sum(wn(r['SpecialWeaponId']) == 'M-25 CDTE' for r in men(AA_MIX)) == 1, 'Troopers AA 9 men; mixed 8 men, 1 M-25')
    rec['pla_light_brigade_troopers_1126'] = {'troopers_aa': kit(AA), 'troopers_aa_mixed': kit(AA_MIX), 'troopers': 70, 'moto_riflemen': 75}
    print('PLA LIGHT BRIGADE TROOPERS', rec['pla_light_brigade_troopers_1126'])

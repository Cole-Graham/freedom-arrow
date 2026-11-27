"""Troopers AA "Multipurpose" loadout (unit 706, option 3334 'Custom_Option_Mixed', HUD 'Troopers AA+RPG'): 8 -> 9 men, M4A1 x7 -> x8 (Lateralus
26 Nov 2026 19:5x PST, thread 1568104480459722894, "queue it up"). One more plain rifleman, a copy of member 1636 (M4A1 only, death priority 4,
dies among the first as the other plain riflemen); armour row 84 'Armor Infantry 8Men' (40 HP) -> 85 '9Men' (45 HP), the row the 9-man Standard
loadout uses. Weapons, rounds and price unchanged (70). Runs after the Light Brigade Troopers AA section and aa_squads_qjy_1126."""
MIXED, PLAIN, A8, A9, M4A1, M240L = 706, 1636, 84, 85, 50, 63


def apply(t, g, ok, rec):
    U, SM, UA, AR, W = t['Units'], t['SquadMembersJson'], t['UnitArmorsJson'], t['ArmorsJson'], t['WeaponsJson']
    men = lambda: sorted([r for r in SM.values() if r and r['UnitId'] == MIXED], key=lambda r: r['Id'])
    m = men()
    ok(U[MIXED]['HUDName'] == 'Troopers AA' and len(m) == 8 and sum(r['PrimaryWeaponId'] == M4A1 for r in m) == 7 and sum(r['PrimaryWeaponId'] == M240L for r in m) == 1,
       ('Troopers AA Multipurpose: 8 men, 7 M4A1 + 1 M240L', len(m)))
    ok(SM[PLAIN]['UnitId'] == MIXED and SM[PLAIN]['PrimaryWeaponId'] == M4A1 and not SM[PLAIN].get('SpecialWeaponId') and SM[PLAIN]['DeathPriority'] == 4, 'plain rifleman 1636')
    ua = [r for r in UA.values() if r and r['UnitId'] == MIXED]
    ok(len(ua) == 1 and ua[0]['ArmorId'] == A8 and AR[A8]['Name'] == 'Armor Infantry 8Men' and AR[A9]['Name'] == 'Armor Infantry 9Men', ('armour rows', [r['ArmorId'] for r in ua]))
    new = g.add('SquadMembersJson', SM[PLAIN])
    g.put('UnitArmorsJson', ua[0]['Id'], {'ArmorId': A9})
    m = men()
    ok(len(m) == 9 and sum(r['PrimaryWeaponId'] == M4A1 for r in m) == 8 and UA[ua[0]['Id']]['ArmorId'] == A9, 'Multipurpose: 9 men, 8 M4A1, 9-man armour')
    rec['troopers_aa_mixed_1126'] = {'men': '8 -> 9', 'M4A1': '7 -> 8', 'armour': f"{AR[A8]['MaxHealthPoints']} -> {AR[A9]['MaxHealthPoints']} HP", 'new_member': new}
    print('TROOPERS AA MIXED', rec['troopers_aa_mixed_1126'])

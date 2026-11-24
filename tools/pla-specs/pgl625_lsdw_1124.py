"""After 0.9.6 (Osama 24 Nov 2026 10:5x PST, thread 1567745029781454889, on the QQ sheet reports FA-101 / FA-098):
- FA-101 "the FK-2000 has two 30 mm rotary cannons but the same damage as the 625": "it's the pgl that should do less damage. We're going to
  drop the pgl-625 to 70% of its current damage." (3.43), then 10:5x "Pgl-625 change to 3.5 damage". PGL-625 six-barrel 25 mm round
  (2009369, used only by the PGL-625): Damage 4.9 -> 3.5.
  Penetration, rate of fire and range unchanged. The FK-2000 is not changed.
- FA-098 "the ZTZ-99 laser suppression system uses kinetic penetration, so it only attacks targets below 10 KE ... change it to HEAT":
  "Ztz-99a this is a good change.", then 10:5x "Can we make the laser APS ignore armor". LSDW laser pulse (2019387; ZTZ-99A, ZTZ-99, ZTZ-98):
  ArmorTargeted 1 (kinetic) -> 0 (no armour: the game gives it unlimited penetration), so every pulse does its full 0.08 damage and 80 stress
  to any target. Kinetic did 0 against armour >= 2 x pen (20 -> 10), so the AI never chose it against vehicles; HEAT (first version) would have
  done ~0.0008-0.002 per pulse to IFVs and less to tanks, too little for the AI's target score. Against infantry 0.059 -> 0.08 per pulse."""
PGL, LSDW = 2009369, 2019387


def apply(t, g, ok, rec):
    A, WA, W = t['AmmunitionsJson'], t['WeaponAmmunitionsJson'], t['WeaponsJson']
    users = lambda a: sorted({W[r['WeaponId']]['HUDName'] for r in WA.values() if r and r['AmmunitionId'] == a})
    ok(A[PGL]['HUDName'] == '625 six-barrel 25 mm gun ammunition' and A[PGL]['Damage'] == 4.9 and users(PGL) == ['625 six-barrel 25 mm gun'],
       ('PGL-625 round, only on the PGL-625 gun', users(PGL)))
    ok(A[LSDW]['HUDName'] == 'LSDW laser pulse' and A[LSDW]['ArmorTargeted'] == 1 and users(LSDW) == ['LSDW'], ('LSDW pulse, kinetic', users(LSDW)))
    g.put('AmmunitionsJson', PGL, {'Damage': 3.5})
    g.put('AmmunitionsJson', LSDW, {'ArmorTargeted': 0})
    ok(A[PGL]['Damage'] == 3.5 and A[LSDW]['ArmorTargeted'] == 0, 'PGL-625 3.5 damage; LSDW ignores armour')
    rec['pgl625_lsdw_1124'] = {'pgl625_damage': [4.9, 3.5], 'lsdw_armor_targeted': [1, 0]}
    print('PGL-625 / LSDW', rec['pgl625_lsdw_1124'])

"""After 0.9.6 (Osama 24 Nov 2026 10:5x PST, thread 1567745029781454889, on the QQ sheet reports FA-101 / FA-098):
- FA-101 "the FK-2000 has two 30 mm rotary cannons but the same damage as the 625": "it's the pgl that should do less damage. We're going to
  drop the pgl-625 to 70% of its current damage." PGL-625 six-barrel 25 mm round (2009369, used only by the PGL-625): Damage 4.9 -> 3.43.
  Penetration, rate of fire and range unchanged. The FK-2000 is not changed.
- FA-098 "the ZTZ-99 laser suppression system uses kinetic penetration, so it only attacks targets below 10 KE ... change it to HEAT":
  "Ztz-99a this is a good change." LSDW laser pulse (2019387; ZTZ-99A, ZTZ-99, ZTZ-98): ArmorTargeted 1 (kinetic) -> 2 (HEAT). HEAT uses
  PenetrationAtGroundRange (10) at every range and always does a little damage (pen^2 / (pen^2 + armour^2)), where kinetic did 0 against
  armour >= 2 x pen. Stress from the blast term does not use armour (docs/engine/stress.md)."""
PGL, LSDW = 2009369, 2019387


def apply(t, g, ok, rec):
    A, WA, W = t['AmmunitionsJson'], t['WeaponAmmunitionsJson'], t['WeaponsJson']
    users = lambda a: sorted({W[r['WeaponId']]['HUDName'] for r in WA.values() if r and r['AmmunitionId'] == a})
    ok(A[PGL]['HUDName'] == '625 six-barrel 25 mm gun ammunition' and A[PGL]['Damage'] == 4.9 and users(PGL) == ['625 six-barrel 25 mm gun'],
       ('PGL-625 round, only on the PGL-625 gun', users(PGL)))
    ok(A[LSDW]['HUDName'] == 'LSDW laser pulse' and A[LSDW]['ArmorTargeted'] == 1 and users(LSDW) == ['LSDW'], ('LSDW pulse, kinetic', users(LSDW)))
    g.put('AmmunitionsJson', PGL, {'Damage': round(4.9 * 0.7, 2)})
    g.put('AmmunitionsJson', LSDW, {'ArmorTargeted': 2})
    ok(A[PGL]['Damage'] == 3.43 and A[LSDW]['ArmorTargeted'] == 2, 'PGL-625 3.43 damage; LSDW HEAT')
    rec['pgl625_lsdw_1124'] = {'pgl625_damage': [4.9, 3.43], 'lsdw_armor_targeted': [1, 2]}
    print('PGL-625 / LSDW', rec['pgl625_lsdw_1124'])

"""Osama 27 Nov 2026 22:4x PST, thread 1567745029781454889: "Jiaolong given flashbangs and 4x smoke (cqc sf classification)". Sea Dragons 蛟龙
(Jiaolong, 1191, PLAN CQC kit) get the vanilla CQC special-forces kit pieces, as Delta Force, SSO, Spetsnaz Alpha / Vympel, Zaliukai:
- Flashbang: vanilla weapon 590 'Flashbang' (round 442, 1 per carrier, as every vanilla row) as the special weapon of one QBS-09 man (the leader
  already carries a PF-97; one special weapon per man), listed last on the card.
- Smoke: ability link 11 'Sprint Smoke' (x1) -> vanilla 81 'Sprint30 Smoke x4', the row every vanilla CQC SF squad uses; the two rows differ only in
  SmokeAmmunitionQuantity (sf_recon_armor_1123). Men, price, armour unchanged. Adds rows, so it runs in the plb scope."""
JL, FLASH, FLASH_A, SMOKE1, SMOKE4 = 1191, 590, 442, 11, 81


def apply(t, g, ok, rec):
    U, W, A, AB = t['Units'], t['WeaponsJson'], t['AmmunitionsJson'], t['AbilitiesJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    ok(U[JL]['HUDName'] == 'Sea Dragons 蛟龙' and W[FLASH]['HUDName'] == 'Flashbang' and A[FLASH_A]['HUDName'] == 'Flashbang', 'Sea Dragons 蛟龙, vanilla flashbang')
    diff = {k for k in set(AB[SMOKE1]) | set(AB[SMOKE4]) if k not in ('Id', 'Name') and AB[SMOKE1].get(k) != AB[SMOKE4].get(k)}
    ok(diff == {'SmokeAmmunitionQuantity'} and AB[SMOKE4]['SmokeAmmunitionQuantity'] == 4, ('smoke rows differ only in quantity', diff))
    (link,) = rows('UnitAbilitiesJson', UnitId=JL); ok(link['AbilityId'] == SMOKE1, ('Sea Dragons ability', link['AbilityId']))
    g.put('UnitAbilitiesJson', link['Id'], {'AbilityId': SMOKE4})
    qbs = [m for m in rows('SquadMembersJson', UnitId=JL) if W[m['PrimaryWeaponId']]['HUDName'] == 'QBS-09' and not m.get('SpecialWeaponId')]
    ok(len(qbs) == 2, 'two QBS-09 men without a special weapon')
    g.put('SquadMembersJson', qbs[0]['Id'], {'SpecialWeaponId': FLASH})
    sw = rows('SquadWeaponsJson', UnitId=JL)
    g.add('SquadWeaponsJson', sw[0], {'UnitId': JL, 'WeaponId': FLASH, 'Order': max(r['Order'] for r in sw) + 1})
    wa = rows('WeaponAmmunitionsJson', UnitId=JL)[0]
    g.add('WeaponAmmunitionsJson', wa, {'UnitId': JL, 'WeaponId': FLASH, 'AmmunitionId': FLASH_A, 'Quantity': 1, 'Order': 0})
    men = rows('SquadMembersJson', UnitId=JL)
    carried = {x for m in men for x in (m['PrimaryWeaponId'], m.get('SpecialWeaponId')) if x}
    ok({r['WeaponId'] for r in rows('SquadWeaponsJson', UnitId=JL)} == carried == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=JL)}, 'card + ammo = carried')
    ok(sorted(r['Order'] for r in rows('SquadWeaponsJson', UnitId=JL)) == list(range(1, len(carried) + 1)), 'weapon order 1..n')
    rec['osama_jiaolong_cqc_1127'] = {'unit': JL, 'smoke': [1, 4], 'ability_row': [SMOKE1, SMOKE4], 'flashbang_carrier': qbs[0]['Id'],
                                      'kit': sorted(W[m['PrimaryWeaponId']]['HUDName'] + (' + ' + W[m['SpecialWeaponId']]['HUDName'] if m.get('SpecialWeaponId') else '') for m in men)}
    print('JIAOLONG CQC', rec['osama_jiaolong_cqc_1127'])

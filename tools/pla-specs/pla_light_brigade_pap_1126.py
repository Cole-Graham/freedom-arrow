"""PLA Light Brigade build, PAP patrols (Osama 26 Nov 2026 03:4x PST, thread 1567745029781454889: "Moto Riflemen renamed PAP Rifle Patrol. And then we
create an identical unit that replaces the PF-98 with the QW-2 and we call it PAP AA Patrol"). Branch codex/batch/osama/pla-light-brigade only;
inside g.scope('plb'), after the transports sections (the copy takes the card's final transports).
- Moto. Riflemen 摩步班 (1196, Light CAB, 75 pts, 8 men): card name (HUDName) -> 'PAP Rifle Patrol' (English only, no Chinese name given). Row Name kept.
- PAP AA Patrol: new unit, a full copy of it (8 men, 75 pts, armour, mobility, abilities, icon, Light CAB card row with its 6 cards and 5 transports);
  the leader's PF-98 (6 rounds) becomes the infantry QW-2 (2012288, round 2012289) with 3 missiles, the QW-2 Team's count per carrier."""
MOTO, PF98, QW2, QW2_A = 1196, 2011832, 2012288, 2012289


def apply(t, g, ok, rec):
    U, W = t['Units'], t['WeaponsJson']
    rows = lambda tab, **kw: sorted([r for r in t[tab].values() if r and all(r.get(k) == v for k, v in kw.items())], key=lambda r: r['Id'])
    wn = lambda i: W[i]['HUDName'] if i else ''
    men = rows('SquadMembersJson', UnitId=MOTO)
    ok(U[MOTO]['HUDName'] == 'Moto. Riflemen 摩步班' and U[MOTO]['Cost'] == 75 and len(men) == 8 and sum(r['SpecialWeaponId'] == PF98 for r in men) == 1, 'Moto. Riflemen: 8 men, 1 PF-98')
    ok(wn(QW2) == 'QW-2' and W[QW2]['Type'] == 85 and not rows('ModificationsJson', UnitId=MOTO), 'infantry QW-2; no loadouts')
    ok(not any(u and u.get('HUDName') in ('PAP Rifle Patrol', 'PAP AA Patrol') for u in U.values()), 'names free')
    g.put('Units', MOTO, {'HUDName': 'PAP Rifle Patrol'})
    aa = g.add('Units', U[MOTO], {'Name': 'PLA PAP AA Patrol', 'HUDName': 'PAP AA Patrol', 'OriginalCost': 0, 'Description': None, 'OriginalName': None})
    for tab in ('UnitArmorsJson', 'UnitPropulsionsJson', 'UnitAbilitiesJson', 'SensorUnitsJson', 'SquadWeaponsJson'):
        for r in rows(tab, UnitId=MOTO): g.add(tab, r, {'UnitId': aa, **({'WeaponId': QW2} if tab == 'SquadWeaponsJson' and r['WeaponId'] == PF98 else {})})
    for r in men: g.add('SquadMembersJson', r, {'UnitId': aa, **({'SpecialWeaponId': QW2} if r['SpecialWeaponId'] == PF98 else {})})
    for r in rows('WeaponAmmunitionsJson', UnitId=MOTO):
        g.add('WeaponAmmunitionsJson', r, {'UnitId': aa, **({'WeaponId': QW2, 'AmmunitionId': QW2_A, 'Quantity': 3} if r['WeaponId'] == PF98 else {})})
    (mc,) = rows('SpecializationAvailabilitiesJson', UnitId=MOTO)
    nc = g.add('SpecializationAvailabilitiesJson', mc, {'UnitId': aa})
    for r in rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=mc['Id']): g.add('TransportAvailabilitiesJson', r, {'SpecializationAvailabilityId': nc})
    # checks after
    carried = {w for r in rows('SquadMembersJson', UnitId=aa) for w in (r['PrimaryWeaponId'], r['SpecialWeaponId']) if w}
    ok({r['WeaponId'] for r in rows('SquadWeaponsJson', UnitId=aa)} == carried == {r['WeaponId'] for r in rows('WeaponAmmunitionsJson', UnitId=aa)} and PF98 not in carried and QW2 in carried, 'AA Patrol: card + ammo = carried, QW-2 not PF-98')
    kit = lambda u: sorted((wn(r['PrimaryWeaponId']), wn(r['SpecialWeaponId'])) for r in rows('SquadMembersJson', UnitId=u))
    ok([k for k in kit(aa) if k[1] != 'QW-2'] == [k for k in kit(MOTO) if k[1] != 'PF-98'] and len(rows('TransportAvailabilitiesJson', SpecializationAvailabilityId=nc)) == 5, 'otherwise identical; 5 transports')
    rec['pla_light_brigade_pap_1126'] = {'rifle_patrol': MOTO, 'aa_patrol': aa, 'aa_kit': kit(aa), 'cards': mc['MaxAvailabilityXp0'], 'spec': mc['SpecializationId']}
    print('PLA LIGHT BRIGADE PAP', rec['pla_light_brigade_pap_1126'])

"""One independent, normal-rate XM25 copy replaces two Stryker M203s."""
def apply(effective, clone, put, contract):
    c = contract
    why = 'Stryker teams: one M-25 CDTE special weapon replaces two M203s; +5 points'
    donor = effective['WeaponsJson'][c['weapon_donor']]
    assert donor['Name'] == 'MGL 25 XM25' and donor['MagazineSize'] == 5
    assert effective['AmmunitionsJson'][c['ammo_donor']]['Name'] == 'InfGrenade 25x40 XM25'
    weapon = clone('WeaponsJson', c['weapon_donor'],
                   dict(Name='MGL 25 M-25 CDTE', HUDName=c['name']), why)
    ammo = clone('AmmunitionsJson', c['ammo_donor'],
                 dict(Name='InfGrenade 25x40 M-25 CDTE', Damage=c['damage'],
                      IgnoreCover=c['ignore_cover']), why)
    for team in c['teams']:
        uid = team['unit']
        assert effective['Units'][uid]['Name'] == team['name']
        carriers = [r for r in effective['SquadMembersJson'].values()
                    if r['UnitId'] == uid and r['SpecialWeaponId'] == 58]
        assert sorted(r['Id'] for r in carriers) == team['carriers']
        assert all(r['PrimaryWeaponId'] == 50 for r in carriers)
        for index, member in enumerate(sorted(carriers, key=lambda r: r['Id'])):
            put('SquadMembersJson', member['Id'],
                dict(SpecialWeaponId=weapon if index == 0 else 0), why)
        for table in ['SquadWeaponsJson', 'WeaponAmmunitionsJson']:
            links = [r for r in effective[table].values()
                     if r['UnitId'] == uid and r['WeaponId'] == 58]
            assert len(links) == 1
            fields = dict(WeaponId=weapon)
            if table == 'WeaponAmmunitionsJson':
                assert links[0]['AmmunitionId'] == 29 and links[0]['Quantity'] == 48
                fields['AmmunitionId'] = ammo
                fields['Quantity'] = c['ammo_quantity']
            put(table, links[0]['Id'], fields, why)
        put('Units', uid, dict(Cost=effective['Units'][uid]['Cost'] + c['cost_increase']), why)

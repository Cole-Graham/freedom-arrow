"""Plane refund data policy. No clones: existing multiplayer IDs stay fixed."""
def apply(effective, contract, put):
    units=effective['Units']
    users={}
    for row in effective['WeaponAmmunitionsJson'].values():
        users.setdefault(row['AmmunitionId'],set()).add(row['UnitId'])
    guns=set(contract['free_gun_ammo'])
    for aid in guns:
        assert aid in users and all(units[u]['Type']==16 for u in users[aid]),('plane gun shared with non-plane',aid)
    for aid,ammo in effective['AmmunitionsJson'].items():
        if aid not in users:continue
        free=aid in guns or (contract['free_air_to_air'] and ammo['Name'].strip().startswith('Missile A2A '))
        if not free:continue
        if not any(units[u]['Type']==16 for u in users[aid]):continue
        assert all(units[u]['Type']==16 for u in users[aid]),('free A2A shared with non-plane',aid)
        put('AmmunitionsJson',aid,{'SupplyCost':0.0},'Plane refund: free A2A and gun ammunition; rearm unchanged')
    ability_users={}
    for link in effective['UnitAbilitiesJson'].values():
        ability_users.setdefault(link['AbilityId'],set()).add(link['UnitId'])
    if contract['free_plane_flares']:
        for aid,ability in effective['AbilitiesJson'].items():
            linked=ability_users.get(aid,set())
            if not linked or not ability['IsDecoy'] or not any(units[u]['Type']==16 for u in linked):continue
            assert all(units[u]['Type']==16 for u in linked),('plane flares shared with non-plane',aid)
            put('AbilitiesJson',aid,{'DecoySupplyCost':0.0},'Plane refund: free flares; quantity and effectiveness unchanged')

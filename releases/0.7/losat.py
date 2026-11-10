"""Isolated LOSAT data graph; allocate last to retain all existing clone IDs."""
def apply(effective, clone, add_unit, rows_of, c):
    uid=c['unit'];parent=c['parent'];why='LOSAT dedicated KE missile and unupgraded Bradley protection'
    assert uid not in effective['Units']
    add_unit(uid,parent,dict(Name=c['name'],HUDName=c['name'],ThumbnailFileName='FA_LOSAT-Label',PortraitFileName='FA_LOSAT-Portrait',Role=13,Cost=c['cost'],Length=6.31,Width=2.745,Height=3.99,InfantrySlots=0,ContentMembership=-1,DisplayInArmory=True),why)
    for table in ['UnitPropulsionsJson','SensorUnitsJson']:
        for rid in list(rows_of(table,parent)):clone(table,rid,{'UnitId':uid},why)
    armor=effective['OptionsJson'][39]['ArmorId']
    aid=clone('ArmorsJson',armor,dict(Name='Armor LOSAT Bradley base',MaxHealthPoints=c['vehicle_hp'],ModelFileName=None,IsDefault=True),why)
    clone('UnitArmorsJson',14,dict(UnitId=uid,ArmorId=aid),why)
    base=effective['AmmunitionsJson'][c['kornet_ammo']]
    ammo=clone('AmmunitionsJson',c['kornet_ammo'],dict(Name='Missile AT LOSAT KE',HUDName='MGM-166 KEM',ArmorTargeted=1,Damage=c['damage'],PenetrationAtMinRange=c['penetration'],PenetrationAtGroundRange=c['penetration'],CanBeIntercepted=False,CanBeTargeted=False,MuzzleVelocity=base['MuzzleVelocity']*2,MaxSpeed=base['MaxSpeed']*2,Acceleration=base['Acceleration']*4,BurnTime=base['BurnTime']/2),why)
    # Double velocity and quadruple acceleration preserve half-time scaled motion until the cap.
    weapon=clone('WeaponsJson',c['kornet_weapon'],dict(Name='LOSAT KEM launcher',HUDName='MGM-166 KEM',MagazineSize=12,ShotsPerBurstMin=1,ShotsPerBurstMax=1,SimultaneousTracking=1,MultiTargetTracking=1),why)
    turret=clone('TurretsJson',15,dict(IsDefault=True),why)
    tw=next(x for x in effective['TurretWeaponsJson'].values() if x['TurretId']==15 and x['Order']==0)
    clone('TurretWeaponsJson',tw['Id'],dict(TurretId=turret,WeaponId=weapon),why)
    clone('TurretUnitsJson',16,dict(UnitId=uid,TurretId=turret),why)
    clone('WeaponAmmunitionsJson',796,dict(UnitId=uid,WeaponId=weapon,AmmunitionId=ammo,Quantity=12,Order=0),why)
    # One intrinsic loadout: no inherited cannon, coax, troops, APS, smoke or armor choices.
    for spec in c['specs']:
        clone('SpecializationAvailabilitiesJson',490,dict(UnitId=uid,SpecializationId=spec,MaxAvailabilityXp0=c['availability'],MaxAvailabilityXp1=0,MaxAvailabilityXp2=0,MaxAvailabilityXp3=0),why)

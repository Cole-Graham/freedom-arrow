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
    speed=c['projectile_speed_ui']/3.6
    ammo=clone('AmmunitionsJson',c['kornet_ammo'],dict(Name='Missile AT LOSAT KE',HUDName='MGM-166 KEM',ArmorTargeted=1,Damage=c['damage'],PenetrationAtMinRange=c['penetration'],PenetrationAtGroundRange=c['penetration'],CanBeIntercepted=False,CanBeTargeted=False,MuzzleVelocity=speed,MaxSpeed=speed,Acceleration=0.0,BurnTime=2.0),why)
    # Card missile speed is raw m/s multiplied by3.6. Keep that converted speed constant from launch.
    weapon=clone('WeaponsJson',c['kornet_weapon'],dict(Name='LOSAT KEM launcher',HUDName='MGM-166 KEM',MagazineSize=12,ShotsPerBurstMin=1,ShotsPerBurstMax=1,TimeBetweenBurstsMin=c['shot_gap'],TimeBetweenBurstsMax=c['shot_gap'],SimultaneousTracking=1,MultiTargetTracking=1),why)
    turret=clone('TurretsJson',15,dict(IsDefault=True),why)
    tw=next(x for x in effective['TurretWeaponsJson'].values() if x['TurretId']==15 and x['Order']==0)
    clone('TurretWeaponsJson',tw['Id'],dict(TurretId=turret,WeaponId=weapon),why)
    clone('TurretUnitsJson',16,dict(UnitId=uid,TurretId=turret),why)
    clone('WeaponAmmunitionsJson',796,dict(UnitId=uid,WeaponId=weapon,AmmunitionId=ammo,Quantity=12,Order=0),why)
    # One intrinsic loadout: no inherited cannon, coax, troops, APS, smoke or armor choices.
    for spec in c['specs']:
        clone('SpecializationAvailabilitiesJson',490,dict(UnitId=uid,SpecializationId=spec,MaxAvailabilityXp0=c['availability'],MaxAvailabilityXp1=0,MaxAvailabilityXp2=0,MaxAvailabilityXp3=0),why)


def apply_vehicle_speed(t,clone,put,c):
    """Allocate after earlier loadouts so their stable IDs remain unchanged."""
    (link,)=[x for x in t['UnitPropulsionsJson'].values() if x['UnitId']==c['unit']]
    donor=t['MobilityJson'][link['MobilityId']];assert donor['MaxSpeedRoad']==60 and donor['MaxCrossCountrySpeed']==45
    own=clone('MobilityJson',donor['Id'],{'Name':'Tracks LOSAT road50','MaxSpeedRoad':float(c['vehicle_speed'])},'Osama: LOSAT vehicle road speed50; Bradley unchanged')
    put('UnitPropulsionsJson',link['Id'],{'MobilityId':own},'LOSAT uses its own50-speed mobility')

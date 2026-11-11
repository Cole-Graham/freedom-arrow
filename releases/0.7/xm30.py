"""XM30 requested data graph; T-15 stand-in until an FBX/Blend source is supplied."""
def apply(effective,original,clone,add_unit,rows_of,patches,audit):
    uid=983;why='XM30 US Armor tank:220 points,2 availability,Booker XM913,2 APS'
    assert uid not in effective['Units']
    add_unit(uid,255,dict(Name='XM30',HUDName='XM30',CountryId=2,Role=11,Cost=220,ContentMembership=-1,PortraitFileName=effective['Units'][16]['PortraitFileName'],ThumbnailFileName=effective['Units'][16]['ThumbnailFileName']),why)
    for table in ['UnitPropulsionsJson','SensorUnitsJson']:
        for rid in list(rows_of(table,255)):clone(table,rid,{'UnitId':uid},why)
    aid=clone('ArmorsJson',306,dict(Name='Armor XM30 Booker base',ModelFileName=None,MaxHealthPoints=14,HeatArmorFront=700,HeatArmorSides=700),why)
    clone('UnitArmorsJson',416,{'UnitId':uid,'ArmorId':aid},why)
    ab=clone('AbilitiesJson',117,dict(Name='XM30 smoke and APS x2',APSQuantity=2,IsDefault=True,ModelFileName=None),why)
    clone('UnitAbilitiesJson',1111,{'UnitId':uid,'AbilityId':ab},why)
    # Keep T-15 native turret Name/shape for its stand-in model. Change weapon rows only.
    mid=clone('ModificationsJson',247,{'UnitId':uid,'Name':'Weapons XM30'},why)
    for order,(wid,ammo,icon,label) in enumerate([(256,458,'TOW_M41','2x TOW-2B'),(76,508,'JAVELIN','2x Javelin')]):
        missile=clone('WeaponsJson',wid,{'Name':'XM30 '+label,'MagazineSize':2},why)
        turret=clone('TurretsJson',472,{},why)
        clone('TurretUnitsJson',663,{'UnitId':uid,'TurretId':turret},why)
        for link in list(effective['TurretWeaponsJson'].values()):
            if link['TurretId']!=472:continue
            replacement={302:658,340:missile}.get(link['WeaponId'],link['WeaponId'])
            clone('TurretWeaponsJson',link['Id'],{'TurretId':turret,'WeaponId':replacement},why)
        # Only the requested missile's ammunition; two ready rounds, no extra reserve.
        src=effective['WeaponAmmunitionsJson'][728 if wid==256 else 2528]  # 728: TOW-2B top attack (ammo 52), not 2462 TOW bunker buster (458)
        clone('WeaponAmmunitionsJson',src['Id'],{'UnitId':uid,'WeaponId':missile,'Quantity':2},why)
        clone('OptionsJson',647,dict(ModificationId=mid,Name='XM30 '+label,UIName=label,Order=order,Cost=0,IsDefault=order==0,Turret0Id=turret,ConcatenateWithUnitName=None,ThumbnailOverride=None,OptionPicture=icon),why)
    for wid,donor in [(658,453),(7,255)]:
        for rid in list(rows_of('WeaponAmmunitionsJson',donor)):
            if effective['WeaponAmmunitionsJson'][rid]['WeaponId']==wid:clone('WeaponAmmunitionsJson',rid,{'UnitId':uid},why)
    clone('SpecializationAvailabilitiesJson',865,dict(UnitId=uid,SpecializationId=4,MaxAvailabilityXp0=2,MaxAvailabilityXp1=0,MaxAvailabilityXp2=0,MaxAvailabilityXp3=0),why)

    # Preserve all IDs already allocated for saved XM30 packages, then remove the PKT links.
    own_turrets={r['TurretId'] for r in effective['TurretUnitsJson'].values() if r['UnitId']==uid}
    for table in ['TurretWeaponsJson','WeaponAmmunitionsJson']:
        ids={r['Id'] for r in effective[table].values() if r['WeaponId']==7 and (r.get('UnitId')==uid if table=='WeaponAmmunitionsJson' else r['TurretId'] in own_turrets)}
        for rid in ids:
            assert rid not in original[table]
            del effective[table][rid];patches[table].pop(str(rid),None)
        audit[:]=[a for a in audit if not(a['table']==table and a['id'] in ids)]

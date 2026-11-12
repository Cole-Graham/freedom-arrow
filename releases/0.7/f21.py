"""Rebuild the existing F-14 card as F-21 from the current Super Hornet without shifting other clone IDs."""
import copy

def apply(t,p,clone,put,migration,c):
    uid=c['unit'];donor=c['parent'];why='F21 Super Tomcat requested Super Hornet baseline and armament'
    original=copy.deepcopy(t['Units'][uid]);fields={k:copy.deepcopy(v) for k,v in t['Units'][donor].items() if k!='Id'}
    fields.update(Name=c['name'],HUDName=c['name'],Cost=t['Units'][donor]['Cost']+c['cost_increment'],DisplayInArmory=True,PortraitFileName=original['PortraitFileName'],ThumbnailFileName=original['ThumbnailFileName']);put('Units',uid,fields,why)
    def own(table):return [r for r in t[table].values() if r.get('UnitId')==uid]
    def erase(table,rid):
        assert rid>=2000000 or table=='OptionsJson';del t[table][rid];p[table].pop(str(rid),None)
    oldmods={r['Id']:r for r in own('ModificationsJson')};oldopts=[o for o in t['OptionsJson'].values() if o['ModificationId'] in oldmods]
    for o in oldopts:erase('OptionsJson',o['Id'])
    for m in oldmods:erase('ModificationsJson',m)
    for table in ['UnitPropulsionsJson','UnitAbilitiesJson','TurretUnitsJson','WeaponAmmunitionsJson','UnitArmorsJson','SensorUnitsJson']:
        for row in own(table):erase(table,row['Id'])
    base=[r for r in t['UnitPropulsionsJson'].values() if r['UnitId']==donor and t['MobilityJson'][r['MobilityId']]['IsDefault']];assert len(base)==1
    flight=clone('FlyPresetsJson',t['MobilityJson'][base[0]['MobilityId']]['FlyPresetId'],{'Name':'F21 Fighter Bomber 950 kph','MaxSpeed':c['flight_speed_mps']},why)
    mob=clone('MobilityJson',base[0]['MobilityId'],{'Name':'Plane F21 Super Tomcat','MaxSpeedRoad':c['speed'],'FlyPresetId':flight},why);clone('UnitPropulsionsJson',base[0]['Id'],{'UnitId':uid,'MobilityId':mob},why)
    defense=[r for r in t['UnitAbilitiesJson'].values() if r['UnitId']==donor and t['AbilitiesJson'][r['AbilityId']]['IsDefault']];assert len(defense)==1
    aid=clone('AbilitiesJson',defense[0]['AbilityId'],{'Name':'F21 intrinsic ECM 40 percent','ECMAccuracyMultiplier':c['ecm_multiplier'],'IsDefault':True},why);clone('UnitAbilitiesJson',defense[0]['Id'],{'UnitId':uid,'AbilityId':aid},why)
    for table in ['UnitArmorsJson','SensorUnitsJson']:
        for row in list(t[table].values()):
            if row['UnitId']==donor:clone(table,row['Id'],{'UnitId':uid},why)
    # Triple AMRAAM, double Gunslinger and double Sidewinder carriers use existing native model paths.
    racks={};ammo=[]
    for tag,tid,wid,count in [('aim9_double',166,113,2),('aim120_triple',934,231,3),('aim174_double',935,679,2)]:
        w=clone('WeaponsJson',wid,{'Name':t['WeaponsJson'][wid]['Name']+' F21 pylon','MagazineSize':count},why)
        turret=clone('TurretsJson',tid,{},why)
        links=[r for r in t['TurretWeaponsJson'].values() if r['TurretId']==tid];assert len(links)==1 and links[0]['WeaponId']==wid
        clone('TurretWeaponsJson',links[0]['Id'],{'TurretId':turret,'WeaponId':w},why);racks[tag]=turret
        src=[r for r in t['WeaponAmmunitionsJson'].values() if r['UnitId']==donor and r['WeaponId']==wid];assert len(src)==1
        ammo.append((src[0]['Id'],{'UnitId':uid,'WeaponId':w,'Quantity':count}))
    used={132,160,166,935,869,*racks.values()}
    template=next(r for r in t['TurretUnitsJson'].values() if r['UnitId']==donor)
    for tid in sorted(used):clone('TurretUnitsJson',template['Id'],{'UnitId':uid,'TurretId':tid,'Order':0},why)
    # Copy only ammunition that one of the requested carriers can fire, including the donor's intrinsic cannon.
    for source_unit,wid in [(donor,88),(donor,113),(donor,679),(c['slam_parent'],634)]:
        src=[r for r in t['WeaponAmmunitionsJson'].values() if r['UnitId']==source_unit and r['WeaponId']==wid];assert len(src)==1
        ammo.append((src[0]['Id'],{'UnitId':uid}))
    for rid,fields in ammo:clone('WeaponAmmunitionsJson',rid,fields,why)
    defaults={};template_option=copy.deepcopy(t['OptionsJson'][980]);base_mod=t['ModificationsJson'][318]
    for order,slot in enumerate(c['slots']):
        mid=clone('ModificationsJson',base_mod['Id'],{'UnitId':uid,'Name':'Weapons F21 '+slot['name'],'UIName':slot['ui'],'Order':order},why)
        for n,load in enumerate(slot['loads']):
            fields={k:copy.deepcopy(v) for k,v in template_option.items() if k!='Id'}
            for i in range(21):fields['Turret'+str(i)+'Id']=0
            for field in ['Ability1Id','Ability2Id','Ability3Id','MobilityId','ArmorId','SensorId']:
                if field in fields:fields[field]=0
            fields.update(ModificationId=mid,Name=load['name'],UIName=load['label'],Cost=load['cost'],Order=n,IsDefault=n==0,OptionPicture=load['icon'])
            for index,kind in load['mounts'].items():fields['Turret'+index+'Id']=racks[kind] if isinstance(kind,str) else kind
            oid=load['id'];assert 0<oid<=32767 and oid not in t['OptionsJson'];put('OptionsJson',oid,fields,why)
            if n==0:defaults[slot['name']]=oid
    # Old wing choices become the inner default; old fuselage/fuel choices become the fuselage default.
    removed={o['Id']:defaults['InnerPylons'] if 'Wings' in oldmods[o['ModificationId']]['Name'] else defaults['Fuselage'] for o in oldopts}
    for old,new in list(migration.items()):
        if new in removed:migration[old]=removed[new]
    migration.update(removed)
    assert len([o for o in t['OptionsJson'].values() if o['ModificationId'] in {r['Id'] for r in own('ModificationsJson')}])==7
    assert all(0<x<=32767 for x in t['OptionsJson'])

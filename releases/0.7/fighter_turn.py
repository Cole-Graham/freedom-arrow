"""Isolate the three requested fighter cards at UI turn radius800 without changing shared donors."""
def apply(t,clone,put,c):
    units=set(c['units']);assert units=={297,44,950}
    why='F22 Su57 Su75 UI turn radius800; Su47 and other shared consumers preserved'
    links=[r for r in t['UnitPropulsionsJson'].values() if r['UnitId'] in units]
    assert len(links)==len(units) and {r['UnitId'] for r in links}==units
    oldmob={r['MobilityId'] for r in links};oldfp={t['MobilityJson'][m]['FlyPresetId'] for m in oldmob};assert len(oldfp)==1
    old=oldfp.pop();base=t['FlyPresetsJson'][old];assert base['Name']=='FA Fighter-Supermaneuver' and base['MaxSpeedYaw']==82.5 and base['MaxSpeed']==250
    ratio=c['max_speed_yaw']/base['MaxSpeedYaw']
    fields={k:round(base[k]*ratio,8) for k in ['MinSpeedYaw','MaxSpeedYaw','AfterburnYaw','CornerSpeedYaw','CornerAfterburnSpeedYaw']}
    new=clone('FlyPresetsJson',old,{'Name':'FA F22 Su57 Su75 turn800',**fields},why)
    mapping={m:clone('MobilityJson',m,{'Name':t['MobilityJson'][m]['Name']+' turn800','FlyPresetId':new},why) for m in sorted(oldmob)}
    for r in links:put('UnitPropulsionsJson',r['Id'],{'MobilityId':mapping[r['MobilityId']]},why)
    mods={r['Id'] for r in t['ModificationsJson'].values() if r['UnitId'] in units}
    # Future fuel/mobility options cannot silently restore the old preset.
    for o in t['OptionsJson'].values():
        if o['ModificationId'] not in mods or not o['MobilityId']:continue
        assert o['MobilityId'] in mapping,(o['Id'],o['MobilityId'])
        put('OptionsJson',o['Id'],{'MobilityId':mapping[o['MobilityId']]},why)


def apply_black_widow(t,clone,put,c):
    """Give YF-23 its own preset after all earlier clones, preserving their IDs."""
    uid=c['unit'];assert uid==982
    why='Osama: YF23 Black Widow II UI turn radius700'
    links=[r for r in t['UnitPropulsionsJson'].values() if r['UnitId']==uid];assert len(links)==1
    link=links[0];mob=t['MobilityJson'][link['MobilityId']];base=t['FlyPresetsJson'][mob['FlyPresetId']]
    assert base['MaxSpeed']==250 and base['MaxSpeedYaw']==82.5
    ratio=c['max_speed_yaw']/base['MaxSpeedYaw']
    fields={k:round(base[k]*ratio,8) for k in ['MinSpeedYaw','MaxSpeedYaw','AfterburnYaw','CornerSpeedYaw','CornerAfterburnSpeedYaw']}
    preset=clone('FlyPresetsJson',base['Id'],{'Name':'FA YF23 turn700',**fields},why)
    mobility=clone('MobilityJson',mob['Id'],{'Name':'FA YF23 turn700','FlyPresetId':preset},why)
    put('UnitPropulsionsJson',link['Id'],{'MobilityId':mobility},why)
    mods={r['Id'] for r in t['ModificationsJson'].values() if r['UnitId']==uid}
    assert not any(o['MobilityId'] for o in t['OptionsJson'].values() if o['ModificationId'] in mods),'Unrecognized YF23 mobility override'

"""Append the private PLA test roster after current live allocations."""
import json,copy
def apply(R,effective,put,clone,add_unit,rows_of,discard):
    # PLA test division: armory preview, 0 points, renamed full copies of Russian units (pla-test-contract.json).
    pl=json.loads((R/'pla-test-contract.json').read_text());why='PLA test division'
    sp=pl['spec'];assert sp['id'] not in effective['SpecializationsJson']
    row=copy.deepcopy(effective['SpecializationsJson'][sp['like']]);row.pop('Id');row.update(sp['fields']);put('SpecializationsJson',sp['id'],row,why)
    unit_tables=['UnitAbilitiesJson','UnitPropulsionsJson','TurretUnitsJson','WeaponAmmunitionsJson','SensorUnitsJson','SquadMembersJson','SquadWeaponsJson','UnitArmorsJson']
    for c in pl['cards']:
        par,new=c['parent'],c['unit'];p=effective['Units'][par]
        assert new not in effective['Units'] and p['CountryId']==(2 if c.get('us') else 1),(new,par)
        add_unit(new,par,{'Name':(c['name'] if c.get('russia') or c.get('us') else 'PLA '+c['name']),'HUDName':c['name'],'DisplayInArmory':True,**({'Cost':c['cost']} if 'cost' in c else {})},why)
        for table in unit_tables:
            for rid in rows_of(table,par):clone(table,rid,{'UnitId':new},why)
        for mod in [m for m in list(effective['ModificationsJson'].values()) if m['UnitId']==par]:
            mine=sorted((o for o in effective['OptionsJson'].values() if o['ModificationId']==mod['Id'] and not o.get('ReplaceUnitId')),key=lambda o:(o['Order'],o['Id']))
            if not mine:continue
            m=clone('ModificationsJson',mod['Id'],{'UnitId':new},why);default=any(o['IsDefault'] for o in mine)
            want=c.get('default_options',[]);hit=[o for o in mine if o['Name'].strip() in want]
            for order,o in enumerate(mine):clone('OptionsJson',o['Id'],{'ModificationId':m,'Order':order,'IsDefault':(o in hit) if hit else (o['IsDefault'] or (not default and order==0)),**({'ReplaceUnitName':c['name']} if o.get('ReplaceUnitName') else {})},why)
        if c.get('transport_only'):continue
        if c.get('russia') or c.get('us'):
            # A new Russian card (Osama): same specializations and slots as its parent, not the PLA test spec.
            mine=[r for r in list(effective['SpecializationAvailabilitiesJson'].values()) if r['UnitId']==par]
            if c.get('specs'):  # a named spec list (Osama: B-21 in Airborne) replaces the parent's specs; slots copy the parent's first row
                for s in c['specs']:clone('SpecializationAvailabilitiesJson',mine[0]['Id'],{'UnitId':new,'SpecializationId':s},why)
            else:
                for r in mine:clone('SpecializationAvailabilitiesJson',r['Id'],{'UnitId':new},why)
            continue
        like=next(r for r in effective['SpecializationAvailabilitiesJson'].values() if r['UnitId']==par)
        pool=clone('SpecializationAvailabilitiesJson',like['Id'],{'UnitId':new,'SpecializationId':sp['id']},why)
        for t,tp in c.get('transports',{}).items():
            src=next(r for r in effective['TransportAvailabilitiesJson'].values() if r['UnitId']==tp)
            clone('TransportAvailabilitiesJson',src['Id'],{'SpecializationAvailabilityId':pool,'UnitId':int(t)},why)
    pla={c['unit'] for c in pl['cards']}
    assert {r['UnitId'] for r in effective['SpecializationAvailabilitiesJson'].values() if r['SpecializationId']==sp['id']}=={c['unit'] for c in pl['cards'] if not c.get('transport_only') and not c.get('russia') and not c.get('us')}
    assert all(any(r['UnitId']==u for r in effective['UnitArmorsJson'].values()) for u in pla),'PLA card without armor'
    # Osama, 9 Nov: Y-20 uses IL-76MD transport stats, with no weapon mounts or ammunition.
    # Apply after all existing clone allocations so saved loadout IDs do not move.
    yc=json.loads((R/'y20-transport-contract.json').read_text());yu,yp=yc['unit'],yc['donor']
    assert not any(m['UnitId']==yp for m in effective['ModificationsJson'].values()),'Y-20 donor options need explicit handling'
    identity={k:effective['Units'][yu][k] for k in ['Name','HUDName','DisplayInArmory']}
    row=copy.deepcopy(effective['Units'][yp]);row.pop('Id');row.update(identity)
    put('Units',yu,row,'Y-20 IL-76MD stat clone, unarmed')
    for table in unit_tables:
        for rid in list(rows_of(table,yu)):
            discard(table,rid)
        if table in ['TurretUnitsJson','WeaponAmmunitionsJson','SquadMembersJson','SquadWeaponsJson']:continue
        for rid in list(rows_of(table,yp)):clone(table,rid,{'UnitId':yu},'Y-20 IL-76MD stat clone, unarmed')
    for table in ['TurretUnitsJson','WeaponAmmunitionsJson']:assert not rows_of(table,yu)
    assert all(effective['Units'][yu][k]==v for k,v in effective['Units'][yp].items() if k not in ['Id',*identity])
    return pl

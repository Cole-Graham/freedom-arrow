"""Twenty-five appearance comparison cards; all use the approved functional PLA squad."""
import json

def apply(R,effective,put,clone,add_unit,rows_of):
    configs=json.loads((R/'pla-configurations-contract.json').read_text())
    source=901
    assert not any(r['UnitId']==source for r in effective['ModificationsJson'].values())
    for index,c in enumerate(configs):
        uid=985+index;c['unit']=uid
        assert uid not in effective['Units']
        why='PLA appearance comparison '+c['label']
        add_unit(uid,source,dict(Name='PLA test '+c['key'],HUDName=c['label'],DisplayInArmory=True,Description='Appearance comparison. Same weapons and balance as PLA Rifle Squad.'),why)
        for table in ['UnitArmorsJson','UnitAbilitiesJson','UnitPropulsionsJson','SensorUnitsJson','SquadMembersJson','SquadWeaponsJson','WeaponAmmunitionsJson']:
            for rid in list(rows_of(table,source)):clone(table,rid,{'UnitId':uid},why)
        for rid in list(rows_of('SpecializationAvailabilitiesJson',source)):
            clone('SpecializationAvailabilitiesJson',rid,{'UnitId':uid,'MaxAvailabilityXp0':8},why)
        assert len(rows_of('SquadMembersJson',uid))==7
        for table in ['SquadWeaponsJson','WeaponAmmunitionsJson']:
            def data(unit):return sorted([json.dumps({k:v for k,v in effective[table][rid].items() if k not in ['Id','UnitId']},sort_keys=True) for rid in rows_of(table,unit)])
            assert data(uid)==data(source),(uid,table)
    (R/'source/UserData/FreedomArrow/pla-infantry-configurations.json').write_text(json.dumps(configs,indent=2)+'\n')
    p=R/'source/UserData/FreedomArrow/pla-build.json';build=json.loads(p.read_text());build.update(build=int(json.loads((R/'mod.json').read_text())['version']),label='PLA TEST Build '+json.loads((R/'mod.json').read_text())['version'],appearance_comparison=configs);p.write_text(json.dumps(build,indent=2)+'\n')

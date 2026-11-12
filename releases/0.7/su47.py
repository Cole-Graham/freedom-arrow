"""Su-47-specific agility, intrinsic ECM and loadout pruning; preserve donor units and wire IDs."""
def apply(t,p,clone,put,migration,c):
    uid=c['unit'];why='Su-47 agility, built-in ECM and requested loadouts'
    base_cost=t['Units'][uid]['Cost'];put('Units',uid,{'Cost':base_cost+c['agility_cost']+c['ecm_cost']},why)
    reference=[r for r in t['UnitPropulsionsJson'].values() if r['UnitId']==c['agility_like'] and t['MobilityJson'][r['MobilityId']]['IsDefault']]
    assert len(reference)==1
    preset=t['MobilityJson'][reference[0]['MobilityId']]['FlyPresetId'];mobmap={}
    for link in [r for r in t['UnitPropulsionsJson'].values() if r['UnitId']==uid]:
        old=link['MobilityId'];mobmap[old]=clone('MobilityJson',old,{'Name':t['MobilityJson'][old]['Name']+' Su47 agility','FlyPresetId':preset},why)
        put('UnitPropulsionsJson',link['Id'],{'MobilityId':mobmap[old]},why)
    mods={r['Id'] for r in t['ModificationsJson'].values() if r['UnitId']==uid}
    options=[r for r in t['OptionsJson'].values() if r['ModificationId'] in mods]
    remove=[o for o in options if o['Name'] in c['remove_options']]
    assert len(remove)==len(c['remove_options'])==11
    defaults={}
    for name in c['defaults']:
        selected=[o for o in options if o['Name']==name];assert len(selected)==1
        o=selected[0];defaults[o['ModificationId']]=o['Id']
    removed={o['Id']:defaults[o['ModificationId']] for o in remove}
    for o in remove:
        del t['OptionsJson'][o['Id']];del p['OptionsJson'][str(o['Id'])]
    for o in options:
        if o['Id'] in removed:continue
        fields={}
        if o['ModificationId'] in defaults:fields['IsDefault']=o['Id']==defaults[o['ModificationId']]
        if o['MobilityId'] in mobmap:fields['MobilityId']=mobmap[o['MobilityId']]
        if fields:put('OptionsJson',o['Id'],fields,why)
    # Existing saved unsafe aliases and the already-safe removed IDs all resolve to a valid slot default.
    for old,new in list(migration.items()):
        if new in removed:migration[old]=removed[new]
    migration.update(removed)
    abilities=[r for r in t['UnitAbilitiesJson'].values() if r['UnitId']==uid]
    default=[r for r in abilities if t['AbilitiesJson'][r['AbilityId']]['IsDefault']]
    assert len(default)==1
    own=clone('AbilitiesJson',default[0]['AbilityId'],{'Name':'Su47 intrinsic ECM 40 percent','ECMAccuracyMultiplier':c['ecm_multiplier'],'IsDefault':True},why)
    put('UnitAbilitiesJson',default[0]['Id'],{'AbilityId':own},why)
    for link in abilities:
        if link['Id']!=default[0]['Id']:
            assert not any(link['AbilityId']==o[f] for o in t['OptionsJson'].values() if o['ModificationId'] in mods for f in ['Ability1Id','Ability2Id','Ability3Id'])
            del t['UnitAbilitiesJson'][link['Id']];del p['UnitAbilitiesJson'][str(link['Id'])]
    assert t['AbilitiesJson'][own]['IsDecoy'] and t['AbilitiesJson'][own]['DecoyQuantity']==25

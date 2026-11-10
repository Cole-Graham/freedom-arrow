"""Combine the latest PLA roster with approved infantry and live prototype cards."""
import copy,json

def apply(R,effective,original,patches,audit,put,clone,add_unit,rows_of,discard):
    from pla_infantry import apply as infantry
    binding=infantry(R,effective,put,clone,discard)
    kc=json.loads((R/'karatel-contract.json').read_text());u=kc['unit'];parent=kc['stats_parent'];why='Complete PLA: approved Karatel'
    assert u not in effective['Units']
    add_unit(u,parent,dict(Name=kc['name'],HUDName=kc['name'],DisplayInArmory=True,InfantrySlots=10,Length=kc['length'],Cost=35),why)
    for table in ['UnitPropulsionsJson','SensorUnitsJson','UnitArmorsJson']:
        for rid in list(rows_of(table,parent)):clone(table,rid,{'UnitId':u},why)
    empty=next(r for r in effective['TurretUnitsJson'].values() if r['UnitId']==96 and r['TurretId']==160)
    clone('TurretUnitsJson',empty['Id'],{'UnitId':u},why)
    users={r['SpecializationAvailabilityId']:r['Id'] for r in effective['TransportAvailabilitiesJson'].values() if r['UnitId'] in kc['transport_donors'] and effective['SpecializationAvailabilitiesJson'][r['SpecializationAvailabilityId']]['SpecializationId']==kc['spec']}
    for rid in users.values():clone('TransportAvailabilitiesJson',rid,{'UnitId':u},why)
    smoke=effective['AbilitiesJson'][1];fields={k:smoke[k] for k in ['IsSmoke','SmokeAmmunitionId','SmokeAmmunitionQuantity','SmokeCooldown']}
    ability=clone('AbilitiesJson',109,dict(Name='Karatel combined supply smoke',IsDefault=True,**fields),why)
    clone('UnitAbilitiesJson',next(iter(original['UnitAbilitiesJson'])),dict(UnitId=u,AbilityId=ability),why)
    from xm30 import apply as xm30
    xm30(effective,original,clone,add_unit,rows_of,patches,audit)
    # Keep the infantry branch's approved XM30 standard jammer in its existing combined APS/smoke profile.
    for a in [effective['AbilitiesJson'][effective['UnitAbilitiesJson'][rid]['AbilityId']] for rid in rows_of('UnitAbilitiesJson',983)]:
        if a['IsAPS']:put('AbilitiesJson',a['Id'],{'ECMAccuracyMultiplier':0.7},'PLA XM30 combined default defenses')
    # Abrams X default defenses must be combined for the native first-default loader.
    ax=json.loads((R/'abramsx-contract.json').read_text());u=ax['unit'];fields={}
    for f in ['Ability1Id','Ability2Id','Ability3Id']:
        aid=ax['option_fields'][f];a=effective['AbilitiesJson'][aid]
        if a['IsSmoke']:fields.update({k:a[k] for k in ['IsSmoke','SmokeAmmunitionId','SmokeAmmunitionQuantity','SmokeCooldown']})
        if a['IsAPS']:aps=aid
        if a['ECMAccuracyMultiplier']>0:fields['ECMAccuracyMultiplier']=a['ECMAccuracyMultiplier']
    ability=clone('AbilitiesJson',aps,dict(Name='Abrams X combined defaults',IsDefault=True,**fields),'Complete PLA default defenses')
    clone('UnitAbilitiesJson',next(iter(original['UnitAbilitiesJson'])),dict(UnitId=u,AbilityId=ability),'Complete PLA default defenses')
    mods={m['Id'] for m in effective['ModificationsJson'].values() if m['UnitId']==u}
    for o in list(effective['OptionsJson'].values()):
        if o['ModificationId'] in mods:put('OptionsJson',o['Id'],dict(Ability1Id=0,Ability2Id=0,Ability3Id=0),'Abrams defaults are intrinsic')
    cfg={'build':1,'label':'PLA TEST Build 1','roster_contract':'pla-test-contract.json','infantry':binding,'additional_cards':{'XM30':983,'Karatel':984},'source_rosters':['PLA.48','PLA.infantry.11'],'runtime_verified':False}
    (R/'source/UserData/FreedomArrow/pla-build.json').write_text(json.dumps(cfg,indent=2)+'\n')
    # Options are transmitted as signed shorts; reject future unmapped additions.
    from option_network_ids import apply as fix_options
    migration=fix_options(effective,patches,json.loads((R/'option-network-ids.json').read_text()))
    (R/'source/UserData/FreedomArrow/option-id-migration.json').write_text(json.dumps(migration,indent=2)+'\n')
    multi=[u for u in effective['Units'] if sum(bool(effective['AbilitiesJson'][x['AbilityId']]['IsDefault']) for x in effective['UnitAbilitiesJson'].values() if x['UnitId']==u)>1]
    assert not multi,('Multiple native default abilities',multi)

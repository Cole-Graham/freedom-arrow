"""F-22 side-bay MAKO and the bomber-only MiG-31BSM loadouts.

Apply last to preserve every earlier generated ID and network option migration.
"""
import copy

def apply(t,p,clone,put,migration,c):
    uid=c['f22']['unit'];assert uid==297
    why='Osama: one ARRW-clone MAKO per F22 side bay at +80'
    (source_weapon,)=[r for r in t['WeaponsJson'].values() if r['Name']=='Cruise AGM183A ARRW wings']
    (source_ammo,)={r['AmmunitionId'] for r in t['WeaponAmmunitionsJson'].values() if r['WeaponId']==source_weapon['Id']}
    assert source_weapon['MagazineSize']==1
    ammo=clone('AmmunitionsJson',source_ammo,{'Name':'Missile Cruise MAKO','HUDName':'MAKO'},why)
    weapon=clone('WeaponsJson',source_weapon['Id'],{'Name':'Cruise MAKO','HUDName':'MAKO'},why)
    # Retain the F22 bay mount semantics; use the existing ARRW missile model.
    (arrw_mount,)=[r['TurretId'] for r in t['TurretWeaponsJson'].values() if r['WeaponId']==source_weapon['Id']]
    turret=clone('TurretsJson',551,{'ModelFileName':t['TurretsJson'][arrw_mount]['ModelFileName']},why)
    clone('TurretWeaponsJson',855,{'TurretId':turret,'WeaponId':weapon},why)
    clone('TurretUnitsJson',984,{'TurretId':turret},why)
    clone('WeaponAmmunitionsJson',1353,{'WeaponId':weapon,'AmmunitionId':ammo,'Quantity':1},why)
    for slot in c['f22']['bays']:
        base=t['OptionsJson'][slot['like_option']];assert base['ModificationId']==slot['modification']
        fields={k:copy.deepcopy(v) for k,v in base.items() if k!='Id'}
        fields.update(Name=slot['name'],UIName='1x MAKO',Cost=80,IsDefault=False,OptionPicture='MOD_KINZHAL_HE',Order=1+max(o['Order'] for o in t['OptionsJson'].values() if o['ModificationId']==base['ModificationId']))
        fields['Turret'+str(slot['mount'])+'Id']=turret
        assert slot['option'] not in t['OptionsJson'] and 0<slot['option']<=32767
        put('OptionsJson',slot['option'],fields,why)
    uid=c['mig31bsm']['unit'];assert uid==743
    why='Osama: MiG31BSM bomber only; remove R37 R77 R73 R27ET'
    mods={r['Id']:r for r in t['ModificationsJson'].values() if r['UnitId']==uid}
    aa=set(c['mig31bsm']['aa_weapons']);assert aa=={243,439,244,437}
    mounts={r['TurretId'] for r in t['TurretWeaponsJson'].values() if r['WeaponId'] in aa}
    mine=[o for o in t['OptionsJson'].values() if o['ModificationId'] in mods]
    removed=[o for o in mine if any(o.get('Turret'+str(i)+'Id') in mounts for i in range(21))]
    assert len(removed)==9
    empty_template=copy.deepcopy(t['OptionsJson'][c['mig31bsm']['outer_empty']])
    defaults={empty_template['ModificationId']:empty_template['Id']}
    put('OptionsJson',empty_template['Id'],{'IsDefault':True},why)
    for slot in c['mig31bsm']['empty_bomber_slots']:
        fields={k:copy.deepcopy(v) for k,v in empty_template.items() if k!='Id'}
        for i in range(21):fields['Turret'+str(i)+'Id']=0
        for i in slot['mounts']:fields['Turret'+str(i)+'Id']=160
        fields.update(ModificationId=slot['modification'],Name=slot['name'],Order=0,IsDefault=True,Cost=0)
        assert slot['option'] not in t['OptionsJson'] and 0<slot['option']<=32767
        put('OptionsJson',slot['option'],fields,why);defaults[slot['modification']]=slot['option']
    replacements={o['Id']:defaults[o['ModificationId']] for o in removed}
    for o in removed:
        del t['OptionsJson'][o['Id']];p['OptionsJson'].pop(str(o['Id']))
    for old,new in list(migration.items()):
        if new in replacements:migration[old]=replacements[new]
    migration.update(replacements)
    for table,field,ids in [('TurretUnitsJson','TurretId',mounts),('WeaponAmmunitionsJson','WeaponId',aa)]:
        for row in list(t[table].values()):
            if row['UnitId']==uid and row[field] in ids:
                assert row['Id']>=2000000
                del t[table][row['Id']];p[table].pop(str(row['Id']))
    assert not any(o.get('Turret'+str(i)+'Id') in mounts for o in t['OptionsJson'].values() if o['ModificationId'] in mods for i in range(21))
    assert all(0<oid<=32767 for oid in t['OptionsJson'])

"""Unit-scoped functional PLA infantry prototype; native donor behavior is explicit."""
import json

def apply(root,effective,put,clone,discard):
    cfg=json.loads((root/'pla-infantry-contract.json').read_text());uid=cfg['unit'];why='PLA infantry functional prototype';bindings={};ammo_ids={}
    members=sorted((r for r in effective['SquadMembersJson'].values() if r['UnitId']==uid),key=lambda r:r['Id'])
    assert len(members)==len(cfg['members'])==7
    # Preserve ammo rows for weapons intentionally kept (RPK and hand grenades).
    existing_ammo=[r.copy() for r in effective['WeaponAmmunitionsJson'].values() if r['UnitId']==uid]
    before={t:{i:dict(r) for i,r in effective[t].items() if r.get('UnitId') not in (None,uid)} for t in ['SquadMembersJson','SquadWeaponsJson','WeaponAmmunitionsJson']}
    for key,c in cfg['weapons'].items():
        donor=effective['WeaponsJson'][c['like']]
        wid=clone('WeaponsJson',c['like'],{'Name':c['name'],'HUDName':c['hud']},why)
        aid=clone('AmmunitionsJson',c['ammo'],{'Name':c['name']+' ammunition','HUDName':c['hud']+' ammo (test)'},why)
        bindings[key]=wid;ammo_ids[key]=aid
        assert effective['WeaponsJson'][wid]['ModelFileName']==donor['ModelFileName']
    def resolve(value):return bindings[value] if isinstance(value,str) else value
    for row,c in zip(members,cfg['members']):put('SquadMembersJson',row['Id'],{'PrimaryWeaponId':resolve(c['primary']),'SpecialWeaponId':resolve(c['special'])},why)
    desired={resolve(c[k]) for c in cfg['members'] for k in ['primary','special'] if c[k]}
    old_squad=[r.copy() for r in effective['SquadWeaponsJson'].values() if r['UnitId']==uid]
    old_wa=[r.copy() for r in effective['WeaponAmmunitionsJson'].values() if r['UnitId']==uid]
    for row in old_squad:discard('SquadWeaponsJson',row['Id'])
    for row in old_wa:discard('WeaponAmmunitionsJson',row['Id'])
    sw_template=next(r['Id'] for r in effective['SquadWeaponsJson'].values())
    wa_template=next(r['Id'] for r in effective['WeaponAmmunitionsJson'].values())
    for order,wid in enumerate(sorted(desired)):
        clone('SquadWeaponsJson',sw_template,{'UnitId':uid,'WeaponId':wid,'Order':order},why)
        key=next((k for k,v in bindings.items() if v==wid),None)
        if key:
            c=cfg['weapons'][key];clone('WeaponAmmunitionsJson',wa_template,{'UnitId':uid,'WeaponId':wid,'AmmunitionId':ammo_ids[key],'Quantity':c['quantity'],'Order':0},why)
        else:
            rows=[r for r in existing_ammo if r['WeaponId']==wid];assert rows,wid
            for row in rows:clone('WeaponAmmunitionsJson',wa_template,{k:v for k,v in row.items() if k!='Id'},why)
    assert desired=={r['WeaponId'] for r in effective['SquadWeaponsJson'].values() if r['UnitId']==uid}
    assert desired=={r['WeaponId'] for r in effective['WeaponAmmunitionsJson'].values() if r['UnitId']==uid}
    for table,rows in before.items():assert rows=={i:r for i,r in effective[table].items() if r.get('UnitId') not in (None,uid)},table
    record={'unit':uid,'status':cfg['status'],'weapons':{k:{'weaponId':v,'ammoId':ammo_ids[k],'donor':cfg['weapons'][k]['like']} for k,v in bindings.items()},'members':[{k:resolve(c[k]) for k in ['primary','special']} for c in cfg['members']]}
    (root/'source/UserData/FreedomArrow/pla-infantry-prototype.json').write_text(json.dumps(record,indent=2)+'\n')
    return record

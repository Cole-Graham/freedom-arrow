"""Generate the narrow dev.1 vehicle overlay on frozen 0.1.1 constants.

Includes dev.1 plus the requested Russian vehicle price/HP/armor batch.
Troopers, squad resizing, option retirement and Booker remain outside this build.
"""
from pathlib import Path
import argparse, copy, hashlib, json, sys
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parents[1]))
from pipeline.crypto import aes_decrypt
from pipeline.tables import FIELD_TO_FILE

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--vanilla-dir',required=True,type=Path)
    args=ap.parse_args()
    base=R.parent/'0.1/source/UserData/FreedomArrow'
    out=R/'source/UserData/FreedomArrow/constants'
    pins=json.loads((base/'compatibility.json').read_text())
    original, effective, patches, frozen = {}, {}, {}, {}
    for table,digest in pins['source_plaintext_sha256'].items():
        raw=aes_decrypt((args.vanilla_dir/(table+'.b64')).read_text())
        assert hashlib.sha256(raw).hexdigest()==digest,table
        original[table]={r['Id']:r for r in json.loads(raw)}
        patches[table]=json.loads((base/'constants'/FIELD_TO_FILE[table]).read_text())
        effective[table]=copy.deepcopy(original[table])
        for key,fields in patches[table].items():
            effective[table].setdefault(int(key),{'Id':int(key)}).update(fields)
        frozen[table]=copy.deepcopy(effective[table])
    next_id=max(i for rows in effective.values() for i in rows if i>=2_000_000)+1
    audit=[]
    def put(table,rid,fields,why):
        before=copy.deepcopy(effective[table].get(rid))
        effective[table].setdefault(rid,{'Id':rid}).update(fields)
        patches[table].setdefault(str(rid),{}).update(fields)
        audit.append(dict(table=table,id=rid,before=before,after=copy.deepcopy(effective[table][rid]),reason=why))
    def clone(table,rid,fields,why):
        nonlocal next_id
        new=next_id;next_id+=1
        row=copy.deepcopy(effective[table][rid]);row.pop('Id');row.update(fields)
        put(table,new,row,why)
        return new
    def options(uid):
        mods={r['Id'] for r in effective['ModificationsJson'].values() if r['UnitId']==uid}
        return [r for r in effective['OptionsJson'].values() if r['ModificationId'] in mods]
    def armor(uid,option,changes,why):
        selected=effective['OptionsJson'][option];old=selected['ArmorId']
        assert option in {r['Id'] for r in options(uid)}
        new=clone('ArmorsJson',old,changes,why)
        hits=0
        for link in list(effective['UnitArmorsJson'].values()):
            if link['UnitId']==uid and link['ArmorId']==old:
                put('UnitArmorsJson',link['Id'],{'ArmorId':new},why);hits+=1
        for opt in options(uid):
            if opt['ArmorId']==old:put('OptionsJson',opt['Id'],{'ArmorId':new},why)
        assert hits>0
    armor(235,551,{'MaxHealthPoints':14},'BMO-T base 12 to14 HP; ERA already14 retained')
    armor(151,2089,{'MaxHealthPoints':10},'Kornet-D1 base14 to10 HP; base protection retained')
    armor(151,2090,{'HeatArmorFront':400,'HeatArmorSides':400},'Kornet-D1 armored10 HP, front/side HEAT400')
    armor(144,1986,{'MaxHealthPoints':10,'HeatArmorFront':400,'HeatArmorSides':400},'Sprut cage10 HP, front/side HEAT400')
    old=effective['OptionsJson'][1986]['MobilityId']
    new=clone('MobilityJson',old,{'MaxSpeedRoad':60.0},'Sprut cage road70 to60 km/h; other mobility retained')
    for link in list(effective['UnitPropulsionsJson'].values()):
        if link['UnitId']==144 and link['MobilityId']==old:
            put('UnitPropulsionsJson',link['Id'],{'MobilityId':new},'Sprut cage mobility association')
    put('OptionsJson',1986,{'MobilityId':new},'Sprut cage selected mobility')
    # Vanilla ability82 already has the two-charge APS desired by the0.1 policy.
    # Reuse it; do not turn on the shared disabled clone used by other vehicles.
    aps=effective['AbilitiesJson'][82]
    assert aps['IsAPS'] and aps['APSQuantity']==2
    opt=effective['OptionsJson'][2082]
    assert opt['Ability2Id']==2000203 and not effective['AbilitiesJson'][2000203]['IsAPS']
    put('OptionsJson',2082,{'Ability2Id':82},'M1283 AMPV BRAT APS retained; two original ready charges')
    put('UnitAbilitiesJson',1029,{'AbilityId':82},'M1283 AMPV APS inventory matches option2082')
    unit_abilities={(r['UnitId'],r['AbilityId']) for r in effective['UnitAbilitiesJson'].values()}
    mods={r['Id']:r['UnitId'] for r in effective['ModificationsJson'].values()}
    for option in effective['OptionsJson'].values():
        for field in ['Ability1Id','Ability2Id','Ability3Id']:
            aid=option[field]
            if not aid or (option['Id']==279 and aid==4):continue
            assert (mods[option['ModificationId']],aid) in unit_abilities,('option ability missing from unit',option['Id'],aid)
    contract=json.loads((R/'vehicle-contract.json').read_text())
    for key,cost in contract['base_costs'].items():
        put('Units',int(key),{'Cost':cost},'Requested base cost; inspect configured surcharges separately')
    for key,cost in contract['option_costs'].items():
        put('OptionsJson',int(key),{'Cost':cost},'Requested surcharge or documented held-split/Reserve fallback')
    for uid,oids in [(1,[504,505]),(425,[1881,1882])]:
        for oid in oids:armor(uid,oid,{'MaxHealthPoints':10},'BTR82A/BTR80 all armor choices10 HP; shared BRDM3 unchanged')
    # B15 is a turret option with no selected armor. Add only its own association.
    old=effective['UnitArmorsJson'][415]['ArmorId']
    assert effective['OptionsJson'][643]['ArmorId']==0
    new=clone('ArmorsJson',old,{'HeatArmorFront':400,'HeatArmorSides':400,'IsDefault':False},'B15 only400/400 HEAT; B10/B11 retain120/100')
    link=next_id;next_id+=1
    put('UnitArmorsJson',link,{'UnitId':254,'ArmorId':new},'B15 new armor association')
    put('OptionsJson',643,{'ArmorId':new},'B15 selected armor without changing B10/B11 default')
    for oid in [3067,3070,3071,3072]:armor(628,oid,{'MaxHealthPoints':8},'Uran9 all four top-slot profiles8 HP; price held')
    for oid in [564,565]:armor(158,oid,{'HeatArmorSides':200},'T80BVM2017/held2018 side HEAT200;2018+ stays400')
    # Existing cloned profiles are immutable. Unit costs are a narrow allow-list.
    for table,rows in frozen.items():
        for rid,row in rows.items():
            if rid>=2_000_000:assert effective[table][rid]==row,(table,rid)
    for uid,row in frozen['Units'].items():
        want=copy.deepcopy(row)
        if str(uid) in contract['base_costs']:want['Cost']=contract['base_costs'][str(uid)]
        assert effective['Units'][uid]==want,('unexpected unit change',uid)
    assert set(effective['Units'])==set(frozen['Units'])
    assert effective['ModificationsJson']==frozen['ModificationsJson']
    assert effective['AmmunitionsJson']==frozen['AmmunitionsJson']
    assert effective['SquadMembersJson']==frozen['SquadMembersJson']
    for table in ['WeaponsJson','SquadWeaponsJson','TurretWeaponsJson','SpecializationAvailabilitiesJson']:
        assert effective[table]==frozen[table]
    # Validate every changed foreign key against the complete effective graph.
    schema=json.loads((R/'source/UserData/FreedomArrow/reference-schema.json').read_text())
    for a in audit:
        for field,(target,nullable) in schema.get(a['table'],{}).items():
            v=a['after'][field]
            assert (v==0 and nullable) or v in effective[target],(a['table'],a['id'],field,v)
    out.mkdir(parents=True,exist_ok=True)
    for table,rows in patches.items():(out/FIELD_TO_FILE[table]).write_text(json.dumps(rows,indent=2)+'\n')
    record={'version':contract['version'],'source_build':pins['source_build_id'],
            'baseline_commit':'72783a51acfd0fac53fc1f40ea881f0f009fe6e0',
            'affected_units':sorted(set([41,144,151,235,254,628]+[int(i) for i in contract['base_costs']])),'new_profile_ids':list(range(2000218,next_id)),
            'baseline_clone_ids_preserved':218,'source_table_pins_matched':24,
            'rows':{k:len(v) for k,v in patches.items()},'changes':audit,
            'scope':'data generation only; no runtime, armory or behavior result'}
    (R/'constant-audit.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:record[k] for k in ['affected_units','new_profile_ids','baseline_clone_ids_preserved','source_table_pins_matched']}))
if __name__=='__main__':main()

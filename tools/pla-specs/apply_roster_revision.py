"""Apply Sam's 12 November roster batch to the exact, immutable PLA30 package.

The package is the input snapshot, so approved body/weapon art and rig alignment
cannot drift through an unrelated regeneration of the historical generator.
"""
import argparse, copy, hashlib, json, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REL = ROOT / 'releases/0.6'
SRC = REL / 'source'
sys.path[:0] = [str(ROOT), str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph

BASE_SHA = '809660cb5ec20c47bc24dff240badf23fa70fcb8f95160805193378ebdc5459a'
NEW = {'J-10A':1226, 'Mi-8 Cargo':1227, 'Lynx ATV':1228,
       'CSK-131 Transport':1229, 'CSK-181 Transport':1230, 'Shaanxi Troop Truck':1231}
REMOVED = [962,1066,1067,1068,1069,1071,1073,1031,1044]
MOVES = {910:[18],1049:[18],915:[17],916:[20],918:[20],929:[20],944:[20],937:[20],
         955:[17,21],971:[17,21],1103:[21],1134:[21],1056:[17],
         1035:[21],1036:[21],963:[21],922:[17],920:[21],934:[17],911:[21],1061:[19]}
enc = lambda d: (json.dumps(d,indent=2)+'\n').encode()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,required=True)
    p.add_argument('--vanilla',type=Path,required=True)
    a=p.parse_args()
    with a.base.open('rb') as f: assert hashlib.file_digest(f,'sha256').hexdigest()==BASE_SHA
    with zipfile.ZipFile(a.base) as z:
        assert json.loads(z.read('UserData/FreedomArrow/pla-package-manifest.json'))['build']==30
        vanilla={tab:{r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())} for tab in FIELD_TO_FILE}
        t=copy.deepcopy(vanilla);patches={}
        for tab,fn in FIELD_TO_FILE.items():
            patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
            for k,v in patches[tab].items():
                if v is None:t[tab].pop(int(k),None)
                else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
        before=copy.deepcopy(t)
        assignments=json.loads(z.read('UserData/FreedomArrow/pla-spec-assignments.json'))
        models=json.loads(z.read('UserData/FAModels/models.json'))
        armament=json.loads(z.read('UserData/FreedomArrow/pla-vehicle-armament.json'))
        special=json.loads(z.read('UserData/FreedomArrow/pla-specializations.json'))
        catalogue=json.loads(z.read('UserData/FreedomArrow/pla-model-catalogue.json'))
        designer=json.loads(z.read('UserData/FreedomArrow/pla-infantry-designer.json'))
        native_ids={k:set(v) for k,v in vanilla.items()};g=Graph(t,patches,native_ids)
        receipt={'build':31,'base_build':30,'base_sha256':BASE_SHA,'native_verified':False,
                 'moves':MOVES,'removed_units':REMOVED,'new_units':NEW,'decisions':[]}
        def save(path,data):
            f=SRC/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(enc(data))
        def rows(tab,uid):return g.rows(tab,uid)
        def unit(uid,fields):return g.put('Units',uid,fields)
        def clone_unit(uid,donor,name,unarmed=False):
            assert uid not in t['Units']
            d=copy.deepcopy(t['Units'][donor]);d.update(Name='PLA '+name,HUDName=name,CountryId=4,DisplayInArmory=True,ContentMembership=-1,IsUnitModification=False)
            unit(uid,d)
            for tab,target,field in [('UnitArmorsJson','ArmorsJson','ArmorId'),('UnitPropulsionsJson','MobilityJson','MobilityId'),('UnitAbilitiesJson','AbilitiesJson','AbilityId'),('SensorUnitsJson','SensorsJson','SensorId')]:
                ls=rows(tab,donor)
                if tab in ['UnitArmorsJson','UnitPropulsionsJson','SensorUnitsJson']:
                    ls=[next((r for r in ls if t[target][r[field]].get('IsDefault')),ls[0])] if ls else []
                else:ls=[r for r in ls if t[target][r[field]].get('IsDefault')]
                for r in ls:g.add(tab,r,{'UnitId':uid,field:g.add(target,t[target][r[field]],{'IsDefault':True})})
            if not unarmed:
                for tab in ['TurretUnitsJson','WeaponAmmunitionsJson']:
                    for r in rows(tab,donor):g.add(tab,r,{'UnitId':uid})
            old=t['Units'][donor]['Name']
            if old in models:models[d['Name']]=copy.deepcopy(models[old])
            return d
        def set_specs(uid,specs):
            pools=rows('SpecializationAvailabilitiesJson',uid)
            template=pools[0] if pools else next(iter(t['SpecializationAvailabilitiesJson'].values()))
            for r in pools:
                for tr in list(t['TransportAvailabilitiesJson'].values()):
                    if tr['SpecializationAvailabilityId']==r['Id']:g.remove('TransportAvailabilitiesJson',tr['Id'])
                g.remove('SpecializationAvailabilitiesJson',r['Id'])
            for sid in specs:g.add('SpecializationAvailabilitiesJson',template,{'UnitId':uid,'SpecializationId':sid})
            assignments['assignments'][str(uid)]=specs
        def remove(uid):
            set_specs(uid,[]);unit(uid,{'DisplayInArmory':False})
            for r in list(t['TransportAvailabilitiesJson'].values()):
                if r['UnitId']==uid:g.remove('TransportAvailabilitiesJson',r['Id'])
            for cs in assignments['carriers'].values():
                if uid in cs:cs.remove(uid)
        def arms(uid):return next(e for e in armament['entries'] if e['unit']==uid)
        def rename(uid,name):unit(uid,{'HUDName':name});arms(uid)['name']=name
        def strip_weapon(uid,wid):
            for ar in rows('WeaponAmmunitionsJson',uid):
                if ar['WeaponId']==wid:g.remove('WeaponAmmunitionsJson',ar['Id'])
            tids={r['TurretId'] for r in rows('TurretUnitsJson',uid)}
            for r in list(t['TurretWeaponsJson'].values()):
                if r['TurretId'] in tids and r['WeaponId']==wid:g.remove('TurretWeaponsJson',r['Id'])
            arms(uid)['weapons']=[w for w in arms(uid)['weapons'] if w['weapon']!=wid]
        def add_weapon(uid,donor,aid,name,count,mag,kind,ammo_fields=None):
            wr=t['WeaponsJson'][donor];w=g.add('WeaponsJson',wr,{'Name':'PLA '+t['Units'][uid]['HUDName']+' '+name,'HUDName':name,'HUDIcon':'FA_PLA_WP_'+kind,'MagazineSize':mag})
            am=g.add('AmmunitionsJson',t['AmmunitionsJson'][aid],{'Name':'PLA '+name,'HUDName':name,'HUDIcon':'FA_PLA_AMMO_'+kind,**(ammo_fields or {})})
            # Use the selected vehicle's turret geometry for additional missile mounts.
            own=rows('TurretUnitsJson',uid)
            source=next((r for r in t['TurretWeaponsJson'].values() if r['TurretId'] in {x['TurretId'] for x in own}),None)
            if source:turret=source['TurretId']
            else:
                source=next(r for r in t['TurretWeaponsJson'].values() if r['WeaponId']==donor)
                turret=g.add('TurretsJson',t['TurretsJson'][source['TurretId']],{'IsDefault':True,'ParentTurretId':None})
                g.add('TurretUnitsJson',next(iter(t['TurretUnitsJson'].values())),{'UnitId':uid,'TurretId':turret,'Order':0})
            g.add('TurretWeaponsJson',source,{'TurretId':turret,'WeaponId':w,'Order':len(arms(uid)['weapons'])})
            ar=next(iter(t['WeaponAmmunitionsJson'].values()));mult=t['AmmunitionsJson'][am]['HUDMultiplier'];assert count%mult==0
            g.add('WeaponAmmunitionsJson',ar,{'UnitId':uid,'WeaponId':w,'AmmunitionId':am,'Quantity':count//mult,'Order':0})
            arms(uid)['weapons'].append({'weapon':w,'name':name,'native_weapon':donor,'native_unit':None,'magazine':mag,'kind':kind,'stocks':[{'ammo':am,'name':name,'requested_rounds':count,'displayed_rounds':count,'logical_quantity':count//mult,'hud_multiplier':mult,'native_ammo':aid}],'basis':'Sam-directed fixed kit; donor performance provisional.','performance':'Native analog; no new match test.'})
        def replace_sam(uid,weapon,ammo,name):
            for old in list(arms(uid)['weapons']):strip_weapon(uid,old['weapon'])
            add_weapon(uid,weapon,ammo,name,4,4,'SAM')
        for uid in REMOVED:remove(uid)
        for uid,specs in MOVES.items():set_specs(uid,specs)
        # Three explicit long-range SAM cards. B retains GEM+ range with active
        # radar homing; A keeps native GEM+ semi-active guidance; C uses 40N6.
        for uid,name,sid,donor,ammo,cost in [(1233,'HQ-9B',20,236,154,230),(1234,'HQ-9A',19,236,154,200)]:
            clone_unit(uid,911,name,True);NEW[name]=uid;set_specs(uid,[sid]);unit(uid,{'Cost':cost})
            armament['entries'].append({'unit':uid,'name':name,'type':4,'native_parent':163,'weapons':[],'slots':0,'custom_model':models.get(t['Units'][uid]['Name']),'native_verified':False})
            add_weapon(uid,donor,ammo,name+' missile',4,4,'SAM',{'Seeker':50} if name=='HQ-9B' else None)
        rename(911,'HQ-9C');replace_sam(911,319,220,'HQ-9C missile');unit(911,{'Cost':t['Units'][227]['Cost']})
        for key in ['ModelFileName','PortraitFileName','ThumbnailFileName','Length','Width','Height','Weight','WaterDiveOffset']:unit(911,{key:t['Units'][227][key]})
        for tab,target,field in [('UnitArmorsJson','ArmorsJson','ArmorId'),('UnitPropulsionsJson','MobilityJson','MobilityId'),('SensorUnitsJson','SensorsJson','SensorId'),('UnitAbilitiesJson','AbilitiesJson','AbilityId')]:
            ls=rows(tab,227);g.clear_unit(911,[tab])
            if tab!='UnitAbilitiesJson':ls=[next((r for r in ls if t[target][r[field]].get('IsDefault')),ls[0])] if ls else []
            else:ls=[r for r in ls if t[target][r[field]].get('IsDefault')]
            for link in ls:g.add(tab,link,{'UnitId':911,field:g.add(target,t[target][link[field]],{'IsDefault':True})})
        # The YJ-18 ground card is explicitly the native Iskander-K cruise analog.
        yw=arms(1129)['weapons'][0]['weapon'];ya=arms(1129)['weapons'][0]['stocks'][0]['ammo']
        wr=copy.deepcopy(t['WeaponsJson'][317]);wr.pop('Id');wr.update(Name='PLA YJ-18 Iskander-K analog',HUDName='YJ-18');g.put('WeaponsJson',yw,wr)
        am=copy.deepcopy(t['AmmunitionsJson'][219]);am.pop('Id');am.update(Name='PLA YJ-18 cruise missile',HUDName='YJ-18');g.put('AmmunitionsJson',ya,am)
        # Standard planes are added to Motorized without removing existing sharing.
        for uid in [917,955,971]:
            specs=assignments['assignments'][str(uid)]
            if 21 not in specs:set_specs(uid,specs+[21])
        clone_unit(1226,917,'J-10A')
        # Isolated model aliases reuse the exact C mesh/UVs/textures; only the
        # blue-grey airframe material gets a warmer/lighter neutral-grey factor.
        for source,alias in [('m_j10c_cg','m_j10a_grey'),('m_j10c_lo2','m_j10a_grey_lo')]:
            f=SRC/'UserData/FAModels'/ (alias+'.fam');f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(z.read('UserData/FAModels/'+source+'.fam'))
            mat=json.loads(z.read('UserData/FAModels/'+source+'.mat.json'))
            for key,value in mat.items():
                if '_tex1.png|' in key and not value.get('cockpitDonor'):value['colorScale']=[2.0,1.5,1.3]
            save(Path('UserData/FAModels')/(alias+'.mat.json'),mat)
        models[t['Units'][1226]['Name']]={'file':'m_j10a_grey.fam','battle':'m_j10a_grey_lo.fam','align':False}
        set_specs(1226,[21]);unit(1226,{'Cost':125,'Description':'J-10A game variant; J-10C geometry stand-in, pale neutral grey finish. Loadout is a provisional gameplay approximation.'})
        plane=copy.deepcopy(arms(917));plane.update(unit=1226,name='J-10A',native_parent=917);armament['entries'].append(plane)
        # Basic Russian cargo helicopter, shared across all five playable specs.
        clone_unit(1227,7,'Mi-8 Cargo',True);unit(1227,{'Cost':70,'CategoryType':4,'Role':71,'Description':'Basic unarmed Mi-8 cargo / infantry transport. Russian native model; shared PLA utility lift.'})
        set_specs(1227,[17,18,19,20,21])
        for uid,donor,name,specs,cost in [(1228,82,'Lynx ATV',[17],20),(1229,900,'CSK-131 Transport',[17],30),(1230,1058,'CSK-181 Transport',[17],35),(1231,912,'Shaanxi Troop Truck',[17],20)]:
            clone_unit(uid,donor,name,True);unit(uid,{'Cost':cost,'CategoryType':2,'Role':12,'Description':'Basic Airborne infantry transport; native or family visual stand-in. No automatic recon or resupply role.'})
            if uid==1231:
                for link in rows('UnitAbilitiesJson',uid):
                    ab=t['AbilitiesJson'][link['AbilityId']]
                    g.put('AbilitiesJson',ab['Id'],{'IsResupplyAbility':False,'CanResupply':False,'CanHeal':False,'CanRepair':False,'ResupplyPoints':0})
            set_specs(uid,specs)
        assert t['Units'][1228]['InfantrySlots']==9
        # ZSL-92 variants replace the redundant WZ-551 card, no ATGMs.
        clone_unit(1232,1079,'ZSL-92 MG',True);NEW['ZSL-92 MG']=1232
        unit(1232,{'Cost':25,'InfantrySlots':8});set_specs(1232,[18,19,20,21])
        armament['entries'].append({'unit':1232,'name':'ZSL-92 MG','type':4,'native_parent':1079,'weapons':[],'slots':8,'custom_model':models.get(t['Units'][1232]['Name']),'native_verified':False})
        add_weapon(1232,97,70,'QJC-88 12.7 mm',500,30,'MG')
        rename(1079,'ZSL-92 Autocannon');set_specs(1079,[18,19,20,21])
        for w in list(arms(1079)['weapons']):
            if w['kind']=='ATGM':strip_weapon(1079,w['weapon'])
        # Cheap legacy gun: four AP shots, remaining stock conventional HE; no high-pen HEAT shortcut.
        unit(1059,{'Cost':40})
        for ar in rows('WeaponAmmunitionsJson',1059):
            am=t['AmmunitionsJson'][ar['AmmunitionId']]
            if ar['WeaponId']!=2010789:continue
            if am['ArmorTargeted']==1:g.put('AmmunitionsJson',am['Id'],{'PenetrationAtGroundRange':200.0,'PenetrationAtMinRange':225.0});g.put('WeaponAmmunitionsJson',ar['Id'],{'Quantity':4})
            elif 'HEAT' in am['HUDName']:g.remove('WeaponAmmunitionsJson',ar['Id'])
            else:g.put('WeaponAmmunitionsJson',ar['Id'],{'Quantity':26})
        # User's +25 close-range rule applies only to these newly specified KE profiles.
        for uid,aid,longpen,cost in [(906,2009131,475,95),(1080,2011301,550,115)]:
            g.put('AmmunitionsJson',aid,{'HUDName':'105 mm DU APFSDS','PenetrationAtGroundRange':float(longpen),'PenetrationAtMinRange':float(longpen+25)})
            unit(uid,{'Cost':cost});g.put('WeaponsJson',arms(uid)['weapons'][0]['weapon'],{'HUDName':'105 mm high-pressure rifled gun'})
        ztlw=arms(1080)['weapons'][0]['weapon'];ztqw=copy.deepcopy(t['WeaponsJson'][arms(906)['weapons'][0]['weapon']]);ztqw.pop('Id');ztqw['Name']='PLA ZTL-191 105 mm high-pressure rifled gun';g.put('WeaponsJson',ztlw,ztqw)
        # Same basic/advanced native TOR performance, with eight rounds on both Chinese cards.
        for uid,donor,aid,label,cost in [(910,28,28,'HQ-17',150),(1049,99,77,'HQ-17A',200)]:
            oldw=arms(uid)['weapons'][0]['weapon'];olda=arms(uid)['weapons'][0]['stocks'][0]['ammo']
            wr=copy.deepcopy(t['WeaponsJson'][donor]);wr.pop('Id');wr.update(Name='PLA '+label,HUDName=label,MagazineSize=8)
            g.put('WeaponsJson',oldw,wr);ar=copy.deepcopy(t['AmmunitionsJson'][aid]);ar.pop('Id');ar.update(Name='PLA '+label+' missile',HUDName=label+' missile');g.put('AmmunitionsJson',olda,ar)
            for link in rows('WeaponAmmunitionsJson',uid):g.put('WeaponAmmunitionsJson',link['Id'],{'Quantity':8})
            unit(uid,{'Cost':cost});arms(uid)['weapons'][0].update(native_weapon=donor,magazine=8)
        # Recon drone: retain its flying chassis, remove missiles and use native recon optics.
        rename(1085,'CR-500 Recon');unit(1085,{'CategoryType':0,'Role':70,'Stealth':t['Units'][107]['Stealth'],'CurrentStealth':t['Units'][107]['CurrentStealth']})
        for w in list(arms(1085)['weapons']):strip_weapon(1085,w['weapon'])
        g.clear_unit(1085,['SensorUnitsJson'])
        for link in rows('SensorUnitsJson',107):
            se=t['SensorsJson'][link['SensorId']]
            if se.get('IsDefault'):g.add('SensorUnitsJson',link,{'UnitId':1085,'SensorId':g.add('SensorsJson',se,{'IsDefault':True})})
        # ZBD-251 remains an explicit native visual stand-in until the linked asset is received.
        for w in list(arms(1056)['weapons']):
            if w['kind']=='ATGM':strip_weapon(1056,w['weapon'])
        add_weapon(1056,616,2009623,'HJ-10',2,2,'ATGM')
        add_weapon(1056,175,578,'ABZ-13 anti-personnel',4,4,'ATGM')
        laser=g.add('AbilitiesJson',t['AbilitiesJson'][10],{'IsDefault':True,'Name':'PLA ZBD-251 laser designator'})
        g.add('UnitAbilitiesJson',next(iter(t['UnitAbilitiesJson'].values())),{'UnitId':1056,'AbilityId':laser})
        unit(1056,{'Cost':95,'Description':'Airborne ZBD-251: laser designator, two HJ-10 and four ABZ-13 anti-personnel missiles. Native IFV visual until the linked Shijiu asset is available. Missile performance is a provisional game analogy.'})
        for pool in rows('SpecializationAvailabilitiesJson',1032):
            g.put('SpecializationAvailabilitiesJson',pool['Id'],{'MaxAvailabilityXp0':1,'MaxAvailabilityXp1':0,'MaxAvailabilityXp2':0,'MaxAvailabilityXp3':0})
        unit(1032,{'HUDName':'DF-31A Nuclear','Description':'Nuclear missile design; one availability. Existing conventional explosion retained pending Sam\'s nuclear effect selection.'})
        # Transport lists are built from actual per-spec capacity, not just armory labels.
        for sid in range(17,22):
            cs=assignments['carriers'][str(sid)]
            if 1227 not in cs:cs.append(1227)
            if 1079 not in cs and sid in [18,19,20,21]:cs.append(1079)
            if 1232 not in cs and sid in [18,19,20,21]:cs.append(1232)
        for uid in [1056,1228,1229,1230,1231]:
            if uid not in assignments['carriers']['17']:assignments['carriers']['17'].append(uid)
        for uid,parent in [(1227,7),(1228,82),(1229,900),(1230,1058),(1231,912)]:
            armament['entries'].append({'unit':uid,'name':t['Units'][uid]['HUDName'],'type':t['Units'][uid]['Type'],'native_parent':parent,'weapons':[],'slots':t['Units'][uid]['InfantrySlots'],'custom_model':models.get(t['Units'][uid]['Name']),'native_verified':False})
        for pool in list(t['SpecializationAvailabilitiesJson'].values()):
            uid,sid=pool['UnitId'],pool['SpecializationId']
            if sid not in range(17,22) or t['Units'][uid]['Type']!=2:continue
            count=sum(r['UnitId']==uid for r in t['SquadMembersJson'].values())
            present={r['UnitId'] for r in t['TransportAvailabilitiesJson'].values() if r['SpecializationAvailabilityId']==pool['Id']}
            for carrier in assignments['carriers'][str(sid)]:
                if carrier not in present and t['Units'][carrier]['InfantrySlots']>=count:g.add('TransportAvailabilitiesJson',next(iter(t['TransportAvailabilitiesJson'].values())),{'SpecializationAvailabilityId':pool['Id'],'UnitId':carrier})
        # Refresh receipts from effective links, so ammo numbers cannot contradict the payload.
        for e in armament['entries']:
            uid=e['unit'];e['name']=t['Units'][uid]['HUDName'];e['specs']=assignments['assignments'].get(str(uid),[]);e['active']=t['Units'][uid]['DisplayInArmory']
            for w in e['weapons']:
                w['name']=t['WeaponsJson'][w['weapon']]['HUDName'];w['magazine']=t['WeaponsJson'][w['weapon']]['MagazineSize']
                oldstock={s['ammo']:s for s in w['stocks']};w['stocks']=[]
                for ar in rows('WeaponAmmunitionsJson',uid):
                    if ar['WeaponId']!=w['weapon']:continue
                    am=t['AmmunitionsJson'][ar['AmmunitionId']];st=copy.deepcopy(oldstock.get(am['Id'],{}));st.update(ammo=am['Id'],name=am['HUDName'],requested_rounds=ar['Quantity']*am['HUDMultiplier'],displayed_rounds=ar['Quantity']*am['HUDMultiplier'],logical_quantity=ar['Quantity'],hud_multiplier=am['HUDMultiplier']);w['stocks'].append(st)
            e['custom_model']=models.get(t['Units'][uid]['Name'])
        assignments['build']=31;assignments['pool_counts']={str(s):sum(r['SpecializationId']==s for r in t['SpecializationAvailabilitiesJson'].values()) for s in range(17,23)}
        for d in [armament,special,designer]:d['build']=31
        armament['count']=len(armament['entries'])
        special['roster_revision']='Sam 12 November: see pla-roster-revision.json'
        for e in catalogue['entries']:
            if e.get('unit') in t['Units']:e['specs']=assignments['assignments'].get(str(e['unit']),[])
        for tab,fn in FIELD_TO_FILE.items():save(Path('UserData/FreedomArrow/constants')/fn,patches[tab])
        for name,d in [('pla-spec-assignments',assignments),('pla-vehicle-armament',armament),('pla-specializations',special),('pla-model-catalogue',catalogue),('pla-infantry-designer',designer)]:save(Path('UserData/FreedomArrow')/(name+'.json'),d)
        save(Path('UserData/FAModels/models.json'),models)
        receipt.update(new_units=NEW,drone_model_audit={str(uid):{'name':t['Units'][uid]['HUDName'],'custom_model':models.get(t['Units'][uid]['Name']),'native_model':t['Units'][uid]['ModelFileName']} for uid in [1084,1085,1086,1105]},pen_targets={'PTL-02':[200,225,4],'ZTQ-15':[475,500,18],'ZTL-191':[550,575,18]},nuclear_effect='pending; conventional explosion retained',nuclear_warning={'ammo':2010399,'path':'existing ActualArrow ballistic poll before team ownership filter','audio':'original synthesized replaceable draft','controls':'existing ballistic warning enable, sound mute and volume; same game bus','runtime_verified':False},checks=verify(t,before,assignments))
        save(Path('UserData/FreedomArrow/pla-roster-revision.json'),receipt)
        (ROOT/'tools/pla-specs/build31-roster-checks.json').write_bytes(enc(receipt))
        print(json.dumps(receipt,indent=2))

def verify(t,before,assignments):
    checks=0
    def check(v,msg):
        nonlocal checks
        assert v,msg;checks+=1
    for uid in REMOVED:
        check(not t['Units'][uid]['DisplayInArmory'],('removed visible',uid))
        check(not any(r['UnitId']==uid for r in t['SpecializationAvailabilitiesJson'].values()),('removed pool',uid))
        check(not any(r['UnitId']==uid for r in t['TransportAvailabilitiesJson'].values()),('removed carrier',uid))
    for uid,want in MOVES.items():check(sorted(r['SpecializationId'] for r in t['SpecializationAvailabilitiesJson'].values() if r['UnitId']==uid)==want,('wrong specs',uid))
    for link in t['TransportAvailabilitiesJson'].values():
        pool=t['SpecializationAvailabilitiesJson'][link['SpecializationAvailabilityId']];unit=t['Units'][pool['UnitId']]
        if unit['CountryId']!=4 or pool['SpecializationId'] not in range(17,22):continue
        count=sum(r['UnitId']==unit['Id'] for r in t['SquadMembersJson'].values())
        check(t['Units'][link['UnitId']]['InfantrySlots']>=count,('capacity',unit['Id'],link['UnitId']))
    for uid,u in before['Units'].items():
        if u['CountryId']!=4:check(t['Units'][uid]==u,('non-PLA changed',uid))
        if u['Type']==2:check(t['Units'][uid]==u,('infantry changed',uid))
    check(t['Units'][1228]['InfantrySlots']==9,'Lynx capacity')
    for tab in ['SquadMembersJson','SquadWeaponsJson']:check(t[tab]==before[tab],('infantry table changed',tab))
    check(t['AmmunitionsJson'][2009131]['PenetrationAtMinRange']==500,'ZTQ close pen')
    check(t['AmmunitionsJson'][2011301]['PenetrationAtGroundRange']==550,'ZTL long pen')
    return {'passed':checks,'native_verified':False,'infantry_body_weapon_alignment_preserved':True,'non_pla_units_preserved':True}

if __name__=='__main__':main()

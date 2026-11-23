"""Freedom Arrow 0.8.0-dev.103 over exact 0.8.0-dev.102 (Osama 14 Nov 03:2x-04:0x PST, thread 1571014792016171120).
- ZTQ-15 Light: new PLAAF (airborne) card, a copy of the ZTQ-15 (with its dev.102 LG3 AGL) with front armour 100 KE / 300 HEAT
  (was 300 / 500). Same price and card count as the ZTQ-15 (not specified). The PLAGF Armored card stays "ZTQ-15".
- ZTZ-96B: 170 pts (was 125); HEAT front 1000 (was 750), HEAT sides 700 (was 200). ZTZ-99: KE front 700 (was 750).
- PLAAF Recon (1149) 25 pts (was 65). Motorized Recon Patrol (1201) 50 pts (was 60).
- HJ-8 vehicle (951): PLARF card removed (it had no other card).
- AR-2000 (1084) to PLAN SOF and Z-6B UAV (1105) to PLAAF: the hidden catalogue units get a card (2, the vanilla MDP-01 Termit
  count) and Osama's seller models (OBJ parts for the pieces whose FBX rotation was lost, as for the Y-8).
- ZTL-191 (vehicle card): green woodland model again; ZTL-191 Recon keeps the desert model (dev.99 had put both on desert).
- Abrams X: the silver finish Osama approved on 10 Nov (silver colour maps + brighter metallic grey masks) is now in the package.
  It was only ever installed locally on his PC, so each 0.8 install put the olive seller texture back.
- Infantry plates: the 901 'Elite 4 pouches' worn by most SF bodies is a chest rig with no plates (Osama). The SF bodies that only
  have it (carrier, assault, grenadier, night up/down, goggles up/down) and the light body (soft vest) get the Condor plate carrier
  from the Condor SF body (same body mesh). Regular bodies already wear the Type 21 plate vest; the heavy (EOD) body is unchanged.
- ZBD-20: APS is now an armory choice (Osama): "No APS" (default, the 175 price with HJ-16 semi-active) or "Iron Fist APS" (+40).
  Same pattern as the vanilla M3A3 (an ability modification whose options repeat the default smoke ability). Side armour KE 150
  (was 120) and HEAT 700 (was 200). Ammunition doubled on every ZBD-20 weapon (Osama: "twice as much ammo").
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.103';PREV='0.8.0-dev.102'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True)
p.add_argument('--drones',type=Path,required=True);p.add_argument('--abramsx',type=Path,required=True);p.add_argument('--infantry',type=Path,required=True);a=p.parse_args()
base=REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];SA=t['SpecializationAvailabilitiesJson'];UAR=t['UnitArmorsJson'];AR=t['ArmorsJson'];rows=g.rows
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
def hud(u,h):ok(U[u]['HUDName']==h,(u,h,U[u]['HUDName']))
def specs(u):return [r['SpecializationId'] for r in rows('SpecializationAvailabilitiesJson',u)]
def armor(u):r=rows('UnitArmorsJson',u);ok(len(r)==1 and sum(1 for x in UAR.values() if x['ArmorId']==r[0]['ArmorId'])==1,(u,'own armour'));return r[0]['ArmorId']
def clone_unit(parent,fields):
    uid=max(U)+1;d=copy.deepcopy(U[parent]);d.pop('Id');d.update(fields);g.put('Units',uid,d);defs={}
    for table,field,target in [('UnitArmorsJson','ArmorId','ArmorsJson'),('UnitPropulsionsJson','MobilityId','MobilityJson'),('UnitAbilitiesJson','AbilityId','AbilitiesJson')]:
        for r in rows(table,parent):
            if (target,r[field]) not in defs:defs[target,r[field]]=g.add(target,t[target][r[field]])
            g.add(table,r,{'UnitId':uid,field:defs[target,r[field]]})
    for table in ['TurretUnitsJson','WeaponAmmunitionsJson','SensorUnitsJson']:
        for r in rows(table,parent):g.add(table,r,{'UnitId':uid})
    ok(not rows('ModificationsJson',parent),'no armory options');return uid
MJ='UserData/FAModels/models.json';raw=z.read(MJ);models=json.loads(raw);mbefore={}
# ---------- ZTQ-15 Light (PLAAF airborne) ----------
hud(906,'ZTQ-15');ok(specs(906)==[18] and assign['assignments'].get('906')==[18],'ZTQ-15 PLAGF Armored only')
NEW='PLA ZTQ-15 Light';ok(not any(u.get('Name')==NEW for u in U.values()),'name free')
lt=clone_unit(906,{'Name':NEW,'HUDName':'ZTQ-15 Light'})
src=rows('SpecializationAvailabilitiesJson',906);g.add('SpecializationAvailabilitiesJson',src[0],{'UnitId':lt,'SpecializationId':17});assign['assignments'][str(lt)]=[17]
la=armor(lt);ok((AR[la]['KinArmorFront'],AR[la]['HeatArmorFront'])==(300,500),'ZTQ-15 front');g.put('ArmorsJson',la,{'KinArmorFront':100,'HeatArmorFront':300,'Name':'PLA ZTQ-15 Light ArmorsJson'})
ok(specs(lt)==[17] and U[lt]['Cost']==150 and sorted(r['TurretId'] for r in rows('TurretUnitsJson',lt))==sorted(r['TurretId'] for r in rows('TurretUnitsJson',906)),'Light card')
mbefore[NEW]=None;models[NEW]=dict(models['PLA ZTQ-15'])
rec['ztq15_light']={'unit':lt,'spec':17,'cost':U[lt]['Cost'],'cards':src[0]['MaxAvailabilityXp0'],'armour_front':{'KE':[300,100],'HEAT':[500,300]}}
# ---------- ZTZ-96B / ZTZ-99 ----------
hud(905,'ZTZ-96B');ok(U[905]['Cost']==125,'96B cost');g.put('Units',905,{'Cost':170});b=armor(905)
ok((AR[b]['HeatArmorFront'],AR[b]['HeatArmorSides'])==(750,200),'96B HEAT');g.put('ArmorsJson',b,{'HeatArmorFront':1000,'HeatArmorSides':700})
hud(1083,'ZTZ-99');c=armor(1083);ok(AR[c]['KinArmorFront']==750,'99 KE');g.put('ArmorsJson',c,{'KinArmorFront':700})
rec['ztz96b']={'cost':[125,170],'HEAT_front':[750,1000],'HEAT_sides':[200,700]};rec['ztz99']={'KE_front':[750,700]}
# ---------- points ----------
hud(1149,'Recon 侦察组');ok(specs(1149)==[17] and U[1149]['Cost']==65,'PLAAF Recon');g.put('Units',1149,{'Cost':25})
hud(1201,'Recon Patrol 侦察班');ok(U[1201]['Cost']==60,'Recon Patrol');g.put('Units',1201,{'Cost':50})
rec['points']={'PLAAF Recon 1149':[65,25],'Recon Patrol 1201':[60,50]}
# ---------- HJ-8 vehicle out of PLARF ----------
hud(951,'HJ-8');r=rows('SpecializationAvailabilitiesJson',951);ok([x['SpecializationId'] for x in r]==[19] and not [x for x in t['TransportAvailabilitiesJson'].values() if x['UnitId']==951],'HJ-8 PLARF card only')
for x in r:g.remove('SpecializationAvailabilitiesJson',x['Id'])
assign['assignments'].pop('951',None);rec['hj8_removed']={'unit':951,'spec':19}
# ---------- AR-2000 / Z-6B UAV ----------
term=rows('SpecializationAvailabilitiesJson',632);ok(len(term)==1 and term[0]['MaxAvailabilityXp0']==2,'Termit card')
for u,h,spec,key,slug in ((1084,'AR-2000',20,'PLA Catalogue AR-2000','m_ar2000'),(1105,'Z-6B UAV',17,'PLA Catalogue Z-6B UAV','m_z6b')):
    hud(u,h);ok(U[u]['Name']==key and U[u].get('DisplayInArmory') is False and not specs(u) and U[u]['ModelFileName']=='DLC3_MDP01_Termit','hidden catalogue '+h)
    g.put('Units',u,{'DisplayInArmory':True});g.add('SpecializationAvailabilitiesJson',term[0],{'UnitId':u,'SpecializationId':spec});assign['assignments'][str(u)]=[spec]
    ok(key not in models,(key,'no model yet'));mbefore[key]=None;models[key]={'file':slug+'_static.fam','battle':slug+'_lo_static.fam','align':False}
    rec.setdefault('drones',{})[h]={'unit':u,'spec':spec,'cards':2,'cost':U[u]['Cost'],'weapons':'as catalogue (UAV guided missile x2)','model':slug}
# ---------- ZTL-191 vehicle green ----------
k='PLA Catalogue ZTL-191';ok(models[k]['file']=='m_ztl191d_static.fam' and models['PLA ZTL-191 Recon']['file']=='m_ztl191d_static.fam','ZTL-191 both desert')
ok('UserData/FAModels/m_ztl191_static.fam' in z.namelist() and 'UserData/FAModels/m_ztl191_lo_static.fam' in z.namelist(),'woodland files')
mbefore[k]=dict(models[k]);models[k]={**models[k],'file':'m_ztl191_static.fam','battle':'m_ztl191_lo_static.fam'}
rec['models_json']={k:{'before':mbefore[k],'after':models[k]} for k in mbefore}
# ---------- ZBD-20 APS option, side armour ----------
VO={r['Id']:r for r in json.loads((a.vanilla/'OptionsJson.json').read_text())};VM={r['Id']:r for r in json.loads((a.vanilla/'ModificationsJson.json').read_text())}
hud(945,'ZBD-20');AB=t['AbilitiesJson'];O=t['OptionsJson'];M=t['ModificationsJson']
ua={r['AbilityId']:r for r in rows('UnitAbilitiesJson',945)};ok(sorted(ua)==[8,82,2009811] and AB[2009811]['IsDefault'] and not AB[82]['IsDefault'] and AB[82]['IsAPS'],'ZBD-20 abilities')
ok(not any(o.get(f'Ability{i}Id')==82 for o in O.values() if M.get(o['ModificationId'],{}).get('UnitId')==945 for i in (1,2,3)),'APS not selectable yet')
ok([m['Type'] for m in rows('ModificationsJson',945)]==[3],'only the HJ-16 package')
m3=[m for m in VM.values() if m['Name']=='Ability M3A3'];ok(len(m3)==1 and m3[0]['Type']==6,'vanilla M3A3 ability slot')
vo=sorted((o for o in VO.values() if o['ModificationId']==m3[0]['Id']),key=lambda o:o['Order']);ok([o['UIName'] for o in vo]==['Custom_Option_None','Custom_Option_IronFist_APS'],[o['UIName'] for o in vo])
mid=g.add('ModificationsJson',m3[0],{'UnitId':945,'Name':'PLA ZBD-20 APS','Order':1});NT={f'Turret{i}Id':0 for i in range(21)}   # the M3A3 options also swap its turret model
none=g.add('OptionsJson',vo[0],{**NT,'ModificationId':mid,'Name':'PLA ZBD-20 No APS','IsDefault':True,'Cost':0,'Ability1Id':2009811,'Ability2Id':4,'Ability3Id':0})
aps=g.add('OptionsJson',vo[1],{**NT,'ModificationId':mid,'Name':'PLA ZBD-20 Iron Fist APS','IsDefault':False,'Cost':40,'Ability1Id':2009811,'Ability2Id':82,'Ability3Id':0})
g.add('UnitAbilitiesJson',ua[82],{'AbilityId':4});ok(not AB[4]['IsDefault'],'empty ability non-default')
za=armor(945);ok((AR[za]['KinArmorSides'],AR[za]['HeatArmorSides'])==(120,200),'ZBD-20 sides');g.put('ArmorsJson',za,{'KinArmorSides':150,'HeatArmorSides':700})
ok(U[945]['Cost']==175,'ZBD-20 175')
WA=t['WeaponAmmunitionsJson'];W=t['WeaponsJson'];dbl={}
for x in rows('WeaponAmmunitionsJson',945):dbl[f"{W[x['WeaponId']]['HUDName']} ({x['Id']})"]=[x['Quantity'],x['Quantity']*2];g.put('WeaponAmmunitionsJson',x['Id'],{'Quantity':x['Quantity']*2})
ok(sorted(v[0] for v in dbl.values())==[8,8,50,117,400],dbl)
ok(all(not O[x].get(f'Turret{i}Id') for x in (none,aps) for i in range(21)),'no turret swap');rec['zbd20']={'modification':mid,'options':{'No APS':[none,0],'Iron Fist APS':[aps,40]},'aps_ability':82,'side_armour':{'KE':[120,150],'HEAT':[200,700]},'ammo':dbl}
# ---------- files ----------
files={}
for f in sorted(a.drones.iterdir()):
    if f.suffix in ('.fam','.json','.png') and f.name.split('_static')[0].replace('_lo','') in ('m_ar2000','m_z6b'):files['UserData/FAModels/'+f.name]=str(f)
ok(len([k for k in files if k.endswith('.fam')])==4 and not any(k in z.namelist() for k in files),'drone files new')
for k in [k for k in files if k.endswith('.mat.json')]:
    for key,v in json.loads(Path(files[k]).read_text()).items():
        tex=key.split('|')[0];ok(v['alpha']!='BLEND',('no blend',k))
        if tex:ok('UserData/FAModels/'+tex in files,('texture',tex))
AX={'m_abramsx_cg_tex0.png':'d3e9c83da6655341e1570e3a64761fbf502a007a4b0ed8fcf3698761adf42dbd','m_abramsx_lo_tex0.png':'33f7ebcd5a577590cf707b8dad5b9f4aaa28ca9cb2a7d35ce340ebc172b49a93',
    'm_abramsx_cg_tex0_mask.png':'c3d0499ba2dc91eed915babb4d30c56ef4224556c591a4a9b63d9cf106a9d00a','m_abramsx_lo_tex0_mask.png':'b18e7ca0075c5773a0fa9322fc5496cd15dc912c449166b12c25e66f9f61d926'}
for n,h in AX.items():
    f=a.abramsx/n;ok(hashlib.sha256(f.read_bytes()).hexdigest()==h,('approved',n));k='UserData/FAModels/'+n;ok(k in z.namelist() and hashlib.sha256(z.read(k)).hexdigest()!=h,('replaces',n));files[k]=str(f)
rec['abramsx']={'approved':'Osama 10 Nov (Blender preview, "looks great"); work/abramsx-brighter-grey-20261110','files':AX}
inf={'changed':[],'new':[]}
for f in sorted(a.infantry.iterdir()):
    if not f.name.startswith('pla2_'):continue
    k='UserData/FAModels/'+f.name;d=f.read_bytes()
    if k in z.namelist():
        if hashlib.sha256(z.read(k)).hexdigest()!=hashlib.sha256(d).hexdigest():inf['changed'].append(f.name);files[k]=str(f)
    else:inf['new'].append(f.name);files[k]=str(f)
want={f'pla2_sf_{b}_{c}_{l}.fas' for b in ('carrier','assault','grenadier','night_up','night_down','goggles_up','goggles_down','light') for c in ('woodland','desert') for l in (0,1,2)}
ok(set(inf['changed'])==want,('changed bodies',inf['changed']))
ok(set(inf['new'])=={f'pla2_gear_plates_{c}_{l}{s}' for c in ('woodland','desert') for l in (0,1,2) for s in ('.png','_n.png')},('new plates textures',inf['new']))
rec['infantry_plates']=inf
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=raw.isascii())+'\n').encode())
(ROOT/f'tools/pla-specs/{V}-assets.txt').write_text(''.join(f'{k}={v}\n' for k,v in sorted(files.items())))
rec.update(version=V,base=PREV,base_sha256=BASE,request='Osama 14 Nov 03:2x-04:0x PST',checks=checks,verified='data and file checks; models rendered offline',
  assumptions={'ZTQ-15 Light':'price 150 and 6 cards copied from ZTQ-15','AR-2000/Z-6B':'2 cards (Termit), catalogue stats and price kept'},
  not_done={'WZ-550 textures':'the zip on Osama PC is byte-identical to the one used before (sha256 d7ebc71f...)'})
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,'files',len(files))

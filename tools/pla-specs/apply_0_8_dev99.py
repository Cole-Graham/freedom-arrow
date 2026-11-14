"""Freedom Arrow 0.8.0-dev.99 over exact 0.8.0-dev.98 (Osama 14 Nov 00:0x-00:2x PST, thread 1571014792016171120).
- Availability (cards): DF-17 1, YJ-18 2, Conscripts / HJ-73D Team / Infantry (Missile-Site Security) / Mech. Rifles 8,
  ZTZ-99A 2, ZTZ-99 4, J-5 / J-6W / J-7 / J-8D 4. PLAN SOF: SF infantry (Godswords, PAP Snow Leopards, Blood Wolves, Falcons,
  Sea Dragons) 2, SF recon (Whistling Arrows, Mountain Leopards, Beijing Swords) 3; Marines unchanged.
- Prices: Forward Observers 25, ZTQ-15 150, ZTQ-15 Recon 165, PLZ-70 95, PLZ-85 90, MD-22 base +100 (280).
- Sharp Blades renamed Sharp Swords (利剑).
- PLZ-85: dispersion 300 m x 240 m, read as radii in metres (world = m / 2): vertical (along range) 120 -> 150,
  horizontal 90 -> 120. PLZ-89: max range 4300 m (GroundRange 1850 -> 2150 world).
- Mortars: PLL-05 and PLL-09 (120 mm gun-mortars) and PLZ-70 get 20 smoke rounds (copies of the vanilla 2A51 120 mm smoke /
  2A64 152 mm smoke rows, with that unit's own trajectory, range and supply cost).
- Transports: in vanilla a unit that is a transport never has its own card (0 of 54), so it shows only under the infantry it
  carries. PLA ground transports with their own card (vehicle tab) lose that card; their transport links stay. ZBD-20 becomes
  a transport for the same infantry as ZBD-04A. Helicopters keep their cards.
- CSK-131 Mengshi (900) removed. CSK-131 (4x4, 1266) no longer a transport in PLAAF; CSK-181 (1230) not in PLAN SOF.
  ZSD-89 (PLAN copy, 1246) removed: ZSD-89 is Rocket Force only.
- Recon helicopters with loadouts (Z-9WA Recon, Z-19 Recon x2, Z-21 Recon): new "Empty" loadout, 0 pts (vanilla Empty pylon).
- Osama 00:3x: PTL-02 50, VT-5 240, ZSD-89A no longer a Motorized transport, Line Infantry renamed Moto. Riflemen and with
  Light Riflemen 6 cards, Marines 6 cards. Recon tanks 2 cards: ZTQ-15 Recon, VT-5 Recon, ZTL-191 Recon (not ZTZ-59D1).
- FK-2000 model 10% smaller. ZTL-191 card on the desert coat too. HQ-9C and HQ-9B 2 cards (HQ-9A has no card).
- PLZ-07B: 130 pts, 20 smoke and 12 laser-guided rounds (GP6 122 mm, a copy of the PLZ-05 GP155 at its own range).
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.99';PREV='0.8.0-dev.98'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
base=REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];SA=t['SpecializationAvailabilitiesJson'];TA=t['TransportAvailabilitiesJson'];A=t['AmmunitionsJson']
WA=t['WeaponAmmunitionsJson'];O=t['OptionsJson'];M=t['ModificationsJson'];TU=t['TurretUnitsJson'];rows=g.rows
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));SAS=assign['assignments'];checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
def hud(u,h):ok(U[u]['HUDName']==h,(u,h,U[u]['HUDName']))
# ---------- availability ----------
def avail(u,h,n,spec=None):
    hud(u,h);rs=[r for r in rows('SpecializationAvailabilitiesJson',u) if spec is None or r['SpecializationId']==spec];ok(rs,(h,'card'))
    for r in rs:rec.setdefault('availability',{}).setdefault(h,[]).append([r['SpecializationId'],r['MaxAvailabilityXp0'],n]);g.put('SpecializationAvailabilitiesJson',r['Id'],{'MaxAvailabilityXp0':n})
for u,h,n in ((1028,'DF-17/ZF',1),(1129,'YJ-18',2),(1166,'Conscripts 义务兵',8),(1168,'HJ-73D Team',8),(1175,'Infantry 步兵',8),(1163,'Mech. Rifles 机步班',8),(1196,'Line Infantry 摩步班',6),(1205,'Light Riflemen 轻步兵',6),(1192,'Marines 陆战队',6),(1240,'ZTQ-15 Recon',2),(1262,'VT-5 Recon',2),(1263,'ZTL-191 Recon',2),
              (904,'ZTZ-99A',2),(911,'HQ-9C',2),(1233,'HQ-9B',2),(1083,'ZTZ-99',4),(1089,'J-5',4),(1091,'J-6W',4),(1092,'J-7',4),(975,'J-8D',4)):avail(u,h,n)
SF=((1181,'Godswords 东方神剑'),(1182,'PAP Snow Leopards 雪豹'),(1183,'Blood Wolves 血狼'),(1185,'Falcons 猎鹰'),(1191,'Sea Dragons 蛟龙'))
SFR=((1184,'Whistling Arrows 响箭'),(1186,'Mountain Leopards 高原雪豹'),(1187,'Beijing Swords 蓝剑'))
for u,h in SF:ok(U[u]['CategoryType']==1,h);avail(u,h,2,20)
for u,h in SFR:ok(U[u]['CategoryType']==0,h);avail(u,h,3,20)
inf20=sorted(r['UnitId'] for r in SA.values() if r['SpecializationId']==20 and U[r['UnitId']]['CategoryType']==1)
ok(inf20==[1181,1182,1183,1185,1191,1192,1193,1194],('PLAN SOF infantry = 5 SF + 3 Marines',inf20))
# ---------- prices, name ----------
for u,h,was,new in ((1164,'Forward Observers 前观组',60,25),(906,'ZTQ-15',95,150),(1240,'ZTQ-15 Recon',100,165),(1040,'PLZ-70',65,95),(1042,'PLZ-85',75,90),(976,'MD-22',180,280),(931,'PLZ-07B',80,130),(1059,'PTL-02',40,50),(1261,'VT-5',140,240)):
    hud(u,h);ok(U[u]['Cost']==was,(h,was));g.put('Units',u,{'Cost':new});rec.setdefault('prices',{})[h]=[was,new]
hud(1174,'Sharp Blades 利刃');g.put('Units',1174,{'HUDName':'Sharp Swords 利剑'});g.put('Units',1196,{'HUDName':'Moto. Riflemen 摩步班'})
rec['rename']={1174:['Sharp Blades 利刃','Sharp Swords 利剑'],1196:['Line Infantry 摩步班','Moto. Riflemen 摩步班']}
# ---------- artillery ----------
def only(aid,u):ok(sorted({r['UnitId'] for r in WA.values() if r['AmmunitionId']==aid})==[u],(aid,u))
only(2010533,1042);ok((A[2010533]['DispersionHorizontalRadius'],A[2010533]['DispersionVerticalRadius'])==(90.0,120.0),'PLZ-85 dispersion')
g.put('AmmunitionsJson',2010533,{'DispersionHorizontalRadius':120.0,'DispersionVerticalRadius':150.0})
only(2010547,1043);ok(A[2010547]['GroundRange']==1850.0,'PLZ-89 range');g.put('AmmunitionsJson',2010547,{'GroundRange':2150.0})
rec['plz85_dispersion']={'horizontal':[90.0,120.0],'vertical':[120.0,150.0],'reading':'300 x 240 m radii, world = m/2'};rec['plz89_range_world']=[1850.0,2150.0]
for u,h,he,src,cal in ((926,'PLL-05',2009463,192,'120 mm'),(1037,'PLL-09',2010465,68,'120 mm'),(1040,'PLZ-70',2010505,68,'122 mm'),(931,'PLZ-07B',2009545,68,'122 mm')):
    hud(u,h);r0=[r for r in rows('WeaponAmmunitionsJson',u)];ok(len(r0)==1 and r0[0]['AmmunitionId']==he,(h,'one HE row'));H=A[he];S=A[src]
    ok(S['TrajectoryType']==H['TrajectoryType'] and S.get('GenerateSmoke'),(h,'smoke source trajectory'))
    sid=g.add('AmmunitionsJson',S,{'Name':f'PLA {h} {cal} smoke','HUDName':f'{cal} smoke','GroundRange':H['GroundRange'],'MinimalRange':H['MinimalRange'],'SupplyCost':H['SupplyCost']})
    g.add('WeaponAmmunitionsJson',r0[0],{'AmmunitionId':sid,'Quantity':20,'Order':r0[0]['Order']+1})
    rec.setdefault('smoke',{})[h]={'ammo':sid,'copy_of':src,'rounds':20,'range':H['GroundRange']}
# PLZ-07B: 12 laser-guided rounds, a 122 mm copy of the PLZ-05 GP155 (damage and supply scaled by the HE ratio of each gun)
GP=A[2018752];ERF=A[2018750];H7=A[2009545];hud(907,'PLZ-05');ok(GP['LaserGuided'] and GP['HUDName']=='GP155 laser-guided','GP155')
he7=[r for r in rows('WeaponAmmunitionsJson',931) if r['AmmunitionId']==2009545][0]
gid=g.add('AmmunitionsJson',GP,{'Name':'PLA PLZ-07B GP6 122 mm laser-guided','HUDName':'GP6 122 mm laser-guided','GroundRange':H7['GroundRange'],'MinimalRange':H7['MinimalRange'],
   'Damage':round(GP['Damage']*H7['Damage']/ERF['Damage'],2),'SupplyCost':round(GP['SupplyCost']*H7['SupplyCost']/ERF['SupplyCost'],1)})
g.add('WeaponAmmunitionsJson',he7,{'AmmunitionId':gid,'Quantity':12,'Order':he7['Order']+2})
rec['plz07b_guided']={'ammo':gid,'rounds':12,'damage':A[gid]['Damage'],'supply':A[gid]['SupplyCost'],'range':A[gid]['GroundRange']}
# ---------- transports ----------
def tas(u):return [r for r in TA.values() if r['UnitId']==u]
def spec_of(sa):return SA[sa]['SpecializationId'] if sa in SA else None
def drop_card(u):
    for r in rows('SpecializationAvailabilitiesJson',u):g.remove('SpecializationAvailabilitiesJson',r['Id'])
    SAS.pop(str(u),None)
def remove_unit(u,h):
    hud(u,h);drop_card(u)
    for r in tas(u):g.remove('TransportAvailabilitiesJson',r['Id'])
    g.put('Units',u,{'DisplayInArmory':False});rec.setdefault('removed',[]).append([u,h])
remove_unit(900,'CSK-131 Mengshi');remove_unit(1246,'ZSD-89')
ok(rows('SpecializationAvailabilitiesJson',1064) and [r['SpecializationId'] for r in rows('SpecializationAvailabilitiesJson',1064)]==[19],'ZSD-89 stays in Rocket Force')
hud(1266,'CSK-131');n=0
for r in tas(1266):
    if spec_of(r['SpecializationAvailabilityId'])==17:g.remove('TransportAvailabilitiesJson',r['Id']);n+=1
ok(n==10,('CSK-131 PLAAF links',n));rec['csk131_plaaf_links_removed']=n
hud(1230,'CSK-181');n=0
for r in tas(1230):
    if spec_of(r['SpecializationAvailabilityId'])==20:g.remove('TransportAvailabilitiesJson',r['Id']);n+=1
ok(n==11,('CSK-181 PLAN SOF links',n));rec['csk181_plan_links_removed']=n
hud(945,'ZBD-20');ok(not tas(945) and U[945]['InfantrySlots']==U[902]['InfantrySlots']==7,'ZBD-20 not yet a transport, 7 seats')
z04=tas(902);ok(len(z04)==9 and all(spec_of(r['SpecializationAvailabilityId'])==18 for r in z04),'ZBD-04A links')
for r in z04:g.add('TransportAvailabilitiesJson',r,{'UnitId':945})
rec['zbd20_transport_links']=len(z04)
moved=[]
for u in sorted({r['UnitId'] for r in TA.values() if r['UnitId']>=900}):
    own=rows('SpecializationAvailabilitiesJson',u)
    if not own or U[u]['CategoryType'] not in (0,2) or U[u].get('DisplayInArmory') is False:continue
    linked={spec_of(r['SpecializationAvailabilityId']) for r in tas(u)}
    ok({r['SpecializationId'] for r in own}-{(1230,20):{20},(1266,17):{17}}.get((u,20 if u==1230 else 17),set())<=linked,(U[u]['HUDName'],'still offered as a transport where its card was'))
    moved.append([u,U[u]['HUDName'],sorted(r['SpecializationId'] for r in own)]);drop_card(u)
ok(len(moved)==16,('ground transports with own cards',moved));rec['transport_cards_removed']=moved
hud(1248,'ZSD-89A');n=0
for r in tas(1248):
    if spec_of(r['SpecializationAvailabilityId'])==21:g.remove('TransportAvailabilitiesJson',r['Id']);n+=1
ok(n==11 and tas(1248),('ZSD-89A Motorized links',n));rec['zsd89a_motorized_links_removed']=n
ok(not [u for u in {r['UnitId'] for r in TA.values() if r['UnitId']>=900} if rows('SpecializationAvailabilitiesJson',u) and U[u]['CategoryType'] in (0,2)],'no ground transport keeps a card')
# ---------- recon helicopter Empty loadouts ----------
for u,h in ((1133,'Z-9WA Recon'),(1134,'Z-19 Recon'),(1135,'Z-21 Recon'),(1237,'Z-19 Recon')):
    hud(u,h);ms=[m for m in M.values() if m.get('UnitId')==u];ok(len(ms)==1,(h,'one loadout'));os_=[o for o in O.values() if o['ModificationId']==ms[0]['Id']]
    ok(all(o['Cost']>0 for o in os_),(h,'no empty yet'));keys=sorted({k for o in os_ for k,v in o.items() if k.startswith('Turret') and v})
    ok(any(r['TurretId']==160 for r in rows('TurretUnitsJson',u)),(h,'Turret Empty row'))
    for o in os_:g.put('OptionsJson',o['Id'],{'Order':o['Order']+1})
    tmpl=min(os_,key=lambda o:o['Id']);fields={f'Turret{i}Id':0 for i in range(21)};fields.update({k:160 for k in keys})
    fields.update({'Name':f'PLA recon loadout {u} empty','UIName':'Empty','Cost':0,'IsDefault':False,'Order':0,'OptionPicture':'EMPTY'})
    oid=g.add('OptionsJson',tmpl,fields);rec.setdefault('empty_loadouts',{})[h+f' {u}']={'option':oid,'slots':keys}
# ---------- FK-2000 model ----------
MJ='UserData/FAModels/models.json';raw=z.read(MJ);models=json.loads(raw)
ok(models['PLA FK-2000']=={'file':'m_fk2000s_static.fam','battle':'m_fk2000s_lo_static.fam','align':False},'FK-2000 entry');models['PLA FK-2000']['scale']=0.9
rec['fk2000_scale']=0.9
# ZTL-191 card on the desert coat as well (Osama 00:4x: "ZTL-191 should use its desert camo"); m_ztl191d ships since dev.98
ok(models['PLA Catalogue ZTL-191']['file']=='m_ztl191_static.fam' and models['PLA ZTL-191 Recon']['file']=='m_ztl191d_static.fam','ZTL-191 models')
e={k:v for k,v in models['PLA Catalogue ZTL-191'].items() if k in ('hide','scale')};models['PLA Catalogue ZTL-191']={'file':'m_ztl191d_static.fam','battle':'m_ztl191d_lo_static.fam','align':False,**e}
ok('UserData/FAModels/m_ztl191d_lo_static.fam' in z.namelist(),'desert ZTL-191 in dev.98');rec['ztl191_desert']=True
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=raw.isascii())+'\n').encode())
(ROOT/f'tools/pla-specs/{V}-assets.txt').write_text('')
rec.update(version=V,base=PREV,base_sha256=BASE,request='Osama 14 Nov 00:0x-00:2x PST',checks=checks,verified='data checks only',
  not_done={'HQ-9B':'request text unclear','J-36 PL-21':'removed in dev.76 at Osama 13 Nov 19:5x request (one Heavy CAP 4x PL-17 4x PL-16); restore on request',
            'HMV3 Cargo 15000':'needs a runtime cargo patch; the truck cargo comes from the US_HEMTT prefab'})
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,'moved',len(moved));print(json.dumps(moved,ensure_ascii=False))

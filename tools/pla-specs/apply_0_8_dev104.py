"""Freedom Arrow 0.8.0-dev.104 over exact 0.8.0-dev.103 (Osama 14 Nov 04:0x PST, thread 1571014792016171120). Batch; push on Osama's word.
- Z-20 family glass: the vanilla US_UH60M_glass material (dev.101 donor) uses the unit body shader (Shader Graphs/UnitV3, seen in
  Osama's MelonLoader log), so the canopy drew as painted body. Z-20/Z-20T, SF Z-20/Z-20S and PLAGF Z-20 now use the AH-1Z glass
  (HDRP/Lit, the same family as the working AH-64/F-16 donors).
- PCL-181: windshield and cab side windows (seller material F0150074, plain dark teal, 393 faces) are clear glass like the HQ-9/HQ-7
  windows; paint darker as on the PHL-03 (texture colour x0.6, flat colours x0.7, material-only colorScale).
- Z-21 Multirole (CM-501GA): two racks of 2 missiles (4 total, was 2 x 4). Price unchanged (not specified). It already fires one
  missile at a time (1 shot per burst, 12-16 s between shots, one missile guided at a time).
- Z-21 / Z-21 Recon canopy: the seller canopy ('cop') shared one plain grey with the cockpit interior, so it drew solid. Rebuilt with
  the canopy as its own material (all other files byte-identical) and given the Z-10's glass (vanilla AH-64 glass).
- Z-20T: FS-90 loadouts beside the FS-70A ones: inner 32x FS-90 (45) and outer 16x FS-90 (20) (Osama 04:2x).
  The FS-70A pylons are copied with the FS-90 rocket (ammo and weapon look of the Z-10/Z-21 FS-90).
- DF-15: 4 cards (was 2). DF-17 (1) and DF-21 (2) already as requested.
- PGZ-09 guns: already an exact Pantsir 2A38M stat copy; ground range 1200 shown (GroundRange 600, was 500; display = data x2).
- HQ-17A: PLAN SOF card removed; it keeps its PLAGF Motorized card (4).
- One CSK transport per deck (Osama): CSK-181 (1230) for PLARF and PLAN SOF, CSK-131 (1266) for PLAAF and PLAGF Motorized. Both
  have 12 seats and carried the same squads in each deck, so links are moved or dropped, never re-chosen. PLAGF Armored had
  neither and is unchanged.
- J-20S canopy: FAModels clear glass at opacity 0.025 (the ground-vehicle canopy value) instead of the F-16 glass donor.
- ZBL-191: HEAT front 500 (was 700), HEAT sides 300 (was 700). ZTL-191 (vehicle card): armour row set to the new ZBL-191 values
  (KE 80/60/30/20, HEAT 500/300/130/20, was 60/40/30/20 both), 180 pts (was 115). ZTL-191 Recon: same armour, 200 pts (ZTL-191 +20, Osama 04:29; was 120).
- ZTL-11: its 105 mm gun also fires a gun-launched missile, a stat copy of the ZBD-04A 100 mm gun-launched missile (8 rounds, as
  on the ZBD-04A); 90 pts (was 70). PTL-02: 60 pts (was 50).
- DF-17: missile supply cost 5000 (was 2000), resupply time 180 s (was 120).
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.104';PREV='0.8.0-dev.103'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--z21',type=Path,required=True);a=p.parse_args()
base=REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];O=t['OptionsJson'];TU=t['TurretUnitsJson'];TR=t['TurretsJson'];WA=t['WeaponAmmunitionsJson'];checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
# ---------- Z-21 CM-501GA ----------
ok(U[1104]['HUDName']=='Z-21','Z-21');CM=2017901;ok(TR[CM]['Name']=='PLA air pylon CM-501GA x4' and [r['UnitId'] for r in TU.values() if r['TurretId']==CM]==[1104],'CM-501GA pylon')
wa=[x for x in WA.values() if x['WeaponId']==2017902];ok(len(wa)==1 and wa[0]['UnitId']==1104 and wa[0]['Quantity']==4,'CM-501GA ammo')
g.put('WeaponAmmunitionsJson',wa[0]['Id'],{'Quantity':2});g.put('TurretsJson',CM,{'Name':'PLA air pylon CM-501GA x2'})
o=O[24645];ok(o['UIName']=='Multirole (CM-501GA)' and [o.get(f'Turret{i}Id') for i in range(5)]==[0,CM,CM,2017194,2017194],'CM-501GA option')
g.put('OptionsJson',24645,{'UIName':'Multirole (4x CM-501GA, 14x FS-70A)'})
rec['z21_cm501ga']={'option':24645,'per_rack':[4,2],'total':[8,4],'cost':o['Cost']}
# ---------- Z-20T FS-90 ----------
W=t['WeaponsJson'];TW=t['TurretWeaponsJson'];M=t['ModificationsJson'];ok(U[1245]['HUDName']=='Z-20T','Z-20T');F90=W[2018820];ok(F90['HUDName']=='FS-90','FS-90 weapon')
f90a=[x for x in WA.values() if x['WeaponId']==2018820];ok(len({x['AmmunitionId'] for x in f90a})==1,'FS-90 ammo');F90A=f90a[0]['AmmunitionId']
new={};rec['z20t_fs90']={}
for tid in (2017558,2017561,2017574,2017577):
    tw=[r for r in TW.values() if r['TurretId']==tid];ok(len(tw)==1 and W[tw[0]['WeaponId']]['HUDName']=='FS-70A',(tid,'FS-70A pylon'))
    w=W[tw[0]['WeaponId']];wa=[x for x in WA.values() if x['UnitId']==1245 and x['WeaponId']==w['Id']];ok(len(wa)==1,(tid,'ammo row'))
    nw=g.add('WeaponsJson',w,{'Name':w['Name'].replace('FS-70A','FS-90'),'HUDName':'FS-90','HUDIcon':F90['HUDIcon'],'NormalGroundAttackBurst':F90['NormalGroundAttackBurst']})
    nt=g.add('TurretsJson',TR[tid],{'Name':TR[tid]['Name'].replace('DAGR','FS-90')});g.add('TurretWeaponsJson',tw[0],{'TurretId':nt,'WeaponId':nw})
    g.add('TurretUnitsJson',next(r for r in TU.values() if r['UnitId']==1245 and r['TurretId']==tid),{'TurretId':nt});g.add('WeaponAmmunitionsJson',wa[0],{'WeaponId':nw,'AmmunitionId':F90A})
    new[tid]=nt;rec['z20t_fs90'][TR[nt]['Name']]={'turret':nt,'weapon':nw,'rounds':wa[0]['Quantity']}
for src,ui,cost in ((24571,'32x FS-90',45),(24575,'16x FS-90',20)):
    o=O[src];ok(o['UIName']==ui.replace('FS-90','FS-70A') and M[o['ModificationId']]['UnitId']==1245,(src,o['UIName']))
    mine=[x['Order'] for x in O.values() if x['ModificationId']==o['ModificationId']]
    oid=g.add('OptionsJson',o,{**{f'Turret{i}Id':new.get(o.get(f'Turret{i}Id'),o.get(f'Turret{i}Id')) for i in range(21)},'UIName':ui,'Name':o['Name']+' FS-90','IsDefault':False,'Order':max(mine)+1,'Cost':cost})
    ok(sorted({O[oid].get(f'Turret{i}Id') for i in range(21)}-{0,2009262})==sorted({new[k] for k in new if k in {o.get(f'Turret{i}Id') for i in range(21)}}),(ui,'pylons'))
    rec['z20t_fs90'][ui]={'option':oid,'cost':o['Cost']}
# ---------- DF-15 cards, PGZ-09 range ----------
SA=t['SpecializationAvailabilitiesJson'];AM=t['AmmunitionsJson']
def cards(u):return [(r['Id'],r['SpecializationId'],r['MaxAvailabilityXp0']) for r in SA.values() if r['UnitId']==u]
ok(U[1029]['HUDName']=='DF-15' and [c[1:] for c in cards(1029)]==[(19,2)],'DF-15 2');g.put('SpecializationAvailabilitiesJson',cards(1029)[0][0],{'MaxAvailabilityXp0':4})
ok([c[1:] for c in cards(1028)]==[(19,1)] and [c[1:] for c in cards(1030)]==[(19,2)],'DF-17 1, DF-21 2')
ok(U[909]['HUDName']=='PGZ-09' and AM[2009185]['GroundRange']==500.0,'PGZ-09 range');g.put('AmmunitionsJson',2009185,{'GroundRange':600.0})
ok(all(AM[2009185][k]==AM[60][k] for k in AM[60] if k not in ('Id','Name','HUDName','HUDIcon','GroundRange')),'Pantsir stat copy')
rec['df15_cards']=[2,4];rec['pgz09_ground_range']={'data':[500,600],'shown':[1000,1200]}
# ---------- HQ-17A out of PLAN SOF ----------
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN))
ok(U[1049]['HUDName']=='HQ-17A' and sorted(c[1:] for c in cards(1049))==[(20,4),(21,4)] and assign['assignments'].get('1049')==[20,21],'HQ-17A SOF + Motorized')
g.remove('SpecializationAvailabilitiesJson',[c[0] for c in cards(1049) if c[1]==20][0]);assign['assignments']['1049']=[21]
ok([c[1:] for c in cards(1049)]==[(21,4)],'HQ-17A Motorized only');ok(assign['shared_transports'].pop('1049')==[20,21],'HQ-17A shared entry');rec['hq17a']={'removed_spec':20,'kept':21}
# ---------- one CSK transport per deck ----------
TA=t['TransportAvailabilitiesJson']
def links(u,sp):return sorted((k for k in TA if TA[k]['UnitId']==u and SA[TA[k]['SpecializationAvailabilityId']]['SpecializationId']==sp),key=lambda k:TA[k]['SpecializationAvailabilityId'])
def pax(ks):return sorted(TA[k]['SpecializationAvailabilityId'] for k in ks)
ok(U[1230]['HUDName']=='CSK-181' and U[1266]['HUDName']=='CSK-131' and U[1230]['InfantrySlots']==U[1266]['InfantrySlots']==12,'CSK pair')
ok(not links(1266,17) and not links(1230,20) and not links(1230,18) and not links(1266,18),'gaps as expected')
ok(pax(links(1230,19))==pax(links(1266,19)) and pax(links(1230,21))==pax(links(1266,21)),'same squads where both')
csk={}
for k in links(1230,17):g.put('TransportAvailabilitiesJson',k,{'UnitId':1266})
for k in links(1266,20):g.put('TransportAvailabilitiesJson',k,{'UnitId':1230})
for k in links(1266,19)+links(1230,21):g.remove('TransportAvailabilitiesJson',k)
for u in (1230,1266):csk[U[u]['HUDName']]={sp:len(links(u,sp)) for sp in (17,18,19,20,21) if links(u,sp)}
ok(csk=={'CSK-181':{19:11,20:11},'CSK-131':{17:10,21:11}},csk)
assign['shared_transports']['1230']=[19,20];assign['shared_transports']['1266']=[17,21]
for sp,u in (('20',1230),('17',1266),('21',1266)):
    if u not in assign['carriers'][sp]:assign['carriers'][sp].append(u)
rec['csk_transports']=csk
# ---------- ZBL-191 / ZTL-191 armour, ZTL-11 missile, prices ----------
AR=t['ArmorsJson'];UAR=t['UnitArmorsJson']
def armor(u):r=[x for x in UAR.values() if x['UnitId']==u];ok(len(r)==1 and sum(1 for x in UAR.values() if x['ArmorId']==r[0]['ArmorId'])==1,(u,'own armour'));return r[0]['ArmorId']
AF=('MaxHealthPoints','HeatArmorFront','HeatArmorRear','HeatArmorSides','HeatArmorTop','KinArmorFront','KinArmorRear','KinArmorSides','KinArmorTop')
ok(U[979]['HUDName']=='ZBL-191' and U[1080]['HUDName']=='ZTL-191','ZBL/ZTL-191');zb,zt=armor(979),armor(1080)
ok((AR[zb]['HeatArmorFront'],AR[zb]['HeatArmorSides'])==(700,700),'ZBL HEAT');g.put('ArmorsJson',zb,{'HeatArmorFront':500,'HeatArmorSides':300})
before={k:AR[zt][k] for k in AF};g.put('ArmorsJson',zt,{k:AR[zb][k] for k in AF});ok(all(AR[zt][k]==AR[zb][k] for k in AF),'ZTL-191 matches')
ok(U[1080]['Cost']==115,'ZTL-191 115');g.put('Units',1080,{'Cost':180})
ok(U[1263]['HUDName']=='ZTL-191 Recon' and U[1263]['Cost']==120,'ZTL-191 Recon 120');zr=armor(1263);g.put('ArmorsJson',zr,{k:AR[zb][k] for k in AF});g.put('Units',1263,{'Cost':200});ok(all(AR[zr][k]==AR[zb][k] for k in AF),'Recon matches')
rec['zbl191_ztl191']={'zbl_heat':{'front':[700,500],'sides':[700,300]},'ztl191_armour':{'before':before,'after':{k:AR[zt][k] for k in AF}},'ztl191_cost':[115,180],'ztl191_recon_cost':[120,200]}
ok(U[938]['HUDName']=='ZTL-11' and U[938]['Cost']==70 and U[1059]['HUDName']=='PTL-02' and U[1059]['Cost']==50,'ZTL-11/PTL-02 prices');g.put('Units',938,{'Cost':90});g.put('Units',1059,{'Cost':60})
AM=t['AmmunitionsJson'];src=[x for x in WA.values() if x['UnitId']==902 and x['AmmunitionId']==2009025];ok(len(src)==1 and AM[2009025]['Seeker']==100 and src[0]['Quantity']==8,'ZBD-04A missile')
gun=[x for x in WA.values() if x['UnitId']==938 and x['WeaponId']==2009665];ok(len(gun)==2 and max(x['Order'] for x in gun)==1,'ZTL-11 gun rows')
na=g.add('AmmunitionsJson',AM[2009025],{'Name':'PLA ZTL-11 105 mm gun-launched missile','HUDName':'105 mm gun-launched missile'})
g.add('WeaponAmmunitionsJson',gun[0],{'AmmunitionId':na,'Order':2,'Quantity':8})
ok(all(AM[na][k]==AM[2009025][k] for k in AM[na] if k not in ('Id','Name','HUDName')),'missile stat copy')
rec['ztl11']={'missile_ammo':na,'rounds':8,'cost':[70,90]};rec['ptl02_cost']=[50,60]
# ---------- DF-17 supply ----------
d=AM[2010351];ok(d['Name']=='PLA DF-17 DF-17 conventional test missile ammunition' and (d['SupplyCost'],d['ResupplyTime'])==(2000.0,120.0) and {x['UnitId'] for x in WA.values() if x['AmmunitionId']==2010351}=={1028},'DF-17 ammo')
g.put('AmmunitionsJson',2010351,{'SupplyCost':5000.0,'ResupplyTime':180.0});rec['df17_supply']={'cost':[2000,5000],'time':[120,180]}
# ---------- materials ----------
gdir=ROOT/f'tools/pla-specs/{V}-mats';gdir.mkdir(exist_ok=True);files={}
for s in ('m_z20na','m_z20n','m_z20a'):
    for n in (s+'_static',s+'_lo_static'):
        k=f'UserData/FAModels/{n}.mat.json';mj=json.loads(z.read(k));d=[v for v in mj.values() if v.get('cockpitDonor')];ok(len(d)==1 and d[0]['cockpitDonor']=='US_UH60M_glass',(n,'donor'))
        d[0]['cockpitDonor']='US_AH-1Z_Viper_Glass';f=gdir/(n+'.mat.json');f.write_text(json.dumps(mj,indent=1)+'\n');files[k]=str(f)
rec['j20s_glass']={}
for n in ('m_j20sg_static','m_j20sg_lo_static'):
    k=f'UserData/FAModels/{n}.mat.json';mj=json.loads(z.read(k));gl=[v for v in mj.values() if v.get('cockpitDonor')];ok(len(gl)==1 and gl[0]['cockpitDonor']=='US_F16_Glass',(n,'F-16 donor'))
    gl[0].pop('cockpitDonor');gl[0].update(clearGlass=True,opacity=0.025,alpha='BLEND',metallic=0.0,smoothness=0.95);f=gdir/(n+'.mat.json');f.write_text(json.dumps(mj,indent=1)+'\n');files[k]=str(f);rec['j20s_glass'][n]=0.025
WIN='|0.0863,0.1961,0.2353,1.0000';rec['pcl181']={}
for n in ('m_pcl181_static','m_pcl181_lo_static'):
    k=f'UserData/FAModels/{n}.mat.json';mj=json.loads(z.read(k));ok(WIN in mj and not mj[WIN].get('clearGlass') and not any(v.get('colorScale') for v in mj.values()),(n,'windows opaque'))
    mj[WIN].update(clearGlass=True,opacity=0.025,alpha='BLEND',metallic=0.0,smoothness=0.95);c={}
    for key,v in mj.items():
        if v.get('clearGlass'):continue
        s=0.7 if key.startswith('|') else 0.6;v['colorScale']=[s,s,s];c[s]=c.get(s,0)+1
    ok(sum(1 for v in mj.values() if v.get('clearGlass'))==2,(n,'two glass materials'));f=gdir/(n+'.mat.json');f.write_text(json.dumps(mj,indent=1)+'\n');files[k]=str(f);rec['pcl181'][n]=c
for n in ('m_z21_static','m_z21_lo_static'):
    for suf in ('.fam','.mat.json'):
        k=f'UserData/FAModels/{n}{suf}';f=a.z21/(n+suf);ok(k in z.namelist() and f.read_bytes()!=z.read(k),(k,'replaced'));files[k]=str(f)
    mj=json.loads((a.z21/(n+'.mat.json')).read_text());old=json.loads(z.read(f'UserData/FAModels/{n}.mat.json'))
    ok(all(mj[k]==v for k,v in old.items()) and mj['|0.5000,0.5000,0.5000,0.9980']=={'cockpitDonor':'US_AH_64_Glass'} and len(mj)==len(old)+1,(n,'only canopy added'))
    ok(len(a.z21.joinpath(n+'.fam').read_bytes())==len(z.read(f'UserData/FAModels/{n}.fam')),(n,'same mesh size'))
    for k2 in [x for x in z.namelist() if x.startswith(f'UserData/FAModels/{n}_tex')]:ok(a.z21.joinpath(k2.split('/')[-1]).read_bytes()==z.read(k2),(k2,'texture unchanged'))
rec['z21_canopy']={'donor':'US_AH_64_Glass','as':'Z-10'}
(ROOT/f'tools/pla-specs/{V}-assets.txt').write_text(''.join(f'{k}={v}\n' for k,v in sorted(files.items())))
rec.update(version=V,base=PREV,base_sha256=BASE,request='Osama 14 Nov 04:0x PST',checks=checks,verified='data and file checks; not in game')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,'files',len(files))

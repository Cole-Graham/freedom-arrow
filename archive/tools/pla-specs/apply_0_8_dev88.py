"""Freedom Arrow 0.8.0-dev.88 over exact 0.8.0-dev.87 (Osama 13 Nov 21:45-21:58 PST, thread 1571014792016171120).
- FireSnake: FS-70A (existing, laser-guided, S8L "rocket pod with laser" icon) and a new FS-90 (FS-70A copy, damage scaled by the
  90/70 mm rocket ratio 4.0/3.5 -> 9). Recon gunships (Z-19 Recon x2, Z-21 Recon) now carry FireSnake 70 or 90 loadouts; the
  higher-end gunship loadouts swap their basic rockets for FireSnakes (Z-19 HJ-10 and CM-501GA, Z-10 HJ-10, Z-10K HJ-10 x2,
  Z-21 HJ-10 and CM-501GA). Basic-rocket fire-support loadouts stay. Rocket counts follow the existing FS-70A loadout (7 per pod,
  14 on the Z-19 combo pylons).
- HJ-16 loadouts: ZBL-191 and ZBD-20 (+Recon) fire the semi-active HJ-16 by default (ZBL-191 moves to the dev.85 HJ-16, 1600 m);
  new option "HJ-16 IIR (fire and forget)" +40 points (Seeker 50, as the Spike LR).
- Abrams X: jammer (ECM Shtora ability link) removed.
- Base ZTZ-59 (1060) in PLARF Rocket/Reservist on the seller ZTZ-59 (ZTZ59A pack) model, 40 points.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.88';PREV='0.8.0-dev.87'
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
g=Graph(t,patches,native);U=t['Units'];W=t['WeaponsJson'];A=t['AmmunitionsJson'];T=t['TurretsJson'];TW=t['TurretWeaponsJson'];TU=t['TurretUnitsJson'];WA=t['WeaponAmmunitionsJson']
O=t['OptionsJson'];M=t['ModificationsJson'];SA=t['SpecializationAvailabilitiesJson'];rows=g.rows
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
def hud(i,n):ok(U[i]['HUDName']==n,(i,U[i]['HUDName'],n))
def tw_of(tid):return sorted([r for r in TW.values() if r['TurretId']==tid],key=lambda r:r['Order'])
def new_turret(src,name,weapons,default=False):
    tid=g.add('TurretsJson',T[src],{'Name':name,'IsDefault':default});tpl=tw_of(src)[0]
    for i,w in enumerate(weapons):g.add('TurretWeaponsJson',tpl,{'TurretId':tid,'WeaponId':w,'Order':tw_of(src)[i]['Order'] if i<len(tw_of(src)) else i})
    return tid
def link(uid,tid):
    if not any(r['UnitId']==uid and r['TurretId']==tid for r in TU.values()):g.add('TurretUnitsJson',rows('TurretUnitsJson',uid)[0],{'TurretId':tid})
def stock(uid,wid,aid,q):
    ex=[r for r in WA.values() if r.get('UnitId')==uid and r['WeaponId']==wid and r['AmmunitionId']==aid]
    if ex:g.put('WeaponAmmunitionsJson',ex[0]['Id'],{'Quantity':q})
    else:g.add('WeaponAmmunitionsJson',rows('WeaponAmmunitionsJson',uid)[0],{'WeaponId':wid,'AmmunitionId':aid,'Quantity':q})
def opts(uid):return [o for o in O.values() if M.get(o.get('ModificationId'),{}).get('UnitId')==uid]
# ---------------- FireSnake
FS70W,FS70A=2017195,2017197;ok(W[FS70W]['HUDIcon']=='S8L' and A[FS70A]['LaserGuided'] and A[FS70A]['HUDName']=='FS-70A','FS-70A rows')
FS90A=g.add('AmmunitionsJson',A[FS70A],{'Name':'PLA air FS-90','HUDName':'FS-90','Damage':round(A[FS70A]['Damage']*A[2017097]['Damage']/A[2017093]['Damage'])})
FS90W7=g.add('WeaponsJson',W[2017095],{'Name':'PLA air FS-90 x7','HUDName':'FS-90','HUDIcon':'S8L'})
FS90W14=g.add('WeaponsJson',W[2017247],{'Name':'PLA air FS-90 x14','HUDName':'FS-90','HUDIcon':'S8L'})
FS70W14=g.add('WeaponsJson',W[2017081],{'Name':'PLA air FS-70A x14','HUDName':'FS-70A','HUDIcon':'S8L'})
T_FS70_7=2017194
T_FS90_7=new_turret(2017094,'PLA air pylon FS-90 x7',[FS90W7]);T_FS90_14=new_turret(2017387,'PLA air pylon FS-90 x14',[FS90W14])
T_FS70_14=new_turret(2017385,'PLA air pylon FS-70A x14',[FS70W14])
T_HJ10_FS=new_turret(2017242,'PLA air pylon HJ-10 x4 + FS-70A x14',[2017062,FS70W14]);T_CM_FS=new_turret(2017256,'PLA air pylon CM-501GA x4 + FS-70A x14',[2017126,FS70W14])
STOCK={T_FS70_7:[(FS70W,FS70A,7)],T_FS90_7:[(FS90W7,FS90A,7)],T_FS90_14:[(FS90W14,FS90A,14)],T_FS70_14:[(FS70W14,FS70A,14)],T_HJ10_FS:[(FS70W14,FS70A,14)],T_CM_FS:[(FS70W14,FS70A,14)]}
SWAP={2017242:T_HJ10_FS,2017256:T_CM_FS,2017090:T_FS70_7,2017904:T_FS70_7,2017094:T_FS90_7,2017385:T_FS70_14,2017387:T_FS90_14}
PLAN={940:[24519,24522],1103:[24523,24526],1236:[24527,24530],1239:[24510],978:[24504],913:[24497,24498],1104:[24514,24645],
      1134:[24580,24581],1237:[24582,24583],1135:[24586,24587]}
changed=[]
def retitle(s):return s.replace('70 mm rocket','FS-70A').replace('90 mm rocket','FS-90').replace('57 mm rocket','FS-70A')
for uid,oids in PLAN.items():
    for oid in oids:
        o=O[oid];ok(M[o['ModificationId']]['UnitId']==uid,(uid,oid))
        new={k:SWAP[v] for k,v in o.items() if k.startswith('Turret') and v in SWAP};ok(new,(oid,'has a basic rocket pylon'))
        for k,tid in new.items():
            link(uid,tid)
            for w,am,q in STOCK[tid]:stock(uid,w,am,q)
        g.put('OptionsJson',oid,{**new,'UIName':retitle(o['UIName'])});changed.append((uid,oid,O[oid]['UIName']))
# drop pylons and stocks a unit no longer uses
dropped=[]
for uid in PLAN:
    used={v for o in opts(uid) for k,v in o.items() if k.startswith('Turret') and v}
    for r in list(rows('TurretUnitsJson',uid)):
        if not T[r['TurretId']].get('IsDefault') and r['TurretId'] not in used:g.remove('TurretUnitsJson',r['Id']);dropped.append((uid,r['TurretId']))
    have={tw['WeaponId'] for r in rows('TurretUnitsJson',uid) for tw in tw_of(r['TurretId'])}
    for r in list(rows('WeaponAmmunitionsJson',uid)):
        if r['WeaponId'] not in have:g.remove('WeaponAmmunitionsJson',r['Id'])
    for o in opts(uid):
        for k,v in o.items():
            if k.startswith('Turret') and v:ok(any(r['UnitId']==uid and r['TurretId']==v for r in TU.values()),('option turret linked',uid,o['Id'],v))
    for r in rows('TurretUnitsJson',uid):
        for tw in tw_of(r['TurretId']):ok(any(x['WeaponId']==tw['WeaponId'] for x in rows('WeaponAmmunitionsJson',uid)),('stock',uid,tw['WeaponId']))
rec['firesnake']={'FS-90':{'ammo':FS90A,'damage':A[FS90A]['Damage'],'pen':A[FS90A]['PenetrationAtMinRange'],'icon':W[FS90W7]['HUDIcon']},'options':changed,'pylons_dropped':dropped}
# ---------------- HJ-16 semi-active + IIR option
HJW,HJA=2018803,2018804;ok(W[HJW]['HUDName']=='HJ-16' and A[HJA]['Seeker']==100,'semi-active HJ-16')
r=[x for x in TW.values() if x['TurretId']==2010324 and x['WeaponId']==2010337];ok(len(r)==1,'zbl hj-16 row');g.put('TurretWeaponsJson',r[0]['Id'],{'WeaponId':HJW})
r=[x for x in WA.values() if x.get('UnitId')==979 and x['WeaponId']==2010337];ok(len(r)==1 and r[0]['Quantity']==4,'zbl stock');g.put('WeaponAmmunitionsJson',r[0]['Id'],{'WeaponId':HJW,'AmmunitionId':HJA})
IIRW=g.add('WeaponsJson',W[HJW],{'Name':'PLA HJ-16 IIR launcher','HUDName':'HJ-16 IIR'})
IIRA=g.add('AmmunitionsJson',A[HJA],{'Name':'PLA HJ-16 IIR','HUDName':'HJ-16 IIR','Seeker':A[2000177]['Seeker']})
T_ZBD_IIR=new_turret(2009820,'PLA ZBD-20 mount 0 HJ-16 IIR',[x['WeaponId'] if x['WeaponId']!=HJW else IIRW for x in tw_of(2009820)])
T_ZBL_IIR=new_turret(2010324,'PLA ZBL-191 mount 0 HJ-16 IIR',[x['WeaponId'] if x['WeaponId']!=HJW else IIRW for x in tw_of(2010324)])
blank={f'Turret{i}Id':0 for i in range(21)}
pk={}
for uid,mount,iir,extra,q in ((979,2010324,T_ZBL_IIR,{'Turret1Id':2010332},4),(945,2009820,T_ZBD_IIR,{},8),(1256,2009820,T_ZBD_IIR,{},8)):
    ok(not rows('ModificationsJson',uid),('no options yet',uid));link(uid,iir);stock(uid,IIRW,IIRA,q)
    arm=[x['ArmorId'] for x in rows('UnitArmorsJson',uid)];ok(len(arm)==1,('one armour',uid))
    mid=g.add('ModificationsJson',M[208],{'UnitId':uid,'Name':f'PLA HJ-16 package {uid}','UIName':'Custom_Slot_Weapon_package'})
    base_o={**blank,**extra,'ModificationId':mid,'ArmorId':arm[0],'MobilityId':0,'MainSensorId':0,'ExtraSensorId':0,'ReplaceUnitName':None,'OptionPicture':'VEH_SPIKE_LR'}
    o1=g.add('OptionsJson',O[544],{**base_o,'Name':f'PLA HJ-16 SA {uid}','UIName':'HJ-16 (semi-active)','Order':0,'Cost':0,'IsDefault':True,'Turret0Id':mount})
    o2=g.add('OptionsJson',O[544],{**base_o,'Name':f'PLA HJ-16 IIR {uid}','UIName':'HJ-16 IIR (fire and forget)','Order':1,'Cost':40,'IsDefault':False,'Turret0Id':iir})
    ok(o1<=32767 and o2<=32767,'short option ids');pk[uid]={'modification':mid,'options':[o1,o2]}
ok(A[IIRA]['Seeker']==50 and A[IIRA]['GroundRange']==A[HJA]['GroundRange'],'IIR = HJ-16 with fire-and-forget seeker')
rec['hj16']={'semi_active':[HJW,HJA],'iir':[IIRW,IIRA],'iir_mounts':[T_ZBD_IIR,T_ZBL_IIR],'packages':pk,'iir_cost':40}
# ---------------- Abrams X jammer removed
hud(964,'Abrams X');r=[x for x in rows('UnitAbilitiesJson',964) if x['AbilityId']==2001845];ok(len(r)==1,'abrams x jammer link');g.remove('UnitAbilitiesJson',r[0]['Id'])
ok(not any(x['AbilityId']==2001845 for x in rows('UnitAbilitiesJson',964)),'jammer gone');rec['abrams_x_jammer_removed']=r[0]['Id']
# ---------------- base ZTZ-59
hud(1060,'ZTZ-59');ok(not rows('SpecializationAvailabilitiesJson',1060),'no card yet')
src=[x for x in rows('SpecializationAvailabilitiesJson',1061) if x['SpecializationId']==19][0];g.add('SpecializationAvailabilitiesJson',src,{'UnitId':1060})
g.put('Units',1060,{'DisplayInArmory':True});assign['assignments']['1060']=[19];rec['ztz59']={'unit':1060,'spec':19,'cost':U[1060]['Cost']}
MJ='UserData/FAModels/models.json';raw=z.read(MJ);models=json.loads(raw)
k='PLA Catalogue Type 59 — FlashPoint';ok(U[1060]['Name']==k,'1060 name');rec['models_json']={k:{'before':models.get(k),'after':{'file':'m_ztz59a_static.fam','battle':'m_ztz59a_lo_static.fam','align':False}}};models[k]=rec['models_json'][k]['after']
ok('UserData/FAModels/m_ztz59a_static.fam' in z.namelist(),'ztz59a model shipped')
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=raw.isascii())+'\n').encode())
rec.update(version=V,base=PREV,base_sha256=BASE,request='Osama 13 Nov 21:45-21:58 PST',checks=checks,verified='data only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks);print('FS-90',rec['firesnake']['FS-90']);print('options',[c[2] for c in changed]);print('dropped',dropped);print('hj16',rec['hj16'])

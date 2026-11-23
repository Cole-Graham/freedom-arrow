"""Freedom Arrow 0.8.0-dev.76 over exact 0.8.0-dev.75 (Osama 13 Nov 19:5x PST, thread 1567745029781454889):
- J-36 (929): card turn radius 985 (was 1095). The card shows floor(round(2*MaxSpeed*(1+1/tan(MaxSpeedYaw)))/5)*5
  (AircraftHelper.GetRotationRadius, see the dev.24 fighter-turn report). Its own flight preset 2018570 keeps MaxSpeed 250;
  all five yaw rates are scaled by 45.76/40 (MaxSpeedYaw 40 -> 45.76, raw 986.9 -> 985).
- J-36 Heavy CAP: one loadout, 4x PL-17 and 4x PL-16 (default option 24393, on the existing PL-16 x1 and PL-17 x4 pylons).
  The other two Heavy CAP loadouts (8x PL-17 + 4x PL-21, PL-16) are removed. Prices are not changed in this build.
- J-8D (975) Light strike: +30 (was +50).
- JH-7A (918): removed for now (hidden, card deleted), as the dev.49 roster removals.
- MD-22 (976): its only strike loadout with air-to-air missiles, Light strike (2x LS-6 500kg), loses its PL-15s.
- MD-22 optics = J-35 (Osama 20:0x: "it's more air superiority"): sensor 33 Optics Drone 2250 (ground 5250, low 1600, high 1000)
  -> 6 Optics Plane Air Superiority (ground 0, low 2000, high 8000), the vanilla row the J-35 uses.
"""
import argparse,hashlib,json,math,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.76'
BASE=json.loads((REL/'out/0.8/FreedomArrow-0.8.0-dev.75.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(a.base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN))
g=Graph(t,patches,native)
U,W,A,WA,O,M,T,TW,TU,UP,MOB,FP,SA,TA=(t[k] for k in ('Units','WeaponsJson','AmmunitionsJson','WeaponAmmunitionsJson','OptionsJson','ModificationsJson','TurretsJson','TurretWeaponsJson','TurretUnitsJson','UnitPropulsionsJson','MobilityJson','FlyPresetsJson','SpecializationAvailabilitiesJson','TransportAvailabilitiesJson'))
def hud(i,n):assert U[i]['HUDName']==n,(i,U[i]['HUDName'])
def opts(uid):return [o for o in O.values() if M.get(o['ModificationId'],{}).get('UnitId')==uid]
def slots(o):return [o[f'Turret{i}Id'] for i in range(21)]
def ui_radius(fp):return math.floor(round(2*fp['MaxSpeed']*(1+1/math.tan(math.radians(fp['MaxSpeedYaw']))))/5)*5
def prune(uid):
    used={x for o in opts(uid) for x in slots(o) if x}
    for r in [r for r in TU.values() if r['UnitId']==uid and r['TurretId'] not in used and r['TurretId']!=160]:g.remove('TurretUnitsJson',r['Id'])
rec={}
# ---------- J-36 turn radius ----------
J36=929;hud(J36,'J-36');link=[r for r in UP.values() if r['UnitId']==J36];assert len(link)==1
mob=MOB[link[0]['MobilityId']];FPID=mob['FlyPresetId'];fp=FP[FPID]
assert sorted(r['UnitId'] for r in UP.values() if r['MobilityId']==mob['Id'])==[J36] and [m['Id'] for m in MOB.values() if m.get('FlyPresetId')==FPID]==[mob['Id']]
assert fp['MaxSpeed']==250 and fp['MaxSpeedYaw']==40 and ui_radius(fp)==1095 and not any(o['MobilityId'] for o in opts(J36))
ratio=45.76/40;before_yaw={k:fp[k] for k in ('MinSpeedYaw','MaxSpeedYaw','AfterburnYaw','CornerSpeedYaw','CornerAfterburnSpeedYaw')}
g.put('FlyPresetsJson',FPID,{**{k:round(v*ratio,6) for k,v in before_yaw.items()},'Name':'PLA J-36 turn985, 900 km/h'})
rec['j36_turn']={'preset':FPID,'yaw_before':before_yaw,'yaw_after':{k:FP[FPID][k] for k in before_yaw},'ui_radius':[1095,ui_radius(FP[FPID])]}
# ---------- J-36 Heavy CAP 4x PL-17 + 4x PL-16 ----------
jo={o['Id']:o for o in opts(J36)};HC,HC21,HC16=24393,24394,24663
assert jo[HC]['IsDefault'] and jo[HC]['UIName']=='Heavy CAP (8x PL-17, 6x PL-15C)' and jo[HC21]['UIName'].startswith('Heavy CAP') and jo[HC16]['UIName']=='Heavy CAP (PL-16)'
PL16,PL17=2017956,2016481
assert [(W[r['WeaponId']]['HUDName']) for r in TW.values() if r['TurretId']==PL16]==['PL-16'] and [(W[r['WeaponId']]['HUDName']) for r in TW.values() if r['TurretId']==PL17]==['PL-17']
new=[PL16,PL16,PL17,PL16,PL16,160,160,160]
g.put('OptionsJson',HC,{**{f'Turret{i}Id':(new[i] if i<len(new) else 0) for i in range(21)},'UIName':'Heavy CAP (4x PL-17, 4x PL-16)','Name':'PLA loadout J-36 Heavy CAP 4x PL-17 4x PL-16'})
for oid in (HC21,HC16):g.remove('OptionsJson',oid)
prune(J36)
def load(uid,o):
    c={}
    for tid in slots(o):
        if not tid:continue
        for r in TW.values():
            if r['TurretId']==tid:
                n=W[r['WeaponId']]['HUDName'];q=sum(x['Quantity'] for x in WA.values() if x['UnitId']==uid and x['WeaponId']==r['WeaponId'])
                c[n]=c.get(n,0)+q
    return c
rec['j36_heavy_cap']={'option':HC,'load':load(J36,O[HC]),'removed_options':[HC21,HC16],'cost':O[HC]['Cost']}
# ---------- J-8D Light strike +30 ----------
J8=975;hud(J8,'J-8D');ls=[o for o in opts(J8) if o['UIName']=='Light strike'];assert len(ls)==1 and ls[0]['Cost']==50
g.put('OptionsJson',ls[0]['Id'],{'Cost':30})
# ---------- JH-7A removed ----------
JH=918;hud(JH,'JH-7A')
g.put('Units',JH,{'DisplayInArmory':False});assign['assignments'].pop(str(JH),None)
ids={r['Id'] for r in SA.values() if r['UnitId']==JH};nta=0
for r in list(TA.values()):
    if r['SpecializationAvailabilityId'] in ids or r['UnitId']==JH:g.remove('TransportAvailabilitiesJson',r['Id']);nta+=1
for rid in ids:g.remove('SpecializationAvailabilitiesJson',rid)
for k in assign['carriers']:assign['carriers'][k]=[c for c in assign['carriers'][k] if c!=JH]
rec['jh7a_removed']={'cards':len(ids),'transport_links':nta}
# ---------- MD-22 strike without air-to-air ----------
MD=976;hud(MD,'MD-22');mo={o['Id']:o for o in opts(MD)};LS=31010
assert mo[LS]['UIName']=='Light strike (2x LS-6 500kg)' and slots(mo[LS])[:2]==[2018241,2018248]
lt2=next(r for r in TW.values() if r['TurretId']==2018241 and W[r['WeaponId']]['HUDName']=='LT-2')
T_LT2=g.add('TurretsJson',T[2018241],{'Name':'PLA air pylon LT-2 x2'});g.add('TurretWeaponsJson',lt2,{'TurretId':T_LT2,'Order':0})
g.add('TurretUnitsJson',next(r for r in TU.values() if r['UnitId']==MD),{'TurretId':T_LT2,'UnitId':MD})
g.put('OptionsJson',LS,{'Turret0Id':T_LT2,'Turret1Id':160})
prune(MD)
SU=t['SensorUnitsJson'];su=[r for r in SU.values() if r['UnitId']==MD];assert len(su)==1 and su[0]['SensorId']==33
j35=[r['SensorId'] for r in SU.values() if r['UnitId']==921];hud(921,'J-35');assert j35==[6]
g.put('SensorUnitsJson',su[0]['Id'],{'SensorId':6});rec['md22_optics']=[33,6]
AA=('PL-5','PL-8','PL-9','PL-10','PL-12','PL-15','PL-15C','PL-16','PL-17','PL-21')
rec['md22']={o['UIName']:load(MD,o) for o in opts(MD)}
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
ok(ui_radius(FP[FPID])==985 and FP[FPID]['MaxSpeed']==250,'J-36 card turn radius 985')
ok(rec['j36_heavy_cap']['load']=={'PL-16':4,'PL-17':4} and O[HC]['IsDefault'],'J-36 Heavy CAP 4x PL-17 4x PL-16, default')
ok([o['UIName'] for o in opts(J36) if o['UIName'].startswith('Heavy CAP')]==['Heavy CAP (4x PL-17, 4x PL-16)'],'one Heavy CAP')
ok(all(x in {r['TurretId'] for r in TU.values() if r['UnitId']==J36} for o in opts(J36) for x in slots(o) if x),'J-36 option turrets on unit')
ok(O[ls[0]['Id']]['Cost']==30,'J-8D light strike +30')
ok(not U[JH]['DisplayInArmory'] and not [r for r in SA.values() if r['UnitId']==JH] and '918' not in assign['assignments'],'JH-7A removed')
ok(all(not any(k in AA for k in v) for n,v in rec['md22'].items() if 'strike' in n.lower()),'MD-22 strike loadouts without air-to-air')
ok([r['SensorId'] for r in SU.values() if r['UnitId']==MD]==[6] and t['SensorsJson'][6]['OpticsHighAltitude']==8000.0 and patches['SensorsJson'].get('6')=={'OpticsHighAltitude':8000.0},'MD-22 optics = J-35, sensor row 6 as in dev.75')
ok(rec['md22']['Light strike (2x LS-6 500kg)']=={'LT-2':2},'MD-22 light strike keeps 2x LS-6 500kg')
ok(all(x in {r['TurretId'] for r in TU.values() if r['UnitId']==MD} for o in opts(MD) for x in slots(o) if x),'MD-22 option turrets on unit')
receipt={'version':V,'base':'0.8.0-dev.75','base_sha256':BASE,'request':'Osama 13 Nov 19:5x PST: J-36 turn radius 985 (now 1095); Heavy CAP only 4x PL-17 and 4x PL-16; this plane about 100 pts (price question open); J-8D light strike +30 not 50; remove JH-7 for now; MD-22 ASF missiles removed from strike loadouts; MD-22 optics same as J-35',**rec,'checks':checks,'verified':'data only'}
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',receipt)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,json.dumps(rec,ensure_ascii=False)[:1500])

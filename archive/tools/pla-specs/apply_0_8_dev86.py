"""Freedom Arrow 0.8.0-dev.86 over exact 0.8.0-dev.85 (Osama 13 Nov 21:37-21:45 PST, thread 1571014792016171120).
- ZTZ-85-II (1264): T-80BV (158) stat copy ("ZTZ-85-II should be same stat as T-80BV"). Default T-80BV variant: armour 2000420,
  mobility 106, main optics 2 (Medium), smoke ability 2000199, 2A46M-1 (334) with Mango AP 13 / HE 19 / HEAT 6, PKT and Kord,
  cost 85, weight 45700. Names, icons, sounds and the Type 85-II model stay. Its gun rows are shared only with the hidden
  ZTZ-85-III (956), which takes the same values.
- QN-506 model 80%. ZTL-11 to Motorized. VT-5 and VT-5 Recon front HEAT armour 700 -> 1000.
- PLAN Navy/SOF ZBD-86 and ZBD-86 Recon cards removed; ZBD-05 (PLAN Navy/SOF) uses the ZBD-86 model.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.86';PREV='0.8.0-dev.85'
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
g=Graph(t,patches,native);U=t['Units'];W=t['WeaponsJson'];A=t['AmmunitionsJson'];WA=t['WeaponAmmunitionsJson'];SA=t['SpecializationAvailabilitiesJson'];TA=t['TransportAvailabilitiesJson']
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));checks=0;rec={}
KEEP={'Id','Name','HUDName','HUDIcon','ModelFileName','AudioPreset','FXPreset'}
def ok(c,l):
    global checks
    assert c,l;checks+=1
rows=lambda tab,uid:[r for r in t[tab].values() if r.get('UnitId')==uid]
def users(tab,field,i):return sorted({r['UnitId'] for r in t[tab].values() if r.get(field)==i})
def copy_stats(tab,dst,src,extra=None):g.put(tab,dst,{**{k:copy.deepcopy(v) for k,v in t[tab][src].items() if k not in KEEP},**(extra or {})})
same=lambda tab,a_,b_:all(t[tab][a_].get(k)==v for k,v in t[tab][b_].items() if k not in KEEP)
N,T80=1264,158;ok(U[N]['HUDName']=='ZTZ-85-II' and U[T80]['HUDName']=='T-80BV','units')
opt=t['OptionsJson'][563];ok(opt['ArmorId']==2000420 and opt['MobilityId']==106 and opt['MainSensorId']==2 and opt['Turret0Id']==417,'T-80BV default variant')
ar=[r['ArmorId'] for r in rows('UnitArmorsJson',N)];mo=[r['MobilityId'] for r in rows('UnitPropulsionsJson',N)];ok(ar==[2018788] and users('UnitArmorsJson','ArmorId',2018788)==[N],'own armour')
ok(mo==[2018790] and users('UnitPropulsionsJson','MobilityId',2018790)==[N],'own mobility')
copy_stats('ArmorsJson',2018788,2000420);copy_stats('MobilityJson',2018790,106)
su=rows('SensorUnitsJson',N);ok(len(su)==1,'one sensor link');g.put('SensorUnitsJson',su[0]['Id'],{'SensorId':2})
ok(not rows('UnitAbilitiesJson',N),'no ability yet');g.add('UnitAbilitiesJson',rows('UnitAbilitiesJson',T80)[0],{'UnitId':N})
WMAP={2010021:334,2010031:7,2010035:97};AMAP={2010025:(246,13),2010027:(247,19),2010029:(541,6),2010033:(9,400),2010039:(70,60)}
for d,s in WMAP.items():ok(users('WeaponAmmunitionsJson','WeaponId',d)==[956,N],('weapon shared only with 956',d));copy_stats('WeaponsJson',d,s)
for d,(s,q) in AMAP.items():
    ok(users('WeaponAmmunitionsJson','AmmunitionId',d)==[956,N],('ammo shared only with 956',d));copy_stats('AmmunitionsJson',d,s)
    for r in WA.values():
        if r['AmmunitionId']==d and r.get('UnitId') in (956,N):g.put('WeaponAmmunitionsJson',r['Id'],{'Quantity':q})
g.put('Units',N,{'Cost':85,'OriginalCost':85,'Weight':45700})
for d,s in WMAP.items():ok(same('WeaponsJson',d,s),('weapon',d))
for d,(s,q) in AMAP.items():ok(same('AmmunitionsJson',d,s),('ammo',d))
ok(same('ArmorsJson',2018788,2000420) and same('MobilityJson',2018790,106),'armour/mobility')
rec['ztz85ii_t80bv']={'unit':N,'armor':2000420,'mobility':106,'sensor':2,'ability':2000199,'weapons':WMAP,'ammo':{str(k):v for k,v in AMAP.items()},'cost':[80,85],'weight':[45000,45700],'shared_with_hidden':956}
# PLAN SOF ZBD-86 removed
gone=[r['Id'] for r in SA.values() if r['UnitId'] in (1063,1259) and r['SpecializationId']==20];ok(sorted(gone)==[2015786,2018439],gone);nta=0
for r in list(TA.values()):
    if r.get('SpecializationAvailabilityId') in gone:g.remove('TransportAvailabilitiesJson',r['Id']);nta+=1
for rid in gone:g.remove('SpecializationAvailabilitiesJson',rid)
assign['assignments']['1063']=[17];assign['assignments'].pop('1259',None);g.put('Units',1259,{'DisplayInArmory':False})
for k in assign.get('carriers',{}):assign['carriers'][k]=[c for c in assign['carriers'][k] if c!=1259]
for k in ('shared_transports',):
    if str(1063) in assign.get(k,{}):assign[k][str(1063)]=[s for s in assign[k][str(1063)] if s!=20]
ok([r['SpecializationId'] for r in rows('SpecializationAvailabilitiesJson',1063)]==[17] and not rows('SpecializationAvailabilitiesJson',1259),'ZBD-86 PLAN removed')
rec['zbd86_plan_removed']={'cards':gone,'transport_links':nta}
# ZTL-11 to Motorized; VT-5 front HEAT 1000 (Osama 21:46)
r=[r for r in SA.values() if r['UnitId']==938];ok(len(r)==1 and r[0]['SpecializationId']==20,'ZTL-11 one card in PLAN')
g.put('SpecializationAvailabilitiesJson',r[0]['Id'],{'SpecializationId':21});assign['assignments']['938']=[21]
for k in assign.get('carriers',{}):pass
rec['ztl11_spec']=[20,21]
for uid,aid in ((1261,2018635),(1262,2018651)):
    ok([x['ArmorId'] for x in rows('UnitArmorsJson',uid)]==[aid] and users('UnitArmorsJson','ArmorId',aid)==[uid] and t['ArmorsJson'][aid]['HeatArmorFront']==700,('vt5 armour',uid))
    g.put('ArmorsJson',aid,{'HeatArmorFront':1000})
rec['vt5_heat_front']=[700,1000]
# models
MJ='UserData/FAModels/models.json';raw=z.read(MJ);models=json.loads(raw);before={}
ok(U[1076]['Name']=='PLA Catalogue ZBD-05' and 'PLA Catalogue ZBD-05' not in models,'zbd05 no model yet')
before['PLA Catalogue ZBD-05']=None;models['PLA Catalogue ZBD-05']={'file':'m_zbd86_static.fam','battle':'m_zbd86_lo_static.fam','align':False}
ok('scale' not in models['PLA QN-506'],'qn506');before['PLA QN-506']=dict(models['PLA QN-506']);models['PLA QN-506']['scale']=0.8
rec['models_json']={k:{'before':before[k],'after':models[k]} for k in before}
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=raw.isascii())+'\n').encode())
rec.update(version=V,base=PREV,base_sha256=BASE,request='Osama 13 Nov 21:37-21:45 PST',checks=checks,verified='data only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,json.dumps(rec['zbd86_plan_removed']))

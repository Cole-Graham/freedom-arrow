"""Freedom Arrow 0.8.0-dev.91 over exact 0.8.0-dev.90 (Osama 13 Nov 22:22-22:30 PST, thread 1571014792016171120).
- ZTZ-59, ZTZ-59D, ZTZ-59D1 invisible: their gun mount used the Toros "Rapira" turret model on the T-62M stand-in and the
  T-62M turret model sat on the MG mount. Now as the vanilla T-62M: gun mount = DLC3_T62M/DLC3_T62M_NoATGM, MG mount no model.
  (The seller model loads in the log; FAModels shows it only where the stand-in renders.) Theoretical fix, needs a look in game.
- ZBD-04 (non-A, 1075) removed (card and transport links, hidden).
- PTZ-89: painted-metal material (metallic 0.6, smoothness 0.4; was 0/0) and model 90%.
- J-5 to J-8 without afterburner: J-8D and J-7 move from the shared vanilla mobility rows 161/163 to own copies with
  IsAfterburner off (J-5 and J-6W already had none).
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.91';PREV='0.8.0-dev.90'
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
g=Graph(t,patches,native);U=t['Units'];T=t['TurretsJson'];SA=t['SpecializationAvailabilitiesJson'];TA=t['TransportAvailabilitiesJson'];MOB=t['MobilityJson'];rows=g.rows
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
def hud(i,n):ok(U[i]['HUDName']==n,(i,U[i]['HUDName'],n))
def users(tid):return sorted({r['UnitId'] for r in t['TurretUnitsJson'].values() if r['TurretId']==tid})
# ZTZ-59 turret models
for gun,mg,us in ((2010818,2010828,[1060]),(2010846,2010856,[1061,1260])):
    ok(T[gun]['ModelFileName']=='RU_Toros/RU_Toros_Rapira' and T[mg]['ModelFileName']=='DLC3_T62M/DLC3_T62M_NoATGM' and users(gun)==us and users(mg)==us,(gun,mg))
    g.put('TurretsJson',gun,{'ModelFileName':'DLC3_T62M/DLC3_T62M_NoATGM'});g.put('TurretsJson',mg,{'ModelFileName':None})
ok(T[1202]['ModelFileName']=='DLC3_T62M/DLC3_T62M_NoATGM','vanilla T-62M main turret model')
rec['ztz59_turret_models']={'gun':'DLC3_T62M/DLC3_T62M_NoATGM','mg':None,'was':['RU_Toros/RU_Toros_Rapira','DLC3_T62M/DLC3_T62M_NoATGM']}
# ZBD-04 removed
Z=1075;hud(Z,'ZBD-04');ids=[r['Id'] for r in SA.values() if r['UnitId']==Z];nta=0
for r in list(TA.values()):
    if r.get('SpecializationAvailabilityId') in ids or r.get('UnitId')==Z:g.remove('TransportAvailabilitiesJson',r['Id']);nta+=1
for rid in ids:g.remove('SpecializationAvailabilitiesJson',rid)
g.put('Units',Z,{'DisplayInArmory':False});assign['assignments'].pop(str(Z),None)
for k in assign.get('carriers',{}):assign['carriers'][k]=[c for c in assign['carriers'][k] if c!=Z]
ok(not [r for r in SA.values() if r['UnitId']==Z],'ZBD-04 removed');rec['zbd04_removed']={'cards':ids,'transport_links':nta}
# J-8D / J-7 afterburner off
cl={}
for uid,n in ((975,'J-8D'),(1092,'J-7')):
    hud(uid,n)
    for r in rows('UnitPropulsionsJson',uid):
        m=r['MobilityId']
        if MOB[m].get('IsAfterburner'):
            if m not in cl:cl[m]=g.add('MobilityJson',MOB[m],{'Name':f'PLA {MOB[m].get("Name")} no afterburner','IsAfterburner':False})
            g.put('UnitPropulsionsJson',r['Id'],{'MobilityId':cl[m]})
    ok(not any(MOB[r['MobilityId']].get('IsAfterburner') for r in rows('UnitPropulsionsJson',uid)),(n,'no afterburner'))
for uid in (1089,1091):ok(not any(MOB[r['MobilityId']].get('IsAfterburner') for r in rows('UnitPropulsionsJson',uid)),(uid,'already none'))
ok(MOB[161]['IsAfterburner'] and MOB[163]['IsAfterburner'],'vanilla rows unchanged');rec['afterburner_off']={'J-8D':975,'J-7':1092,'clones':cl}
# models
MJ='UserData/FAModels/models.json';raw=z.read(MJ);models=json.loads(raw);before={}
k='PLA PTZ-89';ok('scale' not in models[k],k);before[k]=dict(models[k]);models[k]['scale']=0.9
mats={}
for n in ('m_ptz89_static','m_ptz89_lo_static'):
    p_='UserData/FAModels/'+n+'.mat.json'
    if p_ not in z.namelist():continue
    mj=json.loads(z.read(p_))
    for v in mj.values():
        if not v.get('clearGlass') and not v.get('cockpitDonor'):v.update(metallic=0.6,smoothness=0.4)
    mats[p_]=mj
ok(len(mats)==2,sorted(mats))
gdir=ROOT/f'tools/pla-specs/{V}-mats';gdir.mkdir(exist_ok=True);files={}
for p_,mj in mats.items():f=gdir/p_.split('/')[-1];f.write_text(json.dumps(mj,indent=1)+'\n');files[p_]=str(f)
rec['models_json']={k:{'before':before[k],'after':models[k]}};rec['ptz89_material']={'metallic':[0.0,0.6],'smoothness':[0.0,0.4]}
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=raw.isascii())+'\n').encode())
(ROOT/f'tools/pla-specs/{V}-assets.txt').write_text(''.join(f'{k}={v}\n' for k,v in sorted(files.items())))
rec.update(version=V,base=PREV,base_sha256=BASE,request='Osama 13 Nov 22:22-22:30 PST',checks=checks,verified='data only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,rec['afterburner_off'],rec['zbd04_removed'])

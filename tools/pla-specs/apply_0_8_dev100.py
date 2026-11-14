"""Freedom Arrow 0.8.0-dev.100 over exact 0.8.0-dev.99 (Osama 14 Nov 00:4x-01:0x PST, thread 1571014792016171120).
- ZFB-05 (954): a transport, not its own card. It is on the vanilla BPM-97 model, and the vanilla BPM-97 transport has
  10 seats, category 2; ZFB-05 had 4 seats (recon card, category 0), which fits no Motorized squad (the base game never links
  a squad larger than the seats). Now 10 seats, category 2, offered to the same Motorized infantry as the ZSL-92.
- Z-19 (all five cards): stealth 1.75 = raw 0.571 (the vanilla 1.75 tier; was 0.8 = 1.25).
- J-10C and J-10S: no ECM or flare ability at all; they get the J-10CE default ability (ECM Plane 10 Default FA 0.85).
- Y-8: its flap/elevator parts (Y8_wings_L1/R1) and two engine parts lost their rotation in the FBX conversion and stood
  upright; those parts are taken from the seller OBJ (world-space) instead (m_y8b). The Y-8 card uses the C-130 Harvest
  Hawk as its base unit, which faces the other way from the IL-76 that KJ-500/KQ-200 use, so the model gets yaw 180.
- KQ-200: the seller's motion-blur propeller discs (Cylinder010-013) removed; the real six-blade props are kept (m_kq200p).
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.100';PREV='0.8.0-dev.99'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--stage',type=Path,required=True);a=p.parse_args()
base=REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];SA=t['SpecializationAvailabilitiesJson'];TA=t['TransportAvailabilitiesJson'];UA=t['UnitAbilitiesJson'];AB=t['AbilitiesJson'];rows=g.rows
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
def hud(u,h):ok(U[u]['HUDName']==h,(u,h,U[u]['HUDName']))
# ZFB-05 transport
from collections import Counter
sq=Counter(r['UnitId'] for r in t['SquadMembersJson'].values())
hud(954,'ZFB-05');ok(U[954]['ModelFileName']=='DLC3_BPM97' and U[219]['ModelFileName']=='DLC3_BPM97' and U[219]['InfantrySlots']==10 and U[219]['CategoryType']==2,'vanilla BPM-97')
own=rows('SpecializationAvailabilitiesJson',954);ok([r['SpecializationId'] for r in own]==[21] and not [r for r in TA.values() if r['UnitId']==954],'ZFB-05 card only')
for r in own:g.remove('SpecializationAvailabilitiesJson',r['Id'])
assign['assignments'].pop('954',None);g.put('Units',954,{'InfantrySlots':10,'CategoryType':2})
zsl=[r for r in TA.values() if r['UnitId']==1079];ok(len(zsl)==10 and all(SA[r['SpecializationAvailabilityId']]['SpecializationId']==21 for r in zsl),'ZSL-92 links')
ok(max(sq[SA[r['SpecializationAvailabilityId']]['UnitId']] for r in zsl)<=10,'squads fit 10 seats')
for r in zsl:g.add('TransportAvailabilitiesJson',r,{'UnitId':954})
rec['zfb05']={'card_removed':21,'seats':[4,10],'category':[0,2],'transport_links':len(zsl),'passengers':sorted(U[SA[r['SpecializationAvailabilityId']]['UnitId']]['HUDName'] for r in zsl)}
# Z-19 stealth 1.75
for u in (1103,1132,1134,1236,1237):
    ok(U[u]['HUDName'].startswith('Z-19') and U[u]['Stealth']==0.8,(u,'Z-19 stealth'));g.put('Units',u,{'Stealth':0.571,'CurrentStealth':0.571})
rec['z19_stealth']={'raw':[0.8,0.571],'shown':[1.25,1.75]}
# J-10C / J-10S ECM and flares
ce=[r for r in UA.values() if r['UnitId']==1087];ok(len(ce)==1 and ce[0]['AbilityId']==2006990 and AB[2006990]['IsDefault'],'J-10CE ability')
for u,h in ((917,'J-10C'),(955,'J-10S')):
    hud(u,h);ok(not [r for r in UA.values() if r['UnitId']==u],(h,'no ability yet'));g.add('UnitAbilitiesJson',ce[0],{'UnitId':u})
rec['j10_ecm']={'ability':2006990,'name':AB[2006990]['Name'],'units':[917,955]}
# Y-8 / KQ-200 models
MJ='UserData/FAModels/models.json';raw=z.read(MJ);models=json.loads(raw);before={}
for k,was,new,extra in (('PLA Catalogue Y-8 family — seller package','m_y8','m_y8b',{'yaw':180}),('PLA Catalogue KQ-200','m_kq200','m_kq200p',{})):
    ok(models[k]=={'file':was+'_static.fam','battle':was+'_lo_static.fam','align':False},(k,'entry'));before[k]=dict(models[k])
    models[k]={'file':new+'_static.fam','battle':new+'_lo_static.fam','align':False,**extra}
ok(U[1102]['ModelFileName']=='US_C-130_Harvest_Hawk' and U[1097]['ModelFileName']=='RU_IL76MD','base units')
rec['models_json']={k:{'before':before[k],'after':models[k]} for k in before}
files={}
for f in sorted(a.stage.iterdir()):
    if f.suffix in ('.fam','.json','.png') and f.name.split('_static')[0].replace('_lo','') in ('m_y8b','m_kq200p'):files['UserData/FAModels/'+f.name]=str(f)
ok(len([k for k in files if k.endswith('.fam')])==4,sorted(files));ok(not any(k in z.namelist() for k in files),'no overwrite')
for k in [k for k in files if k.endswith('.mat.json')]:
    for key in json.loads(Path(files[k]).read_text()):
        tex=key.split('|')[0]
        if tex:ok('UserData/FAModels/'+tex in files,('texture',tex))
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=raw.isascii())+'\n').encode())
(ROOT/f'tools/pla-specs/{V}-assets.txt').write_text(''.join(f'{k}={v}\n' for k,v in sorted(files.items())))
rec.update(version=V,base=PREV,base_sha256=BASE,request='Osama 14 Nov 00:4x-01:0x PST',checks=checks,verified='data and file checks; models rendered offline')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,'files',len(files))

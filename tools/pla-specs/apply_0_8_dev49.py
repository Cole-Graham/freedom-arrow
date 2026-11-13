"""Freedom Arrow 0.8.0-dev.N batch 1 of Osama's 13 Nov 14:36 PST list (thread 1569806740139282476).
Roster: PHL-11, Shaanxi Troop Truck, VP4, PGZ-04/PGZ-04A, WZ-701, ZSD-90, PHL-81 removed (hidden, cards and transport links
deleted); Lynx ATV keeps VP4's Air Force availability and every squad VP4 carried.
Loadouts: FH-97A strike/SEAD packages lose their PL-15 air-to-air missiles; J-5, J-6W, J-7, J-8D (and hidden J-7E/G, J-8II/F)
lose ECM; new Heavy strike +40: J-5 and J-7 2x 1000 kg bomb, J-6W 2x 500 kg bomb, J-8D 4x 1000 kg bomb.
Names/icons: Light Riflemen 轻步兵, Weapons Squad 火力班; ABZ-13 uses the TOW-2BB (BLAAM) icon; GAM-102LR Team uses the Spike icon.
Models (models.json): PLZ-07/PLZ-07B on the PLZ-89 model; Z-10 x0.8; Z-8L turned 180; ZSD-89A x1.2; Lynx ATV keeps the
M1301 ISV and hides its seated US soldiers (FAModels 0.3.18 'hide'); ZTQ-15/ZTZ-99/ZBL-191/ZTZ-100 seller camo unrigged
(no turret bone), ZTZ-100 opaque; HQ-17A front radar 0.35 m forward, 0.3 m lower.
"""
import argparse,copy,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path('/home/sam/tars/work/ba-dev/replicas/codex/work/pla-hotfix39-worktree');REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
p=argparse.ArgumentParser();p.add_argument('--version',required=True);p.add_argument('--prev',required=True);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--stage',type=Path,required=True);a=p.parse_args()
V,PREV=a.version,a.prev
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256'];base=REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base)
t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];SA=t['SpecializationAvailabilitiesJson'];TA=t['TransportAvailabilitiesJson'];O=t['OptionsJson'];M=t['ModificationsJson']
T=t['TurretsJson'];TW=t['TurretWeaponsJson'];TU=t['TurretUnitsJson'];W=t['WeaponsJson'];WA=t['WeaponAmmunitionsJson'];A=t['AmmunitionsJson'];UA=t['UnitAbilitiesJson'];AB=t['AbilitiesJson']
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN))
checks=0
def ok(c,l):
    global checks
    assert c,l;checks+=1
rec={}
def hud(i,n):assert U[i]['HUDName']==n,(i,U[i]['HUDName'],n)
# ---------- removals ----------
REM={922:'PHL-11',1231:'Shaanxi Troop Truck',1070:'VP4',932:'PGZ-04A',1050:'PGZ-04',957:'WZ-701',959:'ZSD-90',963:'PHL-81'}
for i,n in REM.items():hud(i,n)
VP4=1070;LYNX=1228;hud(LYNX,'Lynx ATV')
vp4_sa=[r for r in SA.values() if r['UnitId']==VP4];lynx_sa=[r for r in SA.values() if r['UnitId']==LYNX]
vp4_carried={r['SpecializationAvailabilityId'] for r in TA.values() if r['UnitId']==VP4}
lynx_carried={r['SpecializationAvailabilityId'] for r in TA.values() if r['UnitId']==LYNX}
added=[]
for sid in sorted(vp4_carried-lynx_carried):
    src=next(r for r in TA.values() if r['UnitId']==VP4 and r['SpecializationAvailabilityId']==sid);added.append(g.add('TransportAvailabilitiesJson',src,{'UnitId':LYNX}))
for vs in vp4_sa:
    ls=[r for r in lynx_sa if r['SpecializationId']==vs['SpecializationId']]
    if ls:g.put('SpecializationAvailabilitiesJson',ls[0]['Id'],{k:vs[k] for k in vs if k.startswith('MaxAvailability')})
    else:g.add('SpecializationAvailabilitiesJson',vs,{'UnitId':LYNX})
rec['lynx']={'vp4_specs':[r['SpecializationId'] for r in vp4_sa],'added_transport_links':len(added)}
removed={}
for i,n in REM.items():
    g.put('Units',i,{'DisplayInArmory':False});assign['assignments'].pop(str(i),None)
    ids={r['Id'] for r in SA.values() if r['UnitId']==i};nta=0
    for r in list(TA.values()):
        if r['SpecializationAvailabilityId'] in ids or r['UnitId']==i:g.remove('TransportAvailabilitiesJson',r['Id']);nta+=1
    for rid in ids:g.remove('SpecializationAvailabilitiesJson',rid)
    for k in assign['carriers']:assign['carriers'][k]=[c for c in assign['carriers'][k] if c!=i]
    removed[n]={'cards':len(ids),'transport_links':nta}
rec['removed']=removed
for i in REM:ok(not U[i]['DisplayInArmory'] and not [r for r in SA.values() if r['UnitId']==i],('removed',i))
ok(vp4_carried<= {r['SpecializationAvailabilityId'] for r in TA.values() if r['UnitId']==LYNX} or not vp4_carried,'lynx carries vp4 squads')
# ---------- FH-97A strike packages without air-to-air ----------
FH=1253;hud(FH,'FH-97A');mids={m['Id'] for m in M.values() if m['UnitId']==FH}
def newturret(src_tid,keep_weapon,name):
    tid=g.add('TurretsJson',T[src_tid],{'Name':name});tw=next(r for r in TW.values() if r['TurretId']==src_tid and r['WeaponId']==keep_weapon)
    g.add('TurretWeaponsJson',tw,{'TurretId':tid,'Order':0});return tid
lt2=next(r['WeaponId'] for r in TW.values() if r['TurretId']==2018514 and 'LT-2' in W[r['WeaponId']]['Name'])
ls6=next(r['WeaponId'] for r in TW.values() if r['TurretId']==2018481 and 'LS-6' in W[r['WeaponId']]['Name'])
T_LT2=newturret(2018514,lt2,'PLA air pylon LT-2 x2');T_LS6=newturret(2018481,ls6,'PLA air pylon LS-6 1000kg x2')
REPL={2018514:T_LT2,2018481:T_LS6,2018548:2018543,2018488:160}
fhopts=[o for o in O.values() if o['ModificationId'] in mids];changed=[]
for o in fhopts:
    if o['UIName'] in ('Light strike (2x LS-6 500kg)','Light strike (LS-6 1000kg)','Light SEAD'):
        upd={k:REPL[o[k]] for k in o if k.startswith('Turret') and k.endswith('Id') and o[k] in REPL};g.put('OptionsJson',o['Id'],upd);changed.append(o['UIName'])
ok(len(changed)==3,('fh97a options',changed))
used={o[k] for o in fhopts for k in o if k.startswith('Turret') and k.endswith('Id') and o[k]}
for tid in (T_LT2,T_LS6):g.add('TurretUnitsJson',next(r for r in TU.values() if r['UnitId']==FH),{'TurretId':tid,'UnitId':FH})
for r in [r for r in TU.values() if r['UnitId']==FH and r['TurretId'] not in used and r['TurretId']!=160]:g.remove('TurretUnitsJson',r['Id'])
AA=('PL-8','PL-9','PL-10','PL-12','PL-15','PL-16','PL-5')
for o in fhopts:
    if 'strike' in o['UIName'].lower() or 'SEAD' in o['UIName']:
        for k in o:
            if k.startswith('Turret') and k.endswith('Id') and o[k] and o[k]!=160:
                ok(not any(any(x in W[r['WeaponId']]['Name'] for x in AA) for r in TW.values() if r['TurretId']==o[k]),('A2A left',o['UIName'],o[k]))
rec['fh97a']={'options':changed,'new_turrets':{'LT-2 x2':T_LT2,'LS-6 1000kg x2':T_LS6}}
# ---------- J-5/6/7/8: no ECM, heavy strike ----------
JETS={1089:'J-5',1091:'J-6W',1092:'J-7',975:'J-8D',1093:'J-7E / J-7G',1094:'J-8II / J-8F'}
ecm=[]
for i,n in JETS.items():
    hud(i,n)
    for r in [r for r in UA.values() if r['UnitId']==i and 'ECM' in AB[r['AbilityId']]['Name']]:g.remove('UnitAbilitiesJson',r['Id']);ecm.append((n,AB[r['AbilityId']]['Name']))
for i in JETS:ok(not [r for r in UA.values() if r['UnitId']==i and 'ECM' in AB[r['AbilityId']]['Name']],('ecm',i))
mk84=next(a_ for a_ in A.values() if a_.get('Name')=='Bomb 907kg Mk84')
AM1000=g.add('AmmunitionsJson',mk84,{'Name':'PLA air 1000 kg bomb','HUDName':'1000 kg bomb'})
W1000=g.add('WeaponsJson',W[2016616],{'Name':'PLA air 1000 kg bomb x1','HUDName':'1000 kg bomb','HUDIcon':W[373]['HUDIcon']})
T1000=g.add('TurretsJson',T[2016615],{'Name':'PLA air pylon 1000 kg bomb x1','ModelFileName':T[529]['ModelFileName']})
g.add('TurretWeaponsJson',next(r for r in TW.values() if r['TurretId']==2016615),{'TurretId':T1000,'WeaponId':W1000})
HEAVY={1089:(T1000,W1000,AM1000,2,'Heavy strike (2x 1000 kg bomb)'),1092:(T1000,W1000,AM1000,2,'Heavy strike (2x 1000 kg bomb)'),
       975:(T1000,W1000,AM1000,4,'Heavy strike (4x 1000 kg bomb)'),1091:(2016615,2016616,next(x['AmmunitionId'] for x in WA.values() if x['WeaponId']==2016616),2,'Heavy strike (2x 500 kg bomb)')}
heavy={}
for i,(tid,wid,am,n,ui) in HEAVY.items():
    mod=next(m for m in M.values() if m['UnitId']==i and m['Type']==3);opts=[o for o in O.values() if o['ModificationId']==mod['Id']]
    ex=[o for o in opts if o['UIName'].startswith('Heavy strike')]
    src=ex[0] if ex else next(o for o in opts if 'strike' in o['UIName'].lower())
    upd={'UIName':ui,'Cost':40,'OptionPicture':'FAB_500'}
    if not ex:upd.update({'IsDefault':False,'Name':f"{src['Name']} heavy",'Order':max(o['Order'] for o in opts)+1})
    for s in range(1,7):upd[f'Turret{s}Id']=tid if s<=n else (src[f'Turret{s}Id'] if i==975 and s>=5 else 160)
    oid=g.put('OptionsJson',src['Id'],upd) if ex else g.add('OptionsJson',src,upd)
    if not [r for r in TU.values() if r['UnitId']==i and r['TurretId']==tid]:g.add('TurretUnitsJson',next(r for r in TU.values() if r['UnitId']==i),{'TurretId':tid,'UnitId':i})
    if not [x for x in WA.values() if x['UnitId']==i and x['WeaponId']==wid]:g.add('WeaponAmmunitionsJson',next(x for x in WA.values() if x['WeaponId']==2016616),{'UnitId':i,'WeaponId':wid,'AmmunitionId':am,'Quantity':1,'Order':0})
    heavy[JETS[i]]={'option':oid,'loadout':ui,'cost':40}
    ok(O[oid]['Cost']==40 and O[oid]['Turret1Id']==tid,('heavy',i))
rec['jets']={'ecm_removed':ecm,'heavy_strike':heavy}
# ---------- names and icons ----------
hud(1205,'Light Riflemen');hud(1199,'Weapons Squad');g.put('Units',1205,{'HUDName':'Light Riflemen 轻步兵'});g.put('Units',1199,{'HUDName':'Weapons Squad 火力班'})
ok(W[2014659]['Name']=='PLA ZBD-251 ABZ-13 anti-personnel','abz13');g.put('WeaponsJson',2014659,{'HUDIcon':W[613]['HUDIcon']})
hud(1221,'GAM-102LR Team');g.put('Units',1221,{'ThumbnailFileName':U[521]['ThumbnailFileName']})
rec['names_icons']={'1205':U[1205]['HUDName'],'1199':U[1199]['HUDName'],'ABZ-13 HUDIcon':W[2014659]['HUDIcon'],'GAM-102LR thumbnail':U[1221]['ThumbnailFileName']}
# ---------- models.json ----------
MJ='UserData/FAModels/models.json';models=json.loads(z.read(MJ));mb={}
def setm(k,**kv):
    ok(k in models or kv.get('file'),('model key',k));mb[k]=copy.deepcopy(models.get(k));models.setdefault(k,{}).update(kv)
for k in ('PLA PLZ-07B','PLA Catalogue PLZ-07'):setm(k,file='m_plz89_static.fam',battle='m_plz89_lo_static.fam',align=False)
for k in ('PLA Z-10','PLA Air Force Z-10','PLA Recon Z-10'):setm(k,scale=0.8)
setm('PLA Catalogue Z-8L',yaw=180.0)
setm('PLA Catalogue Type 89A',scale=1.2)
models['PLA Lynx ATV']={'file':'','battle':'','align':False,'hide':'(?i)soldier|crew|driver|gunner|passenger|human|pilot|infantry|_char'};mb['PLA Lynx ATV']=None
rec['models_json']={k:{'before':mb[k],'after':models[k]} for k in mb}
files=sorted(x.name for x in a.stage.iterdir())
for f in files:ok(f'UserData/FAModels/{f}' in z.namelist(),('replaces an existing file',f))
rec.update({'version':V,'base':PREV,'base_sha256':BASE,'request':'Osama 13 Nov 14:36 PST model/roster list, batch 1','replaced_files':files,'checks':checks})
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign)
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=z.read(MJ).isascii())+'\n').encode())
save(f'UserData/FreedomArrow/pla-{V}.json',rec)
(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,json.dumps({k:rec[k] for k in ('removed','lynx','fh97a','jets')},ensure_ascii=False)[:1500])

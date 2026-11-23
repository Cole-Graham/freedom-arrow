"""Freedom Arrow 0.8.0-dev.101 over exact 0.8.0-dev.100 (Osama 14 Nov 00:3x PST, thread 1571014792016171120). Local build;
not pushed until Osama says so.
- J-36 Heavy CAP: 4x PL-17, 4x PL-16 and 4x PL-21 (dev.76 had dropped the PL-21s). Slots 0-1 PL-16 x2 pylons, slot 2 PL-17 x4,
  slots 3-6 PL-21 x1 (slots 0-6 are pylons the dev.76 Heavy CAP and the other J-36 loadouts already use). Price unchanged.
- Shaanxi HMV3 Cargo (1247) carries 15000 supply. Game code: the shop caps the supply a truck loads at Units.HeavyLift
  (OrderedUnit.AddSupply 0x371A50 -> Units.get_HeavyLift 0x2A3670 = CurrentMobility.HeavyLiftWeight). Its own mobility is the
  PLS 'Wheels LVSR' (HeavyLiftWeight 15000), but its two armory options, copied from the HEMTT, switched it to HEMTT mobility
  108 (9000, default) or 231 (4500). The options now keep the unit's mobility (MobilityId 0, as on the vanilla PLS), so both
  show and load 15000. The Build66 stand-in (a 15000-point resupply ability, a separate pool on top of the cargo) is removed.
- ZTZ-96A and ZTZ-96B models swapped (they were inverted); ZTZ-96B in the seller's green digital camo.
- Helicopter glass from similar vanilla helicopters (FAModels 0.3.24): Z-20 family UH-60M, Z-19 AH-1Z, Z-10 AH-64E,
  Z-9/Z-9WA UH-1Y, Z-11WB OH-58 Kiowa. PLAN SOF Z-19 renamed Z-19G (and its recon card Z-19G Recon).
- Type 59D / ZTZ-59D1: ZTZ-99A-style textures (PLA digital woodland hull, ZTZ-99A tracks), m_ztz59d3.
- Mengshi Recon on the CSK-131 (Mengshi) model, darker (closed doors, glass); the seller model could not be fixed.
- ZBD-05: BMP-2 style loadouts, HJ-8E ATGM (+10, default) or no ATGM; base 35, so the default stays 45.
- CTL-181 NLOS 2 cards. Blood Wolves CH-901 range 1400 m, 75 pts.
- Motorized AT Troopers: 4 PF-89 launchers (3 more riflemen carry one).
- Infantry: backpacks on every non-conscript PLA body (SF types and regular Type 21). The goggle bodies keep their 901 plate carrier
  (the heavy EOD vest added first was removed, Osama 02:07).
- PLARF shown as 'PLARF Rocket Force/Reservist'.
- PLAN SOF spec points: Air 1250 (was 1500), Helicopters 1000 (was 750).
- Z-19 (all cards): no cargo (own copy of the AS365 mobility with HeavyLiftWeight 0). ZBD-20 Recon removed. DF-15 and YJ-18 models 20% smaller.
- CSK-131 (m_csk4c): rebuilt without the face-level glass cut, which had made whole side panels clear (missing); windows
  painted into the texture as dark glossy glass. CSK-181 (6x6): windows dark glossy instead of the wavy F-16 canopy,
  lamp lenses flat clear glass.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.8.0-dev.101';PREV='0.8.0-dev.100'
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
g=Graph(t,patches,native);U=t['Units'];O=t['OptionsJson'];M=t['ModificationsJson'];TU=t['TurretUnitsJson'];TW=t['TurretWeaponsJson'];W=t['WeaponsJson']
WA=t['WeaponAmmunitionsJson'];MB=t['MobilityJson'];UP=t['UnitPropulsionsJson'];UA=t['UnitAbilitiesJson'];AB=t['AbilitiesJson'];checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
def slots(o):return [o.get(f'Turret{i}Id',0) for i in range(21)]
def load(uid,o):
    c={}
    for tid in slots(o):
        for r in TW.values():
            if tid and r['TurretId']==tid:
                n=W[r['WeaponId']]['HUDName'];q=sum(x['Quantity'] for x in WA.values() if x['UnitId']==uid and x['WeaponId']==r['WeaponId']);c[n]=c.get(n,0)+q
    return c
# ---------- J-36 Heavy CAP ----------
J36,HC=929,24393;ok(U[J36]['HUDName']=='J-36','J-36');o=O[HC]
ok(o['UIName']=='Heavy CAP (4x PL-17, 4x PL-16)' and o['IsDefault'] and slots(o)[:8]==[2017956,2017956,2016481,2017956,2017956,160,160,160],'dev.76 Heavy CAP')
P16x2,P17x4,P21=2018021,2016481,2016475
for tid,n in ((P16x2,['PL-16']),(P17x4,['PL-17']),(P21,['PL-21'])):ok([W[r['WeaponId']]['HUDName'] for r in TW.values() if r['TurretId']==tid]==n,(tid,n))
for tid in (P16x2,P21):
    wid=[r['WeaponId'] for r in TW.values() if r['TurretId']==tid][0];ok(any(x['UnitId']==J36 and x['WeaponId']==wid for x in WA.values()),('ammo row',tid))
    if not any(r['UnitId']==J36 and r['TurretId']==tid for r in TU.values()):g.add('TurretUnitsJson',next(r for r in TU.values() if r['UnitId']==J36 and r['TurretId']==P17x4),{'TurretId':tid})
new=[P16x2,P16x2,P17x4,P21,P21,P21,P21,160]
g.put('OptionsJson',HC,{**{f'Turret{i}Id':(new[i] if i<len(new) else 0) for i in range(21)},'UIName':'Heavy CAP (4x PL-17, 4x PL-16, 4x PL-21)','Name':'PLA loadout J-36 Heavy CAP 4x PL-17 4x PL-16 4x PL-21'})
ld=load(J36,O[HC]);ok(ld=={'PL-16':4,'PL-17':4,'PL-21':4},('J-36 Heavy CAP load',ld))
rec['j36_heavy_cap']={'option':HC,'load':ld,'slots':new,'cost':O[HC]['Cost']}
# ---------- Shaanxi HMV3 Cargo 15000 supply ----------
H=1247;ok(U[H]['HUDName']=='Shaanxi HMV3 Cargo','HMV3 Cargo');up=[r for r in UP.values() if r['UnitId']==H]
ok(len(up)==1 and up[0]['MobilityId']==65 and MB[65]['HeavyLiftWeight']==15000,'LVSR mobility 15000')
arm=[m for m in M.values() if m.get('UnitId')==H and 'Armory' in str(m.get('Name'))];ok(len(arm)==1,'armory mod')
ao=[x for x in O.values() if x['ModificationId']==arm[0]['Id']];ok(sorted((x['Id'],x['MobilityId']) for x in ao)==[(24379,231),(24380,108)],'HEMTT mobility options')
for x in ao:g.put('OptionsJson',x['Id'],{'MobilityId':0})
pls=[x for x in O.values() if M.get(x['ModificationId'],{}).get('UnitId')==241 and 'Armory' in str(M[x['ModificationId']].get('Name'))];ok(pls and all(x['MobilityId']==0 for x in pls),'vanilla PLS options keep mobility')
ab=[r for r in UA.values() if r['UnitId']==H];ok([r['AbilityId'] for r in ab]==[2018324] and AB[2018324]['ResupplyPoints']==15000,'Build66 resupply ability')
ok(not [r for r in UA.values() if r['AbilityId']==2018324 and r['UnitId']!=H],'ability used only by HMV3 Cargo')
g.remove('UnitAbilitiesJson',ab[0]['Id']);g.remove('AbilitiesJson',2018324)
rec['hmv3_cargo']={'unit':H,'heavy_lift':15000,'options_mobility':{24379:[231,0],24380:[108,0]},'was':{'default':MB[108]['HeavyLiftWeight'],'armored':MB[231]['HeavyLiftWeight']},'removed_ability':2018324}
SA=t['SpecializationAvailabilitiesJson'];TA=t['TransportAvailabilitiesJson']
# ---------- Z-19: no cargo (Osama 00:5x) ----------
# The five Z-19 cards share the vanilla 'Heli AS365' mobility (258), whose HeavyLiftWeight 1500 is the cargo the card shows
# (same field as truck supply). They get their own copy with 0, as the vanilla AH-1Z has.
z19=(1103,1132,1134,1236,1237);ups=[r for r in UP.values() if r['UnitId'] in z19];ok(len(ups)==5 and {r['MobilityId'] for r in ups}=={258} and MB[258]['HeavyLiftWeight']==1500,'Z-19 mobility')
mid=g.add('MobilityJson',MB[258],{'Name':'PLA Heli Z-19 no cargo','HeavyLiftWeight':0})
for r in ups:g.put('UnitPropulsionsJson',r['Id'],{'MobilityId':mid})
ok(not [o for o in O.values() if M.get(o['ModificationId'],{}).get('UnitId') in z19 and o.get('MobilityId')],'no Z-19 option mobility')
rec['z19_no_cargo']={'mobility':mid,'copy_of':258,'heavy_lift':[1500,0],'units':list(z19)}
# ---------- PLAN SOF spec points (Osama 01:0x): Air 1250, Helicopters 1000 ----------
S=t['SpecializationsJson'];ok(S[20]['Name']=='PLA PLAN Navy/SOF' and (S[20]['AirPoints'],S[20]['HelicoptersPoints'])==(1500,750),('PLAN SOF points',S[20].get('AirPoints'),S[20].get('HelicoptersPoints')))
g.put('SpecializationsJson',20,{'AirPoints':1250,'HelicoptersPoints':1000});rec['plan_sof_points']={'AirPoints':[1500,1250],'HelicoptersPoints':[750,1000]}
# ---------- Motorized AT Troopers: 4 PF-89 (Osama 01:1x) ----------
# Vanilla counts a disposable launcher per carrier (e.g. Troopers AT: 4 AT4 carriers, Quantity 1), so 3 more riflemen carry it.
SM=t['SquadMembersJson'];WAx=t['WeaponAmmunitionsJson'];PF=2011887;ok(U[1198]['HUDName']=='AT Troopers 反坦克组','AT Troopers')
mem=sorted((r for r in SM.values() if r['UnitId']==1198),key=lambda r:r['Id']);ok([r.get('SpecialWeaponId') for r in mem].count(PF)==1,'one PF-89 now')
free=[r for r in mem if not r.get('SpecialWeaponId') and r['PrimaryWeaponId']==2003998];ok(len(free)>=3,'three plain riflemen')
for r in free[:3]:g.put('SquadMembersJson',r['Id'],{'SpecialWeaponId':PF})
ok([r['Quantity'] for r in WAx.values() if r['UnitId']==1198 and r['WeaponId']==PF]==[1],'PF-89 one per carrier')
ok([r.get('SpecialWeaponId') for r in SM.values() if r['UnitId']==1198].count(PF)==4,'4 PF-89');rec['at_troopers_pf89']={'unit':1198,'carriers':4,'members':[r['Id'] for r in free[:3]]}
# ---------- CTL-181 NLOS 2 cards (Osama 01:2x) ----------
ok(U[1054]['HUDName']=='CTL-181 NLOS','CTL-181');rs=[r for r in SA.values() if r['UnitId']==1054];ok(rs,'CTL-181 card')
for r in rs:g.put('SpecializationAvailabilitiesJson',r['Id'],{'MaxAvailabilityXp0':2})
rec['ctl181_availability']=[[r['SpecializationId'],2] for r in rs]
# ---------- Blood Wolves CH-901 1400 m (Osama 01:3x): GroundRange 900 -> 700 world (shown x2) ----------
A=t['AmmunitionsJson'];ok(A[2018448]['HUDName']=='CH-901' and A[2018448]['GroundRange']==900.0,'CH-901 range')
ok(sorted({r['UnitId'] for r in WAx.values() if r['AmmunitionId']==2018448})==[1183],'CH-901 only Blood Wolves');g.put('AmmunitionsJson',2018448,{'GroundRange':700.0})
rec['ch901_range']={'ammo':2018448,'world':[900.0,700.0],'shown_m':[1800,1400]}
# ---------- Blood Wolves 75 pts (Osama 01:37) ----------
ok(U[1183]['HUDName']=='Blood Wolves 血狼','Blood Wolves');rec['blood_wolves_cost']=[U[1183]['Cost'],75];g.put('Units',1183,{'Cost':75})
# ---------- ZBD-05 like the BMP-2 (Osama 01:22): loadouts with and without the ATGM, ATGM +10 ----------
# Base 45 -> 35; options replace the main mount (slot 0) like the vanilla BMP-2 'Weapons' package: HJ-8E (+10, default, so the
# default card still costs 45) or no ATGM (30 mm and coax only, 35).
T_=t['TurretsJson'];TU_=t['TurretUnitsJson'];TW_=t['TurretWeaponsJson'];Z5=1076
ok(U[Z5]['HUDName']=='ZBD-05' and U[Z5]['Cost']==45 and not [m for m in M.values() if m.get('UnitId')==Z5],'ZBD-05 no loadouts yet')
tw=[r for r in TW_.values() if r['TurretId']==2011194];ok(sorted(r['WeaponId'] for r in tw)==[2011193,2011207] and W[2011207]['HUDName']=='HJ-8E','ZBD-05 mount 0')
nt=g.add('TurretsJson',T_[2011194],{'Name':'PLA ZBD-05 mount 0 no ATGM'})
g.add('TurretWeaponsJson',[r for r in tw if r['WeaponId']==2011193][0],{'TurretId':nt})
g.add('TurretUnitsJson',next(r for r in TU_.values() if r['UnitId']==Z5 and r['TurretId']==2011194),{'TurretId':nt})
mid=g.add('ModificationsJson',M[2018888],{'UnitId':Z5,'Name':'PLA ZBD-05 ATGM'})
base={f'Turret{i}Id':0 for i in range(21)}
oa=g.add('OptionsJson',O[31054],{**base,'Turret0Id':2011194,'ModificationId':mid,'Name':'PLA ZBD-05 HJ-8E','UIName':'HJ-8E ATGM','Cost':10,'IsDefault':True,'Order':0,'ArmorId':0})
on=g.add('OptionsJson',O[31053],{**base,'Turret0Id':nt,'ModificationId':mid,'Name':'PLA ZBD-05 no ATGM','UIName':'No ATGM','Cost':0,'IsDefault':False,'Order':1,'ArmorId':0})
ok(max(oa,on)<=32767,'option ids 16-bit');g.put('Units',Z5,{'Cost':35})
rec['zbd05_atgm_option']={'unit':Z5,'cost':[45,35],'options':{'HJ-8E ATGM (default)':[oa,10],'No ATGM':[on,0]},'no_atgm_turret':nt}
# ---------- PLARF display name (Osama 02:3x): 'PLARF Rocket Force/Reservist' (UIName only; Name stays the internal key) ----------
ok(S[19]['UIName']=='PLARF Rocket/Reservist','PLARF UIName');g.put('SpecializationsJson',19,{'UIName':'PLARF Rocket Force/Reservist'});rec['plarf_uiname']=['PLARF Rocket/Reservist','PLARF Rocket Force/Reservist']
# ---------- ZBD-20 Recon removed ----------
ok(U[1256]['HUDName']=='ZBD-20 Recon','ZBD-20 Recon');rs=[r for r in SA.values() if r['UnitId']==1256];ok([r['SpecializationId'] for r in rs]==[18] and not [r for r in TA.values() if r['UnitId']==1256],'ZBD-20 Recon card only')
for r in rs:g.remove('SpecializationAvailabilitiesJson',r['Id'])
g.put('Units',1256,{'DisplayInArmory':False})
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));assign['assignments'].pop('1256',None);rec['removed']=[[1256,'ZBD-20 Recon']]
# ---------- models ----------
MJ='UserData/FAModels/models.json';raw=z.read(MJ);models=json.loads(raw);before={}
for k in ('PLA CSK-181 4x4','PLA CSK-131 Transport','PLA CSK-131 Mengshi'):
    ok(models[k]=={'file':'m_csk4b_static.fam','battle':'m_csk4b_lo_static.fam','align':False},(k,'csk4b'));before[k]=dict(models[k]);models[k]={'file':'m_csk4c_static.fam','battle':'m_csk4c_lo_static.fam','align':False}
# ZTZ-96A/96B were inverted (Osama 02:1x): the 96B card showed the 96A model and the 96A card the 96B model. Swap them; the 96B
# hull texture becomes the seller's green digital camo (mat_ZTZ96B_Hull_Camo), work/pla-0.8/ztz96-swap-20261114.
ok(models['PLA ZTZ-96B']=={'file':'m_ztz96a_static.fam','battle':'m_ztz96a_lo_static.fam','align':False} and models['PLA Catalogue ZTZ-96A']['file']=='m_ztz96b_green.fam','ZTZ-96 entries')
before['PLA ZTZ-96B']=dict(models['PLA ZTZ-96B']);before['PLA Catalogue ZTZ-96A']=dict(models['PLA Catalogue ZTZ-96A'])
a96,b96=dict(models['PLA ZTZ-96B']),dict(models['PLA Catalogue ZTZ-96A']);models['PLA ZTZ-96B']=b96;models['PLA Catalogue ZTZ-96A']=a96
SW=Path('/home/sam/tars/work/ba-dev/replicas/codex/work/pla-0.8/ztz96-swap-20261114')
swapfiles={}
for n in ('m_ztz96b_green_tex2.png','m_ztz96b_green_lo_tex2.png'):ok('UserData/FAModels/'+n in z.namelist(),n);swapfiles['UserData/FAModels/'+n]=str(SW/n)
# Type 59D / ZTZ-59D1 retextured (Osama 01:4x: textures from the ZTZ-99A): m_ztz59d3 = m_ztz59d2 with the PLA digital woodland
# box-projected on hull and ERA (colorScale 0.8) and the ZTZ-99A track texture on the tracks (osama-20261113b/ztz59_retex.py).
for k in ('PLA Catalogue Type 59D','PLA ZTZ-59D1'):
    ok(models[k]['file']=='m_ztz59d2_static.fam',(k,'59D'));before[k]=dict(models[k]);models[k]={**models[k],'file':'m_ztz59d3_static.fam','battle':'m_ztz59d3_lo_static.fam'}
# Mengshi Recon (Osama: windows missing, close the doors if possible): the seller model is one unwelded mesh with fixed open
# doors and no glass. It moves to m_csk4r = the CSK-131 (Dongfeng Mengshi) model from tonight with closed doors and painted
# glass, under its own material file: colorScale 0.7 (darker). The Recon card's 0.75 scale is dropped (CSK-131 size).
k='PLA Mengshi Recon';ok(models[k]['file']=='m_mengshird_static.fam',k);before[k]=dict(models[k]);models[k]={'file':'m_csk4r_static.fam','battle':'m_csk4r_lo_static.fam','align':False}
k='PLA Catalogue YJ-18 ship launcher';ok(models[k]=={'file':'m_yj18_static.fam','battle':'m_yj18_lo_static.fam','align':False},'YJ-18 entry');before[k]=dict(models[k]);models[k]['scale']=0.8
k='PLA Catalogue DF-15';ok(models[k]=={'file':'m_df15_static.fam','battle':'m_df15_lo_static.fam','align':False},'DF-15 entry');before[k]=dict(models[k]);models[k]['scale']=0.8
rec['models_json']={k:{'before':before[k],'after':models[k]} for k in before}
files={};files.update(swapfiles)
for f in sorted(a.stage.iterdir()):
    if f.suffix in ('.fam','.json','.png') and f.name.split('_static')[0].replace('_lo','') in ('m_csk4c','m_csk4r'):files['UserData/FAModels/'+f.name]=str(f)
for f in sorted(a.stage.iterdir()):
    if f.suffix in ('.fam','.json','.png') and f.name.split('_static')[0].replace('_lo','')=='m_ztz59d3':files['UserData/FAModels/'+f.name]=str(f)
ok(len([k for k in files if 'ztz59d3' in k and k.endswith('.fam')])==2 and not any(k in z.namelist() for k in files if 'ztz59d3' in k),'ztz59d3 files')
ok(len([k for k in files if k.endswith('.fam') and ('csk4c' in k or 'csk4r' in k)])==4 and not any(k in z.namelist() for k in files if 'csk4c' in k or 'csk4r' in k),('csk4c files',sorted(files)))
for k in [k for k in files if k.endswith('.mat.json') and ('csk4c' in k or 'csk4r' in k)]:
    mj=json.loads(Path(files[k]).read_text());ok(all(v['alpha']=='OPAQUE' and not any(v['emissive']) and not v.get('clearGlass') and not v.get('cockpitDonor') for v in mj.values()),('csk4c solid',k))
    for key in mj:ok('UserData/FAModels/'+key.split('|')[0] in files,('texture',key))
for k in [k for k in files if k.endswith('.mat.json') and 'ztz59d3' in k]:
    for key in json.loads(Path(files[k]).read_text()):
        if key.split('|')[0]:ok('UserData/FAModels/'+key.split('|')[0] in files,('texture',key))
# CSK-181 (6x6): its window materials used the F-16 canopy (wavy) over a camo body. Windows (|0.5 grey and |0.2235 a0.56):
# solid dark glossy glass (colorScale on the grey), like the CSK-131's painted windows; lamp lenses: flat clear glass 0.025.
gdir=ROOT/f'tools/pla-specs/{V}-mats';gdir.mkdir(exist_ok=True)
WIN=('|0.5000,0.5000,0.5000,1.0000','|0.2235,0.2235,0.2235,0.5647');LENS=('|0.2941,0.2941,0.2941,0.4510','|0.0863,0.1020,0.1412,0.0706')
for n in ('m_csk181_static','m_csk181_lo_static'):
    kk=f'UserData/FAModels/{n}.mat.json';mj=json.loads(z.read(kk))
    for key in WIN+LENS:ok(mj[key].get('cockpitDonor')=='US_F16_Glass',(n,key))
    for key in WIN:mj[key].pop('cockpitDonor',None);mj[key].update(alpha='OPAQUE',metallic=0.0,smoothness=0.92,colorScale=[0.1,0.12,0.14],opacity=1.0)
    for key in LENS:mj[key].pop('cockpitDonor',None);mj[key].update(clearGlass=True,opacity=0.025,alpha='BLEND',metallic=0.0,smoothness=0.95)
    f=gdir/(n+'.mat.json');f.write_text(json.dumps(mj,indent=1)+'\n');files[kk]=str(f)
# Helicopter glass (Osama 01:0x): the glass of a similar vanilla helicopter, FAModels 0.3.24 donors (read from the vanilla
# unit bundle: prefab -> renderer material). Clear 0.025 glass is the stand-in until the donor loads (0.3.23 fallback).
HELO={'m_z20a':'US_UH60M_glass','m_z20n':'US_UH60M_glass','m_z20na':'US_UH60M_glass','m_z19g':'US_AH-1Z_Viper_Glass',
      'm_z10_black':'US_AH_64_Glass','m_z9':'US_UH-1Y_Glass','m_z9t':'US_UH-1Y_Glass','m_z11wb':'US_OH58Kiowa_glass'}
hg={}
for base,donor in HELO.items():
    names=(base+'_static',base+'_lo_static') if base.startswith(('m_z20','m_z19','m_z9')) else (base,base+'_lo')
    for n in names:
        kk=f'UserData/FAModels/{n}.mat.json';ok(kk in z.namelist(),kk);mj=json.loads(z.read(kk))
        gl=[k for k,v in mj.items() if v.get('clearGlass')];ok(len(gl)==1,(n,'one clear glass material',gl))
        mj[gl[0]]={'cockpitDonor':donor};f=gdir/(n+'.mat.json');f.write_text(json.dumps(mj,indent=1)+'\n');files[kk]=str(f);hg[n]=[gl[0],donor]
rec['helo_glass']=hg
for u,h,new in ((1236,'Z-19','Z-19G'),(1237,'Z-19 Recon','Z-19G Recon')):ok(U[u]['HUDName']==h,(u,h));g.put('Units',u,{'HUDName':new})
rec['rename']={1236:['Z-19','Z-19G'],1237:['Z-19 Recon','Z-19G Recon']}
# ---------- Infantry gear (Osama 01:20): backpacks on non-conscript bodies (dev.101b: no heavy EOD vest; goggle bodies keep their 901 carrier) ----------
# Built in work/infantry-gear-20261114 (gear_parts.py, atlas.py, compose.py): the shipped arm-repaired bodies are kept and the
# rigged backpack (bag, back panel, belt-back pouch) from the SF assault rig, and the heavy plate vest from the SF heavy rig, are
# appended as extra textured parts (same 40-bone skeleton). Regular Type 21 bodies get new *_pack files (gear raised 0.01247 m
# for their lower body offset); conscripts (1166) and the flight deck crew (1108) keep the plain body.
GEAR=Path('/home/sam/tars/work/ba-dev/replicas/codex/work/infantry-gear-20261114/out');comp=json.loads((GEAR/'compose.json').read_text())
for n,parts in comp.items():
    ok(len(parts)<=8 and parts[0].startswith('pla2_'),('gear parts',n));files['UserData/FAModels/'+n]=str(GEAR/n)
ok(not list(GEAR.glob('pla2_gear_vest_*')),'no heavy vest gear')
for f in sorted(GEAR.glob('pla2_gear_*.png')):files['UserData/FAModels/'+f.name]=str(f)
for n,parts in comp.items():
    for tex in parts:ok('UserData/FAModels/'+tex in files or 'UserData/FAModels/'+tex in z.namelist(),('body texture',n,tex))
IB='UserData/FAModels/infantry-bodies.json';bodies=json.loads(z.read(IB));moved=[]
for r in bodies:
    l0=r['lods'][0]
    if l0.startswith('pla2_regular_') and r['unitId'] not in (1166,1108):
        camo=l0.split('_')[2];r['lods']=[f'pla2_regular_{camo}_pack_{i}.fas' for i in range(3)];moved.append(r['unitId'])
ok(len(moved)==41,('regular bodies with packs',len(moved)))
f=gdir/'infantry-bodies.json';f.write_text(json.dumps(bodies,ensure_ascii=False)+'\n');files[IB]=str(f)
rec['infantry_gear']={'sf_bodies_with_pack':sorted(n for n in comp if n.startswith('pla2_sf_')),'goggle_bodies_with_vest':sorted(n for n,p in comp.items() if any('gear_vest' in x for x in p)),'regular_units_with_pack':moved,'kept_plain':[1166,1108]}
rec['csk181_windows']={'dark_glossy':list(WIN),'clear_lenses':list(LENS)}
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=raw.isascii())+'\n').encode())
(ROOT/f'tools/pla-specs/{V}-assets.txt').write_text(''.join(f'{k}={v}\n' for k,v in sorted(files.items())))
rec['famodels']='0.3.24';rec.update(version=V,base=PREV,base_sha256=BASE,request='Osama 14 Nov 00:3x PST',checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks,'files',len(files))

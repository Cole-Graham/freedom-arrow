"""Freedom Arrow 0.9.0-dev.11 data batch over exact 0.9.0-dev.10 (Osama, 14-15 Nov 2026, thread 1567745029781454889).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.11';PREV='0.9.0-dev.10'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];O=t['OptionsJson'];M=t['ModificationsJson'];rows=g.rows
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
UAB=t['UnitAbilitiesJson'];SAJ=t['SpecializationAvailabilitiesJson']
A=t['AmmunitionsJson'];SM=t['SquadMembersJson']
# ---------- DZJ-08 ignore cover 50 % -> 25 % (Osama 15 Nov 2026 00:23 PST: "DZJ-08 ignore cover to 25%"). One ammo row, all 5 squads.
ok(A[2012025]['Name']=='PLA infantry DZJ-08 0' and A[2012025]['IgnoreCover']==0.5,'DZJ-08 ammo')
g.put('AmmunitionsJson',2012025,{'IgnoreCover':0.25});rec['dzj08_ignore_cover']={'ammunition':2012025,'ignore_cover':[0.5,0.25]}
# ---------- PAP Snow Leopards 90 -> 70 points (Osama 00:2x PST).
ok(str(U[1182]['HUDName']).startswith('PAP Snow Leopards') and U[1182]['Cost']==90,'Snow Leopards 1182')
g.put('Units',1182,{'Cost':70});rec['snow_leopards_cost']=[90,70]
# ---------- Snow Leopards, Falcons, Sea Dragons availability 2 -> 3 (one PLAN SF card each).
_av={}
for _u,_c,_n in ((1182,2013140,'PAP Snow Leopards'),(1185,2013239,'Falcons'),(1191,2013425,'Sea Dragons')):
    ok(str(U[_u]['HUDName']).startswith(_n) and SAJ[_c]['UnitId']==_u and SAJ[_c]['MaxAvailabilityXp0']==2 and len([s for s in SAJ.values() if s['UnitId']==_u])==1,(_n,'card'))
    g.put('SpecializationAvailabilitiesJson',_c,{'MaxAvailabilityXp0':3});_av[f'{_u} {_n}']=[2,3]
rec['sf_availability']=_av
# ---------- Godswords weapon model (Osama 00:2x PST: "The Godswords have M16's with grenade launchers on their back"). dev.10 gave them
# their own QTS-11 launcher 2019270; FAModels/infantry-weapons.json still mapped the QTS-11 model to 2004006 for unit 1181, so the
# vanilla M4A1_m203 showed. Point that entry at 2019270.
IW=SRC/'UserData/FAModels/infantry-weapons.json';iw=json.loads(IW.read_text())
_e=[r for r in iw if r['unitId']==1181 and r['weaponId']==2004006];ok(len(_e)==1 and _e[0]['file']=='w_qts11.fam','Godswords QTS-11 GL model entry')
ok(any(m['UnitId']==1181 and m['SpecialWeaponId']==2019270 for m in SM.values()),'Godswords carry 2019270')
_e[0]['weaponId']=2019270;rec['godswords_gl_model']={'unit':1181,'weapon':[2004006,2019270],'file':'w_qts11.fam'}
# ---------- Z-19: no CM-501GA (Osama 15 Nov 2026 00:27 PST: "Z-19 remove all CM-501ga"). Loadout 3 "Multirole (CM-501GA)" goes from Z-19
# 940, 1103 and Z-19G 1236 (the Recon Z-19s never had it), with every CM-501GA mount, turret and ammo row of those units. FS-70A
# mounts stay (loadout 0 uses them).
O=t['OptionsJson'];M=t['ModificationsJson'];TU=t['TurretUnitsJson'];TW=t['TurretWeaponsJson'];WA=t['WeaponAmmunitionsJson'];W=t['WeaponsJson'];TJ=t['TurretsJson']
CM={i for i,w in W.items() if w.get('HUDName')=='CM-501GA'};ok(CM=={2017126,2017902,2019187},('CM-501GA weapons',sorted(CM)))
_z19={i:u for i,u in U.items() if str(u.get('HUDName','')).startswith('Z-19') and u.get('CountryId')==4};_cmrec={}
def _turrets(o):return {o.get(f'Turret{k}Id') for k in range(17)}-{0,None}
def _cmturret(tid):return any(r['TurretId']==tid and r['WeaponId'] in CM for r in TW.values())
for _u in sorted(_z19):
    mids={m['Id'] for m in M.values() if m.get('UnitId')==_u};opts=[o for o in O.values() if o.get('ModificationId') in mids]
    cmopts=[o for o in opts if any(_cmturret(x) for x in _turrets(o))]
    ok(all(not o.get('IsDefault') for o in cmopts),(_u,'CM loadout is not the default'))
    for o in cmopts:g.remove('OptionsJson',o['Id'])
    cmtu=[r for r in TU.values() if r['UnitId']==_u and _cmturret(r['TurretId'])]
    for r in cmtu:
        g.remove('TurretUnitsJson',r['Id'])
        if not any(x['TurretId']==r['TurretId'] for x in TU.values()):
            for w in [w for w in TW.values() if w['TurretId']==r['TurretId']]:g.remove('TurretWeaponsJson',w['Id'])
            g.remove('TurretsJson',r['TurretId'])
    cmwa=[r for r in WA.values() if r['UnitId']==_u and r['WeaponId'] in CM]
    for r in cmwa:g.remove('WeaponAmmunitionsJson',r['Id'])
    left=[o for o in O.values() if o.get('ModificationId') in mids]
    ok(not any(_cmturret(x) for o in left for x in _turrets(o)) and not [r for r in WA.values() if r['UnitId']==_u and r['WeaponId'] in CM],(_u,'no CM-501GA left'))
    ok(all(any(r['UnitId']==_u and r['TurretId']==x for r in TU.values()) for o in left for x in _turrets(o)),(_u,'remaining loadouts keep their mounts'))
    if cmopts or cmtu or cmwa:_cmrec[f"{_u} {_z19[_u]['HUDName']}"]={'options_removed':[o['Id'] for o in cmopts],'mounts_removed':len(cmtu),'ammo_rows_removed':len(cmwa),'loadouts_left':len(left)}
ok(sorted(int(k.split()[0]) for k in _cmrec)==[940,1103,1236],('Z-19 units with CM-501GA',_cmrec))
rec['z19_no_cm501ga']=_cmrec
# ---------- Godswords QTS-11 GL rate of fire for ~130 squad DPM (Osama 00:30 PST, from Lateralus's DPM visualizer: squad 202.5 DPM =
# rifle 28.7 + GL 173.8 at TimeBetweenBursts 2.0 s). DPM = 12 guns x 5 rounds / (4 x TBB + 3.5 s reload) x 0.555 damage per shot;
# TBB 4.0 s gives GL 102.5 + rifle 28.7 = 131 DPM. Godswords' own launcher only (2019270, dev.10).
W=t['WeaponsJson'];ok(W[2019270]['Name']=='PLA Godswords QTS-11 grenade launcher' and W[2019270]['TimeBetweenBurstsMin']==2.0==W[2019270]['TimeBetweenBurstsMax'],'Godswords GL 2019270')
g.put('WeaponsJson',2019270,{'TimeBetweenBurstsMin':4.0,'TimeBetweenBurstsMax':4.0});rec['godswords_gl_rof']={'weapon':2019270,'time_between_bursts':[2.0,4.0],'squad_dpm_estimate':[202.5,131.2]}
# ---------- J-10A mixed strike (Osama 15 Nov 2026 00:3x PST: "J-10 needs to redo its mixed strike loadout. 6xAKF-98A, 2x PL-10, for +180.
# replace the current mixed strike loadout thats 140"). Option 31081 (J-10A 1226, was 2x PL-10, 2x LS-6, 2x AKF-98A, 2x PL-12 for 140):
# PL-10 on pylons 1-2 as before, AKF-98A on pylons 3-4 with 3 rounds each (6), pylons 5-6 empty; option cost 180.
_o=O[31081];_akf=2016658
ok(U[1226]['HUDName']=='J-10A' and _o['Cost']==140 and str(_o.get('UIName','')).startswith('Mixed strike') and _o['Turret1Id']==_o['Turret2Id']==2016537 and _o['Turret4Id']==_akf,'J-10A mixed strike 31081')
_mids={m['Id'] for m in M.values() if m.get('UnitId')==1226}
ok([o['Id'] for o in O.values() if o.get('ModificationId') in _mids and _akf in _turrets(o)]==[31081],'AKF mount only in this loadout')
_wa=[r for r in WA.values() if r['UnitId']==1226 and r['WeaponId']==2016659];ok(len(_wa)==1 and _wa[0]['Quantity']==2,'J-10A AKF-98A ammo row')
ok(any(r['UnitId']==1226 and r['TurretId']==160 for r in TU.values()),'J-10A has the empty pylon mount')
g.put('OptionsJson',31081,{'UIName':'Mixed strike (6x AKF-98A, 2x PL-10)','Cost':180,'Turret3Id':_akf,'Turret4Id':_akf,'Turret5Id':160,'Turret6Id':160})
g.put('WeaponAmmunitionsJson',_wa[0]['Id'],{'Quantity':3})
rec['j10a_mixed_strike']={'option':31081,'cost':[140,180],'pylons':'1-2 PL-10 x1, 3-4 AKF-98A x3, 5-6 empty','akf_rounds':[2,6]}
# ---------- ZBD-20 12 HP (Osama 15 Nov 2026 00:42 PST: "ZBD-20 12 hp"). Each ZBD-20 has its own armour row (14 HP); the Recon copy is hidden.
_AR=t['ArmorsJson'];_UA=t['UnitArmorsJson']
for _u,_a in ((945,2009807),(1256,2018377)):
    ok(str(U[_u]['HUDName']).startswith('ZBD-20') and [r['ArmorId'] for r in _UA.values() if r['UnitId']==_u]==[_a] and _AR[_a]['MaxHealthPoints']==14,('ZBD-20 armour',_u))
    ok(sorted({r['UnitId'] for r in _UA.values() if r['ArmorId']==_a})==[_u],('armour row not shared',_a))
    g.put('ArmorsJson',_a,{'MaxHealthPoints':12})
rec['zbd20_hp']={'945 ZBD-20':[14,12],'1256 ZBD-20 Recon (hidden)':[14,12]}
# ---------- China fire support teams: no sprint, no smoke (Osama 15 Nov 2026 01:11 PST: "All chinese fire support teams need sprint and
# smoke removed. That includes: HJ-12 team, QLU-11 team, QJZ-89 team, QLZ-04 Team, Marine HJ-8H team, GAM-102LR team, Weapons squad").
# Every card of those teams (hidden copies too); each has its own ability row.
_AB=t['AbilitiesJson'];_fs={}
for _u,_n in ((1137,'HJ-12 Team'),(1222,'Test HJ-12E Team'),(1140,'QLU-11 Team'),(1157,'QJZ-89 Team'),(1170,'QJZ-89 Team'),(1154,'QLZ-04 Team'),
              (1208,'QLZ-04 Team'),(1193,'Marine HJ-8H Team'),(1221,'GAM-102LR Team'),(1199,'Weapons Squad')):
    ok(str(U[_u]['HUDName']).startswith(_n) and U[_u]['CountryId']==4,(_n,_u))
    _r=[r for r in UAB.values() if r['UnitId']==_u];ok(len(_r)==1,(_n,'one ability row'))
    _a=_r[0]['AbilityId'];ok(sorted({r['UnitId'] for r in UAB.values() if r['AbilityId']==_a})==[_u],(_n,'ability not shared'))
    ok('IsInfantrySprint' in _AB[_a] and 'IsSmoke' in _AB[_a],(_n,'sprint and smoke fields'))   # Reserve QJZ-89 1170 already had neither
    g.put('AbilitiesJson',_a,{'IsInfantrySprint':False,'IsSmoke':False});_fs[f'{_u} {_n}']={'ability':_a,'sprint_smoke_before':[_AB[_a]['IsInfantrySprint'],_AB[_a]['IsSmoke']]}
rec['fire_support_no_sprint_smoke']=_fs
# ---------- ZBL-191 APS becomes a protection-slot option (Osama 15 Nov 2026 01:14 PST: "ZBL-191 needs to take its APS off and put it in the
# protection system option for +40 pts. NOT stacking with the Jammer, its either or or none."). The Iron Fist APS (ability 82) was in every
# protection option; now the slot is None / Jammer +20 / Iron Fist APS +40, like the vanilla M1A1 FEP (None / Jammer / Trophy).
_pm=[m for m in M.values() if m.get('UnitId')==979 and m.get('Type')==6];ok(len(_pm)==1 and _pm[0]['Id']==2019217,'ZBL-191 protection slot')
ok([(O[i]['UIName'],O[i]['Cost'],[O[i].get(f'Ability{k}Id') for k in (1,2,3)]) for i in (31079,31080)]==[('Custom_Option_None',0,[2010319,82,4]),('Custom_Option_ANVLQ6_jammer',20,[2010319,82,80])],'ZBL-191 None/Jammer both carry APS')
ok(len([o for o in O.values() if o.get('ModificationId')==2019217])==2 and not any(o.get('IsDefault') for o in O.values() if o.get('ModificationId')==2019217),'two options, none default')
ok(sorted(r['AbilityId'] for r in UAB.values() if r['UnitId']==979)==[4,80,82,2010319],'ZBL-191 ability links')
g.put('OptionsJson',31079,{'Ability2Id':4,'Ability3Id':0});g.put('OptionsJson',31080,{'Ability2Id':80,'Ability3Id':0})
_aps=g.add('OptionsJson',O[31080],{'UIName':'GL-5 APS','OptionPicture':'APS','Cost':40,'Order':int(O[31080].get('Order',1))+1,'Ability2Id':82,'Ability3Id':0,'Name':'PLA ZBL-191 Iron Fist APS'})
ok(sorted(1 for o in O.values() if o.get('ModificationId')==2019217 and 82 in [o.get(f'Ability{k}Id') for k in range(1,6)])==[1] and not any(80 in [o.get(f'Ability{k}Id') for k in range(1,6)] and 82 in [o.get(f'Ability{k}Id') for k in range(1,6)] for o in O.values() if o.get('ModificationId')==2019217),'APS only in its own option, never with the jammer')
rec['zbl191_aps_option']={'unit':979,'slot':2019217,'options':{'None':[31079,0],'Jammer':[31080,20],'Iron Fist APS':[_aps,40]},'aps_ability':82}
# ---------- ZTL-191 Recon jammer option (Osama 15 Nov 2026 01:1x PST: "ZTL-191 recon needs its ecm loadout"). Same protection slot as the
# ZTL-191 (dev.4: None / ANVLQ6 jammer +20, ECM Hardhat ability 80), on the Recon's own base ability 2018734.
ok(U[1263]['HUDName']=='ZTL-191 Recon' and not [m for m in M.values() if m.get('UnitId')==1263],'ZTL-191 Recon has no options yet')
ok([r['AbilityId'] for r in UAB.values() if r['UnitId']==1263]==[2018734],'ZTL-191 Recon base ability only')
_src=M[2019214];ok(_src['UnitId']==1080 and _src['Type']==6,'ZTL-191 jammer slot')
for _ab in (4,80):g.add('UnitAbilitiesJson',next(r for r in UAB.values() if r['UnitId']==1080 and r['AbilityId']==_ab),{'UnitId':1263})
_rm=g.add('ModificationsJson',_src,{'UnitId':1263,'Name':'PLA ZTL-191 Recon Jammer'})
_ro={}
for _o in sorted((o for o in O.values() if o.get('ModificationId')==2019214),key=lambda o:o['Order']):
    ok(_o['Ability1Id']==2011293 and _o['Ability2Id'] in (4,80),('ZTL-191 jammer option',_o['Id']))
    _ro[_o['UIName']]=[g.add('OptionsJson',_o,{'ModificationId':_rm,'Ability1Id':2018734}),_o['Cost']]
ok(sorted(r['AbilityId'] for r in UAB.values() if r['UnitId']==1263)==[4,80,2018734] and len([o for o in O.values() if o.get('ModificationId')==_rm])==2,'ZTL-191 Recon jammer slot built')
rec['ztl191_recon_jammer']={'unit':1263,'slot':_rm,'options':_ro}
# ---------- China APS options are called GL-5 (Osama 01:23 "any chinese APS should be called GL-5"; 15 Nov 2026 01:2x PST: "Chinese APS is called GL5 by the way, for all of aps options").
# The APS options on ZBD-20, ZBD-251 and VT-5 showed the vanilla "Iron Fist" name (key Custom_Option_IronFist_APS); ZBL-191's new one above
# is already "GL-5 APS". China options show their UIName text as written (as "HJ-16 (semi-active)" does).
_APS={i for i,a in t['AbilitiesJson'].items() if a.get('IsAPS')};_gl5={}
for _o in sorted(O.values(),key=lambda o:o['Id']):
    _m=M.get(_o.get('ModificationId'))
    if not _m or U.get(_m['UnitId'],{}).get('CountryId')!=4 or _m.get('Type')!=6:continue
    _ab=[_o.get(f'Ability{k}Id') for k in range(1,6)]
    if any(x in _APS for x in _ab) and not any(x==80 for x in _ab) and _o.get('UIName')!='Custom_Option_None':
        _gl5[f"{_m['UnitId']} {U[_m['UnitId']]['HUDName']} option {_o['Id']}"]=[_o.get('UIName'),'GL-5 APS'];g.put('OptionsJson',_o['Id'],{'UIName':'GL-5 APS'})
ok(sorted(int(k.split()[0]) for k in _gl5)==[945,979,1056,1261],('China APS options',_gl5))
rec['china_aps_gl5']=_gl5
# ---------- FK-2000 170 -> 250 points (Osama 15 Nov 2026 01:22 PST). One FK-2000 unit, no loadout options or swap rows.
ok(U[935]['HUDName']=='FK-2000' and U[935]['Cost']==170 and [i for i,u in U.items() if 'FK-2000' in str(u.get('HUDName','')) and u.get('CountryId')==4]==[935],'FK-2000 935')
g.put('Units',935,{'Cost':250});rec['fk2000_cost']=[170,250]
# ---------- SR-5 moves to PLAGF Motorized (Osama 15 Nov 2026 01:2x PST: "China SR-5 moved to motorized"). Its one card (PLAN SF, 2
# availability, no transport links) becomes the Motorized card, as Z-11WB in dev.8.
ok(U[934]['HUDName']=='SR-5' and SAJ[2014522]['UnitId']==934 and SAJ[2014522]['SpecializationId']==20 and len([c for c in SAJ.values() if c['UnitId']==934])==1,'SR-5 PLAN card')
ok(not [r for r in t['TransportAvailabilitiesJson'].values() if r['SpecializationAvailabilityId']==2014522],'SR-5 no transport links')
g.put('SpecializationAvailabilitiesJson',2014522,{'SpecializationId':21});assign['assignments']['934']=[21]
rec['sr5_to_motorized']={'card':2014522,'spec':[20,21]}
# ---------- Squad loadouts become separate cards (Osama 15 Nov 2026 01:27-01:3x PST: "Rangers CQC and Rangers NSGW are seperate units now,
# remember CQC is +5 points", "Airborne NGSW and standard should be seperate units too same availability but NGSW is +10", "Mech. Riflemen
# MAAWs split into two units, MAAWS and standard"). Each card's squad-loadout slot (Type 7) goes; every variant gets its own card with the
# same specialization, availability and transports, at base price + its loadout price (the swap-row rule already gives that price).
TAJ=t['TransportAvailabilitiesJson'];_split={}
for _card,_mod,_names in ((619,516,('Rangers','Rangers CQC')),(797,583,('Airborne','Airborne NGSW')),(608,3345 and None,('Mech. Riflemen','Mech. Riflemen MAAWS'))):
    _c=SAJ[_card];_own=_c['UnitId']
    _mods=[m for m in M.values() if m.get('UnitId')==_own and m.get('Type')==7];ok(len(_mods)==1,(_card,'one squad loadout slot'))
    _m=_mods[0];_opts=sorted((o for o in O.values() if o.get('ModificationId')==_m['Id']),key=lambda o:o['Id']);ok(len(_opts)==2 and all(o.get('ReplaceUnitId') for o in _opts),(_card,'two swap options'))
    _tr=[r for r in TAJ.values() if r['SpecializationAvailabilityId']==_card];_res={}
    for _o in _opts:
        _u=_o['ReplaceUnitId'];_cost=U[_own]['Cost']+_o['Cost'];_fields={'Cost':_cost}
        if _o.get('ThumbnailOverride'):_fields['ThumbnailFileName']=_o['ThumbnailOverride']
        if _u!=_own:ok(U[_u]['Cost']==_cost and U[_u].get('DisplayInArmory') is not False and not [c for c in SAJ.values() if c['UnitId']==_u],(_u,'variant price = base + loadout, no card yet'))
        _res[_u]=(_fields,_o)
    ok(sorted(str(U[u]['HUDName']).strip() for u in _res)==sorted(_names) or sorted(str(_res[u][1].get('ReplaceUnitName') or U[u]['HUDName']).strip() for u in _res)==sorted(_names),(_card,'variants',[U[u]['HUDName'] for u in _res]))
    for _o in _opts:g.remove('OptionsJson',_o['Id'])
    g.remove('ModificationsJson',_m['Id'])
    _out={}
    for _u,(_fields,_o) in _res.items():
        if _o.get('ReplaceUnitName'):_fields['HUDName']=_o['ReplaceUnitName']
        g.put('Units',_u,_fields)
        if _u==_own:_out[f"{_u} {U[_u]['HUDName']}"]={'card':_card,'cost':U[_u]['Cost']}
        else:
            _nc=g.add('SpecializationAvailabilitiesJson',_c,{'UnitId':_u})
            for _r in _tr:g.add('TransportAvailabilitiesJson',_r,{'SpecializationAvailabilityId':_nc})
            _out[f"{_u} {U[_u]['HUDName']}"]={'card':_nc,'cost':U[_u]['Cost']}
    ok(all(len([c for c in SAJ.values() if c['UnitId']==u and c['SpecializationId']==_c['SpecializationId'] and c['MaxAvailabilityXp0']==_c['MaxAvailabilityXp0']])==1 for u in _res),(_card,'one card each, same availability'))
    _split[_card]=_out
rec['squad_loadout_split']=_split
# ---------- US M-25 CDTE: penetration 15 -> 40, damage 0.75 -> 1 (Osama 01:27 PST). One ammo row (Troopers, Troopers AT, Troopers AA).
_A=t['AmmunitionsJson'];ok(_A[2002021]['Name']=='InfGrenade 25x40 M-25 CDTE' and _A[2002021]['Damage']==0.75 and _A[2002021]['PenetrationAtMinRange']==15.0==_A[2002021]['PenetrationAtGroundRange'],'M-25 CDTE ammo')
g.put('AmmunitionsJson',2002021,{'PenetrationAtMinRange':40.0,'PenetrationAtGroundRange':40.0,'Damage':1.0});rec['m25_cdte']={'ammunition':2002021,'penetration':[15,40],'damage':[0.75,1.0]}
# ---------- Troopers AA (mixed loadout, unit 706): its two M203 grenadiers carry the M-25 CDTE instead (Osama 15 Nov 2026 01:30 PST: "Troopers
# AA for US Stryker multipurpose needs their M203s replaced by the M-25"). Same weapon, ammo and 120 rounds as the other Troopers squads.
_SM=t['SquadMembersJson'];_SW=t['SquadWeaponsJson'];_WA=t['WeaponAmmunitionsJson']
ok(U[706]['HUDName']=='Troopers AA','Troopers AA 706')
_g=[m for m in _SM.values() if m['UnitId']==706 and m['SpecialWeaponId']==58];ok(len(_g)==2,'two M203 grenadiers')
_sw=[r for r in _SW.values() if r['UnitId']==706 and r['WeaponId']==58];ok(len(_sw)==1,'M203 squad weapon row')
_wa=[r for r in _WA.values() if r['UnitId']==706 and r['WeaponId']==58];ok(len(_wa)==1,'M203 ammo row')
_ref=[r for r in _WA.values() if r['UnitId']==413 and r['WeaponId']==2002020];ok(len(_ref)==1 and _ref[0]['AmmunitionId']==2002021,'Troopers AA 413 M-25 ammo row')
for m in _g:g.put('SquadMembersJson',m['Id'],{'SpecialWeaponId':2002020})
g.put('SquadWeaponsJson',_sw[0]['Id'],{'WeaponId':2002020})
g.put('WeaponAmmunitionsJson',_wa[0]['Id'],{'WeaponId':2002020,'AmmunitionId':2002021,'Quantity':_ref[0]['Quantity']})
ok(not [m for m in _SM.values() if m['UnitId']==706 and 58 in (m['PrimaryWeaponId'],m['SpecialWeaponId'])],'no M203 left on 706')
rec['troopers_aa_m25']={'unit':706,'grenadiers':2,'weapon':[58,2002020],'rounds':[48,_ref[0]['Quantity']]}
# ---------- QLU-11 penetration 15 -> 50 mm (Osama 15 Nov 2026 01:32 PST). One ammo row, every squad with the QLU-11 (33 units).
_A=t['AmmunitionsJson'];ok(_A[2004003]['Name']=='PLA Test Grenade Launcher QLU11 ammunition' and _A[2004003]['PenetrationAtMinRange']==15.0==_A[2004003]['PenetrationAtGroundRange'],'QLU-11 ammo')
ok(sorted({r['WeaponId'] for r in WA.values() if r['AmmunitionId']==2004003})==[2004002],'QLU-11 ammo only on the QLU-11')
g.put('AmmunitionsJson',2004003,{'PenetrationAtMinRange':50.0,'PenetrationAtGroundRange':50.0});rec['qlu11_pen']={'ammunition':2004003,'penetration':[15,50]}
# ---------- Combat Engineers thermobaric loadout picture and card (Osama 15 Nov 2026 01:33 PST: "combat engineers, replace the loadout image for
# thermobaric rockets with the PF-97 icon ... and make sure the loadout unit card is the correct image"). Option 24354 showed the vanilla TBG-7
# picture; it now shows INF_RPG26, the icon the PF-97 itself uses (weapons 2004876, 2012515). The squad it swaps to (Thermobaric Breachers
# 1162, 5x PF-97) used the vanilla Russian engineer portrait; it now uses the Combat Engineers' China portrait.
ok(O[24354]['UIName']=='Custom_Option_Thermobaric_launcher' and O[24354]['OptionPicture']=='INF_TBG7' and O[24354]['ReplaceUnitId']==1162,'Combat Engineers thermobaric option')
ok(t['WeaponsJson'][2012515]['HUDIcon']=='INF_RPG26' and U[1162]['PortraitFileName']=='RU\\INGENERY\\INGENERY','PF-97 icon and old portrait')
g.put('OptionsJson',24354,{'OptionPicture':'INF_RPG26'});g.put('Units',1162,{'PortraitFileName':U[1156]['PortraitFileName']})
rec['combat_engineers_thermobaric']={'option':24354,'picture':['INF_TBG7','INF_RPG26'],'unit':1162,'portrait':['RU\\INGENERY\\INGENERY',U[1156]['PortraitFileName']]}
# ---------- M7 Spear penetration 15->7 becomes 20->10 (Osama 15 Nov 2026 01:40 PST: "M7 spear peentration is 10-20 instead of 7-15").
# Ammo 129 (6.8x51), used only by the M7 Spear (weapon 208, 5 squads).
_A=t['AmmunitionsJson'];ok(_A[129]['Name']=='InfBullet 6.8x51 T2' and _A[129]['PenetrationAtMinRange']==15.0 and _A[129]['PenetrationAtGroundRange']==7.0,'M7 Spear ammo')
ok(sorted({r['WeaponId'] for r in WA.values() if r['AmmunitionId']==129})==[208],'6.8x51 only on the M7 Spear')
g.put('AmmunitionsJson',129,{'PenetrationAtMinRange':20.0,'PenetrationAtGroundRange':10.0});rec['m7_spear_pen']={'ammunition':129,'close':[15,20],'max_range':[7,10]}
# ---------- Stryker Combat Engineers (449): their two M203 grenadiers carry the M-25 CDTE (XM25 CDTE) instead (Osama 15 Nov 2026 01:4x PST:
# "styker combat engineers replace the M203s with XM-25"). Same weapon, ammo and 120 rounds as the Stryker Troopers squads.
ok(U[449]['HUDName']=='Combat Engineers' and U[449]['CountryId']!=4,'Combat Engineers 449')
_g=[m for m in _SM.values() if m['UnitId']==449 and m['SpecialWeaponId']==58];ok(len(_g)==2,'449 two M203 grenadiers')
_sw=[r for r in _SW.values() if r['UnitId']==449 and r['WeaponId']==58];ok(len(_sw)==1,'449 M203 squad weapon row')
_wa=[r for r in _WA.values() if r['UnitId']==449 and r['WeaponId']==58];ok(len(_wa)==1,'449 M203 ammo row')
for m in _g:g.put('SquadMembersJson',m['Id'],{'SpecialWeaponId':2002020})
g.put('SquadWeaponsJson',_sw[0]['Id'],{'WeaponId':2002020})
g.put('WeaponAmmunitionsJson',_wa[0]['Id'],{'WeaponId':2002020,'AmmunitionId':2002021,'Quantity':_ref[0]['Quantity']})
ok(not [m for m in _SM.values() if m['UnitId']==449 and 58 in (m['PrimaryWeaponId'],m['SpecialWeaponId'])],'no M203 left on 449')
rec['stryker_engineers_m25']={'unit':449,'grenadiers':2,'weapon':[58,2002020],'rounds':[_wa[0]['Quantity'],_ref[0]['Quantity']]}
# ---------- VT-5 Recon out of the arsenal, kept in the game (Osama 15 Nov 2026 01:46 PST: "VT-5 recon removed", then "they can be moved out of
# the arsenal but kept in the game"). DisplayInArmory false, as other hidden China units; its card (2018665, PLAGF Motorized, 2), data and
# model stay, so decks that already have it still load it.
ok(U[1262]['HUDName']=='VT-5 Recon' and U[1262].get('DisplayInArmory') is not False and [c['Id'] for c in SAJ.values() if c['UnitId']==1262]==[2018665],'VT-5 Recon one card')
g.put('Units',1262,{'DisplayInArmory':False});rec['vt5_recon_hidden']={'unit':1262,'card_kept':2018665,'DisplayInArmory':[True,False]}
# ---------- AR-2000 95 -> 120 points (Osama 15 Nov 2026 01:4x PST). One unit, no swap rows.
ok(U[1084]['HUDName']=='AR-2000' and U[1084]['Cost']==95 and not [o for o in O.values() if o.get('ReplaceUnitId')==1084],'AR-2000 1084')
g.put('Units',1084,{'Cost':120});rec['ar2000_cost']=[95,120]
# ---------- China Combat Engineers (Lateralus 15 Nov 2026 02:16 PST, thread 1568104480459722894). DZJ-08 ignore cover 25 % is already
# above (Osama), and so is the PF-97 picture on the Thermobaric Rockets loadout.
# New shotgun HAWK 97-2: a stat clone of the M590A1 (weapon 199, ammo 43 12ga SLUG, 90 rounds per man), with the M590A1 icon and model.
# It replaces the QBS-09 in both Combat Engineers loadouts; the QBS-09 stays on its other 12 squads.
# Assault Shield loadout (option 24353, unit 1156): 2x QBS-09 -> 2x HAWK 97-2; DZJ-08 2 -> 5 (the 4 riflemen and 1 HAWK shotgunner);
# renamed "Multipurpose" with the DZJ-08's icon INF_M141. Thermobaric Rockets loadout (option 24354 -> unit 1162): +0 -> +10 (swap row 1162
# 50 -> 60, base 50 + 10), 3x QBS-09 -> 3x HAWK 97-2, smoke 4 -> 1 (ability 2012512, used by 1162 only).
_SM=t['SquadMembersJson'];_SW=t['SquadWeaponsJson'];_WA=t['WeaponAmmunitionsJson'];W=t['WeaponsJson'];A=t['AmmunitionsJson'];AB=t['AbilitiesJson']
QBS,DZJ=2012131,2012024
ok(W[199]['HUDName']=='M590A1' and W[199]['HUDIcon']=='M590A1_MOSBERG' and W[QBS]['HUDName']=='QBS-09' and W[DZJ]['HUDName']=='DZJ-08' and W[DZJ]['HUDIcon']=='INF_M141','M590A1, QBS-09, DZJ-08')
ok(Counter((r['AmmunitionId'],r['Quantity']) for r in _WA.values() if r['WeaponId']==199)==Counter({(43,90):3}),'M590A1 ammo 43, 90 rounds')
_hw=g.add('WeaponsJson',W[199],{'Name':'PLA infantry HAWK 97-2','HUDName':'HAWK 97-2'})
_ha=g.add('AmmunitionsJson',A[43],{'Name':'PLA infantry HAWK 97-2 12ga SLUG'})
ok(U[1156]['HUDName'].startswith('Combat Engineers') and U[1156]['CountryId']==4 and U[1162]['HUDName'].startswith('Thermobaric Breachers') and U[1156]['Cost']==50==U[1162]['Cost'],'Combat Engineers 1156 / Thermobaric Breachers 1162')
ok(O[24353]['UIName']=='Custom_Option_Assault_shield' and O[24353]['ReplaceUnitId']==1156 and O[24353]['OptionPicture']=='FLASHBANG','Assault Shield option 24353')
ok(O[24354]['ReplaceUnitId']==1162 and O[24354]['Cost']==0 and O[24354]['OptionPicture']=='INF_RPG26','Thermobaric option 24354 (PF-97 picture already set above)')
def _hawk(u,n):
    sm=sorted((m for m in _SM.values() if m['UnitId']==u and m['PrimaryWeaponId']==QBS),key=lambda m:m['Id']);ok(len(sm)==n and all(m['SpecialWeaponId']==0 for m in sm),(u,'QBS-09 men',len(sm)))
    for m in sm:g.put('SquadMembersJson',m['Id'],{'PrimaryWeaponId':_hw})
    sw=[r for r in _SW.values() if r['UnitId']==u and r['WeaponId']==QBS];wa=[r for r in _WA.values() if r['UnitId']==u and r['WeaponId']==QBS];ok(len(sw)==1==len(wa),(u,'QBS-09 rows'))
    g.put('SquadWeaponsJson',sw[0]['Id'],{'WeaponId':_hw});g.put('WeaponAmmunitionsJson',wa[0]['Id'],{'WeaponId':_hw,'AmmunitionId':_ha,'Quantity':90})
    ok(not [m for m in _SM.values() if m['UnitId']==u and QBS in (m['PrimaryWeaponId'],m['SpecialWeaponId'])],(u,'no QBS-09 left'))
    return [m['Id'] for m in sm],wa[0]['Quantity']
_h1,_=_hawk(1156,2);_h2,_=_hawk(1162,3)
_rif=sorted((m for m in _SM.values() if m['UnitId']==1156 and m['PrimaryWeaponId']==2003998),key=lambda m:m['Id'])
ok(len(_rif)==4 and [m['SpecialWeaponId'] for m in _rif]==[DZJ,DZJ,0,0],'1156 4 riflemen, 2 with DZJ-08')
for _m in [*_rif[2:],_SM[_h1[0]]]:g.put('SquadMembersJson',_m['Id'],{'SpecialWeaponId':DZJ})
ok(sum(m['SpecialWeaponId']==DZJ for m in _SM.values() if m['UnitId']==1156)==5,'1156 5x DZJ-08')
ok([r['Quantity'] for r in _WA.values() if r['UnitId']==1156 and r['WeaponId']==DZJ]==[1],'DZJ-08 1 round per man')
g.put('OptionsJson',24353,{'UIName':'Multipurpose','OptionPicture':W[DZJ]['HUDIcon']})
g.put('OptionsJson',24354,{'Cost':10});g.put('Units',1162,{'Cost':U[1156]['Cost']+10})
ok([r['UnitId'] for r in UAB.values() if r['AbilityId']==2012512]==[1162] and AB[2012512]['IsSmoke'] and AB[2012512]['SmokeAmmunitionQuantity']==4,'1162 smoke ability 2012512, 4 smokes')
g.put('AbilitiesJson',2012512,{'SmokeAmmunitionQuantity':1})
rec['china_combat_engineers']={'hawk_97_2':{'weapon':_hw,'ammunition':_ha,'clone_of':[199,43],'rounds':90,'icon':'M590A1_MOSBERG'},
 'multipurpose':{'option':24353,'unit':1156,'name':['Custom_Option_Assault_shield','Multipurpose'],'picture':['FLASHBANG','INF_M141'],'hawk_men':_h1,'dzj08':[2,5],'dzj08_new':[m['Id'] for m in _rif[2:]]+[_h1[0]]},
 'thermobaric':{'option':24354,'unit':1162,'option_cost':[0,10],'unit_cost':[50,60],'hawk_men':_h2,'smoke':{'ability':2012512,'quantity':[4,1]}}}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);IW.write_text(json.dumps(iw,indent=2,ensure_ascii=False)+'\n');save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)

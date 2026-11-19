"""Freedom Arrow 0.9.0-dev.44 data over exact 0.9.0-dev.43 (18 Nov 2026). Opened by BA Codex thread 1567745029781454889 (Osama, HHQ-10 = MML AIM-9).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.44';PREV='0.9.0-dev.43'
# dev.43 was built in out/local-dev43.
BASE=json.loads((REL/f'out/local-dev43/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev43/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];O=t['OptionsJson'];M=t['ModificationsJson']
AN='UserData/FreedomArrow/pla-spec-assignments.json';assign=json.loads(z.read(AN));checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
AB=t['AbilitiesJson'];UAB=t['UnitAbilitiesJson']
# ---------- HHQ-10 = MML with AIM-9 in stats, 18 missiles (Osama 18 Nov 2026 13:3x PST, thread 1567745029781454889: "HHQ-10 should be like the MML
# with side winders in stats but of course 18 missiles"). Weapon 2019357 / missile 2019358 (HHQ-10 unit 1273 only) take the combat values of the vanilla
# MML AIM-9 launcher 625 / missile 465. Kept: names, icons, sound and effect, TargetType 1944 (HHQ-10 also engages other missiles; the MML 792 does
# not - a targeting role, left for Osama), 18 rounds, unit price 220.
_W=t['WeaponsJson'];_A=t['AmmunitionsJson'];_WA=t['WeaponAmmunitionsJson']
ok(U[1273]['HUDName']=='HHQ-10' and [(r['WeaponId'],r['AmmunitionId'],r['Quantity']) for r in _WA.values() if r['UnitId']==1273]==[(2019357,2019358,18)],'HHQ-10 one launcher, 18 missiles')
ok(sorted({r['UnitId'] for r in _WA.values() if r['WeaponId']==2019357 or r['AmmunitionId']==2019358})==[1273],'HHQ-10 rows used by HHQ-10 only')
ok(_W[625]['Name']=='SAM AIM9 x15 MML' and _A[465]['Name']=='Missile AA AIM9 Ground','MML AIM-9 rows')
_wkeep={'Id','Name','HUDName','HUDIcon','MagazineSize'};_akeep={'Id','Name','HUDName','HUDIcon','AudioPreset','FXPreset','ModelFileName','TargetType'}
_wch={k:v for k,v in _W[625].items() if k not in _wkeep and _W[2019357].get(k)!=v};_ach={k:v for k,v in _A[465].items() if k not in _akeep and _A[2019358].get(k)!=v}
_before={'weapon':{k:_W[2019357].get(k) for k in _wch},'missile':{k:_A[2019358].get(k) for k in _ach}}
g.put('WeaponsJson',2019357,_wch);g.put('AmmunitionsJson',2019358,_ach)
ok(all(_W[2019357].get(k)==v for k,v in _W[625].items() if k not in _wkeep) and _W[2019357]['MagazineSize']==18,'HHQ-10 launcher = MML AIM-9, magazine 18')
ok(all(_A[2019358].get(k)==v for k,v in _A[465].items() if k not in _akeep),'HHQ-10 missile = AIM-9')
rec['hhq10_as_mml_aim9']={'weapon':2019357,'missile':2019358,'from':_before,'to':{'weapon':_wch,'missile':_ach},'kept':'names, icons, sound/FX, TargetType 1944, 18 rounds, cost 220'}
# ---------- Cover rework: NOT in this batch (Osama 18 Nov 2026 16:2x PST, thread 1567745029781454889: "I don't want to change anything yet from our
# previous play test"). The Wargame-style cover (open 100%, woods 60%, buildings 30%, vanilla Ignore Cover) and the earlier autocannon IgnoreCover
# 0.2439 change are parked on branch codex/batch/osama/cover-rework (83f1f70e). dev.44 keeps the dev.43 cover rules and Ignore Cover values.
# EXCEPTION, in this batch (Osama 18 Nov 2026 16:3x PST: "The only changes I do want to make regarding cover is to remove the open field cover"):
# runtime only, no table rows. game-config InfantryOpenDamageFloor 1 + InfantryOpenDamagePerSoldier 0 (DetectionConfig.WriteBuildings writes them to
# Buff Config StressModifiers Calm/Shocked/Panicked; vanilla 0.36/0.02, 0.36/0.02, 0.10/0.10): infantry outside buildings take full damage at every
# stress level. Buildings (0.18 flat), woods (0.7) and every IgnoreCover value stay as dev.43.
rec['open_ground_protection_off']={'game_config':{'InfantryOpenDamageFloor':1,'InfantryOpenDamagePerSoldier':0},'buildings':0.18,'woods':0.7,'ignore_cover':'dev.43 values','verified':'compiles; not seen in game'}
# ---------- China tank HE = Russian 125 mm HE (Osama 18 Nov 2026 16:4x PST, thread 1567745029781454889: "Chinese tanks should have the same he as Russian
# tanks" ... "can we please normalize it"). Damage 13, penetration 125, blast 12 and stress already match the Russian 125 mm HE rows (e.g. 243 T-90M);
# only IgnoreCover differed (China 0.3, Russia 0.25). GroundRange is per gun (Russia 600-700) and stays.
_RU=_A[243];_CNHE=[2011063,2011091,2011119,2019460,2010197,2009479,2009913,2011359,2009105,2011387,2009077,2009699,2009885]
ok(_RU['Name'].startswith('Round 125 2A46M501') and (_RU.get('IgnoreCover') or 0)==0.25,'Russian 125 mm HE reference')
_cnf=['Damage','PenetrationAtMinRange','PenetrationAtGroundRange','HealthAOERadius','StressDamage','StressAOERadius','ArmorTargeted']
for _i in _CNHE:
    ok(all(_A[_i].get(f)==_RU.get(f) for f in _cnf) and _A[_i].get('IgnoreCover')==0.3,(_i,_A[_i]['HUDName'],'China tank HE = RU except IC 0.3'))
    ok(all(U[r['UnitId']].get('CountryId')==4 for r in _WA.values() if r.get('AmmunitionId')==_i),(_i,'China units only'))
    g.put('AmmunitionsJson',_i,{'IgnoreCover':0.25})
ok(all(_A[_i]['IgnoreCover']==0.25 for _i in _CNHE),'China tank HE IgnoreCover 0.25')
rec['china_tank_he_like_russia']={'rows':_CNHE,'ignore_cover':[0.3,0.25],'reference':243}
# ---------- China tank sabots 10 damage; ZTZ-100 and ZTZ-99A (Osama 18 Nov 2026 20:4x PST, thread 1567745029781454889: "please fix the ztq 15 all tanks
# sabot should be 10 damage. Anyways let's make the ztz 100 front armor 750 and then I'll make the ammo 475 to 525 mm penetration. Ztz 99a should go to
# 850 k e armor and a 550 to 500 penetration"). US/RU tank sabots are all 10; nine China tank AP rows were 8.5 (vanilla RU MT-12 towed AT gun keeps 8.5).
_AR=t['ArmorsJson'];_UA=t['UnitArmorsJson']
_SABOT=[2009131,2009517,2009669,2009967,2010793,2010821,2010849,2011301,2011327]
for _i in _SABOT:
    ok(_A[_i].get('Damage')==8.5 and all(U[r['UnitId']].get('CountryId')==4 for r in _WA.values() if r.get('AmmunitionId')==_i),(_i,_A[_i]['Name'],'China tank AP at 8.5'))
    g.put('AmmunitionsJson',_i,{'Damage':10.0})
ok(all(_A[_i]['Damage']==10.0 for _i in _SABOT),'China tank sabots 10 damage')
# ZTZ-100 (unit 968): own armour row 2010183 KE front 700 -> 750; APFSDS 2010195 penetration 550/500 -> 525 (min range) / 475 (max range)
ok([r['ArmorId'] for r in _UA.values() if r.get('UnitId')==968]==[2010183] and [r['UnitId'] for r in _UA.values() if r.get('ArmorId')==2010183]==[968] and _AR[2010183]['KinArmorFront']==700,'ZTZ-100 own armour row')
g.put('ArmorsJson',2010183,{'KinArmorFront':750})
ok(_A[2010195]['PenetrationAtMinRange']==550 and _A[2010195]['PenetrationAtGroundRange']==500 and {r['UnitId'] for r in _WA.values() if r.get('AmmunitionId')==2010195}=={968},'ZTZ-100 APFSDS own row')
g.put('AmmunitionsJson',2010195,{'PenetrationAtMinRange':525.0,'PenetrationAtGroundRange':475.0})
# ZTZ-99A (unit 904): own armour row 2009063 KE front 800 -> 850; APFSDS 2009075 already 550/500
ok([r['ArmorId'] for r in _UA.values() if r.get('UnitId')==904]==[2009063] and [r['UnitId'] for r in _UA.values() if r.get('ArmorId')==2009063]==[904] and _AR[2009063]['KinArmorFront']==800,'ZTZ-99A own armour row')
g.put('ArmorsJson',2009063,{'KinArmorFront':850})
ok(_A[2009075]['PenetrationAtMinRange']==550 and _A[2009075]['PenetrationAtGroundRange']==500,'ZTZ-99A APFSDS already 550/500')
ok(_AR[2010183]['KinArmorFront']==750 and _AR[2009063]['KinArmorFront']==850 and _A[2010195]['PenetrationAtMinRange']==525,'ZTZ-100/99A applied')
rec['china_tanks_20261118']={'sabot_damage_10':_SABOT,'ztz100':{'armour_row':2010183,'ke_front':[700,750],'apfsds':2010195,'pen':[[550,500],[525,475]]},'ztz99a':{'armour_row':2009063,'ke_front':[800,850]},'prices':'unchanged (ZTZ-100 340, ZTZ-99A 230); awaiting Osama'}
# ---------- Modern China MBT optics = T-14 / M1A2 SEP v3 (Osama 18 Nov 2026 20:5x PST, thread 1567745029781454889: "the Optics and stuff like that should be
# pretty much similar to the T14 in the Abrams"). T-14 (13) and SEP v3 (191) use vanilla sensor 1 "Good Optics" 1650 ground / 1100 low / 1000 high. ZTZ-99A,
# ZTZ-99A2, ZTZ-99G and ZTZ-100 each have their own sensor row (700 or 875 ground); those rows take sensor 1's optics. Names and models kept.
_SE=t['SensorsJson'];_SU=t['SensorUnitsJson'];_G=_SE[1];_of=('OpticsGround','OpticsLowAltitude','OpticsHighAltitude')
ok(_G['Name']=='Good Optics' and _G['OpticsGround']==1650 and [r['SensorId'] for r in _SU.values() if r.get('UnitId') in (13,191)]==[1,1],'T-14 / SEP v3 on Good Optics 1650')
_OPT={904:2009069,939:2009691,948:2009877,968:2010189}
for _u,_s in _OPT.items():
    ok([r['SensorId'] for r in _SU.values() if r.get('UnitId')==_u]==[_s] and [r['UnitId'] for r in _SU.values() if r.get('SensorId')==_s]==[_u],(_u,U[_u]['HUDName'],'own sensor row'))
    g.put('SensorsJson',_s,{f:_G[f] for f in _of})
ok(all(all(_SE[_s][f]==_G[f] for f in _of) for _s in _OPT.values()),'modern China MBT optics 1650/1100/1000')
rec['china_mbt_optics_like_t14']={'units':list(_OPT),'sensor_rows':list(_OPT.values()),'optics':[_G[f] for f in _of]}
# ---------- Autocannon HE IgnoreCover 0.25, like FA tank HE (Osama 18 Nov 2026 16:3x PST, thread 1567745029781454889: "let's give Auto cannons the
# same 25% ignore cover as tank cannons have"). FA tank HE rounds are 0.25 (dev.43). Scope as the parked cb7f185c change: 20-57 mm HE/HEI/HEDP/MP rounds
# (penetration <= 150) on any unit, China included; AP rounds stay as they are (tank AP is 0 too). Excluded: grenade launchers (QLB-06, QLZ-87) and the
# SPAAG/SAM gun rounds Lateralus tuned for missile defence (spaag-weapons.json weapons and sameUnitClaimWeapons).
import re as _re
_A=t['AmmunitionsJson'];_W=t['WeaponsJson'];_WA=t['WeaponAmmunitionsJson'];_VA={r['Id']:r for r in json.loads((a.vanilla/'AmmunitionsJson.json').read_text())}
_sp=json.loads(z.read('UserData/FreedomArrow/spaag-weapons.json'));_aaw=set(_sp['weapons'])|set(_sp['sameUnitClaimWeapons'])
_IC=0.25
_rounds={};_skip={}
for _r in _WA.values():
    _a=_A.get(_r['AmmunitionId']);_w=_W.get(_r['WeaponId'])
    if not _a or not _w:continue
    _nm=str(_a.get('Name'))+' '+str(_w.get('Name'))
    if not _re.search(r'\b(20|23|25|27|30|35|40|50|57)\s?mm|Round (20|23|25|27|30|35|40|57)\b',_nm):continue
    if not _re.search(r'HE|FRAG|HEI|MP|Frag|ABM|HEDP|HE-',str(_a.get('Name'))+str(_a.get('HUDName'))):continue
    if (_a.get('PenetrationAtGroundRange') or 0)>150:continue
    if _r['WeaponId'] in _aaw:_skip.setdefault(_a['Id'],_a['HUDName']);continue
    if _re.search(r'grenade|AGL|QLB|QLZ',_nm+str(_w.get('HUDName'))+str(_a.get('HUDName')),_re.I):continue   # grenade launchers (QLB-06, QLZ-87) are not autocannons
    _rounds[_a['Id']]=_a
for _i in _skip:_rounds.pop(_i,None)
for _i,_a in _rounds.items():
    _v=_VA.get(_i)
    if _v:ok((_v.get('IgnoreCover') or 0)==0,(_i,_a['HUDName'],'vanilla IC 0'))
_chg={}
for _i in sorted(_rounds):
    _old=_A[_i].get('IgnoreCover') or 0
    if _old!=_IC:g.put('AmmunitionsJson',_i,{'IgnoreCover':_IC});_chg[str(_i)]={'name':_A[_i]['HUDName'],'from':_old,'to':_IC}
ok(len(_chg)>=40,('autocannon HE rounds changed',len(_chg)))
rec['autocannon_he_ignore_cover']={'ignore_cover':_IC,'basis':'same as FA tank HE (0.25)','changed':_chg,'excluded_spaag':{str(k):v for k,v in _skip.items()}}
print('autocannon rounds changed',len(_chg),'excluded',len(_skip))
# ---------- JRVG-1 without smoke (Osama 18 Nov 2026 15:2x PST, thread 1571014792016171120: "JRVG should not have smoke"). JRVG-1 (unit 952) has one
# ability, 2009943, used by nothing else; it carries both the radar switch and 1 smoke salvo (ammo 268). Smoke off, radar kept.
ok([r['UnitId'] for r in UAB.values() if r['AbilityId']==2009943]==[952] and AB[2009943].get('IsSmoke') and AB[2009943].get('IsRadar'),'JRVG-1 ability 2009943: own, smoke + radar')
ok(not any(2009943 in (o.get('Ability1Id'),o.get('Ability2Id'),o.get('Ability3Id')) for o in t['OptionsJson'].values()),'2009943 on no option')
g.put('AbilitiesJson',2009943,{'IsSmoke':False,'SmokeAmmunitionQuantity':0})
ok(not AB[2009943]['IsSmoke'] and AB[2009943]['SmokeAmmunitionQuantity']==0 and AB[2009943]['IsRadar'],'JRVG-1 smoke off, radar kept')
rec['jrvg1_no_smoke']={'unit':952,'ability':2009943,'from':{'IsSmoke':True,'SmokeAmmunitionQuantity':1},'to':{'IsSmoke':False,'SmokeAmmunitionQuantity':0},'kept':'radar switch'}
# ---------- Contested zones neutralise on every map (Osama 18 Nov 2026 15:1x PST, thread 1571014792016171120: "make sure on all maps, if someone
# contests a point, it neutralizes it"; Lateralus 21:51 UTC public #oversights: "Dam zones don't neutralize with multiple players in them"). Map files,
# not table data: releases/0.8/scenarios/common.py write() sets forceNeutral on every zone. dev.43 had it off on all 12 zones of the 4 Dam maps
# (3v3 Dam, Dam Skirmish, PvE Dam 3P and its Skirmish), on for all 206 other zones. Test build of all 32 maps: 254 zones on; only the 4 Dam .bascr
# change, the other 28 are byte-identical to dev.43. Not yet seen in game.
rec['zones_force_neutral']={'file':'releases/0.8/scenarios/common.py','changed_maps':['[FA] [3v3] Dam 0.2','[FA] [3v3] Dam Skirmish 0.2','[FA] [PvE] Dam vs China (3P) 0.1','[FA] [PvE] Dam vs China (3P) Skirmish 0.1'],'verified':'map files only; not seen in game'}
# ---------- China AT launchers like vanilla (Osama 18 Nov 2026 15:3x PST, thread 1571014792016171120, after the outlier scan: "tank hunters should
# have 6 ammo for each munition and then 50 points. the 1 PF-89 shot teams, we need to fix them, assault raiders 6, amored scouts 4, Infantry 6,
# marines 6, recon patrol 4. Taishan please fix it so they have 4 disposable at weapons ... Mech. rifles should be 5 PF-89, Blood Wolves should carry 4").
# Vanilla disposables: one round per carrier, several carriers (AT4/LAW/RPG-26: 3-8 men). The PF-89 goes into the empty special slot of more members
# (riflemen first, then DMR/MG men); its ammo row stays 1 per carrier. Marines have only 5 free special slots, so one of the three QLG-10A
# underbarrel grenadiers (2015888) swaps to the PF-89 for the 6th. Prices unchanged except Tank Hunters. Marine Recon (4 men, two of them with the
# QTS-11 grenade launcher) is NOT changed here: 4 carriers would remove both grenade launchers; asked first.
_SM=t['SquadMembersJson'];_WA4=t['WeaponAmmunitionsJson'];_PF89=_SM[2014963]['SpecialWeaponId']
ok(t['WeaponsJson'][_PF89]['HUDName'].strip()=='PF-89','PF-89 weapon id')
_pf={1146:(6,[2014965,2014966,2014967,2014968,2014962]),1160:(4,[2015068,2015069,2015071]),1175:(6,[2015920,2015922,2015923,2015919,2015917]),
     1192:(6,[2015889,2015882,2015883,2015884,2015888]),1201:(4,[2015533,2015534,2015535]),1203:(4,[2015557,2015558,2015555]),
     1163:(5,[2015105,2015106,2015100]),1183:(4,[2015324,2015325])}
_pfrec={}
for _u,(_n,_ms) in _pf.items():
    for _m in _ms:
        ok(_SM[_m]['UnitId']==_u and (_SM[_m]['SpecialWeaponId']==0 or _m==2015888),('free special slot',_u,_m))
        g.put('SquadMembersJson',_m,{'SpecialWeaponId':_PF89})
    _carr=sum(1 for r in _SM.values() if r['UnitId']==_u and _PF89 in (r['PrimaryWeaponId'],r['SpecialWeaponId']))
    _am=[r for r in _WA4.values() if r['UnitId']==_u and r['WeaponId']==_PF89]
    ok(len(_am)==1,('one PF-89 ammo row',_u))
    if _am[0]['Quantity']!=1:g.put('WeaponAmmunitionsJson',_am[0]['Id'],{'Quantity':1})
    ok(_carr==_n and _WA4[_am[0]['Id']]['Quantity']==1,(t['Units'][_u]['HUDName'],'PF-89 carriers',_carr,'want',_n))
    _pfrec[str(_u)]={'name':t['Units'][_u]['HUDName'].strip(),'pf89_carriers':_n,'rounds_each':1}
ok(sum(1 for r in _SM.values() if r['UnitId']==1192 and r['SpecialWeaponId']==_SM[2015886]['SpecialWeaponId'])==2,'Marines keep 2 QLG-10A')
# Tank Hunters (1139): PF-98A HEAT and DZT-98 thermobaric 10 + 10 -> 6 + 6, price 55 -> 50.
for _r in (2014891,2014892):ok(_WA4[_r]['UnitId']==1139,('Tank Hunters ammo row',_r));g.put('WeaponAmmunitionsJson',_r,{'Quantity':6})
ok(t['Units'][1139]['Cost']==55,'Tank Hunters was 55');g.put('Units',1139,{'Cost':50})
rec['china_at_launchers']={'pf89':_pfrec,'marines_qlg10a_to_pf89':2015888,'tank_hunters_1139':{'ammo':'PF-98A 6 + DZT-98 6 (was 10 + 10)','cost':'55 -> 50'},
    'not_changed':'Marine Recon 1224 (would lose both QTS-11 grenade launchers), PF-98 Tank Hunters 1155 (10 rds, 45), PF-98 Team 1172 (10+10, 55)'}
# ---------- Z-10K detection 3200 and Z-19 out of the Air Force (same message: "Z-10K should have 3200 detection, Z-19 removed from Airforce").
# Z-10K (913) used shared sensor 3 'Very Good Optics' (2300/1250/1000, 120 users): it gets its own copy with ground optics 3200.
# Z-19 (940) is the Air Force card; its only specialization row 2008228 (PLAAF Air Force) is removed. Z-19 1103 (Motorized) and the Z-19G stay.
_SU=[r for r in t['SensorUnitsJson'].values() if r['UnitId']==913]
ok(len(_SU)==1 and _SU[0]['SensorId']==3,'Z-10K uses sensor 3')
_z10k=g.add('SensorsJson',t['SensorsJson'][3],{'Name':'Optics Z-10K 3200','IsDefault':False,'OpticsGround':3200.0})
g.put('SensorUnitsJson',_SU[0]['Id'],{'SensorId':_z10k})
ok(set(t['SensorsJson'][_z10k])==set(t['SensorsJson'][3]) and t['SensorsJson'][_z10k]['OpticsGround']==3200.0,'Z-10K sensor fields like vanilla row, 3200')
ok(t['SpecializationAvailabilitiesJson'][2008228]['UnitId']==940,'Z-19 Air Force row')
g.remove('SpecializationAvailabilitiesJson',2008228)
ok(not any(r['UnitId']==940 for r in t['SpecializationAvailabilitiesJson'].values()),'Z-19 940 in no spec')
rec['z10k_z19']={'z10k_sensor':_z10k,'z10k_optics_ground':3200,'z19_940_removed_spec_row':2008228}
# ---------- FAModels 0.3.35: free models nothing uses (Osama 18 Nov 2026 14:4x PST, thread 1572551547726991400: "ishtar is the one that crashed, we should
# free models"). Code only, no data rows. Since 0.3.25 every model loaded stayed in memory for the whole session; ishtar's dev.41 game went down
# while browsing the Arsenal after a match with 132 models held (~2.5 GB of textures; the whole Arsenal is ~6.6 GB, Assets 0.2.46). Unload.cs: on
# every scene load, models no live unit uses are destroyed (mesh, material, FAM_ textures), so Arsenal models go before a battle and battle models
# go back in the menu; in the menu all but the 12 most recently used unused models are freed after each new load. Infantry weapon files are kept.
# FAMODELS memory line every 60 s (process working set/private, cache models, vertices, ~MB meshes and textures, freed count). Not yet seen in game.
# BUILD: complete package --famodels releases/0.6/experimental-model-loader/bin/Release/net6.0/FAModels.dll (0.3.35, built with
# -p:GameDir=work/game-1.2.2.1); FAModels.dll is in the Assets package, so this batch also makes a new Assets version for launcher players.
rec['famodels_free_unused']={'version':'0.3.35','file':'releases/0.6/experimental-model-loader/Unload.cs','menu_keep':12,'verified':'compiles; not seen in game'}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)

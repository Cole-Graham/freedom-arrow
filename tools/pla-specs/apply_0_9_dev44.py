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
# ---------- Vanilla Ignore Cover, China by the vanilla rules (Osama 18 Nov 2026 15:4x PST, thread 1567745029781454889: "ok lets try this out, with
# the vanilla ignore cover. Please make sure for china it is applied like the vanilla rules"). Goes with the runtime change in this batch: no stress
# protection in the open (game-config InfantryOpenDamageFloor 1, PerSoldier 0) and buildings a flat 30% (BuildingDamageFloor 0.3). This replaces
# the earlier dev.44 autocannon change (IC 0.2439, commit cb7f185c). Native rows: every IgnoreCover FA changed goes back to the vanilla value
# (163 rows in dev.43: bombs, rockets, thermobarics, tube and rocket artillery, autocannons, tank HE). New rows (China and FA clones) take the value
# vanilla gives the same kind of round, first rule that matches.
import re as _re
_A=t['AmmunitionsJson'];_VA={r['Id']:r for r in json.loads((a.vanilla/'AmmunitionsJson.json').read_text())}
_used={r.get('AmmunitionId') for r in t['WeaponAmmunitionsJson'].values()}
_ic=lambda r:r.get('IgnoreCover') or 0
_RULES=[  # (pattern on Name + HUDName, vanilla IC, vanilla example)
 (r'smoke|SMK',None,'left as is'),
 (r'incendiar|napalm',1.0,'MROZ / M202 / Grad incendiary 1.0'),
 (r'nuclear|nuke',0.5,'B61 / Kh-102 nuclear 0.5'),
 (r'snip|precision|QBU-10',1.0,'sniper rifles 1.0'),
 (r'DMR|QBU-191|QBU-88',0.25,'DMRs 0.25'),
 (r'QLU-?11|QTS-?11|M-25 CDTE|XM25',0.25,'XM25 airburst 0.25'),
 (r'thermobaric',0.0,'RPG-7 TBG-7V / RShG / TOS-1 thermobaric 0'),
 (r'\bDF-|YJ-21|SY-400|ARRW|MAKO',0.5,'Iskander-M / Tochka-U HE / Kinzhal HE 0.5'),
 (r'Fire Dragon 480',0.4,'PrSM 0.4'),
 (r'Fire Dragon (300|280)|300 mm|370 mm',0.3,'Smerch 300 mm 0.3'),
 (r'220 mm',0.22,'Uragan 220 mm 0.22'),
 (r'122 mm rocket',0.12,'Grad 122 mm 0.12'),
 (r'(155|152) mm|GP155',0.15,'152/155 mm howitzers 0.15'),
 (r'122 mm|120 mm gun-mortar',0.12,'122 mm 2A31, 120 mm Nona 2A51 0.12'),
 (r'76 mm HE \(proximity\)',0.13,'AK-130 / Mk 45 naval guns 0.13'),
 (r'(120|125) mm.*\bHE\b',0.3,'120/125 mm tank HE 0.3'),
 (r'120 mm.*HEAT',0.2,'M256 / Leopard 2A8 120 mm HEAT 0.2 (125 mm HEAT is 0)'),
 (r'(85|100|105) mm.*\bHE\b',0.1,'100 mm 2A70 / MT-12 HE, 105 mm M68 HESH 0.1'),
]
_rows={'native':{},'new':{}};_rule_hits={}
for _i,_r in sorted(_A.items()):
    if _i not in _used:continue
    if _i in _VA:
        _want=_ic(_VA[_i]);_k='native';_why='vanilla row'
    else:
        _nm=str(_r.get('Name'))+' | '+str(_r.get('HUDName'));_want=0.0;_why='no rule: vanilla 0 (autocannons, MGs, rifles, RPG HEAT, ATGMs, bombs, rockets)'
        for _pat,_v,_ex in ([] if _r.get('Seeker') and (_r.get('PenetrationAtGroundRange') or 0)>=300 else _RULES):  # guided AT missiles named "HE" (ZBD-04 HJ-9 rows): vanilla ATGMs 0
            if _re.search(_pat,_nm,_re.I):
                _want=_ic(_r) if _v is None else _v;_why=_ex;break
        _k='new'
    _old=_ic(_r)
    if _old!=_want:
        g.put('AmmunitionsJson',_i,{'IgnoreCover':_want})
        _rows[_k][str(_i)]={'name':_r.get('HUDName') or _r.get('Name'),'from':_old,'to':_want,'rule':_why}
ok(535 not in map(int,_rows['native']),'Ogon A-22 535 untouched')
ok(all(_ic(_A[i])==_ic(_VA[i]) for i in _used if i in _VA),'every used vanilla row has the vanilla IgnoreCover')
ok(len(_rows['native'])>=150,('native rows restored',len(_rows['native'])))
# Spot checks against vanilla: Bushmaster HE 0, 155 mm M109A7 HE 0.15, T-90M 125 mm HE 0.3, TOS-1 0, Mk82 0, sniper 1.0
for _i,_v in ((26,0),(4,0.15),(243,0.3),(178,0),(61,0),(275,1.0),(133,0.08)):ok(_ic(_A[_i])==_v,(_i,_A[_i]['Name'],_v))
_chk={2009831:0,2011225:0,2009077:0.3,2009079:0,2009857:0.2,2009133:0.1,2010479:0.12,2018337:0.15,2009463:0.12,2010163:0.12,2010439:0.3,
      2017460:0.22,2017463:0.4,2010351:0.5,2016544:0,2016607:0,2017197:0,2018321:0,2018448:0,2012516:0,2011921:0,2013058:1.0,2012055:1.0,2004001:0.25,
      2019271:0.25,2009953:0.13,2010071:0.1,2018752:0.15,2009025:0,2011173:0,2009023:0.1}
for _i,_v in _chk.items():ok(_ic(_A[_i])==_v,(_i,_A[_i].get('HUDName'),_v))
rec['vanilla_ignore_cover']={'basis':'vanilla AmmunitionsJson; new rows by the rules above','native_restored':_rows['native'],'new_rows':_rows['new'],
    'runtime':'game-config InfantryOpenDamageFloor 1, InfantryOpenDamagePerSoldier 0, BuildingDamageFloor 0.3, BuildingDamagePerSoldier 0'}
print('ignore cover: native rows restored',len(_rows['native']),'new rows changed',len(_rows['new']))
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

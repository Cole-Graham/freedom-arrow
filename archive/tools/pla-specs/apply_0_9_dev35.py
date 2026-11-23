"""Freedom Arrow 0.9.0-dev.35 data over exact 0.9.0-dev.34 (16 Nov 2026). Opened by BA Codex thread 1571014792016171120 (Osama).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.35';PREV='0.9.0-dev.34'
# dev.34 was built in out/local-dev34.
BASE=json.loads((REL/f'out/local-dev34/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev34/FreedomArrow-{PREV}-complete.bamod'
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
sys.path.insert(0,str(Path(__file__).parent/'lateralus'))
# ---------- Conscript Recon (unit 1213) to 4 men, 25 points (Osama 16 Nov 2026 20:39 PST, thread 1571014792016171120: "conscript recon to 4 man (lose
# the qcw and QBZ-191 and add 3 QBZ-95)", "and 20 points"; 20:4x: "conscript recon are 25 pts"). Was 6 men: 4 x QCW-05, 1 x QBU-88, 1 x QBZ-191, 40 points. Now 3 x QBZ-95 (weapon 2012205,
# ammo 2012206, 120 rounds per row as in the other China squads that carry it) and the QBU-88. Squad weapon orders stay 0, 1 (no gap).
SM,SW,WA=t['SquadMembersJson'],t['SquadWeaponsJson'],t['WeaponAmmunitionsJson']
_m=sorted((r['Id'],r['PrimaryWeaponId']) for r in SM.values() if r['UnitId']==1213)
ok(_m==[(2015657,2013349),(2015658,2013349),(2015659,2013349),(2015660,2013349),(2015661,2012821),(2015662,2003998)] and U[1213]['Cost']==40 and U[1213]['HUDName']=='Conscript Recon','Conscript Recon: 4 QCW-05, QBU-88, QBZ-191, 40 points')
ok(sorted((r['Id'],r['WeaponId'],r['Order']) for r in SW.values() if r.get('UnitId')==1213)==[(2015663,2003998,1),(2015665,2012821,2),(2015667,2013349,0)],'Conscript Recon squad weapons')
ok(sorted((r['Id'],r['WeaponId'],r['AmmunitionId'],r['Quantity']) for r in WA.values() if r.get('UnitId')==1213)==[(2015664,2003998,2003999,160),(2015666,2012821,2012822,60),(2015668,2013349,2013350,20)],'Conscript Recon ammo rows')
ok(t['WeaponsJson'][2012205].get('HUDName')=='QBZ-95' and sorted({(r['AmmunitionId'],r['Quantity']) for r in WA.values() if r.get('WeaponId')==2012205})==[(2012206,120)],'QBZ-95 2012205 with ammo 2012206 x 120')
for _id in (2015657,2015658,2015659):g.put('SquadMembersJson',_id,{'PrimaryWeaponId':2012205})
for _id in (2015660,2015662):g.remove('SquadMembersJson',_id)
g.put('SquadWeaponsJson',2015667,{'WeaponId':2012205,'Order':0});g.put('SquadWeaponsJson',2015665,{'Order':1});g.remove('SquadWeaponsJson',2015663)
g.put('WeaponAmmunitionsJson',2015668,{'WeaponId':2012205,'AmmunitionId':2012206,'Quantity':120});g.remove('WeaponAmmunitionsJson',2015664)
g.put('Units',1213,{'Cost':25})
ok(sorted(r['PrimaryWeaponId'] for r in SM.values() if r['UnitId']==1213)==[2012205,2012205,2012205,2012821] and U[1213]['Cost']==25
   and sorted((r['WeaponId'],r['Order']) for r in SW.values() if r.get('UnitId')==1213)==[(2012205,0),(2012821,1)]
   and sorted((r['WeaponId'],r['Quantity']) for r in WA.values() if r.get('UnitId')==1213)==[(2012205,120),(2012821,60)],'Conscript Recon: 3 QBZ-95 + QBU-88, 25 points')
rec['conscript_recon']={'unit':1213,'men':[6,4],'cost':[40,25],'weapons':'3 x QBZ-95 2012205 + QBU-88 2012821','removed_members':[2015660,2015662]}
# ---------- Falcons (unit 1185): 2 x QLB-06 -> 1 x QLU-11, 75 points (Osama 16 Nov 2026 20:4x PST, thread 1571014792016171120: "falcons replace 2x ALB-06
# with QLU-11 and 75 points", then "sorry only 1x QLU"; "ALB-06" = the squad's two QLB-06 grenade launchers). The second grenadier takes the squad rifle QMK
# 2019300 (its ammo row is per carrier), so the squad stays at 8 men. QLU-11 2004002 with ammo 2004003 x 120, as the 33 other squads that carry it.
_f=sorted((r['Id'],r['PrimaryWeaponId']) for r in SM.values() if r['UnitId']==1185 and r['PrimaryWeaponId'] in (2016050,2004002))
ok(_f==[(2015349,2016050),(2015350,2016050)] and U[1185]['Cost']==65 and U[1185]['HUDName']=='Falcons 猎鹰','Falcons: 2 QLB-06, 65 points')
ok((SW[2018065]['UnitId'],SW[2018065]['WeaponId'])==(1185,2016050) and (WA[2018069]['UnitId'],WA[2018069]['WeaponId'],WA[2018069]['Quantity'])==(1185,2016050,120),'Falcons QLB-06 squad weapon and ammo rows')
ok(t['WeaponsJson'][2004002].get('HUDName')=='QLU-11' and sorted({(r['AmmunitionId'],r['Quantity']) for r in WA.values() if r.get('WeaponId')==2004002})==[(2004003,120)],'QLU-11 2004002 with ammo 2004003 x 120')
g.put('SquadMembersJson',2015349,{'PrimaryWeaponId':2004002});g.put('SquadMembersJson',2015350,{'PrimaryWeaponId':2019300})
g.put('SquadWeaponsJson',2018065,{'WeaponId':2004002});g.put('WeaponAmmunitionsJson',2018069,{'WeaponId':2004002,'AmmunitionId':2004003,'Quantity':120})
g.put('Units',1185,{'Cost':75})
ok(not any(r['UnitId']==1185 and 2016050 in (r['PrimaryWeaponId'],r['SpecialWeaponId']) for r in SM.values()) and sum(r['PrimaryWeaponId']==2004002 for r in SM.values() if r['UnitId']==1185)==1
   and sum(r['PrimaryWeaponId']==2019300 for r in SM.values() if r['UnitId']==1185)==6 and U[1185]['Cost']==75,'Falcons: 1 QLU-11, 6 QMK, no QLB-06, 75 points')
rec['falcons']={'unit':1185,'QLB-06 -> QLU-11':[2015349],'QLB-06 -> QMK':[2015350],'cost':[65,75]}
# ---------- Osama 16 Nov 2026 20:5x PST, thread 1571014792016171120: "VT-5 no APS protection options / PLZ-70 moved to airborne / J-36 I think go touched by
# some SEAD buffs. It should only have 2 availability. Same with J-35. All 5th gen fighters are 2x availability and shouldn't have been touched by any SEAD
# point buffs".
# VT-5 (1261): the protection slot 2019111 (No APS 31075 / Iron Fist APS 31076, +60) and its option ability links go; the default ability 2019108 stays.
_O,_M,_UA=t['OptionsJson'],t['ModificationsJson'],t['UnitAbilitiesJson']
ok(_M[2019111]['UnitId']==1261 and sorted(i for i,o in _O.items() if o.get('ModificationId')==2019111)==[31075,31076],'VT-5 APS slot 2019111 with options 31075/31076')
ok(sorted((r['Id'],r['AbilityId']) for r in _UA.values() if r['UnitId']==1261)==[(2018640,2019108),(2019109,82),(2019110,4)],'VT-5 ability links')
for _i in (31075,31076):g.remove('OptionsJson',_i)
g.remove('ModificationsJson',2019111);g.remove('UnitAbilitiesJson',2019109);g.remove('UnitAbilitiesJson',2019110)
ok(not any(m.get('UnitId')==1261 for m in _M.values()) and [r['AbilityId'] for r in _UA.values() if r['UnitId']==1261]==[2019108],'VT-5: no APS options')
# PLZ-70 (1040) "to airborne": China's airborne corps is part of the air force, so its deck row moves from PLARF Rocket Conscript (19) to PLAAF Air Force (17).
_SA=t['SpecializationAvailabilitiesJson']
ok([(r['Id'],r['SpecializationId']) for r in _SA.values() if r.get('UnitId')==1040]==[(2008885,19)] and U[1040]['HUDName']=='PLZ-70','PLZ-70 in PLARF Conscript')
g.put('SpecializationAvailabilitiesJson',2008885,{'SpecializationId':17})
ok(assign['assignments'].get('1040')==[19],'PLZ-70 assignment 19');assign['assignments']['1040']=[17]   # pla-spec-assignments.json, read by verify_roster_revision.py
ok([r['SpecializationId'] for r in _SA.values() if r.get('UnitId')==1040]==[17],'PLZ-70 in PLAAF Air Force')
# 5th/6th-gen fighters out of the SEAD changes (lateralus/sead_availability.py and sead_prices.py, dev.33): back to 2 cards and their pre-SEAD prices.
# J-36 base price stays 355 (Osama's dev.32 +50 was set over the SEAD price); its x8 loadout is restored.
sys.path.insert(0,str(Path(__file__).parent/'lateralus'));import sead_availability as _SAV,sead_prices as _SP
FIFTH_UNITS=(921,929,966,1251);FIFTH_OPTIONS=(1888,1889,24653,24654,24656,24657,24659,24660,24664,20191,20198,20234)
for _u in FIFTH_UNITS:
    _n,_row,_old,_new=_SAV.ROWS[_u];ok(_SA[_row]['MaxAvailabilityXp0']==3,f'{_n}: 3 cards');g.put('SpecializationAvailabilitiesJson',_row,{'MaxAvailabilityXp0':2})
for _u in (921,966,1251):
    _n,_old,_new=_SP.UNITS[_u];ok(U[_u]['Cost']==_new,f'{_n}: SEAD price {_new}');g.put('Units',_u,{'Cost':_old})
ok(U[929]['Cost']==355,'J-36 355 (left as is)')
for _i in FIFTH_OPTIONS:
    _u,_n,_old,_new=_SP.OPTIONS[_i];ok(_O[_i].get('Cost')==_new,f'{_u} {_n}: SEAD price {_new}');g.put('OptionsJson',_i,{'Cost':_old})
ok(all(_SA[_SAV.ROWS[u][1]]['MaxAvailabilityXp0']==2 for u in FIFTH_UNITS) and [U[u]['Cost'] for u in (921,966,1251,929)]==[255,255,250,355]
   and all(_O[i]['Cost']==_SP.OPTIONS[i][2] for i in FIFTH_OPTIONS),'5th gen: 2 cards, pre-SEAD prices')
rec['vt5_no_aps']={'unit':1261,'removed':{'modification':2019111,'options':[31075,31076],'unit_abilities':[2019109,2019110]}}
rec['plz70_airborne']={'unit':1040,'row':2008885,'spec':[19,17]}
rec['fifth_gen_out_of_sead']={'cards_2':list(FIFTH_UNITS),'unit_cost':{u:_SP.UNITS[u][1] for u in (921,966,1251)},'option_cost':{i:_SP.OPTIONS[i][2] for i in FIFTH_OPTIONS},'j36_cost':355}
# ---------- Osama 16 Nov 2026 21:15 / 22:2x PST, thread 1571014792016171120.
_A,_W,_AR,_ARM=t['AmmunitionsJson'],t['WeaponsJson'],t['UnitArmorsJson'],t['ArmorsJson']
# "CTL-181 NLOS still does not have the option to precision strike": precision strike is the cruise-missile order, which the game gives a cruise launcher
# (weapon Type 82) firing cruise-trajectory ammunition (TrajectoryType 200, vanilla Iskander-K 9M728). 0.8.0-dev.4 copied both; the NLOS rework later
# gave CTL-181 its own ammunition 2018321 on the Hellfire trajectory 110, which has no precision strike. Back to 200; the NLOS trait stays.
ok(_W[2018322]['Type']==82 and _A[2018321]['TrajectoryType']==110 and sorted({x['UnitId'] for x in WA.values() if x['AmmunitionId']==2018321})==[1054],'CTL-181: cruise launcher, Hellfire trajectory')
g.put('AmmunitionsJson',2018321,{'TrajectoryType':200});ok(_A[2018321]['TrajectoryType']==200,'CTL-181 cruise trajectory')
# "Blood Wolves ... CH-901, it should be a precision strike": the CH-901 (weapon 2018447, ammo 2018448, Blood Wolves only) was an infantry ATGM (Type 80,
# trajectory 110). Same cruise launcher type and trajectory as CTL-181. Not yet seen in game on an infantry squad.
ok(_W[2018447]['Type']==80 and _A[2018448]['TrajectoryType']==110 and sorted({x['UnitId'] for x in WA.values() if x['WeaponId']==2018447})==[1183],'CH-901: infantry ATGM on Blood Wolves only')
g.put('WeaponsJson',2018447,{'Type':82,'IsVerticalLauncher':True});g.put('AmmunitionsJson',2018448,{'TrajectoryType':200})
ok(_W[2018447]['Type']==82 and _A[2018448]['TrajectoryType']==200,'CH-901 cruise launcher and trajectory')
# "LY-1 10 hp" (armour row 2019439, LY-1 only) and "LY-1 rate of fire should be 20 not 60 ... once every 3 seconds" (laser 2019445, LY-1 only).
ok(_ARM[2019439]['MaxHealthPoints']==14 and sorted({r['UnitId'] for r in _AR.values() if r['ArmorId']==2019439})==[1275],'LY-1 14 HP, own armour row')
g.put('ArmorsJson',2019439,{'MaxHealthPoints':10})
ok(_W[2019445]['TimeBetweenBurstsMin']==1.0 and _W[2019445]['TimeBetweenBurstsMax']==1.0 and sorted({x['UnitId'] for x in WA.values() if x['WeaponId']==2019445})==[1275],'LY-1 laser 1 s, LY-1 only')
g.put('WeaponsJson',2019445,{'TimeBetweenBurstsMin':3.0,'TimeBetweenBurstsMax':3.0})
ok(_ARM[2019439]['MaxHealthPoints']==10 and _W[2019445]['TimeBetweenBurstsMin']==3.0,'LY-1 10 HP, one pulse every 3 s')
# "ZBD-20 has 16 HJ-16's in game ... I think it's 4": both HJ-16 variants 16 -> 4 on ZBD-20 (945); ZBD-20 Recon (1256) 8 -> 4.
_hj={2018443:16,2018879:16,2018444:8,2018882:8}
ok(all(WA[i]['Quantity']==q and WA[i]['WeaponId'] in (2018803,2018866) for i,q in _hj.items()),'ZBD-20 HJ-16 rows 16/16, Recon 8/8')
for i in _hj:g.put('WeaponAmmunitionsJson',i,{'Quantity':4})
# "ZTZ-59 remove HEAT, ZTZ-80 remove HEAT": ZTZ-59 (1060), ZTZ-59D1 (1260), ZTZ-80 (1061), ZTZ-80 / Type 80 (1081) lose the HEAT row; HE moves to order 1.
_heat={1060:(2010824,2010826),1260:(2018629,2018630),1061:(2010852,2010854),1081:(2011330,2011332)}
for _u,(_h,_he) in _heat.items():
    ok(WA[_h]['UnitId']==_u and 'HEAT' in _A[WA[_h]['AmmunitionId']]['HUDName'] and WA[_h].get('Order')==1 and WA[_he].get('Order')==2,f'{U[_u]["HUDName"]}: HEAT order 1, HE order 2')
    g.remove('WeaponAmmunitionsJson',_h);g.put('WeaponAmmunitionsJson',_he,{'Order':1})
    ok(not any(x['UnitId']==_u and 'HEAT' in (_A[x['AmmunitionId']].get('HUDName') or '') for x in WA.values()),f'{U[_u]["HUDName"]}: no HEAT')
# "MD-22 afterburners ... model it off an F-35 for its stand in": NOT in dev.35. The MD-22 loadouts mount on slot 0 of the S-70 Okhotnik stand-in; the
# F-35A body has no slot 0 (check_mount_weapons.py: 7 loadouts would lose their weapons). Needs the loadouts moved to F-35 slots first.
# "Helocopters didn't seem to fire their CM-501GA": the only carrier is Z-21 (loadout 24645, weapon 2017902, ammo 2017128). Its seeker reached 250 m
# (MaxSeekerDistance) against a 1000 m range; the helicopter ATGMs that fire have seeker reach = range (800-950 m). Seeker reach 1000 m.
ok(_A[2017128]['MaxSeekerDistance']==250.0 and _A[2017128]['GroundRange']==1000.0 and sorted({x['UnitId'] for x in WA.values() if x['AmmunitionId']==2017128})==[1104],'CM-501GA seeker 250 m, range 1000, Z-21 only')
g.put('AmmunitionsJson',2017128,{'MaxSeekerDistance':1000.0});ok(_A[2017128]['MaxSeekerDistance']==1000.0,'CM-501GA seeker 1000 m')
# "Abrams X should not have Jammer" (Osama 22:3x): its default ability 2001843 (Abrams X only) carries ECMAccuracyMultiplier 0.7, the jammer. 0.0 = no jammer
# (as 335 of the abilities, including its own smoke ability 2001844).
_AB=t['AbilitiesJson']
ok(_AB[2001843]['ECMAccuracyMultiplier']==0.7 and sorted(r['UnitId'] for r in t['UnitAbilitiesJson'].values() if r['AbilityId']==2001843)==[964],'Abrams X jammer 0.7, own ability')
g.put('AbilitiesJson',2001843,{'ECMAccuracyMultiplier':0.0});ok(_AB[2001843]['ECMAccuracyMultiplier']==0.0,'Abrams X no jammer')
rec['osama_2215']={'ctl181_trajectory':[110,200],'ch901':{'weapon_type':[80,82],'trajectory':[110,200]},'ly1':{'hp':[14,10],'seconds_between_pulses':[1,3]},
                   'zbd20_hj16':{'zbd20':[16,4],'recon':[8,4]},'heat_removed':{str(u):h for u,(h,_) in _heat.items()},'cm501ga_seeker_m':[250,1000],'abrams_x_ecm':[0.7,0.0]}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)

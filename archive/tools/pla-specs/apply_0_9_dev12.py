"""Freedom Arrow 0.9.0-dev.12 data batch over exact 0.9.0-dev.11 (Osama, 14-15 Nov 2026, thread 1567745029781454889).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.0-dev.12';PREV='0.9.0-dev.11'
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
W=t['WeaponsJson'];WA=t['WeaponAmmunitionsJson']
# ---------- QN-506 QN-502 missile: one missile per shot (Osama 15 Nov 2026 02:45 PST: "QN-506 QN-502 missile only 1 missile per shot").
# Weapon 2009647 fired bursts of 2 (1 s apart); now 1 per shot, 3 s between shots, 4 rounds as before.
ok(W[2009647]['HUDName']=='QN-502 guided missile' and W[2009647]['ShotsPerBurstMin']==2==W[2009647]['ShotsPerBurstMax'],'QN-502 weapon')
ok(sorted({r['UnitId'] for r in WA.values() if r['WeaponId']==2009647})==[937],'QN-502 only on QN-506')
g.put('WeaponsJson',2009647,{'ShotsPerBurstMin':1,'ShotsPerBurstMax':1,'TimeBetweenShotsInBurst':0.0});rec['qn502_single']={'weapon':2009647,'burst':[2,1]}
# ---------- HQ-9C missiles (Osama 15 Nov 2026 02:52 PST: "HQ-9C doesn't have missiles in game"). Unit 911 (S-400 body) had two default
# mounts at Order 0: an old empty one (turret 2009210 "PLA HQ-9 mount 0", S-300PM launcher model, no weapon) and the S-400 launcher
# with the HQ-9C missile (turret 2014557). The empty mount goes, so the missile launcher is the only one, as on the vanilla S-400.
TU=t['TurretUnitsJson'];TW=t['TurretWeaponsJson'];TJ=t['TurretsJson'];O=t['OptionsJson']
ok(U[911]['HUDName']=='HQ-9C' and sorted((r['TurretId'],r['Order']) for r in TU.values() if r['UnitId']==911)==[(2009210,0),(2014557,0)],'HQ-9C mounts')
ok(not [w for w in TW.values() if w['TurretId']==2009210] and sorted({r['UnitId'] for r in TU.values() if r['TurretId']==2009210})==[911],'empty mount, HQ-9C only')
ok(not [o for o in O.values() if 2009210 in [o.get(f'Turret{k}Id') for k in range(17)]],'no option uses it')
ok([W[w['WeaponId']]['HUDName'] for w in TW.values() if w['TurretId']==2014557]==['HQ-9C missile'] and [r['Quantity'] for r in WA.values() if r['UnitId']==911]==[4],'HQ-9C missile mount and 4 rounds')
g.remove('TurretUnitsJson',next(r['Id'] for r in TU.values() if r['UnitId']==911 and r['TurretId']==2009210));g.remove('TurretsJson',2009210)
rec['hq9c_mount']={'unit':911,'removed_empty_turret':2009210,'kept':2014557}
# ---------- One QTS-11 grenade launcher for every China squad (Lateralus 15 Nov 2026 02:52 PST: "The QTS-11 Grenade launcher on china's
# Marine Recon need to be the same one as used on Godswords ... Remove the variant"; 03:14 PST: "I'm overriding Osama's decision ... All units
# should use the new version of the QTS-11 grenade launcher. For infantry, different stats should actually always be a different weapon").
# All 31 squads with shared launcher 2004006 (ammo 2004007: 2.5 dmg, pen 15, 1.0 s) now carry 2019270 (ammo 2019271: 1.5 dmg, pen 40, 4.0 s),
# each with its own rounds (48). Their model entries follow, or the vanilla M4 with M203 is drawn (the dev.11 Godswords fix). No unit carries
# 2004006/2004007 afterwards; the rows stay in the data unused. 2019270 loses "Godswords" from its internal Name.
IW=SRC/'UserData/FAModels/infantry-weapons.json';iw=json.loads(IW.read_text())
_SM=t['SquadMembersJson'];_SW=t['SquadWeaponsJson'];_A=t['AmmunitionsJson'];TW=t['TurretWeaponsJson']
OLD,NEW=2004006,2019270
ok(W[NEW]['Name']=='PLA Godswords QTS-11 grenade launcher' and W[OLD]['Name']=='PLA Test Underbarrel QTS11' and W[OLD]['HUDIcon']==W[NEW]['HUDIcon'],'QTS-11 launchers')
ok(_A[2019271]['Damage']==1.5 and _A[2019271]['PenetrationAtMinRange']==40.0 and _A[2004007]['Damage']==2.5,'QTS-11 launcher ammo')
ok(not [r for r in TW.values() if r['WeaponId']==OLD] and {r['WeaponId'] for r in WA.values() if r['AmmunitionId']==2004007}=={OLD},'2004006 only on squads')
_u=sorted({r['UnitId'] for r in WA.values() if r['WeaponId']==OLD});ok(len(_u)==31 and 1224 in _u and all(U[x]['CountryId']==4 for x in _u),('2004006 squads',len(_u)))
_n={'members':0,'rows':0,'models':0}
for _x in [m for m in _SM.values() if m['UnitId'] in _u and OLD in (m['PrimaryWeaponId'],m['SpecialWeaponId'])]:
    ok(_x['SpecialWeaponId']==OLD and _x['PrimaryWeaponId']!=OLD,('launcher in special slot',_x['Id']))
    g.put('SquadMembersJson',_x['Id'],{'SpecialWeaponId':NEW});_n['members']+=1
for _r in [r for r in _SW.values() if r['WeaponId']==OLD]:
    ok(not [q for q in _SW.values() if q['UnitId']==_r['UnitId'] and q['WeaponId']==NEW],('no second launcher row',_r['UnitId']))
    g.put('SquadWeaponsJson',_r['Id'],{'WeaponId':NEW})
for _r in [r for r in WA.values() if r['WeaponId']==OLD]:
    ok(_r['AmmunitionId']==2004007,('launcher ammo',_r['Id']));g.put('WeaponAmmunitionsJson',_r['Id'],{'WeaponId':NEW,'AmmunitionId':2019271});_n['rows']+=1
# Sharp Swords 1174 has a model entry for 2004006 but no longer carries a launcher; that unused entry is left as it is.
_stale=sorted(e['unitId'] for e in iw if e['weaponId']==OLD and e['unitId'] not in _u);ok(_stale==[1174],('unused 2004006 model entries',_stale))
for _e in iw:
    if _e['weaponId']==OLD and _e['unitId'] in _u:ok(_e['file']=='w_qts11.fam',('model entry',_e['unitId']));_e['weaponId']=NEW;_n['models']+=1
ok(not [m for m in _SM.values() if OLD in (m['PrimaryWeaponId'],m['SpecialWeaponId'])] and not [r for r in WA.values() if r['WeaponId']==OLD] and not [r for r in _SW.values() if r['WeaponId']==OLD],'no unit carries 2004006')
ok(not [e for e in iw if e['weaponId']==OLD and e['unitId'] in _u],'no model entry for 2004006 on a launcher squad')
g.put('WeaponsJson',NEW,{'Name':'PLA infantry QTS-11 grenade launcher'});g.put('AmmunitionsJson',2019271,{'Name':'PLA infantry QTS-11 grenade launcher ammunition'})
rec['qts11_gl_one_weapon']={'from':[OLD,2004007],'to':[NEW,2019271],'squads':len(_u),'units':_u,**_n,'stats':{'damage':[2.5,1.5],'penetration':[15,40],'time_between_shots':[1.0,4.0]}}
# ---------- QBZ-192 = stat clone of the M4A1 URG-I, China's tier 3 rifle (Lateralus 15 Nov 2026 03:14 PST: "change the QBZ-192 to a stat clone
# of M4A1 Mod. II"; 03:31 PST: "Tier 3: QBZ-192 (change from Mod. II clone to M4A1 URG-I clone)"). The weapon rows already match (2013087 vs
# 722: only names, icon, model and sound differ). Its own round 2013088 (used only by the QBZ-192) takes every stat of the URG-I round 358
# (5.56x45 T3): damage 1.2 -> 1.8. 160 rounds per man, as before.
_cos={'Id','Name','HUDName','HUDIcon','ModelFileName','AudioPreset'}
ok({k for k in set(W[2013087])|set(W[722]) if W[2013087].get(k)!=W[722].get(k)}<=_cos,'QBZ-192 weapon = M4A1 URG-I weapon')
_d={k:_A[358][k] for k in _A[358] if k not in _cos and _A[2013088].get(k)!=_A[358][k]};ok(_d=={'Damage':1.8} and _A[2013088]['Damage']==1.2,('QBZ-192 round diff',_d))
ok({r['WeaponId'] for r in WA.values() if r['AmmunitionId']==2013088}=={2013087} and {r['Quantity'] for r in WA.values() if r['WeaponId']==2013087}=={160},'QBZ-192 round only on QBZ-192, 160 rounds')
g.put('AmmunitionsJson',2013088,_d);rec['qbz192_m4a1_urgi']={'weapon':2013087,'ammunition':2013088,'clone_of':[722,358],'damage':[1.2,1.8],'units':sorted({r['UnitId'] for r in WA.values() if r['WeaponId']==2013087})}
# ---------- Mountain Leopards (1186): one HJ-12, not three (Osama 15 Nov 2026 03:02 PST: "mountain leopards have 3 hj-12 missile launchers and
# 6 ammo"). All 3 men carried the HJ-12 at 2 missiles each (ammo rows are per man). Now only one QBZ-192 rifleman carries it, with 2
# missiles, like AT Troopers; the QBU-10 marksman and the other rifleman keep only their rifles. To confirm with Osama: launcher count/missiles.
_SM=t['SquadMembersJson'];HJ=2011864
_ml=sorted((m for m in _SM.values() if m['UnitId']==1186),key=lambda m:m['Id'])
ok(U[1186]['HUDName'].startswith('Mountain Leopards') and [m['SpecialWeaponId'] for m in _ml]==[HJ,HJ,HJ] and [W[m['PrimaryWeaponId']]['HUDName'] for m in _ml]==['QBU-10','QBZ-192','QBZ-192'],'Mountain Leopards 3x HJ-12')
ok([r['Quantity'] for r in WA.values() if r['UnitId']==1186 and r['WeaponId']==HJ]==[2],'2 HJ-12 missiles per man')
for m in (_ml[0],_ml[2]):g.put('SquadMembersJson',m['Id'],{'SpecialWeaponId':0})
ok(sum(1 for m in _SM.values() if m['UnitId']==1186 and m['SpecialWeaponId']==HJ)==1,'one HJ-12 left')
rec['mountain_leopards_hj12']={'unit':1186,'launchers':[3,1],'missiles':[6,2]}
# ---------- Falcons and Blood Wolves: 1 smoke (Osama 15 Nov 2026 03:15 PST: "Falcons and blood wolves 1 smoke"). Each has its own ability row
# (4 smokes); the hidden "Falcon" copy (1188) is left as it is.
_AB=t['AbilitiesJson'];_UAB=t['UnitAbilitiesJson'];_sm={}
for _u,_a,_n in ((1183,2013154,'Blood Wolves'),(1185,2013220,'Falcons')):
    ok(str(U[_u]['HUDName']).startswith(_n) and [r['AbilityId'] for r in _UAB.values() if r['UnitId']==_u]==[_a] and _AB[_a]['IsSmoke'] and _AB[_a]['SmokeAmmunitionQuantity']==4,(_n,'smoke ability'))
    ok(sorted({r['UnitId'] for r in _UAB.values() if r['AbilityId']==_a})==[_u],(_n,'ability not shared'))
    g.put('AbilitiesJson',_a,{'SmokeAmmunitionQuantity':1});_sm[f'{_u} {_n}']=[4,1]
rec['sf_smoke']=_sm
# ---------- J-5 and J-6W 10 HP (Osama 15 Nov 2026 03:2x PST: "J-5 and J-6 10 hp"). Both used vanilla armour row 334 (20 HP), shared with
# unit 512; they get their own copy at 10 HP, and any of their loadouts that names row 334 points at the copy.
_AR=t['ArmorsJson'];_UA=t['UnitArmorsJson']
ok([U[1089]['HUDName'],U[1091]['HUDName']]==['J-5','J-6W'] and all([r['ArmorId'] for r in _UA.values() if r['UnitId']==u]==[334] for u in (1089,1091)) and _AR[334]['MaxHealthPoints']==20,'J-5/J-6W armour 334')
_na=g.add('ArmorsJson',_AR[334],{'MaxHealthPoints':10})
for r in [r for r in _UA.values() if r['UnitId'] in (1089,1091)]:g.put('UnitArmorsJson',r['Id'],{'ArmorId':_na})
_jo=[o for o in O.values() if M.get(o.get('ModificationId'),{}).get('UnitId') in (1089,1091) and o.get('ArmorId')==334]
for o in _jo:g.put('OptionsJson',o['Id'],{'ArmorId':_na})
ok(_AR[334]['MaxHealthPoints']==20 and all([r['ArmorId'] for r in _UA.values() if r['UnitId']==u]==[_na] for u in (1089,1091)),'J-5/J-6W on 10 HP copy, row 334 unchanged')
rec['j5_j6_hp']={'units':[1089,1091],'armor':[334,_na],'hp':[20,10],'options_repointed':[o['Id'] for o in _jo]}
# ---------- Blood Wolves CH-901 laze (Osama 15 Nov 2026 03:1x PST: "Laze for Blood wolves CH-901 sends the missile out of the map").
# Ammo 2018448 was a laser-guided cruise missile (trajectory 200) with no seeker; no vanilla munition combines those. It now uses the
# vanilla laser-guided missile profile of the Hellfire (trajectory 110, laser seeker 100) with its seeker reaching its full 700 m range.
# Speed, burn time, damage and range are unchanged. Theory from the data only: not yet seen in a game.
_A=t['AmmunitionsJson'];ok(_A[2018448]['Name']=='PLA Blood Wolves NLOS missile' and _A[2018448]['TrajectoryType']==200 and _A[2018448]['LaserGuided'] and _A[2018448]['Seeker']==0,'CH-901 ammo')
ok(sorted({r['UnitId'] for r in WA.values() if r['AmmunitionId']==2018448})==[1183],'CH-901 only on Blood Wolves')
g.put('AmmunitionsJson',2018448,{'TrajectoryType':110,'Seeker':100,'MaxSeekerDistance':700.0});rec['ch901_laze']={'ammunition':2018448,'trajectory':[200,110],'seeker':[0,100],'max_seeker_distance':[300,700]}
# ---------- CH-901 icon (Osama 15 Nov 2026 03:58 PST: "CH-901 icon changed to match the QN-202 icon"). Launcher 2018447 showed the vanilla
# Javelin icon; it now uses the QN-202 launcher icon. Both missiles already use FA_PLA_AMMO_ATGM.
ok(W[2018447]['HUDName']=='CH-901' and W[2018447]['HUDIcon']=='INF_JAVELIN' and W[2014236]['HUDName']=='QN-202' and W[2014236]['HUDIcon']=='FA_PLA_WP_QN202','CH-901 / QN-202 icons')
ok(_A[2018448]['HUDIcon']==_A[2014237]['HUDIcon']=='FA_PLA_AMMO_ATGM','CH-901 / QN-202 missile icons')
g.put('WeaponsJson',2018447,{'HUDIcon':'FA_PLA_WP_QN202'});rec['ch901_icon']={'weapon':2018447,'hud_icon':['INF_JAVELIN','FA_PLA_WP_QN202']}
# ---------- J-36 CAP loadouts (Osama 15 Nov 2026 03:2x PST: "J-36 Heavy CAP 8x P-21 and 8x PL-16, Long rang ecap, removed"; "Just stick to fewer
# pylons but more ammo"; 03:35 PST: "J-36 heavy CAP is 4x PL-21 and then 8x PL-16, 4x PL-17 and then 8x PL-16 on the mixed cap but that's now 230").
# Su-57 body: pylons 1-6 bays, 7-8 wingtips. Long-range CAP 31063 goes. A new PL-16 x4 mount (copy of the PL-16 x2 mount, own weapon, 4 rounds)
# sits on pylons 1-2 of both loadouts (8x PL-16).
#   Heavy CAP 24393 (was 4x PL-17, 4x PL-16, 4x PL-21 on 7 pylons): + PL-21 mount 2016475 on 4-5, 2 rounds each (4x PL-21). Cost 255 unchanged.
#   Mixed CAP 31064 (was 8x PL-17, 6x PL-16 on 6 pylons, 255): + PL-17 x4 mount 2016481 on 4-5, 2 rounds each (4x PL-17). Cost 230.
# The PL-21 and PL-17 weapons are in no other J-36 loadout once 31063 goes; the J-50 shares the PL-21 mount with its own rounds row (1), unchanged.
_j36=929;_jm={m['Id'] for m in M.values() if m.get('UnitId')==_j36};_jo={o['Id']:o for o in O.values() if o.get('ModificationId') in _jm}
def _sl(o):return {k:o.get(f'Turret{k}Id') for k in range(21) if o.get(f'Turret{k}Id')}
ok(U[_j36]['HUDName']=='J-36' and _jo[24393]['UIName']=='Heavy CAP (4x PL-17, 4x PL-16, 4x PL-21)' and _jo[24393]['IsDefault'] and str(_jo[31063]['UIName']).startswith('Long-range CAP') and not _jo[31063]['IsDefault'],'J-36 CAP loadouts')
ok(_jo[31064]['UIName']=='Mixed CAP (8x PL-17, 6x PL-16)' and _jo[31064]['Cost']==255 and _jo[24393]['Cost']==255,'J-36 Mixed CAP 31064')
ok(all(any(r['UnitId']==_j36 and r['TurretId']==x for r in TU.values()) for x in (2018021,2016475,2016481)),'J-36 PL-16 x2, PL-21 and PL-17 mounts')
_tw16=[r for r in TW.values() if r['TurretId']==2018021];ok([r['WeaponId'] for r in _tw16]==[2018018] and [r['WeaponId'] for r in TW.values() if r['TurretId']==2016475]==[2016476] and [r['WeaponId'] for r in TW.values() if r['TurretId']==2016481]==[2016482],'mount weapons')
_q={r['WeaponId']:r for r in WA.values() if r['UnitId']==_j36};ok(_q[2018018]['Quantity']==2 and _q[2016476]['Quantity']==1 and _q[2016482]['Quantity']==4,'J-36 PL-16 x2 / PL-21 / PL-17 rounds')
ok(sorted({r['UnitId'] for r in TU.values() if r['TurretId']==2016475})==[_j36,944],'PL-21 mount on J-36 and J-50 (rounds are per unit)')
g.remove('OptionsJson',31063)
ok(sorted(i for i,o in O.items() if i in _jo and 2016475 in _sl(o).values())==[24393] and sorted(i for i,o in O.items() if i in _jo and 2016481 in _sl(o).values())==[24393,31064],'PL-21 only in Heavy CAP, PL-17 x4 only in the two CAPs')
_w16=g.add('WeaponsJson',W[2018018],{'Name':W[2018018]['Name']+' x4'});_t16=g.add('TurretsJson',TJ[2018021],{'Name':'PLA air pylon PL-16 x4'})
g.add('TurretWeaponsJson',_tw16[0],{'TurretId':_t16,'WeaponId':_w16})
g.add('TurretUnitsJson',next(r for r in TU.values() if r['UnitId']==_j36 and r['TurretId']==2018021),{'TurretId':_t16})
g.add('WeaponAmmunitionsJson',_q[2018018],{'WeaponId':_w16,'Quantity':4})
g.put('WeaponAmmunitionsJson',_q[2016476]['Id'],{'Quantity':2});g.put('WeaponAmmunitionsJson',_q[2016482]['Id'],{'Quantity':2})
_e={f'Turret{k}Id':160 for k in range(1,9)}
g.put('OptionsJson',24393,{'UIName':'Heavy CAP (4x PL-21, 8x PL-16)',**_e,'Turret1Id':_t16,'Turret2Id':_t16,'Turret4Id':2016475,'Turret5Id':2016475})
g.put('OptionsJson',31064,{'UIName':'Mixed CAP (4x PL-17, 8x PL-16)','Cost':230,**_e,'Turret1Id':_t16,'Turret2Id':_t16,'Turret4Id':2016481,'Turret5Id':2016481})
ok(sorted((k,v) for k,v in _sl(O[24393]).items() if v!=160)==[(1,_t16),(2,_t16),(4,2016475),(5,2016475)],'J-36 Heavy CAP pylons')
ok(sorted((k,v) for k,v in _sl(O[31064]).items() if v!=160)==[(1,_t16),(2,_t16),(4,2016481),(5,2016481)] and O[31064]['Cost']==230,'J-36 Mixed CAP pylons and cost')
_q2={r['WeaponId']:r['Quantity'] for r in WA.values() if r['UnitId']==_j36};ok(_q2[_w16]==4 and _q2[2016476]==2 and _q2[2016482]==2,'J-36 rounds: PL-16 x4, PL-21 x2, PL-17 x2')
ok([r['Quantity'] for r in WA.values() if r['UnitId']==944 and r['WeaponId']==2016476]==[1],'J-50 PL-21 rounds unchanged')
rec['j36_cap']={'removed_option':31063,'new_pl16_x4':{'weapon':_w16,'turret':_t16},
 'heavy_cap':{'option':24393,'was':'4x PL-17, 4x PL-16, 4x PL-21 (7 pylons)','now':'8x PL-16 (pylons 1-2), 4x PL-21 (4-5)','cost':255},
 'mixed_cap':{'option':31064,'was':'8x PL-17, 6x PL-16 (6 pylons)','now':'8x PL-16 (pylons 1-2), 4x PL-17 (4-5)','cost':[255,230]}}
# ---------- J-35 / J-31 Light SEAD 4x PL-15, 2x LD-8A (Osama 15 Nov 2026 03:2x PST: "J-35/31 Light SEAD 4x PL-15 and 2x LD-8A"; "Just stick to
# fewer pylons but more ammo"). Options 24657 (J-35 921) and 24660 (J-31 1251) were 2x LD-8A (pylons 1-2) and 2x PL-15 (3, 6). Same pylons;
# the PL-15 weapon 2017966 (only on this Light SEAD mount 2017965) carries 2 rounds per pylon. Cost stays 125 (to confirm with Osama).
for _u,_oi in ((921,24657),(1251,24660)):
    _o=O[_oi];ok(_o['UIName']=='Light SEAD' and O[_oi]['ModificationId'] in {m['Id'] for m in M.values() if m.get('UnitId')==_u},(_u,'Light SEAD option'))
    ok(_sl(_o)=={1:2017961,2:2017961,3:2017965,4:160,5:160,6:2017965,7:160,8:160},(_u,'Light SEAD pylons'))
    _um={m['Id'] for m in M.values() if m.get('UnitId')==_u}
    ok([o['Id'] for o in O.values() if o.get('ModificationId') in _um and 2017965 in _sl(o).values()]==[_oi] and [r['WeaponId'] for r in TW.values() if r['TurretId']==2017965]==[2017966],(_u,'PL-15 mount only in Light SEAD'))
    _r=[r for r in WA.values() if r['UnitId']==_u and r['WeaponId']==2017966];ok(len(_r)==1 and _r[0]['Quantity']==1,(_u,'PL-15 1 round'))
    g.put('WeaponAmmunitionsJson',_r[0]['Id'],{'Quantity':2});g.put('OptionsJson',_oi,{'UIName':'Light SEAD (4x PL-15, 2x LD-8A)'})
rec['light_sead_j35_j31']={'options':[24657,24660],'was':'2x LD-8A, 2x PL-15','now':'2x LD-8A, 4x PL-15 (2 per pylon on 3 and 6)','cost':125}
# ---------- JRVG-1 move speed 65 (Osama 15 Nov 2026 03:30 PST: "reduce its move speed to 65"). Its own mobility row 2009941 (only on 952) had
# road 100, off-road 55; road goes to 65. Off-road (55), reverse, turn and acceleration are unchanged. No JRVG-1 option overrides mobility.
_MB=t['MobilityJson'];_UP=t['UnitPropulsionsJson']
ok(U[952]['HUDName']=='JRVG-1' and [r['MobilityId'] for r in _UP.values() if r['UnitId']==952]==[2009941] and sorted(r['UnitId'] for r in _UP.values() if r['MobilityId']==2009941)==[952],'JRVG-1 own mobility row')
ok(_MB[2009941]['MaxSpeedRoad']==100.0 and _MB[2009941]['MaxCrossCountrySpeed']==55.0,'JRVG-1 speeds 100/55')
ok(not [o for o in O.values() if M.get(o.get('ModificationId'),{}).get('UnitId')==952 and o.get('MobilityId')],'no JRVG-1 mobility option')
g.put('MobilityJson',2009941,{'MaxSpeedRoad':65.0});rec['jrvg1_speed']={'unit':952,'mobility':2009941,'road':[100,65],'off_road':55}
# ---------- J-36 loadouts normalised (Osama 15 Nov 2026 03:4x PST: "Standoff strike: 4x PL-16, 4x PL-17, 4x KD-88 +220 / Heavy SEAD: 4x PL-16,
# 4x PL-17 / Light Strike: 4x PL-16, 4x PL-17, 4x LS-6 500kg +230 / Heavy Strike: +220 pts / I need you to normalize the loadouts on the J-36. Make
# anti armor +0 and then all loadouts are lowered by 165 points"). The three listed loadouts trade their 4x PL-15C (pylons 1, 2, 3, 6) for the
# PL-16 x2 mount 2018021 on 1-2 (4x PL-16) and the PL-17 mount 2016481 on 3 and 6 (2 rounds each, 4x PL-17); pylons 4-5 keep KD-88 x2 (4),
# LD-8A x3 (6) and LS-6 500kg x2 (4). Heavy strike and Anti-armor keep their weapons. Normalised: every option -165 and the base +165
# (215 -> 380), so each loadout's total is the price set above; Anti-armor is +0.
_jo={o['Id']:o for o in O.values() if o.get('ModificationId') in _jm}
ok(sorted(_jo)==[24393,24604,24606,24608,24664,31028,31064] and not [o for o in O.values() if o.get('ReplaceUnitId')==_j36] and U[_j36]['Cost']==215,'J-36 loadouts, no swap rows, base 215')
_new={24606:('Standoff strike (4x PL-16, 4x PL-17, 4x KD-88)',2017707,220),24664:('Heavy SEAD (4x PL-16, 4x PL-17, 6x LD-8A)',2018028,235),24604:('Light strike (4x PL-16, 4x PL-17, 4x LS-6 500kg)',2017670,230)}
for _oi,(_n,_ag,_c) in _new.items():
    _s=_sl(_jo[_oi]);ok(_s[1]==_s[2] and _s[3]==_s[6] and _s[4]==_s[5]==_ag and [W[r['WeaponId']]['HUDName'] for r in TW.values() if r['TurretId']==_s[1]]==['PL-15C'],(_oi,'PL-15C on 1-3, 6 and the strike mount on 4-5'))
    g.put('OptionsJson',_oi,{'UIName':_n,'Cost':_c,'Turret1Id':2018021,'Turret2Id':2018021,'Turret3Id':2016481,'Turret6Id':2016481})
_q3={r['WeaponId']:r['Quantity'] for r in WA.values() if r['UnitId']==_j36};ok((_q3[2018018],_q3[2016482],_q3[2017708],_q3[2018029],_q3[2017671])==(2,2,2,3,2),'J-36 rounds per pylon: PL-16 x2, PL-17, KD-88, LD-8A, LS-6')
ok(_jo[31028]['Cost']==175 and _jo[24608]['Cost']==165 and _jo[24393]['Cost']==255 and _jo[31064]['Cost']==230,'J-36 other costs')
g.put('OptionsJson',31028,{'Cost':220})
for _oi in _jo:g.put('OptionsJson',_oi,{'Cost':O[_oi]['Cost']-165})
g.put('Units',_j36,{'Cost':380})
_cost={_oi:O[_oi]['Cost'] for _oi in sorted(_jo)};ok(_cost=={24393:90,24604:65,24606:55,24608:0,24664:70,31028:55,31064:65} and min(_cost.values())==0,('J-36 normalised costs',_cost))
rec['j36_normalised']={'base':[215,380],'options':{O[k]['UIName']:v for k,v in _cost.items()},'totals':{O[k]['UIName']:380+v for k,v in _cost.items()}}
# ---------- Bombs drop all their rounds (Osama 15 Nov 2026 03:4x PST: "MD-22 you can't queue up 2 LT6 lgb, when I do it only drops 1").
# Every vanilla bomb weapon (trajectory 400, 136 rows) has MagazineSize >= its rounds per pylon. 16 FA China bomb weapons had MagazineSize 1
# (or 6/2) under 2-9 rounds, so a second queued drop waited on a reload. MagazineSize now = the largest rounds-per-pylon of each weapon.
# Theory from the data only: not yet seen in a game.
_AM=t['AmmunitionsJson'];_bomb={}
for r in WA.values():
    if _AM[r['AmmunitionId']].get('TrajectoryType')==400 and W[r['WeaponId']]['MagazineSize']<r['Quantity']:_bomb[r['WeaponId']]=max(_bomb.get(r['WeaponId'],0),r['Quantity'])
ok(len(_bomb)==16 and {2018243,2018252,2018483}<=set(_bomb) and not set(_bomb)&native['WeaponsJson'],('FA bomb weapons with a short magazine',sorted(_bomb)))
_brec={}
for _w,_n in sorted(_bomb.items()):
    _brec[f"{_w} {W[_w]['HUDName']}"]=[W[_w]['MagazineSize'],_n];g.put('WeaponsJson',_w,{'MagazineSize':_n})
ok(not [r for r in WA.values() if _AM[r['AmmunitionId']].get('TrajectoryType')==400 and W[r['WeaponId']]['MagazineSize']<r['Quantity']],'every bomb magazine holds its rounds')
rec['bomb_magazines']=_brec
# ---------- China rifle tiers (Lateralus 15 Nov 2026 03:31 / 03:48 PST): T0 QBZ-95, T1 QBZ-191, T2 QMK (new, M4A1 Mod. II clone), T3 QBZ-192
# (URG-I clone, above). "Go with option A for QBZ-95. For QMK, give it to Airborne, Assault Raiders, Pathfinders, Snipers, Falcons, QLU-11 Team,
# and Taishan Eagles. Give QBZ-192 to Thunder Gods". Only armory cards (DisplayInArmory) by those names; none of them has a swap loadout.
_A=t['AmmunitionsJson'];_SM=t['SquadMembersJson'];_SW=t['SquadWeaponsJson']
Q95,Q95A,Q191,Q191A,Q192,Q192A=2012205,2012206,2003998,2003999,2013087,2013088
# T0 QBZ-95, option A: damage 1.2 -> 0.9 and 8.16 -> 4.0 s between shots (every rifle uses 4.0 s; the tier is in the damage).
ok(W[Q95]['HUDName']=='QBZ-95' and W[Q95]['TimeBetweenBurstsMin']==8.16==W[Q95]['TimeBetweenBurstsMax'] and _A[Q95A]['Damage']==1.2,'QBZ-95 now')
ok({k for k in set(W[Q95])|set(W[Q191]) if W[Q95].get(k)!=W[Q191].get(k)}<={'Id','Name','HUDName','HUDIcon','ModelFileName','AudioPreset','TimeBetweenBurstsMin','TimeBetweenBurstsMax'},'QBZ-95 = QBZ-191 but fire rate')
# Weapon 2014501 is shown as "QBZ-191" (iron sights) but fires QBZ-95 round 2012206; its 4 reserve squads move to the QBZ-191 round, which has
# the same stats today, so they stay tier 1 and do not drop to 0.9 under a QBZ-191 name.
_ri=[r for r in WA.values() if r['WeaponId']==2014501];ok(W[2014501]['HUDName']=='QBZ-191' and len(_ri)==4 and all(r['AmmunitionId']==Q95A for r in _ri),'2014501 on the QBZ-95 round')
ok({k for k in set(_A[Q95A])|set(_A[Q191A]) if _A[Q95A].get(k)!=_A[Q191A].get(k)}<={'Id','Name','HUDName','HUDIcon'},'QBZ-95 round = QBZ-191 round today')
for _r in _ri:g.put('WeaponAmmunitionsJson',_r['Id'],{'AmmunitionId':Q191A})
ok({r['WeaponId'] for r in WA.values() if r['AmmunitionId']==Q95A}=={Q95},'QBZ-95 round only on the QBZ-95')
g.put('WeaponsJson',Q95,{'TimeBetweenBurstsMin':4.0,'TimeBetweenBurstsMax':4.0});g.put('AmmunitionsJson',Q95A,{'Damage':0.9})
# T2 QMK: a QBZ-191 row with an M4A1 Mod. II round (weapon 70 = QBZ-191 in every stat; round 357 differs from the QBZ-191 round only in
# damage 1.5). QBZ-191 icon and model until it has its own.
ok({k for k in set(W[70])|set(W[Q191]) if W[70].get(k)!=W[Q191].get(k)}<={'Id','Name','HUDName','HUDIcon','ModelFileName','AudioPreset'},'Mod. II weapon = QBZ-191 weapon')
_d={k:_A[357][k] for k in _A[357] if k not in ('Id','Name','HUDName','HUDIcon','ModelFileName') and _A[Q191A].get(k)!=_A[357][k]};ok(_d=={'Damage':1.5},('Mod. II round vs QBZ-191 round',_d))
QMK=g.add('WeaponsJson',W[Q191],{'Name':'PLA infantry QMK','HUDName':'QMK'});QMKA=g.add('AmmunitionsJson',_A[Q191A],{'Name':'PLA infantry QMK ammunition','HUDName':'QMK ammunition',**_d})
def _swap(u,old,new,newa):
    ms=[m for m in _SM.values() if m['UnitId']==u and m['PrimaryWeaponId']==old];sw=[r for r in _SW.values() if r['UnitId']==u and r['WeaponId']==old];wa=[r for r in WA.values() if r['UnitId']==u and r['WeaponId']==old]
    ok(ms and len(sw)==1 and len(wa)==1 and not [r for r in WA.values() if r['UnitId']==u and r['WeaponId']==new],(u,'rifle rows',len(ms),len(sw),len(wa)))
    for m in ms:g.put('SquadMembersJson',m['Id'],{'PrimaryWeaponId':new})
    g.put('SquadWeaponsJson',sw[0]['Id'],{'WeaponId':new});g.put('WeaponAmmunitionsJson',wa[0]['Id'],{'WeaponId':new,'AmmunitionId':newa})
    # Model entry: the old rifle's entry, or a leftover QBZ-191/QBZ-192 entry the squad no longer carries (Assault Raiders), now points at the new rifle.
    carried={x['PrimaryWeaponId'] for x in _SM.values() if x['UnitId']==u}
    es=[e for e in iw if e['unitId']==u and e['slot']=='primary' and e['weaponId'] in (Q191,Q192) and e['weaponId'] not in carried]
    ok(len(es)==1 and es[0]['file']=='w_qbz191.fam' and not [e for e in iw if e['unitId']==u and e['weaponId']==new],(u,'rifle model entry'))
    es[0]['weaponId']=new
    return {'unit':u,'name':U[u]['HUDName'],'from':old,'to':new,'men':len(ms),'rounds':wa[0]['Quantity']}
_cards={'Airborne 空降兵':Q191,'Assault Raiders 突击队':Q192,'Pathfinders 先遣队':Q191,'Snipers 狙击组':Q191,'Falcons 猎鹰':Q192,'QLU-11 Team':Q191,'Taishan Eagles 泰山雄鹰':Q191}
_qmk=[]
for _n,_old in _cards.items():
    _us=[u for u,x in U.items() if x.get('CountryId')==4 and x.get('HUDName')==_n and x.get('DisplayInArmory') is not False]
    ok(len(_us)==(2 if _n=='Snipers 狙击组' else 1),(_n,_us))
    for _u in _us:_qmk.append(_swap(_u,_old,QMK,QMKA))
ok(U[1143]['HUDName'].startswith('Thunder Gods'),'Thunder Gods 1143');_tg=_swap(1143,Q191,Q192,Q192A)
rec['china_rifle_tiers']={'T0_qbz95':{'weapon':Q95,'ammunition':Q95A,'damage':[1.2,0.9],'time_between_shots':[8.16,4.0]},
 'qbz191_iron_sights_2014501':{'units':[r['UnitId'] for r in _ri],'ammunition':[Q95A,Q191A],'note':'stays tier 1'},
 'T2_qmk':{'weapon':QMK,'ammunition':QMKA,'clone_of':[70,357],'damage':1.5,'squads':_qmk},'T3_qbz192_thunder_gods':_tg}
# ---------- CM-501GA only on the Z-21 (Osama 15 Nov 2026 04:0x PST: "CM-501GA removed from all helos EXCEPT Z-21"). dev.11 took it off the Z-19s.
# Loadout "Heavy anti-armor (CM-501GA)" goes from Z-10 978, Z-10 1239 and Z-10U 1270, with their CM-501GA mounts and ammo rows. Their PL-9
# mounts stay unused. The Z-21 1104 keeps "Multirole (4x CM-501GA, 14x FS-70A)".
_CM={i for i,w in W.items() if w.get('HUDName')=='CM-501GA'};_TJ=t['TurretsJson']
def _tur(o):return {o.get(f'Turret{k}Id') for k in range(21)}-{0,None}
def _cmt(tid):return any(r['TurretId']==tid and r['WeaponId'] in _CM for r in TW.values())
_carry=sorted({r['UnitId'] for r in WA.values() if r['WeaponId'] in _CM});ok(_carry==[978,1104,1239,1270] and all(U[u]['CountryId']==4 for u in _carry),('CM-501GA carriers',_carry))
_cmrec={}
for _u,_oi in ((978,24501),(1239,24507),(1270,31087)):
    _mids={m['Id'] for m in M.values() if m.get('UnitId')==_u};_opts=[o for o in O.values() if o.get('ModificationId') in _mids and any(_cmt(x) for x in _tur(o))]
    ok([o['Id'] for o in _opts]==[_oi] and O[_oi]['UIName']=='Heavy anti-armor (CM-501GA)' and not O[_oi]['IsDefault'],(_u,'one CM-501GA loadout'))
    g.remove('OptionsJson',_oi)
    _tu=[r for r in TU.values() if r['UnitId']==_u and _cmt(r['TurretId'])]
    for r in _tu:
        g.remove('TurretUnitsJson',r['Id'])
        if not any(x['TurretId']==r['TurretId'] for x in TU.values()):
            for w in [w for w in TW.values() if w['TurretId']==r['TurretId']]:g.remove('TurretWeaponsJson',w['Id'])
            g.remove('TurretsJson',r['TurretId'])
    _wa=[r for r in WA.values() if r['UnitId']==_u and r['WeaponId'] in _CM]
    for r in _wa:g.remove('WeaponAmmunitionsJson',r['Id'])
    _left=[o for o in O.values() if o.get('ModificationId') in _mids]
    ok(not any(_cmt(x) for o in _left for x in _tur(o)) and all(any(r['UnitId']==_u and r['TurretId']==x for r in TU.values()) for o in _left for x in _tur(o)),(_u,'no CM-501GA left, loadouts keep their mounts'))
    _cmrec[f"{_u} {U[_u]['HUDName']}"]={'option_removed':_oi,'mounts_removed':len(_tu),'ammo_rows_removed':len(_wa)}
ok(sorted({r['UnitId'] for r in WA.values() if r['WeaponId'] in _CM})==[1104],'CM-501GA only on the Z-21')
rec['cm501ga_z21_only']=_cmrec
# ---------- Gunship pods FS-90, not FS-70A (Osama 15 Nov 2026 04:0x PST: "Swap FS-70 for FS-90 on the rocket pods of helos for the gunship
# loadouts"). The gunships are the Z-20KA 914 and Z-20T 1245 (MH-60M DAP pylons). Z-20KA: its four FS-70A pod weapons (only on 914) become
# FS-90 in place, as the dev.104 Z-20T copies (FS-90 name, icon, burst, ammo 2018819); "32x FS-90" +45 and "16x FS-90" +20, the Z-20T prices.
# Z-20T: its FS-70A loadouts 24571/24575 and their FS-70A mounts go; its FS-90 loadouts 31067/31068 stay.
_F90=W[2018820];_F90A=2018819;ok(_F90['HUDName']=='FS-90' and {r['AmmunitionId'] for r in WA.values() if r['WeaponId']==2018820}=={_F90A},'FS-90 template')
_z20={}
for _oi,_ui,_c in ((24562,'32x FS-90',45),(24566,'16x FS-90',20)):
    _o=O[_oi];ok(M[_o['ModificationId']]['UnitId']==914 and _o['UIName']==_ui.replace('FS-90','FS-70A'),(_oi,'Z-20KA FS-70A loadout'))
    for _tid in sorted({_o.get(f'Turret{k}Id') for k in (2,3,4,5)}-{0,None,2009262,160}):
        _tw=[r for r in TW.values() if r['TurretId']==_tid];ok(len(_tw)==1 and W[_tw[0]['WeaponId']]['HUDName']=='FS-70A',(_tid,'FS-70A pod'))
        _w=_tw[0]['WeaponId'];_wa=[r for r in WA.values() if r['WeaponId']==_w]
        ok([r['UnitId'] for r in _wa]==[914] and sorted({r['UnitId'] for r in TU.values() if r['TurretId']==_tid})==[914] and [r['TurretId'] for r in TW.values() if r['WeaponId']==_w]==[_tid],(_tid,'pod only on the Z-20KA'))
        g.put('WeaponsJson',_w,{'Name':W[_w]['Name'].replace('FS-70A','FS-90'),'HUDName':'FS-90','HUDIcon':_F90['HUDIcon'],'NormalGroundAttackBurst':_F90['NormalGroundAttackBurst']})
        g.put('WeaponAmmunitionsJson',_wa[0]['Id'],{'AmmunitionId':_F90A});g.put('TurretsJson',_tid,{'Name':_TJ[_tid]['Name'].replace('DAGR','FS-90')});_z20[_tid]=_w
    g.put('OptionsJson',_oi,{'UIName':_ui,'Cost':_c})
ok(len(_z20)==4,'four Z-20KA pods')
_z20t=[]
for _oi,_twin in ((24571,31067),(24575,31068)):
    _o=O[_oi];ok(M[_o['ModificationId']]['UnitId']==1245 and 'FS-70A' in _o['UIName'] and 'FS-90' in O[_twin]['UIName'] and not _o['IsDefault'],(_oi,'Z-20T FS-70A loadout with an FS-90 twin'))
    _pods=sorted({_o.get(f'Turret{k}Id') for k in (2,3,4,5)}-{0,None,2009262,160});g.remove('OptionsJson',_oi)
    for _tid in _pods:
        ok(not [o for o in O.values() if _tid in _tur(o)],(_tid,'FS-70A pod in no other loadout'))
        _tw=[r for r in TW.values() if r['TurretId']==_tid];_w=_tw[0]['WeaponId'];ok(W[_w]['HUDName']=='FS-70A' and [r['UnitId'] for r in WA.values() if r['WeaponId']==_w]==[1245],(_tid,'Z-20T FS-70A pod'))
        for r in [r for r in TU.values() if r['TurretId']==_tid]:g.remove('TurretUnitsJson',r['Id'])
        for r in _tw:g.remove('TurretWeaponsJson',r['Id'])
        g.remove('TurretsJson',_tid)
        for r in [r for r in WA.values() if r['WeaponId']==_w]:g.remove('WeaponAmmunitionsJson',r['Id'])
        _z20t.append(_tid)
ok(not [r for r in WA.values() if r['UnitId'] in (914,1245) and W[r['WeaponId']]['HUDName']=='FS-70A'],'no FS-70A on the Z-20 gunships')
rec['gunship_fs90']={'z20ka_pods_to_fs90':_z20,'z20ka_costs':{'32x FS-90':[35,45],'16x FS-90':[15,20]},'z20t_removed_options':[24571,24575],'z20t_removed_mounts':_z20t}
# ---------- FS-90 ignore cover = APKWS (Osama 15 Nov 2026 04:0x PST: "it should have same ignore cover as APKWS"). FS-90 ammo 2018819 (every
# FS-90 helo) 0 -> 0.6, the vanilla APKWS pod round (ammo 45).
ok(_A[45]['HUDName']=='APKWS' and _A[45]['IgnoreCover']==0.6 and _A[_F90A]['HUDName']=='FS-90' and _A[_F90A]['IgnoreCover']==0.0,'APKWS / FS-90 ignore cover')
g.put('AmmunitionsJson',_F90A,{'IgnoreCover':0.6});rec['fs90_ignore_cover']={'ammunition':_F90A,'ignore_cover':[0.0,0.6],'as':45}
# ---------- JRVG-1 12 HP (Osama 15 Nov 2026 04:1x PST: "JRVG 12 hp"). Its own armour row 2009939 (only on 952, no option uses it): 14 -> 12.
_AR2=t['ArmorsJson'];_UA2=t['UnitArmorsJson']
ok([r['ArmorId'] for r in _UA2.values() if r['UnitId']==952]==[2009939] and sorted(r['UnitId'] for r in _UA2.values() if r['ArmorId']==2009939)==[952] and not [o for o in O.values() if o.get('ArmorId')==2009939] and _AR2[2009939]['MaxHealthPoints']==14,'JRVG-1 own armour row, 14 HP')
g.put('ArmorsJson',2009939,{'MaxHealthPoints':12});rec['jrvg1_hp']={'unit':952,'armor':2009939,'hp':[14,12]}
# ---------- Incendiary launchers and Green Berets Flash smoke (Lateralus 15 Nov 2026 04:08 PST: "Change Green Berets Flash smoke from 4 -> 1.
# Nerf damage on M202 Flash and FHJ-02 from 8 -> 5, Nerf damage on MRO-Z from 10 -> 7"). One round per launcher, so every squad that carries it
# changes: M202 550 (Green Berets Flash, Mech. Engineers CQC), FHJ-02 2013058 (FHJ-02 Incendiary Team, Thermobaric Team, Thunder Gods; the
# 1-damage FHJ-02 smoke round 2014407 is not changed), MRO-Z 522 (Ognemetchiki). Green Berets Flash is unit 470 (option 2053 "M202 Flash" on
# Green Berets 177); its smoke ability 2000611 "Sprint30 Smoke x4 Laser" is shared with 3 other squads, so 470 gets its own copy with 1 smoke.
_A=t['AmmunitionsJson'];AB=t['AbilitiesJson']
_inc={550:(698,8.0,5.0,'InfRocket 66 M202Flash Incendiary'),2013058:(2013057,8.0,5.0,'PLA infantry FHJ-02 0'),522:(668,10.0,7.0,'InfRocket 73 MROZ Incendiary')}
for _a,(_w,_o,_n,_nm) in _inc.items():
    ok(_A[_a]['Name']==_nm and _A[_a]['Damage']==_o and {r['WeaponId'] for r in WA.values() if r['AmmunitionId']==_a}=={_w},('incendiary round',_a))
    g.put('AmmunitionsJson',_a,{'Damage':_n})
ok(O[2053]['ReplaceUnitId']==470 and U[470]['HUDName'].strip()=='Green Berets' and any(r['UnitId']==470 and r['WeaponId']==698 for r in WA.values()),'Green Berets Flash 470')
_gr=[r for r in UAB.values() if r['UnitId']==470 and r['AbilityId']==2000611];_gs=sorted(r['UnitId'] for r in UAB.values() if r['AbilityId']==2000611)
ok(len(_gr)==1 and _gs==[136,276,470,527] and AB[2000611]['IsSmoke'] and AB[2000611]['SmokeAmmunitionQuantity']==4,('Green Berets Flash smoke 2000611',_gs))
ok(not [o for o in O.values() if 2000611 in (o.get('Ability1Id'),o.get('Ability2Id'),o.get('Ability3Id'))],'2000611 not on an option')
_ga=g.add('AbilitiesJson',AB[2000611],{'Name':'Sprint30 Smoke x1 Laser Green Berets Flash','SmokeAmmunitionQuantity':1});g.put('UnitAbilitiesJson',_gr[0]['Id'],{'AbilityId':_ga})
ok(AB[2000611]['SmokeAmmunitionQuantity']==4 and [r['AbilityId'] for r in UAB.values() if r['UnitId']==470 and AB[r['AbilityId']].get('IsSmoke')]==[_ga],'470 own smoke row, 2000611 unchanged')
rec['incendiary_and_gb_flash_smoke']={'damage':{'M202 Flash 550':[8,5],'FHJ-02 2013058':[8,5],'MRO-Z 522':[10,7]},'green_berets_flash':{'unit':470,'ability':[2000611,_ga],'smoke':[4,1],'2000611_kept_for':[136,276,527]}}
# ---------- FS-70A ignore cover 60% too (Osama 15 Nov 2026 04:08 PST: "all FS-70 and FS-90 are 60% ignore cover"). FS-70A ammo 2017197, every
# FS-70A helo: 0 -> 0.6, as FS-90 above and the vanilla APKWS pod round.
ok(_A[2017197]['HUDName']=='FS-70A' and _A[2017197]['IgnoreCover']==0.0 and [a['Id'] for a in _A.values() if str(a.get('HUDName','')).startswith('FS-')]==[2017197,2018819],'FS rocket rounds')
g.put('AmmunitionsJson',2017197,{'IgnoreCover':0.6});rec['fs70a_ignore_cover']={'ammunition':2017197,'ignore_cover':[0.0,0.6]}
# ---------- CTL-181 NLOS laze (Osama 15 Nov 2026 04:08 PST: "the Laze fix for the Blood wolves, we need it for the CTL-181 NLOS. We had this issue
# before"). 0.8.0-dev.25 turned its laser guidance off because lasing sent the missile haywire; it was left a cruise missile (trajectory 200)
# with no seeker, the same row the CH-901 had. It gets the CH-901 fix: the vanilla laser-guided missile profile of the Hellfire K/M
# (trajectory 110, laser seeker 100, LaserGuided on) with the seeker reaching its full 900 m range. Speed, burn time, damage and range unchanged.
# Theory from the data only: not yet seen in a game.
_c=_A[2018321];ok(_c['Name']=='PLA CTL-181 NLOS missile' and (_c['TrajectoryType'],_c['Seeker'],_c['LaserGuided'],_c['GroundRange'])==(200,0,False,900.0) and {r['UnitId'] for r in WA.values() if r['AmmunitionId']==2018321}=={1054},'CTL-181 NLOS missile, only on 1054')
ok((_A[164]['TrajectoryType'],_A[164]['Seeker'],_A[164]['LaserGuided'])==(110,100,True),'vanilla AGM-114K laser profile')
g.put('AmmunitionsJson',2018321,{'TrajectoryType':110,'Seeker':100,'LaserGuided':True,'MaxSeekerDistance':900.0})
rec['ctl181_laze']={'ammunition':2018321,'trajectory':[200,110],'seeker':[0,100],'laser_guided':[False,True],'max_seeker_distance':[300,900]}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(AN,assign);IW.write_text(json.dumps(iw,indent=2,ensure_ascii=False)+'\n');save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
